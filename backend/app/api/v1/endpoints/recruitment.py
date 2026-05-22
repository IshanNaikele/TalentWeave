import json
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form
from typing import Optional
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User
from app.models.recruitment import Candidate, Job, Application, ApplicationStatus
from app.services.parser import extract_text_from_pdf
from app.services.llm_gateway import extract_resume_data, evaluate_candidate
from app.schemas.recruitment import JobCreateResponse
from app.services.scheduler_service import register_screening_deadline
from typing import Optional

router = APIRouter()

@router.post("/upload-resume", status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    job_id: int = 1,    
    db: Session = Depends(get_db),
):
    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted."
        )

    try:
        # Step 1: Extract raw text from PDF
        file_bytes = await file.read()
        raw_text = await extract_text_from_pdf(file_bytes)

        if not raw_text.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract text from the PDF. File may be image-based."
            )

        # Step 2: Send to LLM for structured extraction
        try:
            parsed_data = await extract_resume_data(raw_text)
            extracted_skills = json.dumps(parsed_data.skills)
            seniority = parsed_data.seniority_level
            full_name = parsed_data.full_name
            email = parsed_data.email
            phone = parsed_data.phone

        except Exception as llm_error:
            print(f"⚠️ LLM parsing failed: {llm_error}")
            # Graceful fallback
            full_name = "Unknown"
            email = f"unknown_{file.filename}@talentweave.com"
            phone = None
            extracted_skills = json.dumps([])
            seniority = "failed_parsing"

        # Step 3: Check for duplicate candidate
        existing = db.query(Candidate).filter(Candidate.email == email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Candidate with email {email} already exists."
            )

        # Step 4: Save to database
        candidate = Candidate(
            full_name=full_name,
            email=email,
            phone=phone,
            raw_resume_text=raw_text[:4000],
            extracted_skills=extracted_skills,
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        
        # Auto-create application
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            application = Application(
                job_id=job_id,
                candidate_id=candidate.id,
                status=ApplicationStatus.new
            )
            db.add(application)
            db.commit()
            db.refresh(application)
            application_id = application.id
        else:
            application_id = None

        return {
            "message": "Resume uploaded and parsed successfully.",
            "candidate_id": candidate.id,
             "application_id": application_id,
            "full_name": candidate.full_name,
            "email": candidate.email,
            "seniority_level": seniority,
            "skills": json.loads(extracted_skills),
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )
    

@router.post("/applications/{application_id}/evaluate", status_code=status.HTTP_200_OK)
async def evaluate_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["operations_team"]))
):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")

    candidate = db.query(Candidate).filter(Candidate.id == application.candidate_id).first()
    job = db.query(Job).filter(Job.id == application.job_id).first()

    if not candidate or not job:
        raise HTTPException(status_code=404, detail="Candidate or Job not found.")

    try:
        skills = json.loads(candidate.extracted_skills or "[]")

        evaluation = await evaluate_candidate(
            candidate_skills=skills,
            job_requirements=job.requirements,
            candidate_name=candidate.full_name,
            job_title=job.title
        )

        application.ai_match_score = evaluation.match_score
        application.screening_questions = json.dumps([
            {
                "question": q.question,
                "options": q.options,
                "correct_answer": q.correct_answer
            }
            for q in evaluation.screening_questions
        ])
        application.status = ApplicationStatus.screening
        db.commit()

        return {
            "message": "Evaluation complete.",
            "application_id": application_id,
            "candidate_name": candidate.full_name,
            "job_title": job.title,
            "match_score": evaluation.match_score,
            "skill_gaps": evaluation.skill_gaps,
            "strength_areas": evaluation.strength_areas,
            "evaluation_summary": evaluation.evaluation_summary,
            "screening_questions": [
                {
                    "question": q.question,
                    "options": q.options,
                    "correct_answer": q.correct_answer
                }
                for q in evaluation.screening_questions
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}"
        )
    

@router.get("/candidates", status_code=status.HTTP_200_OK)
def get_all_candidates(
    db: Session = Depends(get_db),
    job_id: Optional[int] = None,
    current_user: User = Depends(require_role(["operations_team"]))
):
    result = []

    if job_id:
        applications = db.query(Application).filter(
            Application.job_id == job_id
        ).all()

        for application in applications:
            candidate = db.query(Candidate).filter(
                Candidate.id == application.candidate_id
            ).first()
            if not candidate:
                continue
            result.append({
                "candidate_id": candidate.id,
                "full_name": candidate.full_name,
                "email": candidate.email,
                "extracted_skills": candidate.extracted_skills,
                "application_id": application.id,
                "status": application.status.value if application.status else None,
                "ai_match_score": application.ai_match_score,
                "meet_url": application.meet_url,
                "job_id": application.job_id,
            })
    else:
        candidates = db.query(Candidate).all()
        for candidate in candidates:
            application = db.query(Application).filter(
                Application.candidate_id == candidate.id
            ).order_by(Application.id.desc()).first()
            result.append({
                "candidate_id": candidate.id,
                "full_name": candidate.full_name,
                "email": candidate.email,
                "extracted_skills": candidate.extracted_skills,
                "application_id": application.id if application else None,
                "status": application.status.value if application else None,
                "ai_match_score": application.ai_match_score if application else None,
                "meet_url": application.meet_url if application else None,
                "job_id": application.job_id if application else None,
            })

    return result

@router.post("/jobs/create", response_model=JobCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    title: str = Form(...),
    department: str = Form(...),
    requirements: str = Form(...),
    difficulty: str = Form(default="Medium"),
    num_questions: int = Form(default=10),
    pass_threshold: int = Form(default=70),
    filter_mode: str = Form(default="fixed_threshold"),
    percentile_cutoff: float = Form(default=5.0),
    focus_skills: Optional[str] = Form(default=None),
    screening_duration_minutes: int = Form(...),
    include_assignment: bool = Form(default=False),
    assignment_duration_minutes: Optional[int] = Form(default=None),
    recruiter_email: str = Form(...),
    assignment_pdf: Optional[UploadFile] = File(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["operations_team"]))
):
    # Guard: if assignment included, PDF must be uploaded
    if include_assignment and assignment_pdf is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Assignment PDF is required when include_assignment is True."
        )

    # Guard: PDF must be a PDF file
    if assignment_pdf and not assignment_pdf.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignment file must be a PDF."
        )

    # Compute screening deadline
    screening_deadline = datetime.now() + timedelta(minutes=screening_duration_minutes)

    # Create job row first to get the ID
    job = Job(
        title=title,
        department=department,
        requirements=requirements,
        difficulty=difficulty,
        num_questions=num_questions,
        pass_threshold=pass_threshold,
        filter_mode=filter_mode,
        percentile_cutoff=percentile_cutoff,
        focus_skills=focus_skills,
        screening_deadline=screening_deadline,
        include_assignment=include_assignment,
        public_link_active=True,
        status="screening_open",
        recruiter_email=recruiter_email,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Save assignment PDF if provided
    if include_assignment and assignment_pdf:
        assignments_dir = Path("backend/data/assignments")
        assignments_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = assignments_dir / f"{job.id}.pdf"
        pdf_bytes = await assignment_pdf.read()
        pdf_path.write_bytes(pdf_bytes)
        job.assignment_pdf_path = str(pdf_path)

    # Compute assignment deadline if applicable
    if include_assignment and assignment_duration_minutes:
        job.assignment_deadline = screening_deadline + timedelta(minutes=assignment_duration_minutes)

    db.commit()
    db.refresh(job)

    # Arm the scheduler
    register_screening_deadline(job_id=job.id, run_at=screening_deadline)

    # Build candidate portal URL
    candidate_portal_url = f"http://localhost:8000/static/candidate_exam.html?job_id={job.id}"

    return JobCreateResponse(
        job_id=job.id,
        candidate_portal_url=candidate_portal_url,
        screening_deadline=screening_deadline,
        message=f"Job created successfully. Share the portal URL with candidates."
    )



@router.get("/jobs", status_code=status.HTTP_200_OK)
def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["operations_team"]))
):
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    return [
        {
            "job_id": j.id,
            "title": j.title,
            "department": j.department,
            "status": j.status,
            "include_assignment": j.include_assignment,
            "screening_deadline": j.screening_deadline,
            "created_at": j.created_at,
        }
        for j in jobs
    ]


@router.get("/jobs/{job_id}/exam-attempts", status_code=status.HTTP_200_OK)
def get_exam_attempts(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["operations_team"]))
):
    from app.models.recruitment import ExamAttempt
    attempts = (
        db.query(ExamAttempt)
        .join(Application, ExamAttempt.application_id == Application.id)
        .filter(Application.job_id == job_id)
        .all()
    )
    result = []
    for a in attempts:
        candidate = db.query(Candidate).filter(Candidate.id == a.candidate_id).first()
        result.append({
            "candidate_name": candidate.full_name if candidate else "Unknown",
            "candidate_email": candidate.email if candidate else "",
            "score": a.score,
            "passed": a.passed,
            "attempted_at": a.attempted_at,
            "application_id": a.application_id,
        })
    return result


@router.get("/jobs/{job_id}/assignment-submissions", status_code=status.HTTP_200_OK)
def get_assignment_submissions(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["operations_team"]))
):
    from app.models.recruitment import AssignmentSubmission
    submissions = (
        db.query(AssignmentSubmission)
        .join(Application, AssignmentSubmission.application_id == Application.id)
        .filter(Application.job_id == job_id)
        .all()
    )
    result = []
    for s in submissions:
        candidate = db.query(Candidate).filter(Candidate.id == s.candidate_id).first()
        result.append({
            "candidate_name": candidate.full_name if candidate else "Unknown",
            "candidate_email": candidate.email if candidate else "",
            "github_link": s.github_link,
            "linkedin": s.linkedin,
            "deployment_url": s.deployment_url,
            "notes": s.notes,
            "submitted_at": s.submitted_at,
            "application_id": s.application_id,
        })
    return result


@router.post("/send-meet/{application_id}", status_code=status.HTTP_200_OK)
def send_meet_invite(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["operations_team"]))
):
    from app.services.email_service import send_meet_link_email
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")

    candidate = db.query(Candidate).filter(Candidate.id == application.candidate_id).first()
    job = db.query(Job).filter(Job.id == application.job_id).first()

    if not candidate or not job:
        raise HTTPException(status_code=404, detail="Candidate or job not found.")

    meet_url = application.meet_url or f"https://meet.google.com/talentweave-{job.id}-{candidate.id:03d}"

    send_meet_link_email(
        candidate_name=candidate.full_name,
        candidate_email=candidate.email,
        job_title=job.title,
        meet_url=meet_url
    )

    return {"message": f"Meet invite sent to {candidate.email}"}
import json
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User
from app.models.recruitment import Candidate, Job, Application, ApplicationStatus
from app.services.parser import extract_text_from_pdf
from app.services.llm_gateway import extract_resume_data, evaluate_candidate

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
    current_user: User = Depends(require_role(["operations_team"]))
):
    candidates = db.query(Candidate).all()
    result = []

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
        })

    return result
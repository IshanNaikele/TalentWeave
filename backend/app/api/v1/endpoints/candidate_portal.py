import json
import base64
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.recruitment import (
    Job, Candidate, Application, ApplicationStatus,
    ExamAttempt, AssignmentSubmission
)
from app.services.parser import extract_text_from_pdf
from app.services.llm_gateway import (
    extract_resume_data,
    generate_personalized_questions,
    grade_candidate_answers
)
from app.schemas.candidate_portal import (
    StartExamRequest, StartExamResponse, QuestionItem,
    SubmitExamRequest, SubmitExamResponse,
    SubmitAssignmentRequest, SubmitAssignmentResponse
)

router = APIRouter()


@router.get("/job/{job_id}")
def get_job_info(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if not job.public_link_active:
        raise HTTPException(status_code=403, detail="This job link is no longer active.")
    if job.status != "screening_open":
        raise HTTPException(status_code=403, detail="This job is no longer accepting applications.")
    if job.screening_deadline and datetime.now() > job.screening_deadline:
        raise HTTPException(status_code=403, detail="The screening deadline has passed.")

    return {
        "job_id": job.id,
        "title": job.title,
        "department": job.department,
        "difficulty": job.difficulty,
        "num_questions": job.num_questions,
        "screening_deadline": job.screening_deadline
    }


@router.post("/jobs/{job_id}/start-exam", response_model=StartExamResponse)
async def start_exam(
    job_id: int,
    payload: StartExamRequest,
    db: Session = Depends(get_db)
):
    # Guard 1: job exists and is open
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if not job.public_link_active or job.status != "screening_open":
        raise HTTPException(status_code=403, detail="This job is no longer accepting applications.")
    if job.screening_deadline and datetime.now() > job.screening_deadline:
        raise HTTPException(status_code=403, detail="The screening deadline has passed.")

    # Guard 2: no duplicate application (same email + same job)
    existing_candidate = db.query(Candidate).filter(
        Candidate.email == payload.email
    ).first()
    if existing_candidate:
        existing_application = db.query(Application).filter(
            Application.candidate_id == existing_candidate.id,
            Application.job_id == job_id
        ).first()
        if existing_application:
            raise HTTPException(
                status_code=409,
                detail="You have already applied for this position."
            )

    # Step 1: Decode base64 PDF and extract text
    try:
        pdf_bytes = base64.b64decode(payload.resume_pdf_base64)
        raw_text = await extract_text_from_pdf(pdf_bytes)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Could not read PDF: {str(e)}"
        )

    # Step 2: Parse resume via LLM
    try:
        parsed = await extract_resume_data(raw_text)
        extracted_skills = json.dumps(parsed.skills)
    except Exception:
        extracted_skills = json.dumps([])

    # Step 3: Create or reuse candidate row
    if existing_candidate:
        candidate = existing_candidate
    else:
        candidate = Candidate(
            full_name=payload.name,
            email=payload.email,
            phone=payload.phone,
            raw_resume_text=raw_text[:4000],
            extracted_skills=extracted_skills,
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)

    # Step 4: Create application row
    application = Application(
        job_id=job_id,
        candidate_id=candidate.id,
        status=ApplicationStatus.screening
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    # Step 5: Generate personalized questions
    try:
        focus_skills = job.focus_skills
        questions_full = await generate_personalized_questions(
            jd_text=job.requirements,
            resume_text=raw_text,
            num_questions=job.num_questions,
            difficulty=job.difficulty,
            focus_skills=focus_skills
        )
    except Exception as e:
        db.delete(application)
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Question generation failed: {str(e)}"
        )

    # Step 6: Store full questions (with correct_option) in application
    application.questions = json.dumps(questions_full)
    db.commit()

    # Step 7: Strip correct_option before sending to frontend
    sanitized = [
        QuestionItem(
            question_id=q["question_id"],
            question_text=q["question_text"],
            options=q["options"],
            bucket=q["bucket"]
        )
        for q in questions_full
    ]

    return StartExamResponse(
        questions=sanitized,
        candidate_id=candidate.id,
        application_id=application.id,
        screening_deadline=job.screening_deadline
    )


@router.post("/test/submit", response_model=SubmitExamResponse)
def submit_exam(
    payload: SubmitExamRequest,
    db: Session = Depends(get_db)
):
    # Fetch candidate by email
    candidate = db.query(Candidate).filter(
        Candidate.email == payload.candidate_email
    ).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    # Fetch application for this candidate + job
    application = db.query(Application).filter(
        Application.candidate_id == candidate.id,
        Application.job_id == payload.job_id
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")

    # Guard: no duplicate submission
    existing_attempt = db.query(ExamAttempt).filter(
        ExamAttempt.application_id == application.id
    ).first()
    if existing_attempt:
        raise HTTPException(
            status_code=409,
            detail="Exam already submitted for this application."
        )

    # Fetch job for pass_threshold
    job = db.query(Job).filter(Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    # Fetch answer key from application
    if not application.questions:
        raise HTTPException(
            status_code=500,
            detail="No questions found for this application."
        )
    questions_with_answers = json.loads(application.questions)

    # Grade the submission
    result = grade_candidate_answers(
        questions_with_answers=questions_with_answers,
        submitted_answers=payload.answers
    )

    score = result["score"]
    passed = score >= job.pass_threshold

    # Create ExamAttempt row
    attempt = ExamAttempt(
        application_id=application.id,
        candidate_id=candidate.id,
        answers=json.dumps(payload.answers),
        score=score,
        passed=passed,
        grading_report=json.dumps(result["breakdown"])
    )
    db.add(attempt)

    # Update application status
    application.status = ApplicationStatus.interview if passed else ApplicationStatus.rejected
    application.ai_match_score = float(score)

    db.commit()

    message = (
        f"Congratulations! You scored {score}/100 and passed. "
        f"You will receive an email with next steps after the deadline."
        if passed else
        f"Your score of {score}/100 did not meet the pass threshold of {job.pass_threshold}. "
        f"Thank you for your time."
    )

    return SubmitExamResponse(
        final_score=score,
        passed=passed,
        pass_threshold=job.pass_threshold,
        message=message
    )


@router.post("/assignment/submit", response_model=SubmitAssignmentResponse)
def submit_assignment(
    payload: SubmitAssignmentRequest,
    db: Session = Depends(get_db)
):
    # Guard 1: job must be in assignment_open status
    job = db.query(Job).filter(Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.status != "assignment_open":
        raise HTTPException(
            status_code=403,
            detail="Assignment submission is not open for this job."
        )

    # Guard 2: candidate must exist and have passed exam
    candidate = db.query(Candidate).filter(
        Candidate.email == payload.email
    ).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    application = db.query(Application).filter(
        Application.candidate_id == candidate.id,
        Application.job_id == payload.job_id
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")

    passed_attempt = db.query(ExamAttempt).filter(
        ExamAttempt.application_id == application.id,
        ExamAttempt.passed == True
    ).first()
    if not passed_attempt:
        raise HTTPException(
            status_code=403,
            detail="Only candidates who passed the screening exam can submit assignments."
        )

    # Guard 3: no duplicate submission
    existing = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.application_id == application.id
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Assignment already submitted."
        )

    # Create submission row
    submission = AssignmentSubmission(
        application_id=application.id,
        candidate_id=candidate.id,
        github_link=payload.github_id,
        linkedin=payload.linkedin,
        deployment_url=payload.action_link,
        notes=payload.notes
    )
    db.add(submission)
    db.commit()

    return SubmitAssignmentResponse(
        message="Assignment submitted successfully. The recruiter will review after the submission window closes."
    )
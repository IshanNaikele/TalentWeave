from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.recruitment import Application, ApplicationStatus, Job, Candidate
from app.models.user import User, UserRole
from app.schemas.onboarding import OnboardingConfigSchema
from app.core.security import hash_password

DEPARTMENT_TO_ROLE = {
    "Engineering": UserRole.software_engineer,
    "Sales": UserRole.sales_team,
    "Operations": UserRole.operations_team,
}

DEPARTMENT_TO_LEVEL = {
    "Engineering": "junior",
    "Sales": "junior",
    "Operations": "coordinator",
}

def execute_candidate_hire_transition(
    application_id: int,
    config: OnboardingConfigSchema,
    db: Session
) -> dict:

    # Step 1 — Fetch application
    application = db.query(Application).filter(
        Application.id == application_id
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found."
        )

    # Step 2 — Verify it hasn't already been hired or rejected
    if application.status == ApplicationStatus.hired:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This candidate has already been hired."
        )

    if application.status == ApplicationStatus.rejected:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This application was rejected and cannot be hired."
        )

    # Step 3 — Fetch linked candidate and job
    candidate = db.query(Candidate).filter(
        Candidate.id == application.candidate_id
    ).first()

    job = db.query(Job).filter(
        Job.id == application.job_id
    ).first()

    if not candidate or not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Linked candidate or job record not found."
        )

    # Step 4 — Map department to role
    assigned_role = DEPARTMENT_TO_ROLE.get(job.department)
    if not assigned_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown department '{job.department}'. Cannot assign role."
        )

    # Step 5 — Build corporate email
    if config.corporate_email:
        corporate_email = config.corporate_email
    else:
        first_name = candidate.full_name.split()[0].lower()
        dept_slug = job.department.lower()
        corporate_email = f"{first_name}.{dept_slug}@talentweave.com"

    # Step 6 — Check email conflict
    existing_user = db.query(User).filter(
        User.email == corporate_email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A user with email {corporate_email} already exists."
        )

    try:
        # Step 7 — Atomic transaction: update application + create user
        application.status = ApplicationStatus.hired

        new_user = User(
            full_name=candidate.full_name,
            email=corporate_email,
            hashed_password=hash_password(config.temporary_password),
            role=assigned_role,
            level=DEPARTMENT_TO_LEVEL.get(job.department, "junior"),
            dept=job.department,
        )

        db.add(new_user)
        db.flush()  # Assigns new_user.id before commit

        db.commit()
        db.refresh(new_user)

        return {
            "new_user_id": new_user.id,
            "corporate_email": corporate_email,
            "assigned_role": assigned_role.value,
            "full_name": candidate.full_name,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transaction failed and was rolled back: {str(e)}"
        )
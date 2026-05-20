from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import require_role
from app.models.user import User
from app.models.onboarding import OnboardingPlan, OnboardingTask
from app.schemas.onboarding import OnboardingConfigSchema, HireResponseSchema
from app.services.lifecycle_bridge import execute_candidate_hire_transition
from app.services.onboarding_agent import generate_automated_onboarding_plan


router = APIRouter()


@router.post(
    "/hire/{application_id}",
    response_model=HireResponseSchema,
    status_code=status.HTTP_200_OK
)

async def hire_candidate(
    application_id: int,
    config: OnboardingConfigSchema = None,
    db: Session = Depends(get_db),
     current_user: User = Depends(require_role(["operations_team"]))
):
    if config is None:
        config = OnboardingConfigSchema()

    # Step 7 — Execute lifecycle transition
    result = execute_candidate_hire_transition(
        application_id=application_id,
        config=config,
        db=db
    )
    
    # Step 8 — Immediately trigger onboarding plan generation
    try:
        tasks_generated = await generate_automated_onboarding_plan(
            user_id=result["new_user_id"],
            db=db
        )
    except Exception as e:
        print(f"⚠️ Onboarding generation failed: {e}")
        tasks_generated = 0


    return HireResponseSchema(
        message=f"Candidate successfully hired and corporate identity provisioned.",
        new_user_id=result["new_user_id"],
        corporate_email=result["corporate_email"],
        assigned_role=result["assigned_role"],
        full_name=result["full_name"],
        onboarding_tasks_generated=tasks_generated
    )

@router.get("/plan/{user_id}", status_code=status.HTTP_200_OK)
def get_onboarding_plan(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        ["operations_team", "software_engineer", "sales_team"]
    ))
):
    plan = db.query(OnboardingPlan).filter(
        OnboardingPlan.user_id == user_id
    ).first()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No onboarding plan found for user {user_id}."
        )

    tasks = db.query(OnboardingTask).filter(
        OnboardingTask.plan_id == plan.id
    ).order_by(OnboardingTask.due_day).all()

    return {
        "plan_id": plan.id,
        "user_id": user_id,
        "total_tasks": len(tasks),
        "tasks": [
            {
                "task_id": t.id,
                "title": t.title,
                "description": t.description,
                "due_day": t.due_day,
                "status": t.status
            }
            for t in tasks
        ]
    }


@router.patch("/task/{task_id}/complete", status_code=status.HTTP_200_OK)
def complete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        ["operations_team", "software_engineer", "sales_team"]
    ))
):
    task = db.query(OnboardingTask).filter(
        OnboardingTask.id == task_id
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found."
        )

    task.status = "completed"
    db.commit()

    return {
        "message": f"Task '{task.title}' marked as completed.",
        "task_id": task_id,
        "status": "completed"
    }


@router.get("/users", status_code=status.HTTP_200_OK)
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["operations_team"]))
):
    from app.models.user import User as UserModel
    users = db.query(UserModel).all()
    return [
        {
            "user_id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role.value,
            "level": u.level,
            "dept": u.dept
        }
        for u in users
    ]
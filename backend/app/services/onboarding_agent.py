import os
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from app.models.user import User, UserRole
from app.models.onboarding import OnboardingPlan, OnboardingTask
from app.schemas.onboarding import OnboardingPlanGenerationSchema
from app.services.rag_engine import search_by_role

load_dotenv()

ROLE_TO_DISPLAY = {
    UserRole.software_engineer: "Software Engineer",
    UserRole.sales_team: "Sales Team Member",
    UserRole.operations_team: "Operations Coordinator",
}

ROLE_TO_RAG_KEY = {
    UserRole.software_engineer: "software_engineer",
    UserRole.sales_team: "sales_team",
    UserRole.operations_team: "sales_team",  # fallback to sales docs for ops
}


def get_llm():
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.3-70b-versatile",
        temperature=0
    )


async def generate_automated_onboarding_plan(
    user_id: int,
    db: Session
) -> int:

    # Step 1 — Fetch the newly created user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found."
        )

    role_display = ROLE_TO_DISPLAY.get(user.role, "Employee")
    rag_key = ROLE_TO_RAG_KEY.get(user.role, "sales_team")
    level = user.level or "junior"

    # Step 2 — Guarded FAISS RAG lookup
    query = f"onboarding setup tasks for {role_display}"
    try:
        rag_results = search_by_role(query=query, role=rag_key, k=6)
        context_text = "\n\n".join([doc.page_content for doc in rag_results])
    except Exception as e:
        print(f"⚠️ RAG lookup failed: {e}")
        context_text = f"Standard onboarding process for {role_display}."

    if not context_text.strip():
        context_text = f"Standard onboarding process for {role_display}."

    # Step 3 — Build the prompt
    prompt = f"""
You are an automated HR Operations Supervisor at TalentWeave, a B2B SaaS company.
A new employee has just been hired and needs a personalized onboarding plan.

## NEW EMPLOYEE PROFILE:
- Full Name: {user.full_name}
- Role: {role_display}
- Seniority Level: {level.capitalize()}
- Department: {user.dept or "General"}

## COMPANY KNOWLEDGE BASE CONTEXT:
The following text is extracted directly from TalentWeave's internal corporate policy documents.
Use ONLY this content to build the onboarding tasks. Do not hallucinate tools or processes not mentioned here.

---
{context_text}
---

## YOUR TASK GENERATION INSTRUCTIONS:

1. Generate exactly 6 onboarding tasks tailored to a {level.capitalize()} {role_display}.
2. Tasks must be ordered logically — foundational setup tasks first, then progressively complex ones.
3. Match complexity to seniority:
   - Junior: include highly descriptive step-by-step instructions.
   - Mid: assume basic tool familiarity, focus on integration steps.
   - Senior: focus on architectural understanding and team collaboration.
4. Assign realistic due_day values spread across the first week:
   - Day 1: Immediate account and access setup tasks.
   - Day 3: Tool configuration and environment verification tasks.
   - Day 5: First deliverable or shadow session tasks.
   - Day 7: Independent contribution or review tasks.
5. Every task title must be action-oriented. Start with a verb. Example: "Configure", "Complete", "Review", "Submit".
6. Every task description must contain explicit, implementable steps — not vague suggestions.

## EXPECTED OUTPUT FORMAT:
Return a structured JSON object with a "tasks" array containing exactly 6 task objects.
Each task must have: title (string), description (string), due_day (integer).

Now generate the personalized onboarding plan. Return nothing else.
"""

    # Step 4 — Call LLM with structured output
    llm = get_llm()
    structured_llm = llm.with_structured_output(OnboardingPlanGenerationSchema)
    result = structured_llm.invoke(prompt)

    # Step 5 — Save OnboardingPlan to database
    plan = OnboardingPlan(user_id=user_id)
    db.add(plan)
    db.flush()  # Get plan.id before commit

    # Step 6 — Save each task as individual row
    for task_item in result.tasks:
        task = OnboardingTask(
            plan_id=plan.id,
            title=task_item.title,
            description=task_item.description,
            due_day=task_item.due_day,
            status="pending"
        )
        db.add(task)

    db.commit()
    print(f"✅ Generated {len(result.tasks)} onboarding tasks for user {user_id} ({user.full_name})")
    return len(result.tasks)
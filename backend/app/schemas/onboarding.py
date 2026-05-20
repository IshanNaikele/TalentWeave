from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

class OnboardingConfigSchema(BaseModel):
    corporate_email: Optional[str] = None
    temporary_password: str = "Welcome@123"

class HireResponseSchema(BaseModel):
    message: str
    new_user_id: int
    corporate_email: str
    assigned_role: str
    full_name: str
    onboarding_tasks_generated: int
    class Config:
        from_attributes = True


class TaskGenerationItem(BaseModel):
    title: str = Field(description="Short, action-oriented task name. Example: 'Clone the Backend Repository'")
    description: str = Field(description="Detailed step-by-step implementation instructions for completing this task.")
    due_day: int = Field(description="The day number by which this task must be completed. Example: 1, 3, 5, 7.")

class OnboardingPlanGenerationSchema(BaseModel):
    tasks: List[TaskGenerationItem] = Field(
        description="A complete ordered list of onboarding tasks tailored to the employee's role and seniority."
    )
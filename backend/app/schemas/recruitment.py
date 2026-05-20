from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
class ResumeExtractionSchema(BaseModel):
    full_name: str = Field(description="Full name of the candidate as mentioned in the resume.")
    email: str = Field(description="Primary email address of the candidate.")
    phone: Optional[str] = Field(description="Phone number of the candidate if mentioned.")
    skills: List[str] = Field(description="List of all technical and professional skills mentioned in the resume.")
    experience_years: int = Field(description="Calculate the total cumulative years of professional experience mentioned.")
    seniority_level: str = Field(description="Classify the candidate as one of: Junior, Mid, Senior based on their experience years and role history.")

class MCQQuestionSchema(BaseModel):
    question: str = Field(description="The technical screening question targeting a specific skill gap.")
    options: List[str] = Field(description="Exactly 4 answer options labeled A, B, C, D.")
    correct_answer: str = Field(description="The single correct option label: A, B, C, or D.")

class CandidateEvaluationSchema(BaseModel):
    match_score: float = Field(description="Overall match score from 0 to 100 based on skills alignment.")
    skill_gaps: List[str] = Field(description="List of critical skills required by the job but missing from the candidate.")
    strength_areas: List[str] = Field(description="List of skills where the candidate strongly matches the job requirements.")
    evaluation_summary: str = Field(description="Short 2-3 sentence justification explaining the match score.")
    screening_questions: List[MCQQuestionSchema] = Field(description="Exactly 3 MCQ questions targeting the top 3 skill gaps.")

class CandidateResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str]
    skills: List[str]
    experience_years: int
    seniority_level: str
    message: str

    class Config:
        from_attributes = True

class JobCreateResponse(BaseModel):
    job_id: int
    candidate_portal_url: str
    screening_deadline: datetime
    message: str
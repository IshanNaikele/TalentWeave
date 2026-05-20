from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime


class QuestionItem(BaseModel):
    question_id: str
    question_text: str
    options: Dict[str, str]
    bucket: str
    # correct_option is intentionally excluded — never sent to frontend


class StartExamRequest(BaseModel):
    job_id: int
    name: str
    email: str
    phone: str
    resume_pdf_base64: str


class StartExamResponse(BaseModel):
    questions: List[QuestionItem]
    candidate_id: int
    application_id: int
    screening_deadline: datetime


class SubmitExamRequest(BaseModel):
    job_id: int
    candidate_email: str
    answers: Dict[str, str]  # question_id → chosen letter


class SubmitExamResponse(BaseModel):
    final_score: int
    passed: bool
    pass_threshold: int
    message: str


class SubmitAssignmentRequest(BaseModel):
    job_id: int
    name: str
    email: str
    phone: str
    github_id: str
    linkedin: str
    action_link: Optional[str] = None
    notes: Optional[str] = None


class SubmitAssignmentResponse(BaseModel):
    message: str
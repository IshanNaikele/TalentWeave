import enum
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, Enum, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class ApplicationStatus(str, enum.Enum):
    new = "new"
    screening = "screening"
    interview = "interview"
    hired = "hired"
    rejected = "rejected"

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    department = Column(String, nullable=False)
    requirements = Column(Text, nullable=False)
    difficulty           = Column(String, default="Medium")
    num_questions        = Column(Integer, default=10)
    pass_threshold       = Column(Integer, default=70)
    filter_mode          = Column(String, default="fixed_threshold")
    percentile_cutoff    = Column(Float, default=5.0)
    focus_skills         = Column(Text, nullable=True)
    screening_deadline   = Column(DateTime, nullable=True)
    include_assignment   = Column(Boolean, default=False)
    assignment_pdf_path  = Column(String, nullable=True)
    assignment_deadline  = Column(DateTime, nullable=True)
    public_link_active   = Column(Boolean, default=True)
    status               = Column(String, default="screening_open")
    recruiter_email      = Column(String, nullable=True)
    created_at           = Column(DateTime(timezone=True), server_default=func.now())

    applications           = relationship("Application", back_populates="job")
   
class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String, nullable=True)
    raw_resume_text = Column(Text, nullable=True)
    extracted_skills = Column(Text, nullable=True)  # JSON stringified
    created_at       = Column(DateTime(timezone=True), server_default=func.now())

    applications           = relationship("Application", back_populates="candidate")
    exam_attempts          = relationship("ExamAttempt", back_populates="candidate")
    assignment_submissions = relationship("AssignmentSubmission", back_populates="candidate")

   
class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.new)
    ai_match_score = Column(Float, nullable=True)
    screening_questions = Column(Text, nullable=True)  # JSON stringified
    questions            = Column(Text, nullable=True)
    interview_slot_start = Column(DateTime, nullable=True)
    interview_slot_end   = Column(DateTime, nullable=True)
    meet_url             = Column(String, nullable=True)
    calendar_event_id    = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    job = relationship("Job", back_populates="applications")
    candidate = relationship("Candidate", back_populates="applications")
    exam_attempt           = relationship("ExamAttempt", back_populates="application", uselist=False)
    assignment_submission  = relationship("AssignmentSubmission", back_populates="application", uselist=False)

class ExamAttempt(Base):
    __tablename__ = "exam_attempts"

    id              = Column(Integer, primary_key=True, index=True)
    application_id  = Column(Integer, ForeignKey("applications.id"), unique=True, nullable=False)
    candidate_id    = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    answers         = Column(Text, nullable=False)
    score           = Column(Integer, nullable=False)
    passed          = Column(Boolean, nullable=False)
    grading_report  = Column(Text, nullable=True)
    attempted_at    = Column(DateTime(timezone=True), server_default=func.now())

    application = relationship("Application", back_populates="exam_attempt")
    candidate   = relationship("Candidate", back_populates="exam_attempts")
     


class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"

    id             = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), unique=True, nullable=False)
    candidate_id   = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    github_link    = Column(String, nullable=False)
    linkedin       = Column(String, nullable=False)
    deployment_url = Column(String, nullable=True)
    notes          = Column(Text, nullable=True)
    submitted_at   = Column(DateTime(timezone=True), server_default=func.now())

    application = relationship("Application", back_populates="assignment_submission")
    candidate   = relationship("Candidate", back_populates="assignment_submissions")
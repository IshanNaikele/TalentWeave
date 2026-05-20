import enum
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, Enum, DateTime
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
    status = Column(String, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    applications = relationship("Application", back_populates="job")

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String, nullable=True)
    raw_resume_text = Column(Text, nullable=True)
    extracted_skills = Column(Text, nullable=True)  # JSON stringified
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    applications = relationship("Application", back_populates="candidate")

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.new)
    ai_match_score = Column(Float, nullable=True)
    screening_questions = Column(Text, nullable=True)  # JSON stringified
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    job = relationship("Job", back_populates="applications")
    candidate = relationship("Candidate", back_populates="applications")
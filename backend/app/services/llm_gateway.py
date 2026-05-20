import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from app.schemas.recruitment import ResumeExtractionSchema, CandidateEvaluationSchema


load_dotenv()

def get_llm():
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.3-70b-versatile",
        temperature=0
    )

async def extract_resume_data(raw_text: str) -> ResumeExtractionSchema:
    truncated_text = raw_text[:4000]

    prompt = f"""
You are an elite-level AI Applicant Tracking System (ATS) built for a Series-B tech company.
Your sole responsibility is to parse raw resume text and return a precise, structured JSON object.

## YOUR STRICT OPERATING RULES:
1. Extract ONLY information that is explicitly stated in the resume text.
2. Never hallucinate, infer, or assume data that is not present.
3. Ignore all visual formatting artifacts, bullet symbols, page numbers, and layout noise.
4. For skills, extract every technical tool, programming language, framework, platform, and methodology mentioned anywhere in the resume.
5. For experience_years, calculate the TOTAL cumulative professional work experience in years as an integer. If months are mentioned, round to nearest year. If unclear, default to 0.
6. For seniority_level, classify strictly as:
   - "Junior" → 0 to 2 years of experience
   - "Mid" → 3 to 5 years of experience  
   - "Senior" → 6 or more years of experience
7. For phone, if no phone number is found, return null.
8. For email, if no email is found, return "not_found@talentweave.com".

## EXPECTED JSON OUTPUT FORMAT:
{{
    "full_name": "string — Full legal name of the candidate",
    "email": "string — Primary professional email address",
    "phone": "string or null — Phone number with country code if available",
    "skills": ["string", "string", "..."] — Complete flat list of every technical and professional skill mentioned,
    "experience_years": integer — Total cumulative years of professional experience,
    "seniority_level": "Junior | Mid | Senior — Based strictly on experience_years rule above"
}}

## EXAMPLE OF A CORRECT OUTPUT:
{{
    "full_name": "Rahul Sharma",
    "email": "rahul.sharma@gmail.com",
    "phone": "+91-9876543210",
    "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "React", "Git"],
    "experience_years": 4,
    "seniority_level": "Mid"
}}

## RAW RESUME TEXT TO PARSE:
---
{truncated_text}
---

Now extract and return the structured JSON object. Return nothing else.
"""

    llm = get_llm()
    structured_llm = llm.with_structured_output(ResumeExtractionSchema)
    result = structured_llm.invoke(prompt)
    return result


async def evaluate_candidate(
    candidate_skills: list,
    job_requirements: str,
    candidate_name: str,
    job_title: str
) -> CandidateEvaluationSchema:

    skills_text = ", ".join(candidate_skills)

    prompt = f"""
You are a rigorous, unbiased Senior Technical Interviewer and Talent Evaluation Specialist.
Your job is to evaluate a candidate's fit for a specific job opening and generate a personalized screening test.

## CANDIDATE PROFILE:
- Name: {candidate_name}
- Extracted Skills: {skills_text}

## JOB OPENING:
- Title: {job_title}
- Full Requirements:
{job_requirements[:2000]}

## YOUR EVALUATION INSTRUCTIONS:

### STEP 1 — MATCH SCORE:
Calculate a match_score from 0 to 100.
- 90 to 100: Candidate meets almost all requirements perfectly.
- 70 to 89: Strong match with minor gaps in secondary skills.
- 50 to 69: Moderate match, significant gaps in key areas.
- Below 50: Weak match, missing multiple critical requirements.

### STEP 2 — SKILL GAP ANALYSIS:
- List every critical skill explicitly required by the job that is completely absent from the candidate's profile.
- List the candidate's skills that directly match the job's core requirements as strength areas.

### STEP 3 — MCQ SCREENING TEST GENERATION:
- Identify the top 3 most critical skill gaps.
- For each gap, generate exactly 1 highly specific technical MCQ question.
- Each question must have exactly 4 options labeled: "A) ...", "B) ...", "C) ...", "D) ..."
- The correct answer must be either A, B, C, or D.
- Questions must test foundational understanding, not trivia.

## EXPECTED JSON OUTPUT FORMAT:
{{
    "match_score": float between 0 and 100,
    "skill_gaps": ["gap1", "gap2", "gap3", "..."],
    "strength_areas": ["strength1", "strength2", "..."],
    "evaluation_summary": "2-3 sentence justification of the match score and overall assessment.",
    "screening_questions": [
        {{
            "question": "Specific technical question targeting the skill gap",
            "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
            "correct_answer": "A"
        }}
    ]
}}

## EXAMPLE OF CORRECT OUTPUT:
{{
    "match_score": 72.5,
    "skill_gaps": ["FastAPI", "Docker", "AWS"],
    "strength_areas": ["Python", "PostgreSQL", "Git"],
    "evaluation_summary": "The candidate demonstrates solid Python and database fundamentals but lacks hands-on experience with modern API frameworks and cloud infrastructure. With targeted upskilling, they could reach full productivity within 3 months.",
    "screening_questions": [
        {{
            "question": "In FastAPI, which decorator is used to define an asynchronous POST endpoint?",
            "options": ["A) @app.post()", "B) @app.route()", "C) @app.create()", "D) @app.handle()"],
            "correct_answer": "A"
        }}
    ]
}}

Now perform the evaluation and return the structured JSON. Return nothing else.
"""

    llm = get_llm()
    structured_llm = llm.with_structured_output(CandidateEvaluationSchema)
    result = structured_llm.invoke(prompt)
    return result

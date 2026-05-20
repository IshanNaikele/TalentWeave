# TalentWeave — AI-Powered Talent Acquisition & Onboarding Platform

> TalentWeave is a full-stack AI-driven recruitment and onboarding platform that automates the entire hiring pipeline — from candidate screening, personalized exam generation, assignment rounds, interview scheduling, to employee onboarding — using LLMs, RAG, and automated email workflows.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Tech Stack](#tech-stack)
3. [Folder Structure](#folder-structure)
4. [File-by-File Explanation](#file-by-file-explanation)
5. [System Architecture & Flow](#system-architecture--flow)
6. [Database Schema](#database-schema)
7. [API Reference](#api-reference)
8. [Setup & Installation](#setup--installation)
9. [Demo Walkthrough](#demo-walkthrough)
10. [Known Issues & Limitations](#known-issues--limitations)

---

## Project Overview

TalentWeave eliminates manual recruitment overhead by providing:

- **Operations Team** — A Streamlit dashboard to create jobs, review candidates, hire, and manage onboarding.
- **Candidates** — A static HTML portal to take AI-generated personalized screening exams and submit assignments.
- **Employees** — A Streamlit workspace to view and complete their AI-generated onboarding plan.

The platform supports two hiring paths:
1. **Direct Interview Path** — Candidate passes exam → gets interview slot + Google Meet link via email.
2. **Assignment Path** — Candidate passes exam → receives assignment PDF via email → submits work → ops team reviews → hire decision.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI (Python) |
| Database | PostgreSQL + SQLAlchemy ORM |
| LLM Gateway | Groq API (`llama-3.3-70b-versatile`) |
| LLM Orchestration | LangChain |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` |
| Vector Store | FAISS (local) |
| PDF Parsing | pdfplumber |
| Email | Gmail SMTP + icalendar (ICS) |
| Scheduler | APScheduler (BackgroundScheduler) |
| Frontend Dashboard | Streamlit |
| Candidate Portal | Vanilla HTML + JavaScript |
| Auth | JWT (HS256) via python-jose |
| Password Hashing | bcrypt via passlib |

---

## Folder Structure

```
TALENTWEAVE/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py                     # JWT auth dependency, role enforcement
│   │   │   └── v1/
│   │   │       ├── api.py                  # Central router — wires all endpoint routers
│   │   │       └── endpoints/
│   │   │           ├── __init__.py
│   │   │           ├── auth.py             # POST /auth/login
│   │   │           ├── candidate_portal.py # Exam start, exam submit, assignment submit
│   │   │           ├── onboarding.py       # Hire, onboarding plan, task completion
│   │   │           └── recruitment.py      # Resume upload, job creation, candidate listing
│   │   │
│   │   ├── core/
│   │   │   ├── config.py                   # App settings, seed user config (Pydantic)
│   │   │   ├── database.py                 # SQLAlchemy engine, session, Base
│   │   │   └── security.py                 # JWT creation/decoding, bcrypt hashing
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py                 # Re-exports User, UserRole
│   │   │   ├── onboarding.py               # OnboardingPlan, OnboardingTask ORM models
│   │   │   ├── recruitment.py              # Job, Candidate, Application, ExamAttempt, AssignmentSubmission
│   │   │   └── user.py                     # User, UserRole ORM model
│   │   │
│   │   ├── schemas/
│   │   │   ├── auth.py                     # LoginRequest, TokenResponse
│   │   │   ├── candidate_portal.py         # Exam request/response schemas
│   │   │   ├── onboarding.py               # Hire response, task generation schemas
│   │   │   └── recruitment.py              # Resume extraction, evaluation, job creation schemas
│   │   │
│   │   └── services/
│   │       ├── email_service.py            # Gmail SMTP — interview, assignment, meet emails
│   │       ├── lifecycle_bridge.py         # Candidate → Employee transition logic
│   │       ├── llm_gateway.py              # All LLM calls — resume parse, evaluate, generate questions, grade
│   │       ├── onboarding_agent.py         # RAG + LLM — generates personalized onboarding plan
│   │       ├── parser.py                   # PDF text extraction via pdfplumber
│   │       ├── rag_engine.py               # FAISS vector store build, load, role-filtered search
│   │       └── scheduler_service.py        # APScheduler — deadline jobs, email dispatch, slot assignment
│   │
│   ├── data/
│   │   ├── assignments/                    # Uploaded assignment PDFs stored here (named {job_id}.pdf)
│   │   ├── company_policies/
│   │   │   ├── engineering_setup_guide.md  # RAG source — software engineer onboarding policy
│   │   │   └── sales_crm_playbook.md       # RAG source — sales team onboarding policy
│   │   └── vector_store/
│   │       ├── index.faiss                 # FAISS binary index
│   │       └── index.pkl                   # FAISS metadata (docstore + mappings)
│   │
│   ├── scripts/
│   │   ├── init_vector_store.py            # One-time script to build FAISS from policy docs
│   │   └── seed.py                         # Seeds 10 users + 3 jobs + onboarding plans into DB
│   │
│   ├── static/
│   │   ├── assignment_submit.html          # Candidate assignment submission form
│   │   ├── candidate_exam.html             # Candidate exam portal (entry + exam + results)
│   │   └── recruiter_panel.html            # (Empty — reserved)
│   │
│   ├── .env                                # Environment variables (not committed)
│   ├── google_service_account.json         # (Reserved — not actively used)
│   ├── main.py                             # FastAPI app entry point, middleware, lifespan
│   └── requirements.txt                    # Backend Python dependencies
│
├── frontend/
│   ├── utils/
│   │   └── api_client.py                   # All HTTP calls from Streamlit to FastAPI
│   ├── views/
│   │   ├── employee.py                     # Employee onboarding workspace view
│   │   └── operations.py                   # Ops team dashboard — jobs, candidates, assignments
│   ├── app.py                              # Streamlit app entry point + login + role router
│   └── requirements.txt                    # Frontend Python dependencies
│
├── my_env/                                 # Python virtual environment (not committed)
├── .gitignore
├── LICENSE
└── README.md
```

---

## File-by-File Explanation

### `backend/main.py`
The FastAPI application entry point. Responsibilities:
- Defines the `lifespan` context manager that **starts APScheduler on startup** and shuts it down on exit.
- Mounts the `/static` directory so HTML candidate portals are served directly by FastAPI.
- Registers CORS middleware (open to all origins — development config).
- Includes the central `api_router` under `/api/v1` prefix.
- Also registers `candidate_portal_router` separately under `/api` prefix (note: this creates duplicate route registration — see Known Issues).

---

### `backend/app/core/config.py`
Pydantic `BaseSettings` class that loads all environment variables from `.env`. Contains:
- Project metadata (`PROJECT_NAME`, `VERSION`, `API_V1_STR`).
- Gmail SMTP credentials (`GMAIL_SENDER`, `GMAIL_APP_PASSWORD`).
- `DATABASE_URL`, `SECRET_KEY`, `GROQ_API_KEY`, `HF_TOKEN`.
- `ALLOWED_ROLES` — the three valid roles in the system.
- `SYSTEM_SEED_USERS` — hardcoded list of 10 users (2 ops, 4 engineers, 4 sales) used by `seed.py`.

---

### `backend/app/core/database.py`
SQLAlchemy setup. Creates:
- `engine` from `DATABASE_URL`.
- `SessionLocal` — the session factory.
- `Base` — declarative base all ORM models inherit from.
- `get_db()` — FastAPI dependency that yields a DB session and closes it after the request.

---

### `backend/app/core/security.py`
Authentication utilities:
- `hash_password` / `verify_password` — bcrypt via passlib.
- `create_access_token` — encodes `user_id` and `role` into a HS256 JWT with 30-minute expiry.
- `decode_access_token` — decodes and validates JWT, returns payload dict or `None` on failure.

---

### `backend/app/api/deps.py`
FastAPI dependency functions:
- `get_current_user` — extracts Bearer token from header, decodes it, fetches the `User` row from DB. Raises 401 on any failure.
- `require_role(allowed_roles)` — returns a dependency that calls `get_current_user` and checks the user's role against the allowed list. Raises 403 if not permitted.

---

### `backend/app/api/v1/api.py`
Central router that imports and includes all four endpoint routers:
- `/auth` → `auth.router`
- `/recruitment` → `recruitment.router`
- `/onboarding` → `onboarding.router`
- `` (no prefix) → `candidate_portal.router`

---

### `backend/app/api/v1/endpoints/auth.py`
Single endpoint: `POST /auth/login`.
- Accepts `email` + `password`.
- Queries `User` table, verifies bcrypt password.
- Returns JWT access token, role, and full name on success.
- Returns 401 on invalid credentials.

---

### `backend/app/api/v1/endpoints/recruitment.py`
Operations-team-only endpoints (all require `operations_team` role except `upload_resume`):

- `POST /recruitment/upload-resume` — Accepts PDF upload, extracts text via pdfplumber, calls LLM to parse resume, saves `Candidate` row, auto-creates `Application` row for a hardcoded `job_id=1` (known issue).

- `POST /recruitment/applications/{id}/evaluate` — Calls LLM to evaluate candidate skills vs job requirements. Saves match score and generates 3 MCQ screening questions (legacy flow — superseded by personalized exam flow).

- `GET /recruitment/candidates` — Returns all candidates with their latest application status and AI match score. No job filtering (known issue).

- `POST /recruitment/jobs/create` — Creates a `Job` row with all configuration (difficulty, num_questions, pass_threshold, filter_mode, deadlines, assignment toggle). Saves assignment PDF to disk if provided. Arms APScheduler deadline job. Returns candidate portal URL.

- `GET /recruitment/jobs` — Lists all jobs ordered by creation date.

- `GET /recruitment/jobs/{id}/exam-attempts` — Returns all exam attempts for a specific job with candidate details.

- `GET /recruitment/jobs/{id}/assignment-submissions` — Returns all assignment submissions for a specific job.

- `POST /recruitment/send-meet/{application_id}` — Manually sends a Google Meet link email to a candidate.

---

### `backend/app/api/v1/endpoints/candidate_portal.py`
Public-facing endpoints — no authentication required:

- `GET /job/{job_id}` — Returns job info. Validates job is active, status is `screening_open`, and deadline has not passed.

- `POST /jobs/{job_id}/start-exam` — The core candidate entry point:
  1. Validates job is open and no duplicate application exists.
  2. Decodes base64 PDF, extracts text via pdfplumber.
  3. Calls LLM to parse resume skills.
  4. Creates or reuses `Candidate` row.
  5. Creates `Application` row.
  6. Calls LLM to generate N personalized MCQ questions (with `correct_option`).
  7. Stores full questions (with answers) in `application.questions`.
  8. Returns sanitized questions (without `correct_option`) to frontend.

- `POST /test/submit` — Grades exam submission:
  1. Fetches candidate and application.
  2. Guards against duplicate submission.
  3. Loads answer key from `application.questions`.
  4. Runs pure-Python grader (`grade_candidate_answers`).
  5. Creates `ExamAttempt` row with score and breakdown.
  6. Updates application status to `interview` (passed) or `rejected` (failed).

- `POST /assignment/submit` — Accepts assignment submission:
  1. Guards: job must be `assignment_open`, candidate must have a passing `ExamAttempt`.
  2. Guards against duplicate submission.
  3. Creates `AssignmentSubmission` row with GitHub, LinkedIn, deployment URL, notes.

---

### `backend/app/api/v1/endpoints/onboarding.py`
Operations-team endpoints for hire and plan management:

- `POST /onboarding/hire/{application_id}` — Two-phase hire:
  1. Calls `execute_candidate_hire_transition` (lifecycle_bridge) — flips application to `hired`, creates `User` row with corporate email and temporary password.
  2. Calls `generate_automated_onboarding_plan` (onboarding_agent) — RAG + LLM generates 6 personalized tasks, saves to DB.

- `GET /onboarding/plan/{user_id}` — Returns the user's onboarding plan with all tasks ordered by `due_day`. Accessible by all roles.

- `PATCH /onboarding/task/{task_id}/complete` — Marks a single task as `completed`. Accessible by all roles.

- `GET /onboarding/users` — Returns all users (ops team only).

---

### `backend/app/models/user.py`
SQLAlchemy ORM model for the `users` table:
- `UserRole` enum: `operations_team`, `software_engineer`, `sales_team`.
- Fields: `id`, `full_name`, `email` (unique), `hashed_password`, `role`, `level`, `dept`, `created_at`.

---

### `backend/app/models/recruitment.py`
Five ORM models for the recruitment pipeline:

- **`Job`** — Stores job config: title, department, requirements, difficulty, num_questions, pass_threshold, filter_mode, percentile_cutoff, focus_skills, deadlines, assignment toggle, PDF path, status, recruiter email.

- **`Candidate`** — Stores parsed candidate data: full_name, email (unique), phone, raw_resume_text (truncated to 4000 chars), extracted_skills (JSON string).

- **`Application`** — Links a `Candidate` to a `Job`. Tracks status (`ApplicationStatus` enum), AI match score, questions (JSON with answer key), interview slot, meet URL, calendar event ID.

- **`ExamAttempt`** — One-to-one with Application (unique constraint). Stores submitted answers (JSON), score (0–100), passed (bool), grading_report (JSON breakdown).

- **`AssignmentSubmission`** — One-to-one with Application. Stores GitHub link, LinkedIn, deployment URL, notes.

---

### `backend/app/models/onboarding.py`
Two ORM models:

- **`OnboardingPlan`** — One per hired user. Links to `users.id`. Has cascade-delete relationship to tasks.

- **`OnboardingTask`** — Individual task row. Fields: title, description, due_day (1/3/5/7), status (`pending`/`completed`).

---

### `backend/app/services/llm_gateway.py`
All LLM interactions via LangChain + Groq (`llama-3.3-70b-versatile`, temperature=0):

- `extract_resume_data(raw_text)` — Structured output extraction. Returns `ResumeExtractionSchema` with name, email, phone, skills list, experience years, seniority level.

- `evaluate_candidate(skills, requirements, name, title)` — Legacy evaluation. Returns match score, skill gaps, strength areas, summary, and 3 MCQ questions. Used by ops manual evaluation flow.

- `generate_personalized_questions(jd_text, resume_text, num_questions, difficulty, focus_skills)` — Generates N MCQs split across 4 buckets: `core_strengths`, `jd_requirements`, `skill_gaps`, `focus_skills`. Returns full list including `correct_option`. Uses raw LLM call (not structured output) + `_parse_questions_json` to extract JSON array safely.

- `grade_candidate_answers(questions_with_answers, submitted_answers)` — Pure Python grader. Compares submitted letter answers against stored `correct_option`. Returns score (0–100) and per-question breakdown.

---

### `backend/app/services/parser.py`
Single async function `extract_text_from_pdf(file_bytes)`:
- Opens PDF bytes with pdfplumber.
- Extracts text from each page.
- Joins all pages with newlines and returns full text string.

---

### `backend/app/services/rag_engine.py`
FAISS-based RAG engine for onboarding context:

- `load_and_chunk_documents()` — Reads markdown policy files from `data/company_policies/`, splits into 300-char chunks with 30-char overlap using `RecursiveCharacterTextSplitter`. Tags each chunk with `target_role` metadata.

- `build_vector_store()` — Embeds all chunks using HuggingFace `all-MiniLM-L6-v2` and saves FAISS index to `data/vector_store/`.

- `load_vector_store()` — Loads saved FAISS index from disk.

- `search_by_role(query, role, k)` — Searches FAISS for top 20 results, then filters by `target_role` metadata to return only role-relevant chunks.

Role mapping: `engineering_setup_guide.md` → `software_engineer`; `sales_crm_playbook.md` → `sales_team`. Operations role falls back to sales docs.

---

### `backend/app/services/onboarding_agent.py`
Generates personalized onboarding plans for newly hired employees:

1. Fetches user from DB, determines role display name and RAG key.
2. Runs `search_by_role` to retrieve role-relevant policy chunks.
3. Builds a detailed prompt combining user profile + policy context.
4. Calls LLM with structured output (`OnboardingPlanGenerationSchema`) to generate exactly 6 tasks with title, description, and due_day.
5. Saves `OnboardingPlan` + 6 `OnboardingTask` rows to DB.
6. Returns count of tasks generated.

---

### `backend/app/services/lifecycle_bridge.py`
Handles the candidate → employee transition atomically:

1. Fetches and validates the `Application` (must not be already hired or rejected).
2. Maps `job.department` to `UserRole` using `DEPARTMENT_TO_ROLE` dict.
3. Builds corporate email as `firstname.department@talentweave.com` (known issue — collision risk).
4. Checks for email conflicts in the `users` table.
5. In a single transaction: flips `application.status` to `hired`, creates new `User` row with corporate email and hashed temporary password.
6. Returns new user details dict to the calling endpoint.

---

### `backend/app/services/email_service.py`
Gmail SMTP email functions using `smtplib`:

- `send_interview_email` — Sends interview invitation with ICS calendar attachment. Called by scheduler (interview path). ICS built using `icalendar` library — adds event directly to recipient's calendar app.

- `send_assignment_email` — Sends assignment PDF as email attachment. Called by scheduler (assignment path). PDF read from disk path stored in `job.assignment_pdf_path`.

- `send_meet_link_email` — Sends simple Meet URL email. Called manually from ops dashboard via `POST /recruitment/send-meet/{application_id}`.

- `test_email_connection` — Utility to verify SMTP config by sending a test email to self.

---

### `backend/app/services/scheduler_service.py`
APScheduler-based deadline automation (runs on background thread, uses its own DB session):

- `register_screening_deadline(job_id, run_at)` — Arms a one-shot job to call `process_screening_deadline` at the exact screening deadline moment.

- `register_assignment_deadline(job_id, run_at)` — Arms a one-shot job to call `process_assignment_deadline` at the assignment deadline.

- `process_screening_deadline(job_id)` — The main automation trigger:
  1. Loads job config.
  2. Fetches all `ExamAttempt` rows for this job.
  3. Applies filter mode (`fixed_threshold` or `top_percentile`) via `_filter_candidates`.
  4. Branches: assignment path → `_handle_assignment_branch`; interview path → `_handle_interview_branch`.

- `_handle_assignment_branch` — Flips job to `assignment_open`, emails each passing candidate their assignment PDF, arms assignment deadline clock.

- `_handle_interview_branch` — Assigns sequential 30-minute slots starting next day at 10:00 AM UTC, generates placeholder Meet URLs, sends calendar invite emails, flips job to `interviews_scheduled`.

- `process_assignment_deadline(job_id)` — Flips job to `assignment_closed` so ops dashboard shows submissions are ready for review.

---

### `backend/app/schemas/`
All Pydantic schemas for request/response validation:

- **`auth.py`** — `LoginRequest` (email + password), `TokenResponse` (token + role + full_name).
- **`candidate_portal.py`** — `QuestionItem` (no correct_option), `StartExamRequest/Response`, `SubmitExamRequest/Response`, `SubmitAssignmentRequest/Response`.
- **`recruitment.py`** — `ResumeExtractionSchema`, `CandidateEvaluationSchema`, `MCQQuestionSchema`, `JobCreateResponse`.
- **`onboarding.py`** — `OnboardingConfigSchema`, `HireResponseSchema`, `TaskGenerationItem`, `OnboardingPlanGenerationSchema`.

---

### `backend/scripts/seed.py`
Database seeder — run once before first launch:
1. Creates all tables via `Base.metadata.create_all`.
2. Seeds 10 users (2 ops, 4 engineers, 4 sales) with bcrypt-hashed passwords from `SEED_PASSWORDS`.
3. Seeds 3 jobs (Backend Engineer, Sales AE, HR Coordinator).
4. For each non-ops employee, calls `generate_automated_onboarding_plan` via `asyncio.run` to pre-generate onboarding tasks.

---

### `backend/scripts/init_vector_store.py`
One-time script to build the FAISS vector store from policy markdown files. Must be run before the first hire so `onboarding_agent.py` can perform RAG lookups.

---

### `backend/static/candidate_exam.html`
Three-screen single-page exam portal (pure HTML + JS):
- **Screen 1 (Entry)** — Candidate fills name, email, phone, uploads PDF. On submit, converts PDF to base64, calls `POST /api/jobs/{job_id}/start-exam`.
- **Screen 2 (Exam)** — Renders questions one at a time with dot navigation map, countdown timer (counts down to `screening_deadline` returned by API), option selection. On submit, calls `POST /api/test/submit`.
- **Screen 3 (Results)** — Shows score, pass/fail status, and next steps message.

Job ID is auto-filled from URL query param `?job_id=`.

---

### `backend/static/assignment_submit.html`
Simple single-screen assignment submission form (pure HTML + JS):
- Fields: name, email, phone, GitHub URL, LinkedIn URL, deployment URL (optional).
- Calls `POST /api/assignment/submit`.
- Job ID read from URL query param `?job_id=`.

---

### `frontend/app.py`
Streamlit app entry point:
- Manages session state: `token`, `role`, `full_name`, `user_id`.
- `show_login()` — Login form, calls `login_user`, decodes JWT to extract `user_id`.
- Routes authenticated users: `operations_team` → `show_operations()`, `software_engineer`/`sales_team` → `show_employee()`.
- Sidebar with logout button.

---

### `frontend/utils/api_client.py`
All HTTP client functions for Streamlit → FastAPI communication:
- Attaches Bearer token from `st.session_state` to every authenticated request.
- Functions: `login_user`, `upload_resume`, `evaluate_application`, `hire_candidate`, `get_all_candidates`, `get_onboarding_plan`, `complete_task`, `get_all_users`, `create_job`, `get_exam_attempts`, `get_assignment_submissions`, `send_meet_invite`, `get_all_jobs`.

---

### `frontend/views/operations.py`
Streamlit operations dashboard with 3 tabs:

**Tab 1 — Create Job:**
- Form with all job config fields.
- Assignment toggle — reveals PDF uploader and duration field.
- Calls `create_job`, displays returned portal URL for sharing with candidates.

**Tab 2 — Candidates:**
- Fetches all jobs for dropdown selector.
- Fetches exam scores for selected job.
- Lists all candidates (unfiltered — known issue) with skills, status, LLM score, exam score badge.
- Per-candidate action buttons: Evaluate (LLM), Hire, Send Meet (only shown if exam passed).

**Tab 3 — Assignments:**
- Filters to only jobs with `include_assignment=True`.
- Lists submissions for selected job with GitHub, LinkedIn, deployment, notes.
- "Approve for Interview" button triggers hire.

---

### `frontend/views/employee.py`
Streamlit employee workspace:
- Fetches onboarding plan for logged-in `user_id`.
- Shows progress bar (completed / total tasks).
- Groups tasks by `due_day` (Day 1, Day 3, Day 5, Day 7).
- Checkbox per task — checking triggers `PATCH /onboarding/task/{id}/complete` and reruns.
- Completed tasks shown with strikethrough.

---

## System Architecture & Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        TALENTWEAVE FLOWS                         │
└─────────────────────────────────────────────────────────────────┘

FLOW A — JOB CREATION (Ops Team via Streamlit)
──────────────────────────────────────────────
Ops fills job form
  → POST /recruitment/jobs/create
  → Job row created in DB
  → APScheduler arms screening deadline job
  → Returns candidate portal URL

FLOW B — CANDIDATE EXAM (candidate_exam.html)
─────────────────────────────────────────────
Candidate opens portal URL (job_id in query param)
  → Fills name, email, phone, uploads PDF
  → POST /jobs/{job_id}/start-exam
      → PDF decoded from base64
      → pdfplumber extracts text
      → LLM parses resume → extracts skills
      → Candidate + Application rows created
      → LLM generates N personalized MCQs (4 buckets)
      → Full questions (with answers) saved to application.questions
      → Sanitized questions (no correct_option) returned to browser
  → Candidate takes timed exam
  → POST /test/submit
      → Pure Python grader compares answers to answer key
      → ExamAttempt row created with score + breakdown
      → Application status → interview (pass) or rejected (fail)
  → Results screen shown

FLOW C — SCREENING DEADLINE FIRES (APScheduler background thread)
──────────────────────────────────────────────────────────────────
Deadline time reached
  → process_screening_deadline(job_id)
  → All ExamAttempts fetched for this job
  → filter_candidates applied (fixed_threshold or top_percentile)
  
  [IF include_assignment = False — Interview Path]
    → Sequential 30-min slots assigned (tomorrow 10:00 AM UTC)
    → Placeholder Meet URL generated per candidate
    → send_interview_email → Gmail SMTP with ICS calendar attachment
    → Application rows updated with slot + meet_url
    → Job status → interviews_scheduled

  [IF include_assignment = True — Assignment Path]
    → Job status → assignment_open
    → send_assignment_email → Gmail SMTP with PDF attachment
    → APScheduler arms assignment deadline job

FLOW D — ASSIGNMENT SUBMISSION (assignment_submit.html)
────────────────────────────────────────────────────────
Candidate opens assignment submission URL (job_id in query param)
  → Fills GitHub, LinkedIn, deployment URL
  → POST /assignment/submit
      → Guards: job must be assignment_open
      → Guards: candidate must have passed ExamAttempt
      → AssignmentSubmission row created

FLOW E — ASSIGNMENT DEADLINE FIRES (APScheduler)
─────────────────────────────────────────────────
  → process_assignment_deadline(job_id)
  → Job status → assignment_closed
  → Ops dashboard now shows submissions for review

FLOW F — HIRE & ONBOARDING (Ops Team via Streamlit)
────────────────────────────────────────────────────
Ops clicks Hire (or Approve for Interview in assignment tab)
  → POST /onboarding/hire/{application_id}
  → lifecycle_bridge:
      → Application status → hired
      → User row created (corporate email + temp password)
  → onboarding_agent:
      → search_by_role → FAISS RAG → role-relevant policy chunks
      → LLM generates 6 personalized tasks
      → OnboardingPlan + 6 OnboardingTask rows saved
  → HireResponseSchema returned

FLOW G — EMPLOYEE ONBOARDING (Employee via Streamlit)
──────────────────────────────────────────────────────
Employee logs in with corporate email + temp password
  → GET /onboarding/plan/{user_id}
  → Views tasks grouped by due_day
  → Checks off tasks → PATCH /onboarding/task/{id}/complete
  → Progress bar updates
```

---

## Database Schema

```
users
  id, full_name, email (unique), hashed_password, role (enum), level, dept, created_at

jobs
  id, title, department, requirements, difficulty, num_questions, pass_threshold,
  filter_mode, percentile_cutoff, focus_skills, screening_deadline, include_assignment,
  assignment_pdf_path, assignment_deadline, public_link_active, status, recruiter_email, created_at

candidates
  id, full_name, email (unique), phone, raw_resume_text, extracted_skills (JSON), created_at

applications
  id, job_id (FK), candidate_id (FK), status (enum), ai_match_score,
  screening_questions (JSON), questions (JSON + answer key), interview_slot_start,
  interview_slot_end, meet_url, calendar_event_id, created_at

exam_attempts
  id, application_id (FK, unique), candidate_id (FK), answers (JSON),
  score, passed, grading_report (JSON), attempted_at

assignment_submissions
  id, application_id (FK, unique), candidate_id (FK), github_link, linkedin,
  deployment_url, notes, submitted_at

onboarding_plans
  id, user_id (FK), created_at

onboarding_tasks
  id, plan_id (FK, cascade delete), title, description, due_day, status, created_at
```

---

## API Reference

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/auth/login` | None | Login, get JWT |
| POST | `/api/v1/recruitment/upload-resume` | ops | Upload PDF, parse resume |
| POST | `/api/v1/recruitment/applications/{id}/evaluate` | ops | LLM evaluate candidate |
| GET | `/api/v1/recruitment/candidates` | ops | List all candidates |
| POST | `/api/v1/recruitment/jobs/create` | ops | Create job opening |
| GET | `/api/v1/recruitment/jobs` | ops | List all jobs |
| GET | `/api/v1/recruitment/jobs/{id}/exam-attempts` | ops | Exam results for job |
| GET | `/api/v1/recruitment/jobs/{id}/assignment-submissions` | ops | Assignment submissions |
| POST | `/api/v1/recruitment/send-meet/{id}` | ops | Send meet link email |
| POST | `/api/v1/onboarding/hire/{id}` | ops | Hire candidate + generate onboarding |
| GET | `/api/v1/onboarding/plan/{user_id}` | all roles | Get onboarding plan |
| PATCH | `/api/v1/onboarding/task/{id}/complete` | all roles | Complete a task |
| GET | `/api/v1/onboarding/users` | ops | List all users |
| GET | `/api/job/{job_id}` | None | Get job info (candidate portal) |
| POST | `/api/jobs/{job_id}/start-exam` | None | Start exam (candidate portal) |
| POST | `/api/test/submit` | None | Submit exam answers |
| POST | `/api/assignment/submit` | None | Submit assignment |

---

## Setup & Installation

### Prerequisites
- Python 3.11+
- PostgreSQL (running locally or remote)
- Gmail account with App Password enabled
- Groq API key (free tier available)

### 1. Clone & Environment Setup

```bash
git clone https://github.com/your-org/talentweave.git
cd talentweave

# Create virtual environment
python -m venv my_env
source my_env/bin/activate  # Windows: my_env\Scripts\activate
```

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

Create `.env` file in `backend/`:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/talentweave
SECRET_KEY=your-secret-key-here
GROQ_API_KEY=your-groq-api-key
HF_TOKEN=your-huggingface-token
GMAIL_SENDER=your-gmail@gmail.com
GMAIL_APP_PASSWORD=your-gmail-app-password
```

### 3. Database Initialization

```bash
# From backend/ directory

# Step 1: Build vector store from policy docs
python scripts/init_vector_store.py

# Step 2: Seed database (creates tables + 10 users + 3 jobs + onboarding plans)
python scripts/seed.py
```

### 4. Start Backend

```bash
# From backend/ directory
uvicorn main:app --reload --port 8000
```

API docs available at: `http://localhost:8000/docs`

### 5. Frontend Setup

```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

Frontend available at: `http://localhost:8501`

---

## Demo Walkthrough

### Step 1 — Login as Operations Team
- Open `http://localhost:8501`
- Login: `maria.ops@talentweave.com` / `maria@123`

### Step 2 — Create a Job
- Tab: **Create Job**
- Fill title, department, requirements, difficulty, questions, threshold
- Set screening window (e.g. 60 minutes)
- Toggle **Include Assignment** if desired (upload PDF)
- Click **Create Job**
- Copy the **Candidate Portal URL**

### Step 3 — Candidate Takes Exam
- Open the candidate portal URL in a browser (or incognito)
- Fill name, email, phone, upload a resume PDF
- Click **Start Exam** — wait ~10 seconds for LLM to generate questions
- Answer all questions using the dot navigation
- Click **Submit Exam**
- Score and pass/fail result shown immediately

### Step 4A — Interview Path (no assignment)
- Wait for screening deadline to pass (APScheduler fires automatically)
- Candidate receives email with ICS calendar invite and Meet URL

### Step 4B — Assignment Path
- Wait for screening deadline — passing candidates receive assignment PDF via email
- Candidate opens assignment submission URL (`/static/assignment_submit.html?job_id=X`)
- Fills GitHub, LinkedIn, deployment URL, submits
- Ops team reviews in **Assignments tab** of dashboard
- Click **Approve for Interview** to hire

### Step 5 — Hire Candidate
- In **Candidates tab**, find the candidate
- Send Meet invite first (if interview path)
- Click **Hire** button
- System creates corporate email, hashes temp password, generates onboarding plan

### Step 6 — Employee Onboarding
- Logout from ops account
- Login with the corporate email generated (e.g. `john.engineering@talentweave.com`) / `Welcome@123`
- Employee workspace shows 6 AI-generated onboarding tasks
- Check off tasks as completed — progress bar updates

---

## Known Issues & Limitations

1. **Duplicate route registration** — `candidate_portal_router` registered twice in `main.py` (once via `api_router` at `/api/v1`, once directly at `/api`). Frontend HTML calls `/api/...` path.

2. **Corporate email collision** — `lifecycle_bridge.py` generates email as `firstname.department@talentweave.com` using only first name. Two "John" candidates in Engineering will collide. Fix: use first + last name or append candidate ID.

3. **Candidate list not job-filtered** — `GET /recruitment/candidates` returns all candidates. The Streamlit candidates tab shows everyone regardless of which job is selected in the dropdown.

4. **Hire button visible before meet link sent** — No guard in `operations.py` prevents showing the Hire button before a meet link is dispatched. Fix: check `meet_url` presence or application status before rendering button.

5. **Assignment path hire button** — Candidates tab shows Hire button even for assignment-path jobs. Hire should only be triggered from the Assignments tab for those jobs.

6. **UTC vs local time mismatch** — `create_job` uses `datetime.now()` (local) for `screening_deadline`, but `_handle_interview_branch` uses `datetime.utcnow()` for slot scheduling. This causes slot times to be offset by the server's timezone.

7. **Hardcoded `job_id=1`** — `upload_resume` endpoint defaults applications to job ID 1.

8. **`asyncio.run` in seed loop** — Calling `asyncio.run(generate_automated_onboarding_plan(...))` in a for-loop creates/destroys an event loop per iteration. Works but is inefficient.

9. **No assignment round `filter_mode=top_percentile`** — `percentile_cutoff` field is not exposed in Streamlit job creation form (hardcoded to 5.0).

10. **FAISS vector store must exist before first hire** — If `init_vector_store.py` was not run, `onboarding_agent.py` will fail silently (catches exception, uses fallback text).
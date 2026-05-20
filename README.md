# 🧵 TalentWeave — AI-Powered Talent Acquisition & Onboarding Platform

> An end-to-end intelligent HRMS platform that automates the full employee lifecycle — from resume ingestion and AI-driven screening to role-based onboarding plan generation — built with FastAPI, LangChain, FAISS, Groq LLaMA, and Streamlit.

---

## 📌 Table of Contents

1. [Problem Statement](#problem-statement)
2. [What TalentWeave Solves](#what-talentweave-solves)
3. [System Overview](#system-overview)
4. [Tech Stack](#tech-stack)
5. [Project Architecture](#project-architecture)
6. [Folder Structure](#folder-structure)
7. [Database Schema](#database-schema)
8. [User Roles & Permissions](#user-roles--permissions)
9. [API Reference](#api-reference)
10. [Step-by-Step Implementation Guide](#step-by-step-implementation-guide)
11. [Environment Setup](#environment-setup)
12. [How to Run](#how-to-run)
13. [Demo Walkthrough](#demo-walkthrough)
14. [Key Engineering Decisions](#key-engineering-decisions)
15. [Project Flow Diagram](#project-flow-diagram)

---

## Problem Statement

In most companies, the hiring and onboarding process is entirely manual:

- HR teams read resumes by hand and shortlist candidates subjectively.
- Interview questions are generic and not tailored to the candidate's actual skill gaps.
- After hiring, onboarding plans are copy-pasted from old documents, regardless of the new hire's role or seniority.
- There is no single system tracking the full lifecycle from applicant → employee → productive team member.

This creates slow hiring cycles, poor candidate screening, inconsistent onboarding quality, and wasted HR bandwidth.

---

## What TalentWeave Solves

TalentWeave is an internal AI-powered HRMS platform that automates the entire talent lifecycle across three modules:

**Recruitment Intelligence**
- Automatically parses PDF resumes using an LLM and extracts structured candidate data (skills, experience, seniority level).
- Computes an AI match score by comparing candidate skills against job requirements.
- Generates a personalized MCQ screening test targeting the candidate's exact skill gaps — not generic questions.

**Lifecycle Transition Bridge**
- A single admin action atomically converts an external candidate into an authenticated internal employee.
- ACID-compliant SQL transactions ensure database integrity — if any step fails, everything rolls back.

**Agentic Onboarding Engine**
- Immediately after hire, the system queries a role-locked FAISS vector store to retrieve only the corporate documents relevant to the new hire's role.
- An LLM transforms those documents into a structured, trackable first-week onboarding plan.
- Sales hires only receive sales playbooks. Engineers only receive engineering setup guides. Zero data leakage between roles.

---

## System Overview

```
External Candidate
      │
      ▼
[Resume PDF Upload]
      │
      ▼
[LLM Parsing → Structured Skills JSON]
      │
      ▼
[AI Match Score + MCQ Generation]
      │
      ▼
[Operations Admin Reviews → Clicks Hire]
      │
      ▼
[Atomic Transaction: Candidate → User]
      │
      ▼
[RAG Engine: FAISS Role-Filtered Lookup]
      │
      ▼
[LLM Generates Personalized Onboarding Plan]
      │
      ▼
[Employee Logs In → Checks Off Tasks]
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend API | FastAPI | Async HTTP routing, dependency injection, RBAC |
| Database ORM | SQLAlchemy + PostgreSQL | Relational data models, ACID transactions |
| Authentication | JWT (python-jose) + bcrypt (passlib) | Token-based auth, password hashing |
| LLM Provider | Groq API — LLaMA 3.3 70B Versatile | Resume parsing, evaluation, onboarding generation |
| LLM Orchestration | LangChain + langchain-groq | Structured output binding, prompt chaining |
| Vector Database | FAISS (local) | Role-filtered semantic document retrieval |
| Embeddings | HuggingFace sentence-transformers (all-MiniLM-L6-v2) | Text vectorization for RAG |
| PDF Parsing | pdfplumber | In-memory PDF text extraction |
| Frontend UI | Streamlit | Interactive dashboard for ops and employee views |
| Data Validation | Pydantic v2 | Schema enforcement for LLM outputs and API I/O |
| Environment Config | python-dotenv | Secrets and connection string management |

---

## Project Architecture

TalentWeave follows a clean **layered architecture** with strict separation of concerns:

```
HTTP Request
    │
    ▼
main.py (FastAPI App + CORS)
    │
    ▼
api/v1/api.py (Master Router)
    │
    ├── endpoints/auth.py       → Login, token generation
    ├── endpoints/recruitment.py → Resume upload, evaluation
    └── endpoints/onboarding.py → Hire, plan fetch, task update
         │
         ▼
    api/deps.py (JWT Auth + RBAC Guards)
         │
         ▼
    services/
    ├── parser.py          → PDF text extraction
    ├── llm_gateway.py     → LLM prompt execution
    ├── rag_engine.py      → FAISS vector store operations
    ├── lifecycle_bridge.py → Candidate → User transaction
    └── onboarding_agent.py → AI plan generation
         │
         ▼
    models/ (SQLAlchemy ORM)
    ├── user.py
    ├── recruitment.py
    └── onboarding.py
         │
         ▼
    PostgreSQL Database
```

---

## Folder Structure

```
TalentWeave/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py                   # JWT auth + require_role() RBAC dependency
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── api.py                # Master APIRouter aggregating all endpoints
│   │   │       └── endpoints/
│   │   │           ├── __init__.py
│   │   │           ├── auth.py           # POST /auth/login
│   │   │           ├── recruitment.py    # Resume upload, evaluation, candidates list
│   │   │           └── onboarding.py     # Hire, plan fetch, task complete, users list
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py                 # AppConfig (pydantic-settings), 10-user seed map
│   │   │   ├── database.py               # SQLAlchemy engine, SessionLocal, Base, get_db()
│   │   │   └── security.py               # bcrypt hashing, JWT create/decode
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py               # Single import entry point for all models
│   │   │   ├── user.py                   # User model + UserRole enum
│   │   │   ├── recruitment.py            # Job, Candidate, Application models
│   │   │   └── onboarding.py             # OnboardingPlan, OnboardingTask models
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                   # LoginRequest, TokenResponse
│   │   │   ├── recruitment.py            # ResumeExtractionSchema, MCQQuestionSchema, CandidateEvaluationSchema
│   │   │   └── onboarding.py             # OnboardingConfigSchema, TaskGenerationItem, HireResponseSchema
│   │   │
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── llm_gateway.py            # extract_resume_data(), evaluate_candidate()
│   │       ├── rag_engine.py             # build_vector_store(), search_by_role()
│   │       ├── parser.py                 # extract_text_from_pdf()
│   │       ├── lifecycle_bridge.py       # execute_candidate_hire_transition()
│   │       └── onboarding_agent.py       # generate_automated_onboarding_plan()
│   │
│   ├── data/
│   │   ├── company_policies/
│   │   │   ├── engineering_setup_guide.md   # RAG source for software_engineer role
│   │   │   └── sales_crm_playbook.md        # RAG source for sales_team role
│   │   └── vector_store/
│   │       ├── index.faiss                  # Generated FAISS binary index (do not edit)
│   │       └── index.pkl                    # Generated FAISS metadata store (do not edit)
│   │
│   ├── scripts/
│   │   ├── seed.py                      # Seeds 10 users + 3 jobs into the database
│   │   └── init_vector_store.py         # Builds FAISS index from markdown policy files
│   │
│   ├── .env                             # Secrets (never commit to git)
│   ├── Dockerfile
│   ├── main.py                          # FastAPI app bootstrap + CORS middleware
│   └── requirements.txt
│
├── frontend/
│   ├── pages/
│   │   ├── operations.py                # Admin dashboard: upload, evaluate, hire
│   │   └── employee.py                  # Employee workspace: tasks, progress, checkboxes
│   │
│   ├── utils/
│   │   └── api_client.py                # HTTP wrappers for all FastAPI endpoint calls
│   │
│   └── app.py                           # Streamlit entry point, login form, role router
│
├── README.md
└── docker-compose.yml
```

---

## Database Schema

### Tables

**`users`**
| Column | Type | Description |
|---|---|---|
| id | Integer (PK) | Auto-increment primary key |
| full_name | String | Employee full name |
| email | String (unique) | Corporate email address |
| hashed_password | String | bcrypt hashed password |
| role | Enum | operations_team / software_engineer / sales_team |
| level | String | junior / mid / senior / lead |
| dept | String | HR / Engineering / Sales |
| created_at | DateTime | Auto timestamp |

**`jobs`**
| Column | Type | Description |
|---|---|---|
| id | Integer (PK) | Auto-increment primary key |
| title | String | Job title |
| department | String | Engineering / Sales / Operations |
| requirements | Text | Full job description text |
| status | String | active / closed |
| created_at | DateTime | Auto timestamp |

**`candidates`**
| Column | Type | Description |
|---|---|---|
| id | Integer (PK) | Auto-increment primary key |
| full_name | String | Parsed from resume by LLM |
| email | String (unique) | Parsed from resume by LLM |
| phone | String | Parsed from resume by LLM |
| raw_resume_text | Text | First 4000 chars of extracted PDF text |
| extracted_skills | Text | JSON stringified list of skills |
| created_at | DateTime | Auto timestamp |

**`applications`**
| Column | Type | Description |
|---|---|---|
| id | Integer (PK) | Auto-increment primary key |
| job_id | Integer (FK → jobs.id) | Linked job opening |
| candidate_id | Integer (FK → candidates.id) | Linked candidate profile |
| status | Enum | new / screening / interview / hired / rejected |
| ai_match_score | Float | 0–100 score computed by LLM |
| screening_questions | Text | JSON stringified MCQ array |
| created_at | DateTime | Auto timestamp |

**`onboarding_plans`**
| Column | Type | Description |
|---|---|---|
| id | Integer (PK) | Auto-increment primary key |
| user_id | Integer (FK → users.id) | Linked employee |
| created_at | DateTime | Auto timestamp |

**`onboarding_tasks`**
| Column | Type | Description |
|---|---|---|
| id | Integer (PK) | Auto-increment primary key |
| plan_id | Integer (FK → onboarding_plans.id, CASCADE DELETE) | Linked plan |
| title | String | Action-oriented task name |
| description | Text | Step-by-step implementation instructions |
| due_day | Integer | Day 1 / 3 / 5 / 7 |
| status | String | pending / completed |
| created_at | DateTime | Auto timestamp |

### Relationships

```
users (1) ──────────── (1) onboarding_plans
                               │
                               └── (many) onboarding_tasks [CASCADE DELETE]

jobs (1) ──────────── (many) applications
candidates (1) ──── (many) applications
```

---

## User Roles & Permissions

### Seeded Users (10 total)

| # | Name | Email | Password | Role | Level |
|---|---|---|---|---|---|
| 1 | Maria | maria.ops@talentweave.com | maria@123 | operations_team | — |
| 2 | Rahul | rahul.ops@talentweave.com | rahul@123 | operations_team | — |
| 3 | Alex | alex.dev@talentweave.com | alex@123 | software_engineer | junior |
| 4 | Priya | priya.dev@talentweave.com | priya@123 | software_engineer | mid |
| 5 | Kevin | kevin.dev@talentweave.com | kevin@123 | software_engineer | senior |
| 6 | Rohan | rohan.dev@talentweave.com | rohan@123 | software_engineer | junior |
| 7 | Sarah | sarah.sales@talentweave.com | sarah@123 | sales_team | mid |
| 8 | Amit | amit.sales@talentweave.com | amit@123 | sales_team | senior |
| 9 | Viktor | viktor.sales@talentweave.com | viktor@123 | sales_team | lead |
| 10 | Neha | neha.sales@talentweave.com | neha@123 | sales_team | junior |

### Role-Based Access Control (RBAC)

| Endpoint | operations_team | software_engineer | sales_team |
|---|---|---|---|
| POST /auth/login | ✅ | ✅ | ✅ |
| POST /recruitment/upload-resume | ✅ | ❌ | ❌ |
| POST /recruitment/applications/{id}/evaluate | ✅ | ❌ | ❌ |
| GET /recruitment/candidates | ✅ | ❌ | ❌ |
| POST /onboarding/hire/{id} | ✅ | ❌ | ❌ |
| GET /onboarding/plan/{user_id} | ✅ | ✅ | ✅ |
| PATCH /onboarding/task/{id}/complete | ✅ | ✅ | ✅ |
| GET /onboarding/users | ✅ | ❌ | ❌ |

---

## API Reference

### Authentication

**POST** `/api/v1/auth/login`

Request:
```json
{
  "email": "maria.ops@talentweave.com",
  "password": "maria@123"
}
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "role": "operations_team",
  "full_name": "Maria"
}
```

---

### Recruitment

**POST** `/api/v1/recruitment/upload-resume?job_id=1`

- Multipart form upload (PDF only)
- Extracts text via pdfplumber
- Parses via Groq LLaMA structured output
- Saves to `candidates` table and creates an `applications` row

Response:
```json
{
  "message": "Resume uploaded and parsed successfully.",
  "candidate_id": 1,
  "application_id": 1,
  "full_name": "John Doe",
  "email": "john@example.com",
  "seniority_level": "Mid",
  "skills": ["Python", "FastAPI", "PostgreSQL"]
}
```

---

**POST** `/api/v1/recruitment/applications/{application_id}/evaluate`

- Requires: `operations_team` JWT token
- Fetches candidate skills + job requirements
- Calls LLM for match scoring + MCQ generation
- Updates `applications` row with `ai_match_score` and `screening_questions`

Response:
```json
{
  "match_score": 85.0,
  "skill_gaps": ["Docker", "SQLAlchemy ORM"],
  "strength_areas": ["Python", "FastAPI", "PostgreSQL"],
  "evaluation_summary": "Strong backend candidate with minor gaps.",
  "screening_questions": [
    {
      "question": "Which decorator defines a POST endpoint in FastAPI?",
      "options": ["A) @app.post()", "B) @app.route()", "C) @app.create()", "D) @app.handle()"],
      "correct_answer": "A"
    }
  ]
}
```

---

**GET** `/api/v1/recruitment/candidates`

- Requires: `operations_team` JWT token
- Returns all candidates with their linked application status and match scores

---

### Onboarding

**POST** `/api/v1/onboarding/hire/{application_id}`

- Requires: `operations_team` JWT token
- Atomically: updates application status → hired, creates new user row
- Immediately triggers AI onboarding plan generation
- Returns new user corporate email and task count

Request body:
```json
{
  "temporary_password": "Welcome@123"
}
```

Response:
```json
{
  "message": "Candidate successfully hired and onboarding plan generated.",
  "new_user_id": 11,
  "corporate_email": "john.engineering@talentweave.com",
  "assigned_role": "software_engineer",
  "full_name": "John Doe",
  "onboarding_tasks_generated": 6
}
```

---

**GET** `/api/v1/onboarding/plan/{user_id}`

- Requires: valid JWT token (any role)
- Returns the employee's full onboarding plan with all tasks grouped by due_day

---

**PATCH** `/api/v1/onboarding/task/{task_id}/complete`

- Requires: valid JWT token (any role)
- Updates task status from `pending` → `completed`

---

## Step-by-Step Implementation Guide

### Step 1 — Product Scope & Config

**File:** `backend/app/core/config.py`

Defines the single source of truth for the application — 10 seeded users, allowed roles, and system metadata using `pydantic-settings`.

**Verify:** Import `settings` and print `settings.SYSTEM_SEED_USERS` — should show all 10 users.

---

### Step 2 — Database Schema & Models

**Files:** `database.py`, `models/user.py`, `models/recruitment.py`, `models/onboarding.py`, `scripts/seed.py`

Creates all 6 PostgreSQL tables via SQLAlchemy ORM and seeds 10 users + 3 jobs.

**Pre-requisite:** Create an empty PostgreSQL database named `talentweave_db` via pgAdmin.

**Run:**
```bash
python -m backend.scripts.seed
```

**Verify:**
```
Creating tables...
✅ Successfully seeded 10 users.
✅ Successfully seeded 3 jobs.
```

Open pgAdmin → `talentweave_db` → Tables → confirm 6 tables exist with data.

---

### Step 3 — FastAPI Core Engine & JWT Security

**Files:** `core/security.py`, `schemas/auth.py`, `api/deps.py`, `endpoints/auth.py`, `api/v1/api.py`, `main.py`

Implements JWT token generation, bcrypt password verification, and `require_role()` RBAC dependency.

**Run:**
```bash
cd backend
uvicorn main:app --reload
```

**Verify:**
- `GET http://localhost:8000` → `{"message": "Welcome to TalentWeave API"}`
- `GET http://localhost:8000/docs` → Swagger UI loads with login endpoint
- Login as Alex → get token → try accessing `/recruitment/candidates` → get `403 Forbidden`

---

### Step 4 — Knowledge Base Vectorization (RAG)

**Files:** `data/company_policies/*.md`, `services/rag_engine.py`, `scripts/init_vector_store.py`

Loads markdown policy documents, splits into 300-word chunks, stamps role metadata, generates embeddings using `sentence-transformers/all-MiniLM-L6-v2`, and saves a local FAISS index.

**Run:**
```bash
python -m backend.scripts.init_vector_store
```

**Verify:**
- Terminal shows chunks loaded from both `.md` files
- `backend/data/vector_store/` contains `index.faiss` and `index.pkl`
- Search test returns only engineering chunks when queried with `role="software_engineer"`

---

### Step 5 — Resume Ingestion & Parsing Pipeline

**Files:** `services/parser.py`, `schemas/recruitment.py`, `services/llm_gateway.py`, `endpoints/recruitment.py`

Accepts PDF upload → extracts text in-memory via pdfplumber → sends to Groq LLaMA with structured output binding → saves parsed candidate to database.

**Verify:**
- Upload PDF via Swagger `/docs`
- Response contains `full_name`, `email`, `skills`, `seniority_level`
- New row visible in `candidates` table in pgAdmin

---

### Step 6 — Candidate Evaluation & MCQ Generation

**Files:** `schemas/recruitment.py` (new schemas), `services/llm_gateway.py` (evaluate function), `endpoints/recruitment.py` (evaluate endpoint)

Also adds 3 seed jobs to `seed.py`. Compares candidate skills against job requirements, generates match score 0–100, produces 3 role-specific MCQ questions targeting skill gaps.

**Verify:**
- Login as Maria → get token → evaluate application
- Response contains `match_score`, `skill_gaps`, `strength_areas`, `screening_questions`
- `applications` table in pgAdmin shows `ai_match_score` and `screening_questions` populated

---

### Step 7 — Lifecycle Transition Bridge

**Files:** `schemas/onboarding.py`, `services/lifecycle_bridge.py`, `endpoints/onboarding.py`

Atomically transitions candidate → hired application + new user row in a single SQL transaction. Department-to-role mapping: Engineering → `software_engineer`, Sales → `sales_team`, Operations → `operations_team`.

**Verify:**
- Hire endpoint returns `new_user_id` and `corporate_email`
- `applications` table shows status = `hired`
- New row in `users` table with correct role
- New user can login with corporate email + temporary password

---

### Step 8 — Agentic Onboarding Plan Generation

**Files:** `schemas/onboarding.py` (task schemas), `services/onboarding_agent.py`, `endpoints/onboarding.py` (updated hire endpoint)

Triggered immediately after hire. Queries FAISS with role as metadata filter → retrieves role-locked corporate documents → LLM generates 6 structured onboarding tasks → saves to `onboarding_tasks` table.

**Verify:**
- Hire response shows `onboarding_tasks_generated: 6`
- `onboarding_plans` and `onboarding_tasks` tables populated
- `GET /onboarding/plan/{user_id}` returns tasks grouped by `due_day`
- `PATCH /onboarding/task/{id}/complete` flips status to `completed`

---

### Step 9 — Streamlit Frontend Interface

**Files:** `frontend/app.py`, `frontend/pages/operations.py`, `frontend/pages/employee.py`, `frontend/utils/api_client.py`

Single-entry Streamlit app with real login form. Role-based routing: Operations team sees admin dashboard (upload, evaluate, hire). Engineers and Sales see personal onboarding workspace with interactive task checkboxes.

**Run:**
```bash
cd frontend
streamlit run app.py
```

**Verify:**
- Login as Maria → see Admin Dashboard with upload zone and candidate pipeline
- Login as Alex → see Employee Workspace with 0 tasks (Alex is a seeded employee, not hired via pipeline)
- Login as newly hired user (e.g., `ishan.engineering@talentweave.com` / `Welcome@123`) → see 6 AI-generated tasks
- Check off a task → progress bar updates

---

## Environment Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ with pgAdmin
- Node.js (optional, for future tooling)

### 1. Create virtual environment

```bash
python -m venv my_env
my_env\Scripts\activate   # Windows
source my_env/bin/activate  # Mac/Linux
```

### 2. Install dependencies

```bash
pip install -r backend/requirements.txt
pip install streamlit requests
```

### 3. Create PostgreSQL database

Open pgAdmin → right-click Databases → Create → Database → name it `talentweave_db` → Save.

### 4. Configure `.env` file

Create `backend/.env`:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/talentweave_db
SECRET_KEY=talentweave-super-secret-key-2024
GROQ_API_KEY=your_groq_api_key_here
HF_TOKEN=your_huggingface_token_here
```

### 5. Seed the database

```bash
python -m backend.scripts.seed
```

### 6. Build the vector store

```bash
python -m backend.scripts.init_vector_store
```

---

## How to Run

**Terminal 1 — Start Backend:**

```bash
cd backend
uvicorn main:app --reload
```

Backend runs at: `http://localhost:8000`
Swagger UI at: `http://localhost:8000/docs`

**Terminal 2 — Start Frontend:**

```bash
cd frontend
streamlit run app.py
```

Frontend runs at: `http://localhost:8501`

---

## Demo Walkthrough

Use this exact sequence when presenting TalentWeave to show the complete end-to-end AI pipeline:

### 1. Show the Login System
- Open `http://localhost:8501`
- Login as `maria.ops@talentweave.com` / `maria@123`
- Point out: "The backend validates credentials, issues a JWT token, and the frontend routes to the correct dashboard based on the decoded role."

### 2. Show Resume Upload & AI Parsing
- In the Operations Dashboard, select **Backend Software Engineer** from the job dropdown
- Upload a real PDF resume
- Click **Upload & Parse Resume**
- Show the response: name, email, skills list, seniority level
- Explain: "The system uses pdfplumber to extract raw text in-memory, then Groq LLaMA 3.3 70B parses it into a strict Pydantic schema — no raw text is stored except the first 4000 characters."

### 3. Show AI Evaluation & MCQ Generation
- Find the uploaded candidate in the Candidate Pipeline section
- Click **Evaluate**
- Show: match score, skill gaps, strength areas, and the 3 MCQ questions
- Explain: "The LLM compares the candidate's skills against the job requirements, identifies the top 3 weaknesses, and generates targeted technical questions — not generic ones."

### 4. Show the Lifecycle Transition Bridge
- Click **Hire** on the evaluated candidate
- Show the response: new corporate email, assigned role, tasks generated
- Explain: "This is a single atomic SQL transaction. If creating the user fails, the entire operation rolls back. The candidate is now an authenticated employee."

### 5. Show Agentic Onboarding Plan
- Logout from Maria
- Login with the new corporate email (e.g., `john.engineering@talentweave.com`) and password `Welcome@123`
- Show the Employee Workspace with 6 AI-generated tasks grouped by Day 1, Day 3, Day 5, Day 7
- Explain: "The system queried a local FAISS vector store filtered by role, retrieved only the engineering documentation, and used the LLM to build this plan. A sales hire would get a completely different plan from different documents."

### 6. Show Task Completion & State Mutation
- Check off a task
- Show the progress bar updating
- Explain: "Each checkbox triggers a PATCH request to the FastAPI backend, updating the SQL row from 'pending' to 'completed'. The state is persistent — refreshing the page preserves all completed tasks."

### 7. Show Role-Based Access Control
- Login as `alex.dev@talentweave.com` / `alex@123`
- Confirm Alex only sees the Employee Workspace — no access to recruitment features
- Explain: "The `require_role()` dependency on every protected endpoint checks the role decoded from the JWT token and returns 403 Forbidden for unauthorized access."

---

## Key Engineering Decisions

### Why FAISS over a hosted vector DB?
FAISS runs fully locally with no API costs and no network latency. For a demo platform with a small corpus of policy documents, it is the optimal choice. Pinecone or Weaviate would be appropriate when the document corpus scales to thousands of files.

### Why Groq LLaMA over OpenAI GPT?
Groq's inference API is significantly faster (lower latency per token) and free-tier accessible, making it ideal for a demo platform where multiple LLM calls happen per recruitment cycle. The LLaMA 3.3 70B Versatile model produces structured outputs reliably with `temperature=0`.

### Why Separate `candidates` and `users` tables?
Domain separation. A candidate is an external entity with a resume and application. A user is an authenticated internal employee. Merging them into one table would corrupt the domain model and prevent clean lifecycle tracking. The transition bridge is the architectural boundary between the two.

### Why ACID transactions for the hire event?
The hire event modifies two tables simultaneously (applications + users). If the application status updates to "hired" but the user creation fails, the system would show a hired candidate with no login credentials — an unrecoverable state. SQLAlchemy's `db.rollback()` on exception prevents this.

### Why Pydantic for LLM outputs?
LLMs produce unstructured text. Without Pydantic schema binding via LangChain's `.with_structured_output()`, the LLM could return inconsistent formats that crash the database insert. Pydantic enforces field types, required fields, and validation before any data touches the database.

### Why metadata-filtered RAG over a single shared index?
Without metadata filtering, a query for "onboarding tasks" would return chunks from both engineering guides and sales playbooks simultaneously. This "context pollution" would cause the LLM to generate technically incorrect plans (e.g., telling a sales rep to clone a Git repository). The `target_role` metadata tag on every chunk ensures each role's AI receives only their authorized documentation.

---

## Project Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         TALENTWEAVE FLOW                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  RECRUITMENT MODULE                                                 │
│  ─────────────────                                                  │
│  [PDF Resume] → pdfplumber → raw_text                               │
│       │                                                             │
│       ▼                                                             │
│  Groq LLaMA (structured output) → {name, email, skills, level}     │
│       │                                                             │
│       ▼                                                             │
│  candidates table + applications table (status: new)               │
│       │                                                             │
│       ▼                                                             │
│  Groq LLaMA (evaluation) → match_score + MCQ questions             │
│       │                                                             │
│       ▼                                                             │
│  applications table (status: screening, ai_match_score populated)  │
│                                                                     │
│  LIFECYCLE BRIDGE                                                   │
│  ────────────────                                                   │
│  Operations Admin clicks Hire                                       │
│       │                                                             │
│       ▼                                                             │
│  BEGIN SQL TRANSACTION                                              │
│  ├── applications.status → hired                                    │
│  └── users INSERT (new corporate identity)                          │
│  COMMIT (or ROLLBACK if any step fails)                             │
│                                                                     │
│  ONBOARDING ENGINE                                                  │
│  ─────────────────                                                  │
│  new user.role → FAISS metadata filter                              │
│       │                                                             │
│       ▼                                                             │
│  Role-locked document chunks retrieved                              │
│       │                                                             │
│       ▼                                                             │
│  Groq LLaMA → 6 structured TaskGenerationItem objects              │
│       │                                                             │
│       ▼                                                             │
│  onboarding_plans + onboarding_tasks tables populated               │
│       │                                                             │
│       ▼                                                             │
│  Employee logs in → checks tasks → PATCH /task/{id}/complete       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## requirements.txt (Backend)

```
fastapi
uvicorn
sqlalchemy
psycopg2-binary
pydantic-settings
python-dotenv
passlib[bcrypt]==1.7.4
bcrypt==4.0.1
python-jose[cryptography]
python-multipart
pdfplumber
langchain
langchain-community
langchain-groq
langchain-huggingface
faiss-cpu
sentence-transformers
groq
streamlit
requests
```

---

*Built with FastAPI · LangChain · Groq LLaMA 3.3 · FAISS · PostgreSQL · Streamlit*
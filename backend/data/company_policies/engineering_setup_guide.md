# Engineering Setup Guide — TalentWeave Internal

## Target Role: Software Engineer

## 1. Repository Access
- Clone the main backend repository from the internal GitHub organization.
- Request access from your team lead within Day 1.
- Repository URL: github.com/talentweave/backend-core

## 2. Local Environment Setup
- Install Docker Desktop from docker.com
- Install Python 3.11+ and create a virtual environment
- Run `docker-compose up` from the project root to spin up all services
- Verify PostgreSQL is running on port 5432

## 3. Development Tools
- Install VS Code with the Python and Docker extensions
- Configure your `.env` file using the `.env.example` template
- Install all dependencies via `pip install -r requirements.txt`

## 4. Codebase Orientation
- The backend follows a FastAPI layered architecture
- All API routes live under `backend/app/api/v1/endpoints/`
- Database models are defined using SQLAlchemy ORM
- Run `uvicorn main:app --reload` to start the local dev server

## 5. Pull Request Guidelines
- Always create a feature branch from `develop`
- Branch naming convention: `feature/your-name-feature-description`
- PRs require at least one peer review before merging
- Run all tests before submitting a PR

## 6. QA & Testing
- Unit tests live under `backend/tests/`
- Use `pytest` to run the full test suite
- Integration tests require Docker services to be running
- Bug reports go into the Linear project board under your team's workspace
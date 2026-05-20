import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine, Base
from app.models import User, UserRole
from app.models.recruitment import Job
from app.core.config import settings
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SEED_PASSWORDS = {
    "maria.ops@talentweave.com": "maria@123",
    "rahul.ops@talentweave.com": "rahul@123",
    "alex.dev@talentweave.com": "alex@123",
    "priya.dev@talentweave.com": "priya@123",
    "kevin.dev@talentweave.com": "kevin@123",
    "rohan.dev@talentweave.com": "rohan@123",
    "sarah.sales@talentweave.com": "sarah@123",
    "amit.sales@talentweave.com": "amit@123",
    "viktor.sales@talentweave.com": "viktor@123",
    "neha.sales@talentweave.com": "neha@123",
}

SEED_NAMES = {
    "maria.ops@talentweave.com": "Maria",
    "rahul.ops@talentweave.com": "Rahul",
    "alex.dev@talentweave.com": "Alex",
    "priya.dev@talentweave.com": "Priya",
    "kevin.dev@talentweave.com": "Kevin",
    "rohan.dev@talentweave.com": "Rohan",
    "sarah.sales@talentweave.com": "Sarah",
    "amit.sales@talentweave.com": "Amit",
    "viktor.sales@talentweave.com": "Viktor",
    "neha.sales@talentweave.com": "Neha",
}

SEED_JOBS = [
    {
        "title": "Backend Software Engineer",
        "department": "Engineering",
        "requirements": """
We are looking for a skilled Backend Software Engineer to join our core engineering team.

Required Skills:
- Strong proficiency in Python and FastAPI or Django REST Framework
- Solid understanding of PostgreSQL and SQLAlchemy ORM
- Experience with Docker and containerized deployments
- Familiarity with REST API design principles and JWT authentication
- Knowledge of asynchronous programming using async/await
- Experience with Git version control and pull request workflows
- Understanding of CI/CD pipelines and automated testing with pytest

Responsibilities:
- Design and maintain scalable backend API services
- Write clean, testable, and well-documented Python code
- Collaborate with frontend and DevOps teams on system integration
- Participate in code reviews and architectural discussions
- Debug production issues and optimize database query performance

Experience Required: 2 to 5 years of professional backend development experience.
        """,
        "status": "active"
    },
    {
        "title": "Outbound Sales Account Executive",
        "department": "Sales",
        "requirements": """
We are hiring a high-performing Outbound Sales Account Executive to drive new business revenue.

Required Skills:
- Proven experience with CRM platforms, preferably Salesforce
- Strong cold-calling and outbound email sequence execution skills
- Ability to develop and deliver compelling product demonstrations
- Experience with consultative selling methodologies (SPIN, Challenger)
- Familiarity with lead qualification frameworks such as BANT or MEDDIC
- Excellent written and verbal communication skills
- Ability to manage a pipeline of 50 or more active prospects simultaneously
- Track record of consistently meeting or exceeding monthly sales quotas

Responsibilities:
- Prospect and qualify new enterprise and mid-market leads
- Execute structured outbound email and call sequences daily
- Conduct discovery calls and product demos with decision makers
- Negotiate contract terms and close deals within assigned territory
- Maintain accurate and up-to-date records inside the CRM dashboard

Experience Required: 2 to 6 years of outbound B2B sales experience.
        """,
        "status": "active"
    },
    {
        "title": "HR Operations Coordinator",
        "department": "Operations",
        "requirements": """
We are seeking a detail-oriented HR Operations Coordinator to manage our internal people processes.

Required Skills:
- Experience with HR Information Systems and employee lifecycle management
- Strong understanding of onboarding workflows and compliance documentation
- Proficiency in tools like Notion, Google Workspace, and project trackers
- Ability to coordinate across multiple departments simultaneously
- Knowledge of labor compliance regulations and HR policy frameworks
- Strong data management skills for maintaining accurate employee records
- Experience facilitating new hire orientation programs

Responsibilities:
- Manage end-to-end employee onboarding and offboarding processes
- Maintain accurate records across HR systems and internal databases
- Coordinate with department leads to schedule interviews and reviews
- Draft and distribute HR policy documents and internal communications
- Track onboarding task completion rates and report metrics to leadership

Experience Required: 1 to 4 years of HR operations or people operations experience.
        """,
        "status": "active"
    }
]


def seed():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing = db.query(User).count()
        if existing > 0:
            print(f"Database already has {existing} users. Skipping seed.")
        else :
            print("Seeding 10 users...")
            for user_data in settings.SYSTEM_SEED_USERS:
                email = user_data["email"]
                user = User(
                    full_name=SEED_NAMES[email],
                    email=email,
                    hashed_password=pwd_context.hash(SEED_PASSWORDS[email]),
                    role=UserRole(user_data["role"]),
                    level=user_data.get("level"),
                    dept=user_data.get("dept"),
                )
                db.add(user)
            db.commit()
            print("✅ Successfully seeded 10 users into the database.")

        # Seed Jobs
        existing_jobs = db.query(Job).count()
        if existing_jobs > 0:
            print(f"Jobs already seeded ({existing_jobs} found). Skipping jobs.")
        else:
            print("Seeding 3 jobs...")
            for job_data in SEED_JOBS:
                job = Job(
                    title=job_data["title"],
                    department=job_data["department"],
                    requirements=job_data["requirements"],
                    status=job_data["status"]
                )
                db.add(job)
            db.commit()
            print("✅ Successfully seeded 3 jobs.")

            
    except Exception as e:
        db.rollback()
        print(f"❌ Seed failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
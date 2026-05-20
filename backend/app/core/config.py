# config.py
from pydantic_settings import BaseSettings
from typing import List, Dict, Any

class AppConfig(BaseSettings):
    # System Environment Meta
    PROJECT_NAME: str = "TalentWeave"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    GMAIL_SENDER: str = ""
    GMAIL_APP_PASSWORD: str = ""
    DATABASE_URL: str = ""
    SECRET_KEY: str = ""
    HF_TOKEN: str = ""
    GROQ_API_KEY: str = ""
    GMAIL_SENDER: str = ""
    GMAIL_APP_PASSWORD: str = ""
    # Strict Role Declarations
    ALLOWED_ROLES: List[str] = ["operations_team", "software_engineer", "sales_team"]
    
    # Hardcoded 10-User Mock Configuration Constraints
    SYSTEM_SEED_USERS: List[Dict[str, Any]] = [
        {"email": "maria.ops@talentweave.com", "role": "operations_team", "dept": "HR"},
        {"email": "rahul.ops@talentweave.com", "role": "operations_team", "dept": "HR"},
        
        {"email": "alex.dev@talentweave.com", "role": "software_engineer", "level": "junior"},
        {"email": "priya.dev@talentweave.com", "role": "software_engineer", "level": "mid"},
        {"email": "kevin.dev@talentweave.com", "role": "software_engineer", "level": "senior"},
        {"email": "rohan.dev@talentweave.com", "role": "software_engineer", "level": "junior"},
        
        {"email": "sarah.sales@talentweave.com", "role": "sales_team", "level": "mid"},
        {"email": "amit.sales@talentweave.com", "role": "sales_team", "level": "senior"},
        {"email": "viktor.sales@talentweave.com", "role": "sales_team", "level": "lead"},
        {"email": "neha.sales@talentweave.com", "role": "sales_team", "level": "junior"}
    ]

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = AppConfig()
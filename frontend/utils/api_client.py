import requests
import streamlit as st

BASE_URL = "http://127.0.0.1:8000/api/v1"

def get_headers():
    token = st.session_state.get("token", "")
    return {"Authorization": f"Bearer {token}"}

def login_user(email: str, password: str):
    try:
        res = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
        return res.json(), res.status_code
    except Exception as e:
        return {"detail": str(e)}, 500

def upload_resume(file, job_id: int = 1):
    try:
        files = {"file": (file.name, file.getvalue(), "application/pdf")}
        res = requests.post(f"{BASE_URL}/recruitment/upload-resume?job_id={job_id}", files=files, headers=get_headers())
        return res.json(), res.status_code
    except Exception as e:
        return {"detail": str(e)}, 500

def evaluate_application(application_id: int):
    try:
        res = requests.post(f"{BASE_URL}/recruitment/applications/{application_id}/evaluate", headers=get_headers())
        return res.json(), res.status_code
    except Exception as e:
        return {"detail": str(e)}, 500

def hire_candidate(application_id: int, temp_password: str = "Welcome@123"):
    try:
        res = requests.post(
            f"{BASE_URL}/onboarding/hire/{application_id}",
            json={"temporary_password": temp_password},
            headers=get_headers()
        )
        return res.json(), res.status_code
    except Exception as e:
        return {"detail": str(e)}, 500

def get_all_candidates():
    try:
        res = requests.get(f"{BASE_URL}/recruitment/candidates", headers=get_headers())
        return res.json(), res.status_code
    except Exception as e:
        return {"detail": str(e)}, 500

def get_onboarding_plan(user_id: int):
    try:
        res = requests.get(f"{BASE_URL}/onboarding/plan/{user_id}", headers=get_headers())
        return res.json(), res.status_code
    except Exception as e:
        return {"detail": str(e)}, 500

def complete_task(task_id: int):
    try:
        res = requests.patch(f"{BASE_URL}/onboarding/task/{task_id}/complete", headers=get_headers())
        return res.json(), res.status_code
    except Exception as e:
        return {"detail": str(e)}, 500

def get_all_users():
    try:
        res = requests.get(f"{BASE_URL}/onboarding/users", headers=get_headers())
        return res.json(), res.status_code
    except Exception as e:
        return {"detail": str(e)}, 500
    


def create_job(job_data: dict, pdf_file=None):
    try:
        data = {k: str(v) for k, v in job_data.items()}
        files = {}
        if pdf_file:
            files["assignment_pdf"] = (pdf_file.name, pdf_file.getvalue(), "application/pdf")
        res = requests.post(
            f"{BASE_URL}/recruitment/jobs/create",
            data=data,
            files=files if files else None,
            headers=get_headers()
        )
        return res.json(), res.status_code
    except Exception as e:
        return {"detail": str(e)}, 500

def get_exam_attempts(job_id: int):
    try:
        res = requests.get(f"{BASE_URL}/recruitment/jobs/{job_id}/exam-attempts", headers=get_headers())
        return res.json(), res.status_code
    except Exception as e:
        return {"detail": str(e)}, 500

def get_assignment_submissions(job_id: int):
    try:
        res = requests.get(f"{BASE_URL}/recruitment/jobs/{job_id}/assignment-submissions", headers=get_headers())
        return res.json(), res.status_code
    except Exception as e:
        return {"detail": str(e)}, 500

def send_meet_invite(application_id: int):
    try:
        res = requests.post(f"{BASE_URL}/recruitment/send-meet/{application_id}", headers=get_headers())
        return res.json(), res.status_code
    except Exception as e:
        return {"detail": str(e)}, 500

def get_all_jobs():
    try:
        res = requests.get(f"{BASE_URL}/recruitment/jobs", headers=get_headers())
        return res.json(), res.status_code
    except Exception as e:
        return {"detail": str(e)}, 500
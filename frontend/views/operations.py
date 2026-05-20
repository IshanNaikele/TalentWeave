import streamlit as st
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
 
from utils.api_client import (
    evaluate_application, hire_candidate,
    get_all_candidates, create_job, get_exam_attempts,
    get_assignment_submissions, send_meet_invite, get_all_jobs
)
def show():
    st.title("🏢 Operations Dashboard")
    st.markdown(f"Welcome, **{st.session_state.get('full_name', 'Admin')}** | Role: `operations_team`")
    st.divider()

    tab1, tab2, tab3 = st.tabs(["➕ Create Job", "👥 Candidates", "📦 Assignments"])

    # ── TAB 1: Job Creation ───────────────────────────────────────────────
    with tab1:
        st.subheader("Create New Job Opening")

        title = st.text_input("Job Title")
        department = st.selectbox("Department", ["Engineering", "Sales", "Operations"])
        requirements = st.text_area("Job Description", height=200)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
            num_questions = st.number_input("Questions", min_value=5, max_value=30, value=10)
        with col2:
            pass_threshold = st.number_input("Pass Threshold (%)", min_value=10, max_value=100, value=70)
            filter_mode = st.selectbox("Filter Mode", ["fixed_threshold", "top_percentile"])
        with col3:
            screening_duration_minutes = st.number_input("Screening Window (mins)", min_value=1, value=60)
            recruiter_email = st.text_input("Recruiter Email", value="maria.ops@talentweave.com")

        include_assignment = st.toggle("Include Assignment Round")
        assignment_pdf = None
        assignment_duration_minutes = None
        if include_assignment:
            assignment_pdf = st.file_uploader("Upload Assignment PDF", type=["pdf"])
            assignment_duration_minutes = st.number_input("Assignment Window (mins)", min_value=1, value=2880)

        if st.button("🚀 Create Job"):
            if not title or not requirements or not recruiter_email:
                st.error("Title, requirements, and recruiter email are required.")
            elif include_assignment and not assignment_pdf:
                st.error("Please upload an assignment PDF.")
            else:
                job_data = {
                    "title": title,
                    "department": department,
                    "requirements": requirements,
                    "difficulty": difficulty,
                    "num_questions": num_questions,
                    "pass_threshold": pass_threshold,
                    "filter_mode": filter_mode,
                    "percentile_cutoff": 5.0,
                    "screening_duration_minutes": screening_duration_minutes,
                    "include_assignment": include_assignment,
                    "recruiter_email": recruiter_email,
                }
                if include_assignment and assignment_duration_minutes:
                    job_data["assignment_duration_minutes"] = assignment_duration_minutes

                with st.spinner("Creating job..."):
                    res, code = create_job(job_data, assignment_pdf)

                if code == 201:
                    st.success("✅ Job created!")
                    st.write(f"**Job ID:** {res.get('job_id')}")
                    st.write("**Share this link with candidates:**")
                    st.code(res.get("candidate_portal_url", ""))
                    st.write(f"**Screening Deadline:** {res.get('screening_deadline')}")
                else:
                    st.error(f"❌ {res.get('detail', 'Job creation failed')}")

     

    # ── TAB 3: Candidate Pipeline ─────────────────────────────────────────
    with tab2:
        st.subheader("Candidate Pipeline")

        # Job selector for exam scores
        jobs_data, jobs_code = get_all_jobs()
        job_map = {}
        if jobs_code == 200 and isinstance(jobs_data, list):
            job_map = {f"{j['title']} (ID: {j['job_id']})": j['job_id'] for j in jobs_data}
        exam_score_map = {}
        if job_map:
            selected_job_label = st.selectbox("Filter by Job (for exam scores)", list(job_map.keys()))
            selected_job_id = job_map[selected_job_label]

            attempts_data, _ = get_exam_attempts(selected_job_id)
             
            if isinstance(attempts_data, list):
                for a in attempts_data:
                    exam_score_map[a["candidate_email"]] = a

        data, code = get_all_candidates()
        if code == 200 and data:
            for candidate in data:
                email = candidate.get("email", "")
                exam_info = exam_score_map.get(email) if job_map else None

                with st.expander(f"📋 {candidate['full_name']} — {email}"):
                    skills = json.loads(candidate.get('extracted_skills') or '[]')
                    st.write(f"**Skills:** {', '.join(skills) if skills else 'Not parsed'}")
                    st.write(f"**Status:** `{candidate.get('status', 'N/A')}`")
                    st.write(f"**LLM Match Score:** {candidate.get('ai_match_score') or 'Not evaluated'}")

                    if exam_info:
                        score = exam_info["score"]
                        passed = exam_info["passed"]
                        badge = "🟢 Pass" if passed else "🔴 Fail"
                        st.write(f"**Exam Score:** {score}/100 — {badge}")

                    app_id = candidate.get("application_id")
                    if not app_id:
                        st.warning("No application linked.")
                        continue

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("🔍 Evaluate", key=f"eval_{app_id}"):
                            with st.spinner("Running AI evaluation..."):
                                res, c = evaluate_application(app_id)
                            if c == 200:
                                st.success(f"Match Score: {res.get('match_score')}")
                            else:
                                st.error(res.get("detail", "Evaluation failed"))
                    with col2:
                        status = candidate.get("status", "")
                        if status == "hired":
                            st.success("✅ Already Hired")
                        else:
                            if st.button("✅ Hire", key=f"hire_{app_id}"):
                                with st.spinner("Processing hire..."):
                                    res, c = hire_candidate(app_id)
                                if c == 200:
                                    st.success(f"🎉 Hired! Email: {res.get('corporate_email')}")
                                    st.rerun()
                                else:
                                    st.error(res.get("detail", "Hire failed"))
                    with col3:
                        if exam_info and exam_info.get("passed"):
                            if st.button("📧 Send Meet", key=f"meet_{app_id}"):
                                res, c = send_meet_invite(app_id)
                                if c == 200:
                                    st.success("Meet invite sent!")
                                else:
                                    st.error(res.get("detail", "Failed"))
        else:
            st.info("No candidates found.")

    # ── TAB 4: Assignment Submissions ─────────────────────────────────────
    with tab3:
        st.subheader("Assignment Submissions")

        jobs_data2, jobs_code2 = get_all_jobs()
        if jobs_code2 == 200 and isinstance(jobs_data2, list):
            assignment_jobs = [j for j in jobs_data2 if j.get("include_assignment")]
            if not assignment_jobs:
                st.info("No jobs with assignment rounds found.")
            else:
                job_map2 = {f"{j['title']} (ID: {j['job_id']})": j['job_id'] for j in assignment_jobs}
                selected = st.selectbox("Select Job", list(job_map2.keys()), key="assign_job_select")
                sel_job_id = job_map2[selected]

                subs, s_code = get_assignment_submissions(sel_job_id)
                if s_code == 200 and isinstance(subs, list) and subs:
                    for s in subs:
                        with st.expander(f"📋 {s['candidate_name']} — {s['candidate_email']}"):
                            st.write(f"**GitHub:** {s['github_link']}")
                            st.write(f"**LinkedIn:** {s['linkedin']}")
                            if s.get("deployment_url"):
                                st.write(f"**Deployment:** {s['deployment_url']}")
                            if s.get("notes"):
                                st.write(f"**Notes:** {s['notes']}")
                            st.write(f"**Submitted:** {s['submitted_at']}")

                            if st.button("✅ Approve for Interview", key=f"approve_{s['application_id']}"):
                                with st.spinner("Processing hire..."):
                                    res, c = hire_candidate(s["application_id"])
                                if c == 200:
                                    st.success(f"🎉 Hired! Email: {res.get('corporate_email')}")
                                    st.rerun()
                                else:
                                    st.error(res.get("detail", "Hire failed"))
                else:
                    st.info("No submissions yet for this job.")
        else:
            st.info("Could not load jobs.")
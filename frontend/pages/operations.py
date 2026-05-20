import streamlit as st
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.api_client import upload_resume, evaluate_application, hire_candidate, get_all_candidates

def show():
    st.title("🏢 Operations Dashboard")
    st.markdown(f"Welcome, **{st.session_state.get('full_name', 'Admin')}** | Role: `operations_team`")
    st.divider()

    # Section 1 - Upload Resume
    st.subheader("📄 Upload Candidate Resume")
    uploaded_file = st.file_uploader("Upload PDF Resume", type=["pdf"])

    job_options = {
        "Backend Software Engineer (Engineering)": 1,
        "Outbound Sales Account Executive (Sales)": 2,
        "HR Operations Coordinator (Operations)": 3
    }
    selected_job = st.selectbox("Select Job Opening", list(job_options.keys()))
    job_id = job_options[selected_job]

    if uploaded_file:
        if st.button("🚀 Upload & Parse Resume"):
            with st.spinner("Parsing resume with AI..."):
                result, code = upload_resume(uploaded_file, job_id)
            if code == 201:
                st.success(f"✅ Resume parsed successfully!")
                st.json(result)
            else:
                st.error(f"❌ Error: {result.get('detail', 'Unknown error')}")

    st.divider()

    # Section 2 - Candidate Pipeline
    st.subheader("👥 Candidate Pipeline")

    data, code = get_all_candidates()
    if code == 200 and data:
        for candidate in data:
            with st.expander(f"📋 {candidate['full_name']} — {candidate['email']}"):
                skills = json.loads(candidate.get('extracted_skills') or '[]')
                st.write(f"**Skills:** {', '.join(skills) if skills else 'Not parsed'}")
                st.write(f"**Application ID:** {candidate.get('application_id', 'N/A')}")
                st.write(f"**Status:** `{candidate.get('status', 'N/A')}`")
                st.write(f"**Match Score:** {candidate.get('ai_match_score') or 'Not evaluated'}")

                app_id = candidate.get("application_id")
                if not app_id:
                    st.warning("No application linked.")
                    continue

                col1, col2 = st.columns(2)

                with col1:
                    if st.button(f"🔍 Evaluate", key=f"eval_{app_id}"):
                        with st.spinner("Running AI evaluation..."):
                            res, c = evaluate_application(app_id)
                        if c == 200:
                            st.success(f"✅ Match Score: {res.get('match_score')}")
                            st.write(f"**Gaps:** {', '.join(res.get('skill_gaps', []))}")
                            st.write(f"**Strengths:** {', '.join(res.get('strength_areas', []))}")
                        else:
                            st.error(res.get("detail", "Evaluation failed"))

                with col2:
                    status = candidate.get("status", "")
                    if status == "hired":
                        st.success("✅ Already Hired")
                    else:
                        if st.button(f"✅ Hire", key=f"hire_{app_id}"):
                            with st.spinner("Processing hire..."):
                                res, c = hire_candidate(app_id)
                            if c == 200:
                                st.success(f"🎉 Hired! Corporate Email: {res.get('corporate_email')}")
                                st.write(f"Onboarding tasks generated: {res.get('onboarding_tasks_generated')}")
                                st.rerun()
                            else:
                                st.error(res.get("detail", "Hire failed"))
    else:
        st.info("No candidates found. Upload a resume to get started.")
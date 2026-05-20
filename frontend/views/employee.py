import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.api_client import get_onboarding_plan, complete_task

def show():
    st.title("👤 My Workspace")
    st.markdown(f"Welcome, **{st.session_state.get('full_name', 'Employee')}**")
    st.write(f"Role: `{st.session_state.get('role', '')}` | User ID: `{st.session_state.get('user_id', '')}`")
    st.divider()

    user_id = st.session_state.get("user_id")
    if not user_id:
        st.error("User ID not found. Please login again.")
        return

    data, code = get_onboarding_plan(user_id)

    if code == 404:
        st.info("📋 No onboarding plan assigned yet. Please check back later.")
        return

    if code != 200:
        st.error(f"Could not fetch onboarding plan: {data.get('detail', 'Unknown error')}")
        return

    tasks = data.get("tasks", [])
    total = data.get("total_tasks", 0)
    completed = sum(1 for t in tasks if t["status"] == "completed")

    st.subheader(f"📊 Progress: {completed}/{total} tasks completed")
    st.progress(completed / total if total > 0 else 0)
    st.divider()

    # Group tasks by due_day
    days = sorted(set(t["due_day"] for t in tasks))

    for day in days:
        st.subheader(f"📅 Day {day} Tasks")
        day_tasks = [t for t in tasks if t["due_day"] == day]

        for task in day_tasks:
            task_id = task["task_id"]
            is_done = task["status"] == "completed"

            col1, col2 = st.columns([0.08, 0.92])
            with col1:
                checked = st.checkbox("", value=is_done, key=f"task_{task_id}", disabled=is_done)
            with col2:
                if is_done:
                    st.markdown(f"~~**{task['title']}**~~ ✅")
                else:
                    st.markdown(f"**{task['title']}**")
                st.caption(task["description"])

            if checked and not is_done:
                with st.spinner("Marking as complete..."):
                    res, c = complete_task(task_id)
                if c == 200:
                    st.success(f"✅ Task marked complete!")
                    st.rerun()
                else:
                    st.error("Failed to update task.")

        st.divider()
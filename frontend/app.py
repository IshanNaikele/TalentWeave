import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.api_client import login_user
from pages.operations import show as show_operations
from pages.employee import show as show_employee

st.set_page_config(
    page_title="TalentWeave",
    page_icon="🧵",
    layout="wide"
)

# Initialize session state
if "token" not in st.session_state:
    st.session_state.token = None
if "role" not in st.session_state:
    st.session_state.role = None
if "full_name" not in st.session_state:
    st.session_state.full_name = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None


def show_login():
    st.title("🧵 TalentWeave")
    st.subheader("AI-Powered Talent & Onboarding Platform")
    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🔐 Login")
        email = st.text_input("Email", placeholder="Enter your email")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        if st.button("Login", use_container_width=True, type="primary"):
            if not email or not password:
                st.warning("Please enter both email and password.")
            else:
                with st.spinner("Authenticating..."):
                    result, code = login_user(email, password)

                if code == 200:
                    st.session_state.token = result["access_token"]
                    st.session_state.role = result["role"]
                    st.session_state.full_name = result["full_name"]

                    # Decode user_id from token
                    import base64, json
                    try:
                        payload = result["access_token"].split(".")[1]
                        payload += "=" * (4 - len(payload) % 4)
                        decoded = json.loads(base64.b64decode(payload))
                        st.session_state.user_id = int(decoded.get("sub", 0))
                    except:
                        st.session_state.user_id = None

                    st.success(f"Welcome, {result['full_name']}!")
                    st.rerun()
                else:
                    st.error(f"❌ {result.get('detail', 'Login failed')}")


def show_sidebar():
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.full_name}")
        st.markdown(f"Role: `{st.session_state.role}`")
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            for key in ["token", "role", "full_name", "user_id"]:
                st.session_state[key] = None
            st.rerun()


# Main router
if not st.session_state.token:
    show_login()
else:
    show_sidebar()
    role = st.session_state.role

    if role == "operations_team":
        show_operations()
    elif role in ["software_engineer", "sales_team"]:
        show_employee()
    else:
        st.error("Unknown role. Please logout and login again.")
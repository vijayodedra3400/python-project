import streamlit as st
from database import init_db, login_user
from mentor_dashboard import mentor_dashboard
from student_dashboard import student_dashboard

# Set wide layout and custom page title/icon
st.set_page_config(page_title="Student Tracker 🎓", page_icon="🎓", layout="wide")
init_db()

# --- PROFESSIONAL & ENLARGED UI CSS INJECTION ---
st.markdown("""
    <style>
    /* 1. Base typography & Font Family */
    html, body, [class*="css"] {
        font-family: 'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Standardize all basic text */
    p, span, div, label {
        font-size: 17px !important;
    }
    
    /* 2. Adjusting Header Sizes */
    h1 {
        font-size: 64px !important;
        font-weight: 700 !important;+00
        margin-bottom: 0.5rem !important;
        padding-bottom: 0px !important;
    }
    h2 {
        font-size: 26px !important;
        font-weight: 600 !important;
        margin-top: 1rem !important;
    }
    h3 {
        font-size: 22px !important;
        font-weight: 600 !important;
    }
    
    /* 3. Metric Cards Styling */
    [data-testid="stMetricValue"] {
        font-size: 34px !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 16px !important;
        color: #555 !important;
        font-weight: 600 !important;
    }

    /* 4. Buttons */
    .stButton>button { 
        width: 100%; 
        border-radius: 6px; 
        font-size: 17px !important;
        font-weight: 600 !important;
        padding: 0.5rem 0.6rem !important;
    }
    
    /* 5. DataFrame (Tables) text size - MADE BIGGER */
    [data-testid="stDataFrame"] {
        font-size: 18px !important;
    }
    
    /* 6. Inputs */
    input, textarea, select {
        font-size: 16px !important;
    }
    </style>
""", unsafe_allow_html=True)

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    # --- Centered Login Layout ---
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>🎓 College Management System</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray; font-size: 16px !important;'>Please login to continue</p>", unsafe_allow_html=True)
        st.write("") # Spacer
        
        with st.form("login", clear_on_submit=True):
            u = st.text_input("Username", placeholder="Enter your username")
            p = st.text_input("Password", type="password", placeholder="Enter your password")
            
            submit_col1, submit_col2, submit_col3 = st.columns([1, 2, 1])
            with submit_col2:
                submitted = st.form_submit_button("Login", use_container_width=True)
                
            if submitted:
                user = login_user(u, p)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")

        st.info("💡 **Demo Login:** HOD → `hod` / `hod123`")

else:
    # --- Styled Sidebar ---
    st.sidebar.markdown(f"### 👋 Welcome, {st.session_state.user['username']}")
    st.sidebar.markdown(f"**Role:** `{st.session_state.user['role'].upper()}`")
    st.sidebar.divider()
    
    if st.sidebar.button("🚪 Logout", type="primary", use_container_width=True):
        st.session_state.user = None
        st.rerun()

    if st.session_state.user["role"] in ("mentor","hod"):
        mentor_dashboard()
    else:
        student_dashboard()
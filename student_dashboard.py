import streamlit as st
from database import get_student_marks, get_db_connection, get_attendance
import matplotlib.pyplot as plt
import pandas as pd

def student_dashboard(target_student_id=None):
    
    if target_student_id:
        uid = target_student_id
        st.markdown(f"### 👁️ Viewing Student Dashboard (ID: {uid})")
    else:
        # If logging in as a student, we need to use the username
        # database.login_user returns a dict with 'username', ensure we use that
        uid = st.session_state.user["username"]
        st.title("🎓 Student Dashboard")

    # ---------- PROFILE ----------
    con = get_db_connection()
    # FIX: Changed 'user_id=?' to 'username=?'
    p = con.execute(
        "SELECT * FROM student_details WHERE username=?", (uid,)
    ).fetchone()
    con.close()

    if not p:
        st.error(f"Student details not found for user: {uid}")
        return

    # Schema indices: 
    # 0:username, 1:full_name, 2:age, 3:college, 4:dept, 5:address, 6:city, 7:mobile
    st.subheader("👤 Profile")
    st.write(f"**Name:** {p[1]} | **Dept:** {p[4]} | **College:** {p[3]}")
    st.write(f"**City:** {p[6]} | **Mobile:** {p[7]}")

    st.divider()

    # ---------- MARKS ----------
    df = get_student_marks(uid)

    if df.empty:
        st.info("📌 Marks have not been assigned yet.")
    else:
        st.subheader("📊 Performance Summary")

        total_subjects = len(df)
        avg_marks = round(df["score"].mean(), 2)
        max_marks = df["score"].max()
        min_marks = df["score"].min()

        def calculate_grade(score):
            if score >= 85: return "A"
            elif score >= 70: return "B"
            else: return "C"

        df["Grade"] = df["score"].apply(calculate_grade)
        
        grade_points = {"A": 3, "B": 2, "C": 1}
        df["Grade Point"] = df["Grade"].map(grade_points)
        avg_gp = df["Grade Point"].mean()
        
        if avg_gp >= 2.5: avg_grade = "A"
        elif avg_gp >= 1.5: avg_grade = "B"
        else: avg_grade = "C"

        status = "Passed" if avg_marks >= 40 else "Needs Improvement"
        status_color = "green" if avg_marks >= 40 else "orange"

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("📚 Subjects", total_subjects)
        c2.metric("📈 Avg", avg_marks)
        c3.metric("🎓 Grade", avg_grade)
        c4.metric("🏆 High", max_marks)
        c5.metric("🔻 Low", min_marks)
        c6.metric("📌 Status", status)

        st.markdown(f"<h4 style='color:{status_color}'>Result: {status}</h4>", unsafe_allow_html=True)
        st.divider()

        # Graph
        st.subheader("📈 Marks Overview")
        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(5.5, 3))        
        ax.bar(df["subject"], df["score"], width=0.2, color="#04A126")
        ax.set_ylim(0, 100)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        
        fig.patch.set_facecolor("#0E1117")
        ax.set_facecolor("#0E1117")
        
        st.pyplot(fig, use_container_width=False)       
        st.dataframe(df.rename(columns={"subject": "Subject", "score": "Marks"}), use_container_width=True)
        st.divider()

    # ---------- ATTENDANCE (UPDATED) ----------
    st.subheader("📅 Attendance Summary")
    
    # Calculate directly from the logs
    att_stats = get_attendance(uid)
    total = att_stats["total_classes"]
    attended = att_stats["present_classes"]

    if total == 0:
        st.info("📌 Attendance has not started yet.")
    else:
        percent = round((attended / total) * 100, 2)
        eligibility = "Eligible" if percent >= 75 else "Not Eligible"
        color = "green" if percent >= 75 else "red"

        a1, a2, a3, a4 = st.columns(4)
        a1.metric("Total Days", total)
        a2.metric("Present Days", attended)
        a3.metric("%", f"{percent}%")
        a4.metric("Status", eligibility)

        st.markdown(f"<h4 style='color:{color}'>Status: {eligibility}</h4>", unsafe_allow_html=True)
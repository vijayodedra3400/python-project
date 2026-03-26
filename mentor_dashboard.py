import streamlit as st
import datetime
import pandas as pd
import plotly.express as px

from database import (
    DEPARTMENTS, get_total_students, get_total_faculty, get_avg_score,
    get_grade_wise_students, get_student_list, register_student, register_faculty,
    faculty_count_for_subject, get_faculty_details, search_students, search_faculty,
    get_students_for_attendance, save_attendance_log, get_all_attendance_summary,
    get_all_students, get_all_faculty, delete_user, is_valid_mobile, get_all_divisions,
    get_division_result, recalculate_divisions, get_division_marks_data, update_all_marks,
    update_faculty_division # <-- Make sure this is imported!
)
from student_dashboard import student_dashboard

# --- POP UP DIALOG ---
@st.dialog("Assign Marks")
def open_grading_popup(student_id, student_name, current_marks):
    st.write(f"Grading Student: **{student_name}**")
    
    with st.form("grading_form"):
        c1, c2 = st.columns(2)
        ps = c1.number_input("PS", 0, 100, value=current_marks.get("PS", 0))
        de = c1.number_input("DE", 0, 100, value=current_marks.get("DE", 0))
        py = c2.number_input("Python", 0, 100, value=current_marks.get("Python", 0))
        fsd = c2.number_input("FSD", 0, 100, value=current_marks.get("FSD", 0))
        
        if st.form_submit_button("💾 Save Marks", type="primary"):
            update_all_marks(student_id, ps, de, py, fsd)
            st.toast(f"✅ Marks updated for {student_name}!")
            st.rerun()

def mentor_dashboard():
    user = st.session_state.user
    role = user["role"]
    uid = user["username"]

    st.title(f"👨‍🏫 {role.upper()} Dashboard")

    # ==================================================
    # 🔒 ROLE-BASED DIVISION FILTERING LOGIC
    # ==================================================
    all_divs = get_all_divisions()
    
    if role == "hod":
        avail_divs = all_divs # HOD sees everything
    else:
        # Mentor only sees their assigned division
        fac_det = get_faculty_details(uid)
        assigned_div = fac_det["assigned_div"] if fac_det else "None"
        
        if assigned_div and assigned_div != "None":
            avail_divs = [assigned_div] # Restrict the list to ONLY their division
            st.caption(f"📌 Your Assigned Division: **{assigned_div}**")
        else:
            avail_divs = [] # No division assigned yet
            st.warning("⚠️ You have not been assigned a division yet. Please contact the HOD.")

    # Added "🔄 Assign Mentor" to the HOD's tabs
    tabs_list = [
        "📊 Dashboard", "👀 View Student", "📊 Result Analysis", 
        "🎓 Add Student", "👨‍🏫 Add Faculty", "🔄 Assign Mentor", 
        "📝 Assign Marks", "📅 Attendance", "🗑 Remove Users"
    ] if role == "hod" else [
        "👀 View Student", "📊 Result Analysis", "🎓 Add Student", 
        "📝 Assign Marks", "📅 Attendance"
    ]
    tabs = st.tabs(tabs_list)
    t_idx = 0

    # ==================================================
    # 📊 DASHBOARD (HOD)
    # ==================================================
    if role == "hod":
        with tabs[t_idx]:
            c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
            with c1: st.metric("🎓 Students", get_total_students())
            with c2: st.metric("👨‍🏫 Faculty", get_total_faculty())
            with c3: st.metric("📈 Avg Marks", get_avg_score())
            with c4:
                st.write(" ")
                if st.button("🔄 Recalculate Divisions", use_container_width=True):
                    recalculate_divisions()
                    st.toast("✅ Global Divisions updated!")

            st.divider()

            grades = get_grade_wise_students()
            if grades:
                pc1, pc2 = st.columns([1, 3]) 
                with pc1:
                    st.subheader("Grade Distribution")
                    df_grades = pd.DataFrame(list(grades.items()), columns=["Grade", "Count"])
                    fig = px.pie(df_grades, values='Count', names='Grade', hole=0.5, 
                                 color_discrete_sequence=px.colors.sequential.Plasma)
                    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
                    st.plotly_chart(fig, use_container_width=True)

                with pc2:
                    view = st.pills("View Database Records", ["All Students", "All Faculty"], default="All Students")
                    if view == "All Students":
                        st.dataframe(get_all_students(), use_container_width=True, height=350)
                    elif view == "All Faculty":
                        st.dataframe(get_all_faculty(), use_container_width=True, height=350)

        t_idx += 1

    # ==================================================
    # 👀 VIEW STUDENT
    # ==================================================
    with tabs[t_idx]:
        st.subheader("👀 View Student Profile")
        
        if avail_divs:
            with st.container(border=True):
                c1, c2 = st.columns(2)
                sel_div = c1.selectbox("Select Division", avail_divs, key="view_div_select")
                if sel_div:
                    students = get_student_list(sel_div)
                    if students:
                        opts = {f"{s['name']} ({s['username']})": s["id"] for s in students}
                        sel = c2.selectbox("Select Student", opts.keys(), key="view_stu_select")
                        st.divider()
                        if sel:
                            student_dashboard(target_student_id=opts[sel])
                    else:
                        st.warning("No students in this division.")
        else:
            st.info("No divisions available.")
    t_idx += 1

    # ==================================================
    # 📊 RESULT ANALYSIS
    # ==================================================
    with tabs[t_idx]:
        st.subheader("📊 Division Result Analysis")
        
        if avail_divs:
            res_div = st.selectbox("Select Division for Result", avail_divs, key="res_div_select")
            
            if res_div:
                df_res = get_division_result(res_div)
                
                if not df_res.empty:
                    df_res["Percentage"] = (df_res["total"] / 400) * 100
                    df_res["Status"] = df_res["Percentage"].apply(
                        lambda x: "✅ Pass" if x >= 33 else "❌ Fail"
                    )

                    st.dataframe(
                        df_res,
                        column_config={
                            "full_name": "Student Name",
                            "department": "Dept",
                            "PS": st.column_config.NumberColumn("PS", format="%d"),
                            "DE": st.column_config.NumberColumn("DE", format="%d"),
                            "Python": st.column_config.NumberColumn("Python", format="%d"),
                            "FSD": st.column_config.NumberColumn("FSD", format="%d"),
                            "total": st.column_config.ProgressColumn(
                                "Total Score",
                                help="Total marks out of 400",
                                format="%d",
                                min_value=0,
                                max_value=400,
                            ),
                            "Percentage": st.column_config.NumberColumn(" %", format="%.1f%%"),
                            "Status": st.column_config.TextColumn("Result", help="Pass criteria: 33%")
                        },
                        hide_index=True,
                        use_container_width=True,
                        height=400 
                    )
                    
                    csv = df_res.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download Result CSV", data=csv, file_name=f"{res_div}_result.csv", mime='text/csv')
                else:
                    st.info("No marks data found for this division.")
        else:
            st.info("No divisions available.")
            
    t_idx += 1

    # ==================================================
    # 🎓 ADD STUDENT
    # ==================================================
    with tabs[t_idx]:
        st.subheader("Add Student")
        st.caption("Auto-assigned to next available Global Division (A1, A2...).")
        with st.form("stu"):
            u, p = st.text_input("Username"), st.text_input("Password", type="password")
            n, a = st.text_input("Full Name"), st.number_input("Age", 16, 60)
            c, d = st.text_input("College", value="L.J institute"), st.selectbox("Department", DEPARTMENTS)
            ad, city, m = st.text_area("Address"), st.text_input("City"), st.text_input("Mobile")

            if st.form_submit_button("Register", type="primary"):
                if all([u, p, n, m]) and is_valid_mobile(m):
                    if register_student(u, p, {"name": n, "age": a, "college": c, "department": d, "address": ad, "city": city, "mobile": m}):
                        st.toast("✅ Student registered!")
                    else:
                        st.error("Username exists")
                else:
                    st.error("Invalid data")
    t_idx += 1

    # ==================================================
    # 👨‍🏫 ADD FACULTY
    # ==================================================
    if role == "hod":
        with tabs[t_idx]:
            st.subheader("Add New Faculty")
            with st.form("fac"):
                subjects = ["PS", "DE", "Python", "FSD"]
                u, p, n = st.text_input("Username"), st.text_input("Password", type="password"), st.text_input("Full Name")
                a, d, s = st.number_input("Age", 22, 70), st.selectbox("Department", DEPARTMENTS), st.selectbox("Subject", subjects)
                e, m = st.number_input("Experience", 0, 40), st.text_input("Mobile")
                pot_divs = [f"A{i}" for i in range(1, 10)]
                assign = st.selectbox("Assign Global Division", ["None"] + pot_divs)

                if st.form_submit_button("Register Faculty", type="primary"):
                    if all([u, p, n, s, m]):
                        if faculty_count_for_subject(s) >= 5: st.error("❌ Max 5 faculty per subject")
                        elif register_faculty(u, p, {"name": n, "age": a, "department": d, "subject": s, "experience": e, "mobile": m, "assigned_div": assign if assign != "None" else ""}):
                             st.toast("✅ Faculty added successfully")
                        else: st.error("Username already exists")
                    else: st.error("Fill all required fields")
        t_idx += 1

    # ==================================================
    # 🔄 ASSIGN MENTOR (NEW TAB)
    # ==================================================
    if role == "hod":
        with tabs[t_idx]:
            st.subheader("🔄 Assign Mentor to Division")
            
            faculty_df = get_all_faculty()
            
            if not faculty_df.empty:
                # Show current assignments clearly
                st.markdown("**Current Faculty Assignments:**")
                st.dataframe(
                    faculty_df[["full_name", "username", "department", "subject", "assigned_div"]], 
                    hide_index=True, 
                    use_container_width=True
                )
                
                st.divider()
                st.markdown("**Update Assignment:**")
                
                with st.form("reassign_mentor_form"):
                    c1, c2 = st.columns(2)
                    
                    # Create a nice dictionary mapping "Name (Username)" -> "Username" for the dropdown
                    fac_options = {f"{row['full_name']} ({row['username']})": row['username'] for _, row in faculty_df.iterrows()}
                    selected_fac_label = c1.selectbox("Select Faculty Member", list(fac_options.keys()))
                    
                    # Provide A1 through A10 and 'None' as options
                    pot_divs = ["None"] + [f"A{i}" for i in range(1, 11)]
                    new_div = c2.selectbox("Assign to Division", pot_divs)
                    
                    if st.form_submit_button("💾 Update Assignment", type="primary"):
                        target_username = fac_options[selected_fac_label]
                        update_faculty_division(target_username, new_div if new_div != "None" else "")
                        st.toast(f"✅ {selected_fac_label} is now assigned to {new_div}!")
                        st.rerun()
            else:
                st.info("No faculty members found in the system yet.")
        t_idx += 1

    # ==================================================
    # 📝 ASSIGN MARKS
    # ==================================================
    with tabs[t_idx]:
        st.subheader("📝 Assign Marks (Pop-up)")

        if avail_divs:
            target_div = st.selectbox("1️⃣ Select Division", avail_divs, key="mark_div_select")
            
            if target_div:
                df_marks = get_division_marks_data(target_div)
                
                if not df_marks.empty:
                    st.markdown(f"**Students in {target_div}:**")
                    st.dataframe(df_marks, use_container_width=True, hide_index=True, height=350)
                    
                    st.divider()
                    
                    student_options = {row["full_name"]: row for index, row in df_marks.iterrows()}
                    selected_student_name = st.selectbox("2️⃣ Select Student to Grade", options=list(student_options.keys()), key="grade_stu_select")
                    
                    if st.button("📝 Open Grading Form"):
                        selected_row = student_options[selected_student_name]
                        current_m = {
                            "PS": selected_row["PS"], "DE": selected_row["DE"],
                            "Python": selected_row["Python"], "FSD": selected_row["FSD"]
                        }
                        open_grading_popup(selected_row["username"], selected_student_name, current_m)
                        
                else:
                    st.info("No students in this division.")
        else:
            st.info("No divisions available.")

    t_idx += 1

    # ==================================================
    # 📅 ATTENDANCE
    # ==================================================
    with tabs[t_idx]:
        st.subheader("📅 Attendance")
        
        c1, c2 = st.columns(2)
        if avail_divs:
            target_div = c1.selectbox("Select Division", avail_divs, key="att_div_select")
            date = c2.date_input("Date", datetime.date.today(), key="att_date_picker")

            if target_div:
                df = get_students_for_attendance(target_div, str(date))
                if not df.empty:
                    edited = st.data_editor(
                        df, hide_index=True,
                        column_config={"user_id": None, "Present": st.column_config.CheckboxColumn("Present")},
                        key="att_editor",
                        use_container_width=True,
                        height=400
                    )
                    if st.button("💾 Save Attendance", type="primary", key="save_att_btn"):
                        data = [{"student_id": r["user_id"], "present": r["Present"]} for _, r in edited.iterrows()]
                        save_attendance_log(str(date), data)
                        st.toast("✅ Attendance saved")
                else:
                    st.warning("No students found in this division")
            
            st.divider()
            st.subheader("📊 Attendance Summary")
            
            # Fetch summary and filter it for mentors so they don't see other divisions' summaries
            df_summary = get_all_attendance_summary()
            if role == "mentor" and target_div:
                df_summary = df_summary[df_summary['division'] == target_div]
                
            st.dataframe(df_summary, use_container_width=True, height=350)
            
        else:
            st.info("No divisions available.")
    t_idx += 1

    # ==================================================
    # 🗑 REMOVE USERS
    # ==================================================
    if role == "hod":
        with tabs[t_idx]:
            st.subheader("🗑 Remove Users")
            tpe = st.radio("User Type", ["Student", "Faculty"], key="rem_user_type")
            k = st.text_input("Search User to Remove", key="rem_user_search")
            if k:
                res = search_students(k) if tpe == "Student" else search_faculty(k)
                if not res: st.info("No users found.")
                for r in res:
                    label = r.get("name") or r.get("full_name")
                    div_info = f" ({r['division']})" if 'division' in r else ""
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"{label}{div_info}")
                    if c2.button(f"Delete", key=f"del_{r['id']}"):
                        delete_user(r["id"])
                        st.toast(f"🗑 Removed {label}")
                        st.rerun()
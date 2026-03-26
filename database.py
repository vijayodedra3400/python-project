import sqlite3
import pandas as pd
import hashlib

DB_NAME = "college.db"
DEPARTMENTS = ["AIDS", "CE", "IT", "ME", "EC", "EE"]

def get_db_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)    

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed

def is_valid_mobile(mobile):
    return (mobile.isdigit() and len(mobile) == 10 and mobile[0] in ("6", "7", "8", "9"))

def init_db():
    con = get_db_connection()
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS student_details (username TEXT PRIMARY KEY, full_name TEXT, age INTEGER, college TEXT, department TEXT, division TEXT, address TEXT, city TEXT, mobile TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS faculty_details (username TEXT PRIMARY KEY, full_name TEXT, age INTEGER, department TEXT, subject TEXT, experience INTEGER, mobile TEXT, assigned_div TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS marks (username TEXT PRIMARY KEY, full_name TEXT, PS INTEGER DEFAULT 0, DE INTEGER DEFAULT 0, Python INTEGER DEFAULT 0, FSD INTEGER DEFAULT 0, total INTEGER DEFAULT 0)")
    cur.execute("CREATE TABLE IF NOT EXISTS attendance_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, date TEXT, status TEXT, UNIQUE(username, date))")
    
    cur.execute("SELECT * FROM users WHERE username='hod'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users VALUES (NULL,?,?,?)", ("hod", hash_password("hod123"), "hod"))
    con.commit()
    con.close()

def login_user(username, password):
    con = get_db_connection()
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    con.close()
    if row and verify_password(password, row[2]):
        return {"id": row[0], "username": row[1], "role": row[3]}
    return None

# --- Global Sorting (A1, A2...) ---
def recalculate_divisions():
    con = get_db_connection()
    students = con.execute("""
        SELECT s.username 
        FROM student_details s
        JOIN marks m ON s.username = m.username
        ORDER BY m.total DESC
    """).fetchall()
    
    for index, (uid,) in enumerate(students):
        div_num = (index // 30) + 1
        new_div = f"A{div_num}"
        con.execute("UPDATE student_details SET division=? WHERE username=?", (new_div, uid))
            
    con.commit()
    con.close()

def get_next_division_global():
    con = get_db_connection()
    count = con.execute("SELECT COUNT(*) FROM student_details").fetchone()[0]
    con.close()
    div_number = (count // 30) + 1
    return f"A{div_number}"

def get_all_divisions():
    con = get_db_connection()
    rows = con.execute("SELECT DISTINCT division FROM student_details ORDER BY length(division), division").fetchall()
    con.close()
    return [r[0] for r in rows]

def register_student(username, password, d):
    if not is_valid_mobile(d["mobile"]): return False
    division = get_next_division_global()
    con = get_db_connection()
    cur = con.cursor()
    try:
        cur.execute("INSERT INTO users VALUES (NULL,?,?,?)", (username, hash_password(password), "student"))
        cur.execute("INSERT INTO student_details VALUES (?,?,?,?,?,?,?,?,?)", (username, d["name"], d["age"], d["college"], d["department"], division, d["address"], d["city"], d["mobile"]))
        cur.execute("INSERT INTO marks (username, full_name, PS, DE, Python, FSD, total) VALUES (?, ?, 0, 0, 0, 0, 0)", (username, d["name"]))
        con.commit()
        return True
    except: return False
    finally: con.close()

def register_faculty(username, password, d):
    if not is_valid_mobile(d["mobile"]): return False
    con = get_db_connection()
    cur = con.cursor()
    try:
        cur.execute("INSERT INTO users VALUES (NULL,?,?,?)", (username, hash_password(password), "mentor"))
        cur.execute("INSERT INTO faculty_details VALUES (?,?,?,?,?,?,?,?)", (username, d["name"], d["age"], d["department"], d["subject"], d["experience"], d["mobile"], d["assigned_div"]))
        con.commit()
        return True
    except: return False
    finally: con.close()

def get_student_list(division=None):
    con = get_db_connection()
    query = "SELECT username, full_name, department, division FROM student_details"
    params = ()
    if division:
        query += " WHERE division=?"
        params = (division,)
    rows = con.execute(query, params).fetchall()
    con.close()
    return [{"id": r[0], "name": r[1], "username": r[0], "dept": r[2], "div": r[3]} for r in rows]

def get_all_students():
    con = get_db_connection()
    df = pd.read_sql_query("SELECT username, full_name, department, division, mobile, city, age FROM student_details", con)
    con.close()
    return df

def get_all_faculty():
    con = get_db_connection()
    df = pd.read_sql_query("SELECT username, full_name, department, subject, mobile, assigned_div FROM faculty_details", con)
    con.close()
    return df

def search_students(keyword):
    con = get_db_connection()
    rows = con.execute("SELECT username, full_name, department, division FROM student_details WHERE full_name LIKE ? OR username LIKE ?", (f"%{keyword}%", f"%{keyword}%")).fetchall()
    con.close()
    return [{"id": r[0], "name": r[1], "department": r[2], "division": r[3]} for r in rows]

def search_faculty(keyword):
    con = get_db_connection()
    rows = con.execute("SELECT username, full_name FROM faculty_details WHERE full_name LIKE ?", (f"%{keyword}%",)).fetchall()
    con.close()
    return [{"id": r[0], "full_name": r[1]} for r in rows]

# --- Marks Logic ---
def get_division_marks_data(division):
    con = get_db_connection()
    df = pd.read_sql_query("""
        SELECT s.username, s.full_name, m.PS, m.DE, m.Python, m.FSD, m.total
        FROM student_details s
        JOIN marks m ON s.username = m.username
        WHERE s.division = ?
        ORDER BY s.username
    """, con, params=(division,))
    con.close()
    return df

def update_all_marks(username, ps, de, py, fsd):
    con = get_db_connection()
    total = ps + de + py + fsd
    con.execute("""
        UPDATE marks 
        SET PS=?, DE=?, Python=?, FSD=?, total=? 
        WHERE username=?
    """, (ps, de, py, fsd, total, username))
    con.commit()
    con.close()
    # Auto-sort divisions after update
    recalculate_divisions()

def add_marks(username, subject, score):
    # Backward compatibility
    valid_subjects = ["PS", "DE", "Python", "FSD"]
    if subject not in valid_subjects: return
    con = get_db_connection()
    con.execute(f"UPDATE marks SET {subject} = ? WHERE username = ?", (score, username))
    con.execute("UPDATE marks SET total = PS + DE + Python + FSD WHERE username = ?", (username,))
    con.commit()
    con.close()
    recalculate_divisions()

def get_student_marks(username):
    con = get_db_connection()
    row = con.execute("SELECT PS, DE, Python, FSD FROM marks WHERE username=?", (username,)).fetchone()
    con.close()
    if not row: return pd.DataFrame(columns=["subject", "score"])
    data = [{"subject": "PS", "score": row[0]}, {"subject": "DE", "score": row[1]}, {"subject": "Python", "score": row[2]}, {"subject": "FSD", "score": row[3]}]
    return pd.DataFrame(data)

def get_grade_wise_students():
    con = get_db_connection()
    df = pd.read_sql_query("SELECT total FROM marks", con)
    con.close()
    if df.empty: return {}
    df["avg_score"] = df["total"] / 4 
    return df["avg_score"].apply(lambda avg: "A" if avg >= 85 else ("B" if avg >= 70 else "C")).value_counts().to_dict()

def get_division_result(division):
    con = get_db_connection()
    df = pd.read_sql_query("""
        SELECT s.full_name, s.department, m.PS, m.DE, m.Python, m.FSD, m.total
        FROM student_details s
        JOIN marks m ON s.username = m.username
        WHERE s.division = ?
        ORDER BY m.total DESC
    """, con, params=(division,))
    con.close()
    return df

def get_students_for_attendance(division, date):
    con = get_db_connection()
    df = pd.read_sql_query("SELECT s.username AS user_id, s.full_name, COALESCE((SELECT status FROM attendance_logs WHERE username=s.username AND date=?), 'Present') = 'Present' AS Present FROM student_details s WHERE s.division=?", con, params=(date, division))
    con.close()
    return df

def save_attendance_log(date, records):
    con = get_db_connection()
    cur = con.cursor()
    for r in records:
        cur.execute("INSERT OR REPLACE INTO attendance_logs (username, date, status) VALUES (?, ?, ?)", (r["student_id"], date, "Present" if r["present"] else "Absent"))
    con.commit()
    con.close()

def get_all_attendance_summary():
    con = get_db_connection()
    df = pd.read_sql_query("SELECT s.full_name, s.division, ROUND(100.0 * SUM(a.status='Present') / COUNT(*), 2) AS attendance_percentage FROM attendance_logs a JOIN student_details s ON a.username=s.username GROUP BY s.full_name, s.division", con)
    con.close()
    return df

def get_attendance(username):
    con = get_db_connection()
    df = pd.read_sql_query("SELECT COUNT(*) AS total_classes, SUM(status='Present') AS present_classes FROM attendance_logs WHERE username=?", con, params=(username,))
    con.close()
    if df.empty or df.iloc[0]["total_classes"] == 0: return {"total_classes": 0, "present_classes": 0, "percentage": 0}
    total = int(df.iloc[0]["total_classes"])
    present = int(df.iloc[0]["present_classes"] or 0)
    return {"total_classes": total, "present_classes": present, "percentage": round((present / total) * 100, 2)}

def get_faculty_details(username):
    con = get_db_connection()
    row = con.execute("SELECT department, assigned_div FROM faculty_details WHERE username=?", (username,)).fetchone()
    con.close()
    if row:
        return {"department": row[0], "assigned_div": row[1]}
    return None

def get_faculty_department(username):
    row = get_faculty_details(username)
    return row["department"] if row else None

def faculty_count_for_subject(subject):
    con = get_db_connection()
    c = con.execute("SELECT COUNT(*) FROM faculty_details WHERE subject=?", (subject,)).fetchone()[0]
    con.close()
    return c

def delete_user(username):
    con = get_db_connection()
    for t in ["users", "student_details", "faculty_details", "marks", "attendance_logs"]:
        con.execute(f"DELETE FROM {t} WHERE username=?", (username,))
    con.commit()
    con.close()

def get_avg():
    return get_db_connection().execute("select total from marks").fetchone()[0]
def get_total_students():
    return get_db_connection().execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0]

def get_total_faculty():
    return get_db_connection().execute("SELECT COUNT(*) FROM users WHERE role='mentor'").fetchone()[0]

def get_avg_score():
    r = get_db_connection().execute("SELECT AVG(total) FROM marks").fetchone()[0]
    return round(r/4, 2) if r else 0

def update_faculty_division(username, new_division):
    con = get_db_connection()
    con.execute("UPDATE faculty_details SET assigned_div=? WHERE username=?", (new_division, username))
    con.commit()
    con.close()

if __name__ == "__main__":
    init_db()   
import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

# Initialize session state variables
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'user_data' not in st.session_state:
    st.session_state.user_data = None

def init_db():
    conn = sqlite3.connect('files/timetable.db')
    return conn

def check_login(user_type, username, password):
    conn = init_db()
    if user_type == "Student":
        cursor = conn.execute(f"SELECT PASSW, SECTION, NAME, ROLL FROM STUDENT WHERE SID='{username}'")
        data = cursor.fetchone()
        if data and data[0] == password:
            return True, {"section": data[1], "name": data[2], "roll": data[3]}
    elif user_type == "Faculty":
        cursor = conn.execute(f"SELECT PASSW, INI, NAME, EMAIL FROM FACULTY WHERE FID='{username}'")
        data = cursor.fetchone()
        if data and data[0] == password:
            return True, {"ini": data[1], "name": data[2], "email": data[3]}
    elif user_type == "Admin":
        if username == "admin" and password == "admin":
            return True, {"name": "Administrator"}
    return False, None

def show_timetable(section=None, faculty_ini=None):
    conn = init_db()
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    periods = range(1, 7)
    
    # Create empty DataFrame for timetable
    timetable = pd.DataFrame(index=days, columns=periods)
    
    for day_idx, day in enumerate(days):
        for period in periods:
            if section:  # For students
                cursor = conn.execute(f"""
                    SELECT SCHEDULE.SUBCODE, SUBJECTS.SUBNAME, FACULTY.NAME 
                    FROM SCHEDULE 
                    JOIN SUBJECTS ON SCHEDULE.SUBCODE = SUBJECTS.SUBCODE 
                    JOIN FACULTY ON SCHEDULE.FINI = FACULTY.INI 
                    WHERE SECTION='{section}' AND DAYID={day_idx} AND PERIODID={period-1}
                """)
            else:  # For faculty
                cursor = conn.execute(f"""
                    SELECT SCHEDULE.SUBCODE, SUBJECTS.SUBNAME, SCHEDULE.SECTION 
                    FROM SCHEDULE 
                    JOIN SUBJECTS ON SCHEDULE.SUBCODE = SUBJECTS.SUBCODE 
                    WHERE FINI='{faculty_ini}' AND DAYID={day_idx} AND PERIODID={period-1}
                """)
            
            data = cursor.fetchone()
            if data:
                if section:
                    timetable.at[day, period] = f"{data[1]}\n({data[0]})\n{data[2]}"
                else:
                    timetable.at[day, period] = f"{data[1]}\n({data[0]})\nSection: {data[2]}"
            else:
                timetable.at[day, period] = "No Class"
    
    return timetable

def show_notifications():
    conn = init_db()
    current_time = datetime.now()
    day_of_week = current_time.weekday()
    
    if st.session_state.user_type == "Student":
        section = st.session_state.user_data["section"]
        cursor = conn.execute(f"""
            SELECT SCHEDULE.SUBCODE, SUBJECTS.SUBNAME, FACULTY.NAME, SCHEDULE.PERIODID 
            FROM SCHEDULE 
            JOIN SUBJECTS ON SCHEDULE.SUBCODE = SUBJECTS.SUBCODE 
            JOIN FACULTY ON SCHEDULE.FINI = FACULTY.INI 
            WHERE SECTION='{section}' AND DAYID={day_of_week}
            ORDER BY PERIODID
        """)
    else:
        faculty_ini = st.session_state.user_data["ini"]
        cursor = conn.execute(f"""
            SELECT SCHEDULE.SUBCODE, SUBJECTS.SUBNAME, SCHEDULE.SECTION, SCHEDULE.PERIODID 
            FROM SCHEDULE 
            JOIN SUBJECTS ON SCHEDULE.SUBCODE = SUBJECTS.SUBCODE 
            WHERE FINI='{faculty_ini}' AND DAYID={day_of_week}
            ORDER BY PERIODID
        """)
    
    classes = cursor.fetchall()
    if classes:
        st.sidebar.markdown("### Today's Classes")
        for class_info in classes:
            if st.session_state.user_type == "Student":
                st.sidebar.info(f"""
                Period {class_info[3] + 1}
                Subject: {class_info[1]} ({class_info[0]})
                Faculty: {class_info[2]}
                """)
            else:
                st.sidebar.info(f"""
                Period {class_info[3] + 1}
                Subject: {class_info[1]} ({class_info[0]})
                Section: {class_info[2]}
                """)

# Main Streamlit app
st.title("Timetable Management System")

if not st.session_state.logged_in:
    st.markdown("### Login")
    col1, col2 = st.columns(2)
    
    with col1:
        username = st.text_input("Username")
    with col2:
        password = st.text_input("Password", type="password")
    
    user_type = st.selectbox("Login as", ["Student", "Faculty", "Admin"])
    
    if st.button("Login"):
        success, user_data = check_login(user_type, username, password)
        if success:
            st.session_state.logged_in = True
            st.session_state.user_type = user_type
            st.session_state.user_data = user_data
            st.experimental_rerun()
        else:
            st.error("Invalid credentials!")

else:
    st.markdown(f"### Welcome, {st.session_state.user_data['name']}!")
    
    if st.session_state.user_type == "Student":
        st.markdown(f"**Section:** {st.session_state.user_data['section']}")
        timetable = show_timetable(section=st.session_state.user_data['section'])
    elif st.session_state.user_type == "Faculty":
        st.markdown(f"**Email:** {st.session_state.user_data['email']}")
        timetable = show_timetable(faculty_ini=st.session_state.user_data['ini'])
    else:  # Admin
        st.markdown("### Admin Dashboard")
        admin_option = st.selectbox("Select Option", ["View All Sections", "View All Faculty"])
        if admin_option == "View All Sections":
            conn = init_db()
            sections = pd.read_sql_query("SELECT * FROM STUDENT", conn)
            st.dataframe(sections)
        else:
            conn = init_db()
            faculty = pd.read_sql_query("SELECT * FROM FACULTY", conn)
            st.dataframe(faculty)
    
    if st.session_state.user_type in ["Student", "Faculty"]:
        st.markdown("### Your Timetable")
        st.dataframe(timetable.style.set_properties(**{
            'background-color': 'lightblue',
            'color': 'black',
            'border-color': 'white'
        }))
        
        # Show notifications in sidebar
        show_notifications()
    
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_type = None
        st.session_state.user_data = None
        st.experimental_rerun() 
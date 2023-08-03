import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date, timedelta
import base64
from streamlit.delta_generator import DeltaGenerator
from urllib.request import urlopen
import json
import atexit
import requests
import pytz
import socket
# Helper function to create tables in SQLite
#@st.cache_resource(allow_output_mutation=True)
def create_tables1():
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dept TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            designation TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            check_in DATETIME NOT NULL,
            check_out DATETIME,
            date DATE NOT NULL -- New column for the date of the attendance record
        )
    """)
    conn.commit()
    conn.close()

# Helper function to create tables in SQLite
def create_tables():
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dept TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            designation TEXT NOT NULL,
            password_changed INTEGER DEFAULT 0  -- New column to track if password is changed (0: Not changed, 1: Changed)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            check_in DATETIME NOT NULL,
            check_out DATETIME,
            date DATE NOT NULL -- New column for the date of the attendance record
        )
    """)
    conn.commit()
    conn.close()
atexit.register(create_tables)
def insert_employee(name, dept, email, password, designation, password_changed):
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO employees (name, dept, email, password, designation, password_changed)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, dept, email, password, designation, password_changed))
    conn.commit()
    conn.close()

def add_data_from_csv(csv_file):
    df = pd.read_csv(csv_file)

    for _, row in df.iterrows():
        name = row["Name"]
        dept = row["Department"]
        email = row["U_id"]
        password = row["Password"]
        designation = row["Designation"]
        password_changed = row['password_changed']

        insert_employee(name, dept, email, password, designation, password_changed)

# Add this before running the Streamlit app
#add_data_from_csv("updateddata1.csv")

def log_attendance(employee_id, check_in, check_out):
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()

    # Check if the employee has already checked in or checked out for the current date
    cursor.execute("SELECT check_in, check_out FROM attendance WHERE employee_id = ? AND date = ?", (employee_id, date.today()))
    result = cursor.fetchone()
    existing_check_in, existing_check_out = result if result else (None, None)

    if check_in and check_out:
        if not existing_check_in and not existing_check_out:
            cursor.execute("""
                INSERT INTO attendance (employee_id, check_in, check_out, date)
                VALUES (?, ?, ?, ?)
            """, (employee_id, check_in, check_out, date.today()))
            conn.commit()
            st.success("Checked in and checked out successfully.")
        else:
            st.error("You have already checked in and checked out for today.")
    elif check_in:
        if not existing_check_in:
            cursor.execute("""
                INSERT INTO attendance (employee_id, check_in, date)
                VALUES (?, ?, ?)
            """, (employee_id, check_in, date.today()))
            conn.commit()
            st.success("Checked in successfully.")
        else:
            st.error("You have already checked in for today.")
    elif check_out:
        if existing_check_in and not existing_check_out:
            cursor.execute("""
                UPDATE attendance
                SET check_out = ?
                WHERE employee_id = ? AND check_out IS NULL
            """, (check_out, employee_id))
            conn.commit()
            st.success("Checked out successfully.")
        else:
            st.error("You have already checked out for today.")

    conn.close()

class SessionState:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __contains__(self, key):
        return key in self.__dict__

    def get(self, key, default=None):
        return self.__dict__.get(key, default)

    def set(self, key, value):
        self.__dict__[key] = value

# Define a custom SessionState class to handle attribute initialization

# Helper function to get all attendance records for a specific employee
def get_employee_attendance(employee_id):
    conn = sqlite3.connect("attendance.db")
    query = f"SELECT * FROM attendance WHERE employee_id = {employee_id}"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Helper function to get all attendance records for all employees
def get_all_attendance():
    conn = sqlite3.connect("attendance.db")
    query = """
        SELECT e.name, e.dept, e.designation, a.check_in, a.check_out, a.date 
        FROM attendance AS a
        JOIN employees AS e ON a.employee_id = e.id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Helper function to get attendance records of all employees of a specific department
def get_all_attendance_by_department(department):
    conn = sqlite3.connect("attendance.db")
    query = f"""
        SELECT e.name, e.dept, e.designation, a.check_in, a.check_out, a.date 
        FROM attendance AS a
        JOIN employees AS e ON a.employee_id = e.id
        WHERE e.dept = '{department}'
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Helper function to check if the user is an admin based on their email
def is_admin(email):
    # Replace this with your actual implementation
    return email == "admin@example.com"

# Helper function to get employee ID from the database based on the email
def get_employee_id(email):
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM employees WHERE email = ?", (email,))
    employee_id = cursor.fetchone()
    conn.close()
    return employee_id[0] if employee_id else None

# Helper function to clean attendance records for the next day
def clean_attendance():
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()

    # Delete all attendance records
    cursor.execute("DELETE FROM attendance")

    conn.commit()
    conn.close()

def is_email_unique(email):
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM employees WHERE email = ?", (email,))
    result = cursor.fetchone()
    conn.close()
    return not result
# Rest of the
#
ALLOWED_IP_ADDRESSES = ["124.109.36.140","39.32.124.20"]
def get_user_ip1():
    data = json.load(urlopen("http://httpbin.org/ip"))
    return data["origin"]
def get_user_ip():
    try:
        client_ip = st.request.headers.get('x-forwarded-for')
        if client_ip is None:
            client_ip = st.request.headers.get('X-Real-IP')
        if client_ip is None:
            client_ip = st.request.client.ip
        return client_ip
    except AttributeError:
        return "127.0.0.1","124.109.36.140","39.32.124.20"
def get_employee_password(email):
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM employees WHERE email = ?", (email,))
    password = cursor.fetchone()
    conn.close()
    return password[0] if password else None
# Define a custom SessionState class to handle attribute initialization

def main():
    favicon_path = "https://raw.githubusercontent.com/MalikMuneebshahid86/KPLeads_attandance_system/master/KP%20favicon%20(1).png"  # Replace with the filename of your custom favicon
    st.set_page_config(page_title="KP Leads", page_icon=favicon_path)
    st.title("Kp Leads Employee Attendance")
    session_state = SessionState(authenticated=False, email="", designation="", hide_signup=False, ip_checked=False)
    #if not session_state.ip_checked:
        #user_ip = get_user_ip()
        #if user_ip not in ALLOWED_IP_ADDRESSES:
            #st.error("Access denied. Your IP address is not allowed.")
            #return
    user_ip = get_user_ip()
    if user_ip not in ALLOWED_IP_ADDRESSES:
        print(user_ip)
        st.error("Access denied. Your IP address is not allowed.")
        return

    #st.success("Access granted. You are allowed to access the app.")
    #session_state.ip_checked = True
    create_tables()
    #add_data_from_csv("updateddata1.csv")
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
        st.session_state['email'] = ""
        st.session_state['designation'] = ""
        st.session_state['hide_signup'] = False
        st.session_state['ip_checked'] = False

    # Handle URL parameters to show/hide signup button for admins
    if st.session_state.authenticated and st.session_state.designation == "Admin":
        st.sidebar.checkbox("Sign Up")

        #st.subheader("Sign Up")
        name = st.text_input("Name")
        dept = st.selectbox("Department",
                            ["QA", "FE Live", "FE Closing", "Medicare", "MVA", "IT","FE Csr","MVA Csr", "Development", "HR"])
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        designation = st.selectbox("Designation",
                                   ["Admin", "Team Lead", "Manager", "Intern", "Verifiers", "Closers", "Assistant",
                                    "Executive"])

        if st.button("Sign Up"):
            if is_email_unique(email):
                insert_employee(name, dept, email, password, designation, password_changed=0)

                st.success("Account created successfully. Please sign in.")
            else:
                st.error("Email already exists. Please choose a different")


    logo_image = "https://raw.githubusercontent.com/MalikMuneebshahid86/KPLeads_attandance_system/master/KP%20favicon%20(1).png"
    # Authentication
    col_container = st.container()
    col_container.write("")
    col1, col2, col3 = col_container.columns([1, 2, 1])

    # Display the image in the center column with size 300x300
    col2.image(logo_image, width=200)
    #st.sidebar.title("Authentication")

    # Signup Page (Only show if signup is not hidden for admins)
    if st.session_state.authenticated and st.session_state.designation == "Admin":
        pass


    # Login Page
    else:
        st.subheader("Sign In")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            # Perform login and redirect to dashboard
            employee_id = get_employee_id(email)
            if employee_id is not None:
                conn = sqlite3.connect("attendance.db")
                cursor = conn.cursor()
                cursor.execute("SELECT password, designation FROM employees WHERE email = ?", (email,))
                result = cursor.fetchone()
                conn.close()

                if result and result[0] == password:
                    st.session_state.authenticated = True
                    st.session_state.email = email
                    designation = result[1]
                    st.session_state.designation = designation
                else:
                    st.error("Wrong email or password. Please try again.")

    # Logout Button
    if st.session_state.authenticated:
        st.sidebar.text(f"Logged in as: {st.session_state.email}")
        logout = st.sidebar.button("Logout")
        if logout:
            st.session_state.authenticated = False
            st.session_state.email = ""
            st.session_state.designation = ""
            st.experimental_rerun()
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT password_changed FROM employees WHERE email = ?", (st.session_state.email,))
    result = cursor.fetchone()
    conn.close()

    password_changed = result[0] if result else 0
    # Dashboard
    if st.session_state.authenticated:
        if st.session_state.authenticated and not password_changed:
            st.title("Change Password")
            old_password = st.text_input("Old Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")

            if st.button("Change Password"):
                # Check if old password matches the current password
                current_password = get_employee_password(st.session_state.email)
                if current_password != old_password:
                    st.error("Old password does not match. Please try again.")
                elif new_password != confirm_password:
                    st.error("New password and Confirm new password do not match. Please try again.")
                else:
                    # Update the password in the database and set password_changed to 1
                    conn = sqlite3.connect("attendance.db")
                    cursor = conn.cursor()
                    cursor.execute("UPDATE employees SET password = ?, password_changed = 1 WHERE email = ?",
                                   (new_password, st.session_state.email))
                    conn.commit()
                    conn.close()
                    st.success("Password changed successfully.")
        st.title("Employee Dashboard")
        employee_id = get_employee_id(st.session_state.email)

        # For all authenticated users, show Check-In and Check-Out buttons.
        check_in = st.button("Check In")
        check_out = st.button("Check Out")
        pst = pytz.timezone("Asia/Karachi")

        if check_in:
            # Get the current time in the local time zone
            local_time = datetime.now()

            # Convert local time to PST
            check_in_pst = local_time.astimezone(pst)

            # Log the attendance with the converted time
            log_attendance(employee_id, check_in_pst, None)
            #st.success("Checked in successfully.")
        if check_out:
            # Get the current time in the local time zone
            local_time = datetime.now()

            # Convert local time to PST
            check_out_pst = local_time.astimezone(pst)

            # Log the attendance with the converted time
            log_attendance(employee_id, None, check_out_pst)
            #st.success("Checked out successfully.")

    if st.session_state.authenticated and st.session_state.designation == "Admin":
        if st.checkbox("Delete Account"):
            st.subheader("Delete Account")
            email_to_delete = st.text_input("Employee Email to Delete Account")
            #print(email_to_delete)
            if st.button("Delete"):
                conn = sqlite3.connect("attendance.db")
                cursor = conn.cursor()
                cursor.execute("DELETE FROM employees WHERE email = ?", (email_to_delete,))
                if cursor.rowcount > 0:
                    conn.commit()
                    conn.close()
                    st.success("Account deleted successfully.")
                else:
                    conn.rollback()
                    conn.close()
                    st.error("Employee with the provided email does not exist.")
    # For Admin and Team Lead, show additional functionalities.
    if st.session_state.authenticated and st.session_state.designation == "Admin":

        st.title("Admin Panel")

        # Button to hide signup for all users
        hide_signup = st.sidebar.checkbox("Signup")
        #st.experimental_set_query_params(hide_signup=hide_signup)

        # Clean Attendance Button
        if st.button("Clean Attendance for Next Day"):
            clean_attendance()
            st.success("Attendance records for the next day cleaned successfully.")

        # Download Attendance Button
        if st.button("Download Attendance"):
            df = get_all_attendance()
            csv = df.to_csv(index=False)
            b64 = base64.b64encode(csv.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="attendance.csv">Download CSV</a>'
            st.markdown(href, unsafe_allow_html=True)
        if st.button("Forget Password"):
            st.subheader("Forget Password")
            email_to_reset = st.text_input("Employee Email to Reset Password")

            show_password = st.button("Show Password")
            password_placeholder = st.empty()

            if show_password:
                password = get_employee_password(email_to_reset)
                if password:
                    password_placeholder.text_input("Password", value=password, type="password")
                else:
                    st.error("Employee with the provided email does not exist.")

        if st.session_state.designation in ["Admin", "Team Lead", "Executives"]:
            department = st.selectbox("Select Department",
                                      ["QA", "FE", "Closers", "MEDICARE", "MVA", "IT", "FE Fronter","MVA Fronter","Development", "HR"])
            #print(department)
            df = get_all_attendance_by_department(department)
            st.dataframe(df)

    if st.session_state.authenticated and st.session_state.designation == "Team Lead":
        st.title("Team Lead Panel")
        if st.session_state.designation in ["Admin", "Team Lead", "Executives"]:
            department = st.selectbox("Select Department",
                                      ["QA", "FE", "Closers", "MEDICARE", "MVA", "IT", "FE Fronter","MVA Fronter","Development", "HR"])
            #print(department)
            df = get_all_attendance_by_department(department)
            st.dataframe(df)

    if st.session_state.authenticated and st.session_state.designation == "Executive":
        st.title("Team Lead Panel")
        if st.session_state.designation in ["Admin", "Team Lead", "Executives"]:
            department = st.selectbox("Select Department",
                                      ["QA", "FE Live", "Closer", "Medicare", "MVA", "IT", "FE Fronter","MVA Fronter", "Development", "HR"])
            df = get_all_attendance_by_department(department)
            st.dataframe(df)


if __name__ == "__main__":
    main()




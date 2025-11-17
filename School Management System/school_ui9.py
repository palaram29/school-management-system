import streamlit as st
import pyodbc
import smtplib
import datetime
from datetime import timedelta
from email.message import EmailMessage
import pandas as pd
import os

# DB connection setup
conn = pyodbc.connect(
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost\\SQLEXPRESS;"
    "Database=SchoolDB;"
    "Trusted_Connection=yes;"
)
cursor = conn.cursor()

st.set_page_config(page_title="School Management System", layout="centered")
st.title("\U0001F3EB School Management System")

# Sidebar navigation
menu = st.sidebar.radio("\U0001F4C2 Select a Page", [
    "Add Class & Subject",
    "Add Parent & Student",
    "Mark Attendance",
    "Enter Term Marks",
    "View Summaries",
    "Send Email Report",
    "Delete Records"
])

# Page: Add Class
if menu == "Add Class & Subject":
    st.header("🏫 Add Class")
    with st.form(key="add_class_form"):
        class_id = st.text_input("Class ID (integer)", key="class_id")
        grade = st.number_input("Grade (1–13)", min_value=1, max_value=13, step=1, key="grade")
        section = st.text_input("Section (e.g., A, B, C)", key="section")
        submit_class = st.form_submit_button("Add Class")

        if submit_class:
            if not class_id or not section:
                st.error("Please fill all Class fields.")
            else:
                try:
                    class_id_int = int(class_id)
                    cursor.execute(
                        "INSERT INTO Class (ClassID, Grade, Section) VALUES (?, ?, ?)",
                        class_id_int, grade, section
                    )
                    conn.commit()
                    st.success(f"✅ Class '{grade} - {section}' added!")
                except pyodbc.IntegrityError as e:
                    st.error(f"Class already exists or invalid ID: {e}")
                except ValueError:
                    st.error("Class ID must be an integer.")
                except Exception as e:
                    st.error(f"Error adding class: {e}")

    st.markdown("---")

    st.header("📚 Add Subject")
    with st.form(key="add_subject_form"):
        subject_id = st.text_input("Subject ID (integer)", key="subject_id")
        subject_name = st.text_input("Subject Name", key="subject_name")
        submit_subject = st.form_submit_button("Add Subject")

        if submit_subject:
            if not subject_id or not subject_name:
                st.error("Please fill all Subject fields.")
            else:
                try:
                    subject_id_int = int(subject_id)
                    cursor.execute(
                        "INSERT INTO Subject (SubjectID, Name) VALUES (?, ?)",
                        subject_id_int, subject_name
                    )
                    conn.commit()
                    st.success(f"✅ Subject '{subject_name}' added!")
                except pyodbc.IntegrityError as e:
                    st.error(f"Subject already exists or invalid ID: {e}")
                except ValueError:
                    st.error("Subject ID must be an integer.")
                except Exception as e:
                    st.error(f"Error adding subject: {e}")

    st.markdown("---")

    st.header("🗑️ Delete Subject")
    try:
        # Fetch subject list
        cursor.execute("SELECT SubjectID, Name FROM Subject")
        subjects = cursor.fetchall()
        if subjects:
            subject_options = {f"{row.SubjectID} - {row.Name}": row.SubjectID for row in subjects}
            selected_subject = st.selectbox("Select Subject to Delete", list(subject_options.keys()))

            if st.button("Delete Selected Subject"):
                subject_id_to_delete = subject_options[selected_subject]
                cursor.execute("DELETE FROM Subject WHERE SubjectID = ?", subject_id_to_delete)
                conn.commit()
                st.success(f"🗑️ Subject '{selected_subject}' deleted successfully!")
                # st.experimental_rerun()  # Uncomment if your Streamlit version supports it
                st.write("Please refresh the page to see updated list.")
        else:
            st.info("No subjects available to delete.")
    except Exception as e:
        st.error(f"Error fetching or deleting subject: {e}")


# Page 2: Add Parent & Student
elif menu == "Add Parent & Student":
    st.header("\U0001F468‍\U0001F469‍\U0001F467 Add Parent")
    parent_id = st.text_input("Parent ID", key="parent_id_add")
    parent_name = st.text_input("Parent Name", key="parent_name_add")
    parent_email = st.text_input("Parent Email", key="parent_email_add")
    parent_phone = st.text_input("Parent Phone", key="parent_phone_add")

    if st.button("Add Parent", key="btn_add_parent"):
        if not parent_id or not parent_name or not parent_email or not parent_phone:
            st.error("Please fill all fields.")
        else:
            try:
                # Insert into Parent table (excluding phone)
                cursor.execute(
                    "INSERT INTO Parent (ParentID, Name, Email) VALUES (?, ?, ?)",
                    parent_id, parent_name, parent_email
                )

                # Insert phone into Parent_Phone table
                cursor.execute(
                    "INSERT INTO Parent_Phone (ParentID, Phone) VALUES (?, ?)",
                    parent_id, parent_phone
                )

                conn.commit()
                st.success(f"Parent '{parent_name}' added!")
            except Exception as e:
                conn.rollback()
                st.error(f"Failed to add parent: {e}")

    st.markdown("---")
    st.header("\U0001F466\U0001F467 Add Student")
    student_id = st.text_input("Student ID", key="student_id_add")
    student_name = st.text_input("Student Name", key="student_name_add")
    dob = st.date_input(
        "Date of Birth",
        min_value=datetime.date(1990, 1, 1),
        max_value=datetime.date.today(),
        key="dob_add"
    )
    gender = st.selectbox("Gender", ["M", "F"], key="gender_add")
    class_id_fk = st.text_input("Class ID (FK)", key="class_id_fk_add")
    parent_id_fk = st.text_input("Parent ID (FK)", key="parent_id_fk_student")

    if st.button("Add Student", key="btn_add_student"):
        if not student_id or not student_name or not class_id_fk or not parent_id_fk:
            st.error("Please complete all fields.")
        else:
            try:
                # Insert into Student table including ParentID
                cursor.execute(
                    "INSERT INTO Student (StudentID, Name, DOB, Gender, ClassID, ParentID) VALUES (?, ?, ?, ?, ?, ?)",
                    student_id, student_name, dob, gender, class_id_fk, parent_id_fk
                )

                conn.commit()
                st.success(f"Student '{student_name}' added with linked Parent ID '{parent_id_fk}'!")
            except Exception as e:
                conn.rollback()
                st.error(f"Failed to add student: {e}")

# Page 3: Mark Attendance
elif menu == "Mark Attendance":
    st.header("\U0001F4DD Add Attendance Record")

    attendance_id = st.text_input("Attendance ID")
    student_id_att = st.text_input("Student ID")
    attendance_date = st.date_input("Date")
    time_in = st.time_input("Time In", step=timedelta(minutes=1))
    status = st.selectbox("Status", ["Present", "Absent"])

    # New: Add Year and Term input
    year = st.number_input("Year", min_value=2000, max_value=2100, value=2025)
    term = st.selectbox("Term", ["T1", "T2", "T3"])

    if st.button("Add Attendance"):
        if not attendance_id or not student_id_att:
            st.error("Please fill required fields.")
        else:
            try:
                cursor.execute(
                    "INSERT INTO Attendance (AttendanceID, StudentID, Date, TimeIn, Status, Year, Term) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    attendance_id, student_id_att, attendance_date, time_in, status, year, term
                )
                conn.commit()
                st.success("Attendance record added!")
            except Exception as e:
                st.error(f"Error adding attendance: {e}")

# Page 4: Enter Term Marks
elif menu == "Enter Term Marks":
    st.header("📊 Enter Term Marks")

    # ----- Add Term Marks -----
    # Fetch valid Student IDs and Names for dropdown
    cursor.execute("SELECT StudentID, Name FROM Student ORDER BY Name")
    students = cursor.fetchall()
    student_options = {str(row.StudentID): row.Name for row in students}
    student_id_tm = st.selectbox("Select Student", options=list(student_options.keys()), format_func=lambda x: student_options[x])

    # Fetch valid Subject IDs and Names for dropdown
    cursor.execute("SELECT SubjectID, Name FROM Subject ORDER BY Name")
    subjects = cursor.fetchall()
    subject_options = {str(row.SubjectID): row.Name for row in subjects}
    subject_id_tm = st.selectbox("Select Subject", options=list(subject_options.keys()), format_func=lambda x: subject_options[x])

    term = st.text_input("Term (e.g., Term 1)")

    # Show previously entered marks
    if student_id_tm and subject_id_tm and term:
        cursor.execute("""
            SELECT MarkID, Mark
            FROM TermMark
            WHERE StudentID = ? AND SubjectID = ? AND Term = ?
        """, student_id_tm, subject_id_tm, term)
        existing_marks = cursor.fetchall()

        if existing_marks:
            st.markdown("#### 📌 Existing Mark(s) for Selected Student, Subject, and Term:")
            for row in existing_marks:
                st.write(f"🆔 MarkID: `{row.MarkID}` | 🔢 Mark: `{row.Mark}`")
        else:
            st.info("No previous marks entered for this combination.")

    mark_id = st.text_input("Mark ID")
    mark = st.number_input("Mark", min_value=0, max_value=100)

    if st.button("Add Term Mark"):
        if not mark_id or not term:
            st.error("Please fill all required fields.")
        else:
            try:
                cursor.execute(
                    "INSERT INTO TermMark (MarkID, StudentID, SubjectID, Term, Mark) VALUES (?, ?, ?, ?, ?)",
                    mark_id, student_id_tm, subject_id_tm, term, mark
                )
                conn.commit()
                st.success("Term mark added!")
                st.rerun()
            except Exception as e:
                st.error(f"Error adding term mark: {e}")


    # ----- Delete Term Marks -----
    st.header("🗑️ Delete Student Mark")

    try:
        # Step 1: Select student
        cursor.execute("SELECT StudentID, Name FROM Student ORDER BY Name")
        students = cursor.fetchall()
        delete_student_options = {str(row.StudentID): row.Name for row in students}
        selected_student_id = st.selectbox(
            "Select Student (to view/delete marks)",
            options=list(delete_student_options.keys()),
            format_func=lambda x: delete_student_options[x]
        )

        # Step 2: Optional term filter
        cursor.execute("SELECT DISTINCT Term FROM TermMark WHERE StudentID = ?", selected_student_id)
        terms = [row.Term for row in cursor.fetchall()]
        selected_term = st.selectbox("Filter by Term (Optional)", options=["All"] + terms)

        # Step 3: Optional subject filter
        cursor.execute("""
            SELECT DISTINCT Sub.SubjectID, Sub.Name
            FROM TermMark TM
            JOIN Subject Sub ON TM.SubjectID = Sub.SubjectID
            WHERE TM.StudentID = ?
        """, selected_student_id)
        subjects = cursor.fetchall()
        subject_options = {"All": "All Subjects"}
        subject_options.update({str(row.SubjectID): row.Name for row in subjects})
        selected_subject_id = st.selectbox(
            "Filter by Subject (Optional)",
            options=list(subject_options.keys()),
            format_func=lambda x: subject_options[x]
        )

        # Step 4: Build dynamic query
        query = """
            SELECT TM.MarkID, S.Name AS StudentName, Sub.Name AS SubjectName, TM.Term, TM.Mark
            FROM TermMark TM
            JOIN Student S ON TM.StudentID = S.StudentID
            JOIN Subject Sub ON TM.SubjectID = Sub.SubjectID
            WHERE TM.StudentID = ?
        """
        params = [selected_student_id]

        if selected_term != "All":
            query += " AND TM.Term = ?"
            params.append(selected_term)

        if selected_subject_id != "All":
            query += " AND TM.SubjectID = ?"
            params.append(selected_subject_id)

        query += " ORDER BY TM.Term, Sub.Name"

        cursor.execute(query, params)
        filtered_marks = cursor.fetchall()

        # Step 5: Show filtered marks
        if filtered_marks:
            st.markdown("### 🎯 Select a mark to delete")

            mark_options = [
                f"{row.MarkID} | {row.StudentName} | {row.SubjectName} | Term: {row.Term} | Mark: {row.Mark}"
                for row in filtered_marks
            ]
            selected_mark = st.selectbox("Select Term Mark", mark_options)

            if selected_mark:
                if st.checkbox("⚠️ Confirm deletion of this mark"):
                    if st.button("🗑️ Delete Selected Mark"):
                        mark_id_to_delete = selected_mark.split("|")[0].strip()
                        cursor.execute("DELETE FROM TermMark WHERE MarkID = ?", mark_id_to_delete)
                        conn.commit()
                        st.success("✅ Selected term mark deleted!")
                        st.rerun()

            # Optional: Bulk delete
            st.markdown("---")
            st.markdown("### 🧹 Bulk Delete (Optional)")

            selected_bulk_marks = st.multiselect("Select Multiple Term Marks to Delete", mark_options)

            if selected_bulk_marks and st.checkbox("⚠️ Confirm bulk deletion"):
                if st.button("🗑️ Delete Selected Marks"):
                    for entry in selected_bulk_marks:
                        mark_id = entry.split("|")[0].strip()
                        cursor.execute("DELETE FROM TermMark WHERE MarkID = ?", mark_id)
                    conn.commit()
                    st.success(f"✅ {len(selected_bulk_marks)} term marks deleted successfully!")
                    st.experimental_rerun()
        else:
            st.info("No marks found for the selected filters.")

    except Exception as e:
        st.error(f"Error handling student marks: {e}")

# Page 5: View Summaries
elif menu == "View Summaries":
    st.header("📈 Student Summaries")


    # Get student count
    cursor.execute("SELECT COUNT(*) FROM Student")
    student_count = cursor.fetchone()[0]

    # Show in KPI
    st.metric(label="Total Students", value=student_count)

    # Attendance Summary
    st.subheader("📅 Attendance Summary")
    try:
        attendance_df = pd.read_sql_query("SELECT * FROM vw_StudentAttendanceSummary2", conn)
        st.dataframe(attendance_df)
    except Exception as e:
        st.error(f"Error loading attendance summary: {e}")

    # Student-Parent Information
    st.subheader("👨‍👩‍👧 Student-Parent Information")
    try:
        parent_info_df = pd.read_sql_query("SELECT * FROM vw_StudentParentInfo", conn)
        st.dataframe(parent_info_df)
    except Exception as e:
        st.error(f"Error loading student-parent info: {e}")

    # Student Result Summary
    st.subheader("📊 Student Result Summary")
    try:
        result_df = pd.read_sql_query("SELECT * FROM vw_StudentTermPerformance2", conn)

        desired_columns = [
            'StudentID',
            'StudentName',
            'ClassName',
            'Term',
            'TotalMark',          
            'AverageMarkPerTerm', 
            'ClassRankPerTerm'    
        ]
        existing_columns = [col for col in desired_columns if col in result_df.columns]

        if not existing_columns:
            st.warning("Expected summary columns not found. Showing raw data.")
            st.dataframe(result_df)
        else:
            summary_df = result_df[existing_columns].drop_duplicates()

            sort_columns = [col for col in ['Term', 'ClassRankPerTerm'] if col in summary_df.columns]
            if sort_columns:
                summary_df = summary_df.sort_values(by=sort_columns)

            st.dataframe(summary_df)
    except Exception as e:
        st.error(f"Error loading result summary: {e}")


# Page 6: Send Email Report
elif menu == "Send Email Report":
    st.header("\U0001F4E7 Send Student Report")

    student_id = st.text_input("Enter Student ID")

    if st.button("Fetch Student Data"):
        if not student_id:
            st.warning("Please enter a Student ID.")
        else:
            try:
                query = "SELECT * FROM vw_StudentTermPerformance2 WHERE StudentID = ?"
                student_data = pd.read_sql_query(query, conn, params=[student_id])
                if not student_data.empty:
                    st.session_state.student_data = student_data
                    st.success("Student data fetched successfully.")
                    st.dataframe(student_data)
                else:
                    st.error("No records found.")
            except Exception as e:
                st.error(f"Error fetching data: {e}")

    if "student_data" in st.session_state:
        student_data = st.session_state.student_data
        sender_email = st.text_input("Your Email")
        app_password = st.text_input("App Password", type="password")
        recipient_email = st.text_input("Parent Email")
        subject = st.text_input("Email Subject", value="Student Report")
        body = st.text_area("Message Body", value="Attached is your child's report.")

        if st.button("Send Report"):

            def send_student_report_email(sender_email, app_password, recipient_email, subject, body, student_data, student_id, file_name="student_report.xlsx"):
                try:
                    df = pd.DataFrame(student_data)

                    if 'AttendancePercentage' not in df.columns:
                        df['AttendancePercentage'] = ''

                    terms = df['Term'].unique()

                    cursor = conn.cursor()

                    for term in terms:
                        cursor.execute("SELECT dbo.fn_CalculateTermAttendancePercentage(?, ?)", (student_id, term))
                        result = cursor.fetchone()
                        attendance_pct = result[0] if result else 0
                        df.loc[df['Term'] == term, 'AttendancePercentage'] = f"{attendance_pct:.2f}%"

                    # Save DataFrame to Excel
                    df.to_excel(file_name, index=False)

                    # Prepare email
                    msg = EmailMessage()
                    msg['Subject'] = subject
                    msg['From'] = sender_email
                    msg['To'] = recipient_email
                    msg.set_content(body)

                    with open(file_name, 'rb') as f:
                        msg.add_attachment(
                            f.read(),
                            maintype='application',
                            subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                            filename=file_name
                        )

                    # Send email via Gmail SMTP SSL
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                        smtp.login(sender_email, app_password)
                        smtp.send_message(msg)

                    os.remove(file_name)
                    return True

                except Exception as e:
                    return str(e)

            # Call the function and show status
            result = send_student_report_email(
                sender_email, app_password,
                recipient_email, subject, body,
                student_data, student_id
            )

            if result == True:
                st.success("Email sent successfully!")
            else:
                st.error(f"Failed to send email: {result}")



# Page 7: Delete Records
elif menu == "Delete Records":
    st.header("🗑️ Delete Parents or Students")

    delete_choice = st.radio("Choose what to delete:", ["Student", "Parent"])

    if delete_choice == "Student":
        # Fetch students for selection
        cursor.execute("SELECT StudentID, Name FROM Student ORDER BY Name")
        students = cursor.fetchall()
        if students:
            student_options = {f"{row.StudentID} - {row.Name}": row.StudentID for row in students}
            selected_student = st.selectbox("Select Student to Delete", list(student_options.keys()))

            if st.button("Delete Selected Student"):
                student_id_to_delete = student_options[selected_student]
                try:
                    # Delete attendance and term marks if exist
                    cursor.execute("DELETE FROM Attendance WHERE StudentID = ?", student_id_to_delete)
                    cursor.execute("DELETE FROM TermMark WHERE StudentID = ?", student_id_to_delete)

                    # Now delete student
                    cursor.execute("DELETE FROM Student WHERE StudentID = ?", student_id_to_delete)

                    conn.commit()
                    st.success(f"✅ Student '{selected_student}' deleted successfully!")
                except Exception as e:
                    conn.rollback()
                    st.error(f"Error deleting student: {e}")
        else:
            st.info("No students available to delete.")

    elif delete_choice == "Parent":
        # Fetch parents for selection
        cursor.execute("SELECT ParentID, Name FROM Parent ORDER BY Name")
        parents = cursor.fetchall()
        if parents:
            parent_options = {f"{row.ParentID} - {row.Name}": row.ParentID for row in parents}
            selected_parent = st.selectbox("Select Parent to Delete", list(parent_options.keys()))

            if st.button("Delete Selected Parent"):
                parent_id_to_delete = parent_options[selected_parent]
                try:
                    # First, remove parent reference in Student table
                    cursor.execute("UPDATE Student SET ParentID = NULL WHERE ParentID = ?", parent_id_to_delete)

                    # Delete from Parent_Phone table
                    cursor.execute("DELETE FROM Parent_Phone WHERE ParentID = ?", parent_id_to_delete)

                    # Now delete parent
                    cursor.execute("DELETE FROM Parent WHERE ParentID = ?", parent_id_to_delete)

                    conn.commit()
                    st.success(f"✅ Parent '{selected_parent}' deleted successfully!")
                except Exception as e:
                    conn.rollback()
                    st.error(f"Error deleting parent: {e}")
        else:
            st.info("No parents available to delete.")

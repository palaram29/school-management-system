# School Management System

A **Streamlit-based School Management System** with a **SQL Server backend** for managing classes, students, parents, attendance, term marks, and generating student reports via email.

---

## Features

- 🏫 **Add Classes & Subjects**
- 👨‍👩‍👧 **Register Parents & Students**
- 📅 **Mark Attendance** (with year and term)
- 📊 **Enter Term Marks**
- 🗂️ **View Summaries**
  - Student Attendance Summary
  - Student-Parent Information
  - Student Result Summary (Total Marks, Average, Class Rank)
- ✉️ **Send Email Reports to Parents**
- 🗑️ **Delete Records** (Students, Parents, Subjects, Term Marks)

---

## Requirements
- streamlit
- pyodbc
- pandas
- openpyxl


---

## Database Setup

  1. Install **SQL Server** and **SQL Server Management Studio (SSMS)**.  
  2. Create a database named `SchoolDB`.  
  3. Run `database.sql` to create all required objects:
     - **Tables**: Class, Parent, Parent_Phone, Student, Attendance, Subject, TermMark, EmailNotificationLog  
     - **Triggers**: trg_Attendance1_Insert, trg_LowAttendanceAlert  
     - **Functions**: fn_GetStudentFullName, fn_GetAttendancePercentage, fn_CalculateAttendancePercentage, fn_CalculateTermAttendancePercentage  
     - **Stored Procedures**: sp_InsertAttendance1, sp_EmailParentSummary  
     - **Views**: vw_StudentParentInfo, vw_StudentAttendanceSummary2, vw_StudentTermPerformance2

  4.  Change it in python
     conn = pyodbc.connect(
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=YOUR_SERVER_NAME;"
    "Database=SchoolDB;"
    "Trusted_Connection=yes;")
     
    
  
## Python file setup
- Download the requirements
- Run the file











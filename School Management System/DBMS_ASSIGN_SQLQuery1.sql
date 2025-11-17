
CREATE TABLE Class (
    ClassID INT PRIMARY KEY,
    Grade INT NOT NULL,
    Section VARCHAR(100) NOT NULL
);

CREATE TABLE Parent (
    ParentID INT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE Parent_Phone (
    ParentID INT,
    Phone VARCHAR(15),
    PRIMARY KEY (ParentID, Phone),
    FOREIGN KEY (ParentID) REFERENCES Parent(ParentID)
);


CREATE TABLE Student (
    StudentID INT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    DOB DATE NOT NULL,
    Gender CHAR(1) CHECK (Gender IN ('M','F')),
    ClassID INT FOREIGN KEY REFERENCES Class(ClassID),
    ParentID INT FOREIGN KEY REFERENCES Parent(ParentID)
);



CREATE TABLE Attendance (
   AttendanceID INT,
	StudentID INT,
	PRIMARY KEY (AttendanceID, StudentID),
	FOREIGN KEY (StudentID) REFERENCES Student(StudentID),
    Date DATE NOT NULL,
    Status VARCHAR(10) CHECK (Status IN ('Present', 'Absent')),
    TimeIn TIME
);
ALTER TABLE Attendance
ADD Year INT;

ALTER TABLE Attendance
ADD Term VARCHAR(10);


CREATE TABLE Subject (
    SubjectID INT PRIMARY KEY ,
    Name VARCHAR(50) NOT NULL
);


CREATE TABLE TermMark (
    MarkID INT ,
    StudentID INT,
	PRIMARY KEY (StudentID, MarkID),
	FOREIGN KEY (StudentID) REFERENCES Student(StudentID),
    SubjectID INT FOREIGN KEY REFERENCES Subject(SubjectID),
    Term VARCHAR(10),
    Mark INT CHECK (Mark BETWEEN 0 AND 100)
);


CREATE TABLE EmailNotificationLog (
    LogID INT PRIMARY KEY ,
    StudentID INT FOREIGN KEY REFERENCES Student(StudentID),
    ParentID INT FOREIGN KEY REFERENCES Parent(ParentID),
    SentDate DATETIME,
    Status VARCHAR(10)
);



CREATE TRIGGER trg_Attendance1_Insert
ON Attendance
AFTER INSERT
AS
BEGIN
    PRINT 'A new attendance record has been added.'
END;



CREATE TRIGGER trg_LowAttendanceAlert
ON Attendance
AFTER INSERT
AS
BEGIN
    IF EXISTS (SELECT 1 FROM inserted WHERE Status = 'Absent')
    BEGIN
        PRINT 'Alert: Student marked absent.'
    END
END;



CREATE FUNCTION fn_GetStudentFullName(@StudentID INT)
RETURNS NVARCHAR(100)
AS
BEGIN
    DECLARE @FullName NVARCHAR(100)
    SELECT @FullName = FirstName + ' ' + LastName FROM Students WHERE StudentID = @StudentID
    RETURN @FullName
END;



CREATE FUNCTION fn_GetAttendancePercentage(@StudentID INT)
RETURNS FLOAT
AS
BEGIN
    DECLARE @Total INT, @Present INT;

    SELECT @Total = COUNT(*) 
    FROM Attendance 
    WHERE StudentID = @StudentID;

    SELECT @Present = COUNT(*) 
    FROM Attendance 
    WHERE StudentID = @StudentID AND Status = 'Present';

    IF @Total = 0
        RETURN 0;

    RETURN (CAST(@Present AS FLOAT) / @Total) * 100;
END;



CREATE PROCEDURE sp_InsertAttendance1
    @StudentID INT,
    @Date DATE,
    @TimeIn TIME,
    @Status VARCHAR(10)
AS
BEGIN
    INSERT INTO Attendance (StudentID, Date, TimeIn, Status)
    VALUES (@StudentID, @Date, @TimeIn, @Status)
END;


CREATE OR ALTER VIEW vw_StudentParentInfo AS
SELECT 
    s.StudentID,
    s.Name AS StudentName,
    p.ParentID,
    p.Name AS ParentName,
    p.Email,
    pp.Phone
FROM Student s
JOIN Parent p ON s.ParentID = p.ParentID
LEFT JOIN Parent_Phone pp ON p.ParentID = pp.ParentID;



CREATE OR ALTER PROCEDURE sp_EmailParentSummary
    @StudentID INT
AS
BEGIN
    DECLARE @StudentName NVARCHAR(100), @ParentEmail NVARCHAR(100), @Attendance FLOAT;

    SELECT 
        @StudentName = s.Name,
        @ParentEmail = p.Email
    FROM Student s
    JOIN Parent p ON s.ParentID = p.ParentID
    WHERE s.StudentID = @StudentID;

    SET @Attendance = dbo.fn_GetAttendancePercentage(@StudentID);

    PRINT 'Sending email to: ' + @ParentEmail;
    PRINT 'Subject: Student Performance Report';
    PRINT 'Body: Hello, ' + @StudentName + '''s attendance is ' + CAST(@Attendance AS VARCHAR) + '%.';
END;






CREATE FUNCTION dbo.fn_CalculateAttendancePercentage (@StudentID INT)
RETURNS FLOAT
AS
BEGIN
    DECLARE @Total INT = (SELECT COUNT(*) FROM Attendance WHERE StudentID = @StudentID);
    DECLARE @Present INT = (SELECT COUNT(*) FROM Attendance WHERE StudentID = @StudentID AND Status = 'Present');
    
    RETURN CASE WHEN @Total = 0 THEN 0 ELSE CAST(@Present * 100.0 / @Total AS FLOAT) END;
END;


CREATE OR ALTER FUNCTION dbo.fn_CalculateTermAttendancePercentage
(
    @StudentID INT,
    @Term VARCHAR(10)
)
RETURNS FLOAT
AS
BEGIN
    DECLARE @Total INT, @Present INT;

    SELECT 
        @Total = COUNT(*)
    FROM Attendance a
    JOIN TermMark t ON a.StudentID = t.StudentID
    WHERE a.StudentID = @StudentID AND t.Term = @Term;

    SELECT 
        @Present = COUNT(*)
    FROM Attendance a
    JOIN TermMark t ON a.StudentID = t.StudentID
    WHERE a.StudentID = @StudentID AND a.Status = 'Present' AND t.Term = @Term;

    IF @Total = 0
        RETURN 0;

    RETURN (CAST(@Present AS FLOAT) / @Total) * 100;
END;




CREATE VIEW vw_StudentAttendanceSummary2 AS
SELECT 
    S.StudentID,
    S.Name AS StudentName,
    C.Grade,
    C.Section,
    COUNT(A.AttendanceID) AS TotalAttendanceDays,
    SUM(CASE WHEN A.Status = 'Present' THEN 1 ELSE 0 END) AS DaysPresent,
    dbo.fn_CalculateAttendancePercentage(S.StudentID) AS AttendancePercentage
FROM 
    Student S
JOIN 
    Class C ON S.ClassID = C.ClassID
LEFT JOIN 
    Attendance A ON S.StudentID = A.StudentID
GROUP BY 
    S.StudentID, S.Name, C.Grade, C.Section;





CREATE PROCEDURE sp_InsertAttendance1
    @StudentID INT,
    @Date DATE,
    @TimeIn TIME,
    @Status VARCHAR(10)
AS
BEGIN
    INSERT INTO Attendance (StudentID, Date, TimeIn, Status)
    VALUES (@StudentID, @Date, @TimeIn, @Status)
END;



CREATE OR ALTER VIEW vw_StudentTermPerformance2 AS
WITH StudentTermTotals AS (
    SELECT
        StudentID,
        Term,
        SUM(Mark) AS TotalMark,
        AVG(CAST(Mark AS FLOAT)) AS AverageMarkPerTerm  -- Cast for decimal avg
    FROM TermMark
    GROUP BY StudentID, Term
),
ClassTermRanks AS (
    SELECT
        sta.StudentID,
        s.ClassID,
        sta.Term,
        RANK() OVER (PARTITION BY s.ClassID, sta.Term ORDER BY sta.AverageMarkPerTerm DESC) AS ClassRankPerTerm
    FROM StudentTermTotals sta
    JOIN Student s ON sta.StudentID = s.StudentID
)
SELECT 
    s.StudentID,
    s.Name AS StudentName,
    CONCAT(c.Grade, ' ', c.Section) AS ClassName,
    stt.Term,
    stt.TotalMark,
    stt.AverageMarkPerTerm,
    ctr.ClassRankPerTerm
FROM StudentTermTotals stt
JOIN Student s ON stt.StudentID = s.StudentID
JOIN Class c ON s.ClassID = c.ClassID
JOIN ClassTermRanks ctr ON ctr.StudentID = s.StudentID AND ctr.Term = stt.Term;



SELECT name FROM sys.databases;




Create schema cmps_db;

Set search_path to cmps_db;

-- Table definition

-- Defines the exam table
Create table exam (
	excode char(4) primary key,
	extitle varchar(200) not null unique,
	exlocation varchar(200) not null,
	exdate date check (extract(month from exdate) = 11 and extract(year from exdate) = 2025),
	extime time check (extime between '09:00' and '18:00')
);

-- Defines the student table
Create table student (
	sno integer primary key,
	sname varchar(200) not null,
	semail varchar(200) not null check (semail ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Defines the entry table
Create table entry (
	eno integer primary key,
	excode char(4) not null,
	sno integer not null,
	egrade decimal(5,2) check (egrade is null or egrade between 0 and 100),
	foreign key (excode) references exam(excode),
	foreign key (sno) references student(sno)
);

-- Defines the cancel table
Create table cancel (
	eno integer primary key,
	excode char(4) not null unique,
	sno integer not null,
	cdate timestamp not null default current_timestamp,
	cuser varchar(200) not null
);

-- Functions

-- Function to cancel an entry
Create or replace function cancelEntry(entryID integer) returns void as $$
Begin
	 If not exists (select 1 from entry where eno = entryID) then
        Raise exception 'Entry does not exist';
    End if;
	Insert into cancel (eno, excode, sno, cdate, cuser) select eno, excode, sno, current_timestamp, 'system' from entry where eno = entryID;
	Delete from entry where eno = entryID;
End;
$$ language plpgsql;

-- Function to delete student
Create or replace function handleStudentDelete() returns trigger as $$
Begin
    Insert into cancel (eno, excode, sno, cuser) select e.eno, e.excode, e.sno, 'system' from entry e where e.sno = old.sno and e.eno not in (select eno from cancel);
    Delete from entry where sno = old.sno;
    Return old;
End;
$$ language plpgsql;


-- Function to delete an exam
Create or replace function handleExamDelete() returns trigger as $$
Begin
    If exists (select 1 from entry e where e.excode = old.excode) then
        Raise exception 'Cannot delete exam when there are active entries';
    End if;
    Return old;
End;
$$ language plpgsql;

-- Function to create an exam entry
Create or replace function insertExamEntry() returns trigger as $$
Begin
    -- Checks if the student exists
    If not exists (select 1 from student s where s.sno = new.sno) then
        Raise exception 'Student does not exist';
    End if;

    -- Checks if the exam exists
    If not exists (select 1 from exam e where e.excode = new.excode) then
        Raise exception 'Exam does not exist';
    End if;

    -- Checks for any duplicate entry
    If exists (select 1 from entry e where e.excode = new.excode and e.sno = new.sno) then
        Raise exception 'Student already entered for this exam';
    End if;

    -- Checks for same-day exam bookings (collisions)
    If exists (select 1 from entry e join exam ex on e.excode = ex.excode where e.sno = new.sno and ex.exdate = (select exdate from exam where excode = new.excode)) then
        Raise exception 'Student already has an exam scheduled for this date';
    End if;

    Return new;
End;
$$ language plpgsql;

-- Function to update an entry
Create or replace function updateEntryGrade(enoInput integer, grade decimal(5,2)) returns void as $$
Begin
    -- Check if the entry exists
    If not exists (select 1 from entry e where e.eno = enoInput) then
        Raise exception 'Entry does not exist';
    End if;

    -- Check if the entry is cancelled
    If exists (select 1 from cancel c where c.eno = enoInput) then
        Raise exception 'Cannot update a cancelled entry';
    End if;

    -- Check if the grade is valid (0-100)
    If grade is not null and (grade < 0 or grade > 100) then
        Raise exception 'Grade must be between 0 and 100';
    End if;

    Update entry set egrade = grade where eno = enoInput;
End;
$$ language plpgsql;

-- Function to get table of results for a specific exam
Create or replace function getResultsForExam(examCode char(4))
Returns table (
    excode char(4),
    extitle varchar(200),
    sno integer,
    sname varchar(200),
    egrade decimal(5,2),
    resultText varchar(20)
) as $$
Begin
    Return query
    Select 
        e.excode,
        e.extitle,
        s.sno,
        s.sname,
        en.egrade,
		Cast(
            Case
                When en.egrade is null then 'Not taken'
                When en.egrade >= 70 then 'Distinction'
                When en.egrade >= 50 then 'Pass'
                Else 'Fail'
            End as varchar(20)
        ) As resultText
    From exam e
    Left join entry en on e.excode = en.excode
	Left join student s on en.sno = s.sno
    Where e.excode = examCode
    Order by s.sno;
End;
$$ language plpgsql;

-- Function to get timetable of a specific student
Create or replace function getStudentTimetable(studentID integer)
Returns table (
    sname varchar(200),
    excode char(4),
    extitle varchar(200),
    exlocation varchar(200),
    exdate date,
    extime time
) As $$
Begin
    Return query
    Select 
        s.sname,
        e.excode,
        e.extitle,
        e.exlocation,
        e.exdate,
        e.extime
    From student s
    Join entry en on s.sno = en.sno
    Join exam e on en.excode = e.excode
    Where s.sno = studentID
    And not exists (
        select 1 from cancel c 
        Where c.eno = en.eno
    )
    Order by e.exdate, e.extime;
End;
$$ Language plpgsql;

-- Triggers

-- Trigger when deleting a student
Create trigger deleteStudentTrigger before delete on student for each row execute procedure handleStudentDelete();

-- Trigger when deleting an exam
Create trigger deleteExamTrigger before delete on exam for each row execute procedure handleExamDelete();

-- Trigger when inserting a new entry
Create trigger insertEntryTrigger before insert on entry for each row execute procedure insertExamEntry();

-- Views

-- View to display exam results
Create or replace view examResults as
Select 
    e.excode,
    e.extitle,
    s.sno,
    s.sname,
    en.egrade,
    Case
        When en.egrade is null Then 'Not taken'
        When en.egrade >= 70 Then 'Distinction'
        When en.egrade >= 50 Then 'Pass'
        Else 'Fail'
    End as resultText
From exam e
Left join entry en on e.excode = en.excode
Left join student s on en.sno = s.sno
Order by e.excode, s.sname;

-- Indexes

-- Index for
Create index indexStudentSname on student(sname);
Create index indexExamExtitle on exam(extitle);
Create index inddexEntrySno on entry(sno);
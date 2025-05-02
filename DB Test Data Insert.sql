Set search_path to cmps_db;

-- Insert sample exams
Insert into exam (excode, extitle, exlocation, exdate, extime) values
    ('DB01', 'Database Systems', 'Main Building Room 101', '2025-11-05', '09:30'),
    ('CS02', 'Computer Networks', 'North Building Room 203', '2025-11-05', '14:00'),
    ('MT03', 'Mathematics for Computing', 'East Building Room 104', '2025-11-06', '09:30'),
    ('AL04', 'Algorithms and Data Structures', 'Main Building Room 101', '2025-11-06', '14:00'),
    ('PB05', 'Programming Basics', 'North Building Room 102', '2025-11-07', '09:30');

-- Insert sample students
Insert into student (sno, sname, semail) values
    (001, 'John Smith', 'john.smith@cmps.org'),
    (002, 'Sarah Johnson', 'sarah.johnson@cmps.org'),
    (003, 'Michael Brown', 'michael.brown@cmps.org'),
    (004, 'Walter Wilson', 'walter.wilson@cmps.org'),
    (005, 'David Taylor', 'david.taylor@cmps.org'),
    (006, 'Lisa Garcia', 'lisa.garcia@cmps.org'),
    (007, 'Robert Davis', 'robert.davis@cmps.org'),
    (008, 'Jessica Miller', 'jessica.miller@cmps.org'),
    (009, 'William Anderson', 'william.anderson@cmps.org'),
    (010, 'Olivia Thomas', 'olivia.thomas@cmps.org'),
    (011, 'James Wilson', 'james.wilson@cmps.org'),
    (012, 'Elizabeth Brown', 'elizabeth.brown@cmps.org'),
    (013, 'David Martinez', 'david.martinez@cmps.org'),
    (014, 'Margaret Davis', 'margaret.davis@cmps.org'),
    (015, 'Richard Miller', 'richard.miller@cmps.org');

-- Insert sample entries
Insert into entry (eno, excode, sno, egrade) values
    (1001, 'DB01', 001, NULL),
    (1002, 'CS02', 002, NULL),
    (1003, 'MT03', 003, NULL),
    (1004, 'AL04', 004, NULL),
    (1005, 'PB05', 005, NULL),
    (1006, 'DB01', 006, NULL),
    (1007, 'CS02', 007, NULL),
    (1008, 'MT03', 008, NULL),
    (1009, 'AL04', 009, NULL),
    (1010, 'PB05', 010, NULL),
    (1011, 'DB01', 011, NULL),
    (1012, 'CS02', 012, NULL),
    (1013, 'MT03', 013, NULL),
    (1014, 'AL04', 014, NULL),
    (1015, 'PB05', 015, NULL);

-- Insert sample cancelled entries
Insert into cancel (eno, excode, sno, cdate, cuser) values
    (1001, 'DB01', 001, '2025-11-01 10:00:00', 'admin'),
    (1003, 'MT03', 002, '2025-11-02 14:30:00', 'system');
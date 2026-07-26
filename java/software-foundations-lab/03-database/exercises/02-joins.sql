-- ============================================================
-- 02-joins.sql — INNER / LEFT / RIGHT / CROSS / SELF joins
-- Prerequisites: schema.sql + seed.sql
-- ============================================================

-- 1. INNER JOIN (most common)
-- Students and their grades
SELECT s.sname, c.cname, sc.grade
FROM sc
JOIN student s ON sc.sid = s.sid
JOIN course  c ON sc.cid = c.cid;

-- 2. LEFT JOIN (keep all rows from the left table)
-- All students, even those with no enrolments
SELECT s.sname, c.cname, sc.grade
FROM student s
LEFT JOIN sc     ON s.sid = sc.sid
LEFT JOIN course c ON sc.cid = c.cid;

-- 3. RIGHT JOIN (keep all rows from the right table)
-- All courses, even those with no enrolments
SELECT s.sname, c.cname, sc.grade
FROM sc
RIGHT JOIN student s ON sc.sid = s.sid
RIGHT JOIN course  c ON sc.cid = c.cid;

-- 4. CROSS JOIN (Cartesian product — every combination)
-- Rarely useful in practice, but appears on exams
SELECT s.sname, c.cname
FROM student s
CROSS JOIN course c;

-- 5. SELF JOIN
-- Find pairs of students in the same department
SELECT a.sname AS student1, b.sname AS student2, a.dept
FROM student a
JOIN student b ON a.dept = b.dept AND a.sid < b.sid;

-- 6. NATURAL JOIN (join on columns with the same name)
-- Avoid in production — fragile; shown for exam awareness
SELECT * FROM student NATURAL JOIN sc;

-- 7. USING clause (shorthand when join columns share the same name)
SELECT sname, cid, grade
FROM student JOIN sc USING (sid);

-- 8. Multi-table join with aggregation
-- Average grade per department
SELECT s.dept, AVG(sc.grade) AS avg_grade
FROM student s
JOIN sc ON s.sid = sc.sid
GROUP BY s.dept;

-- 9. Join with filter
-- CS students and their Database Systems grade
SELECT s.sname, sc.grade
FROM student s
JOIN sc ON s.sid = sc.sid
JOIN course c ON sc.cid = c.cid
WHERE s.dept = 'CS' AND c.cname = 'Database Systems';

-- ============================================================
-- Practice questions
-- ============================================================

-- Q1: List all courses and the number of students enrolled.
-- Count 0 for courses with no enrolments.
-- SELECT c.cname, COUNT(sc.sid) AS enrolment
-- FROM course c
-- LEFT JOIN sc ON c.cid = sc.cid
-- GROUP BY c.cname;

-- Q2: Find students who have NOT taken course 101.
-- SELECT s.sname FROM student s
-- LEFT JOIN sc ON s.sid = sc.sid AND sc.cid = 101
-- WHERE sc.cid IS NULL;

-- Q3: Find pairs of students who share at least 2 courses.
-- SELECT a.sid AS s1, b.sid AS s2
-- FROM sc a JOIN sc b ON a.cid = b.cid AND a.sid < b.sid
-- GROUP BY a.sid, b.sid
-- HAVING COUNT(*) >= 2;

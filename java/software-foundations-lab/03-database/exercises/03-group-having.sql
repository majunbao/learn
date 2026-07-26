-- ============================================================
-- 03-group-having.sql — GROUP BY, HAVING, aggregate functions
-- Prerequisites: schema.sql + seed.sql
-- ============================================================

-- 1. Aggregate functions without GROUP BY
SELECT COUNT(*)   AS total_students FROM student;
SELECT AVG(age)   AS avg_age       FROM student;
SELECT MAX(grade) AS highest       FROM sc;
SELECT MIN(grade) AS lowest        FROM sc;
SELECT SUM(credit) AS total_credits FROM course;

-- 2. GROUP BY — one column
-- Number of students per department
SELECT dept, COUNT(*) AS student_count
FROM student
GROUP BY dept;

-- Average grade per course
SELECT cid, AVG(grade) AS avg_grade
FROM sc
GROUP BY cid;

-- 3. GROUP BY — multiple columns
-- Average grade per (department, course)
SELECT s.dept, sc.cid, AVG(sc.grade) AS avg_grade
FROM student s
JOIN sc ON s.sid = sc.sid
GROUP BY s.dept, sc.cid;

-- 4. HAVING — filter groups (NOT WHERE!)
-- Departments with more than 2 students
SELECT dept, COUNT(*) AS student_count
FROM student
GROUP BY dept
HAVING COUNT(*) > 2;

-- Courses with average grade above 85
SELECT cid, AVG(grade) AS avg_grade
FROM sc
GROUP BY cid
HAVING AVG(grade) > 85;

-- 5. WHERE vs HAVING
-- WHERE filters rows BEFORE grouping
-- HAVING filters groups AFTER grouping

-- CS students only, then count per department
SELECT dept, COUNT(*) AS cnt
FROM student
WHERE dept = 'CS'
GROUP BY dept;

-- Departments where the average age > 21
SELECT dept, AVG(age) AS avg_age
FROM student
GROUP BY dept
HAVING AVG(age) > 21;

-- 6. Complete SELECT execution order (memorise!)
-- FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT

-- Example: CS students, grouped by age, only groups with >1 student
SELECT age, COUNT(*) AS cnt
FROM student
WHERE dept = 'CS'
GROUP BY age
HAVING COUNT(*) > 1
ORDER BY age;

-- 7. GROUP BY with ROLLUP (MySQL extension)
-- Subtotals + grand total
SELECT dept, COUNT(*) AS cnt
FROM student
GROUP BY dept WITH ROLLUP;

-- ============================================================
-- Practice questions
-- ============================================================

-- Q1: Find the student(s) with the highest grade in course 101.
-- SELECT s.sname, sc.grade
-- FROM student s JOIN sc ON s.sid = sc.sid
-- WHERE sc.cid = 101
-- ORDER BY sc.grade DESC LIMIT 1;

-- Q2: For each student, show the number of courses taken and
--     average grade. Only include students with avg > 80.
-- SELECT s.sname, COUNT(*) AS courses, AVG(sc.grade) AS avg_grade
-- FROM student s JOIN sc ON s.sid = sc.sid
-- GROUP BY s.sname
-- HAVING AVG(sc.grade) > 80;

-- Q3: Find departments where ALL students are older than 19.
-- SELECT dept FROM student
-- GROUP BY dept
-- HAVING MIN(age) > 19;

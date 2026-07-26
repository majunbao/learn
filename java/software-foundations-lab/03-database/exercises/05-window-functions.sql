-- ============================================================
-- 05-window-functions.sql — ROW_NUMBER, RANK, LAG/LEAD, etc.
-- Prerequisites: schema.sql + seed.sql
-- Note: Window functions are available in MySQL 8+ and
--       PostgreSQL 8.4+.
-- ============================================================

-- 1. ROW_NUMBER() — unique sequential number per partition
-- Rank students by grade within each course
SELECT s.sname, c.cname, sc.grade,
       ROW_NUMBER() OVER (PARTITION BY sc.cid ORDER BY sc.grade DESC) AS rn
FROM student s
JOIN sc ON s.sid = sc.sid
JOIN course c ON sc.cid = c.cid;

-- Top 2 students per course
WITH ranked AS (
    SELECT s.sname, c.cname, sc.grade,
           ROW_NUMBER() OVER (PARTITION BY sc.cid ORDER BY sc.grade DESC) AS rn
    FROM student s
    JOIN sc ON s.sid = sc.sid
    JOIN course c ON sc.cid = c.cid
)
SELECT sname, cname, grade FROM ranked WHERE rn <= 2;

-- 2. RANK() and DENSE_RANK()
-- RANK: ties share the same rank, next rank skips
-- DENSE_RANK: ties share the same rank, next rank does NOT skip

SELECT s.sname, sc.cid, sc.grade,
       RANK()       OVER (PARTITION BY sc.cid ORDER BY sc.grade DESC) AS rnk,
       DENSE_RANK() OVER (PARTITION BY sc.cid ORDER BY sc.grade DESC) AS drnk
FROM student s
JOIN sc ON s.sid = sc.sid;

-- Example: grades 95, 90, 90, 85
-- RANK:       1, 2, 2, 4
-- DENSE_RANK: 1, 2, 2, 3
-- ROW_NUMBER: 1, 2, 3, 4  (arbitrary order for ties)

-- 3. Aggregate window functions
-- Running total of credits per department
SELECT cname, credit,
       SUM(credit) OVER (PARTITION BY dept ORDER BY credit) AS running_total
FROM course;

-- Average grade across all students (no partition = entire table)
SELECT s.sname, c.cname, sc.grade,
       AVG(sc.grade) OVER () AS overall_avg
FROM student s
JOIN sc ON s.sid = sc.sid
JOIN course c ON sc.cid = c.cid;

-- 4. LAG() and LEAD() — access previous/next row
-- Grade difference from the previous student (alphabetically) in same course
SELECT s.sname, sc.cid, sc.grade,
       LAG(sc.grade, 1) OVER (PARTITION BY sc.cid ORDER BY s.sname) AS prev_grade,
       LEAD(sc.grade, 1) OVER (PARTITION BY sc.cid ORDER BY s.sname) AS next_grade
FROM student s
JOIN sc ON s.sid = sc.sid;

-- 5. FIRST_VALUE() and LAST_VALUE()
-- Highest and lowest grade per course
SELECT s.sname, c.cname, sc.grade,
       FIRST_VALUE(sc.grade) OVER (PARTITION BY sc.cid ORDER BY sc.grade DESC) AS highest,
       FIRST_VALUE(sc.grade) OVER (PARTITION BY sc.cid ORDER BY sc.grade ASC)  AS lowest
FROM student s
JOIN sc ON s.sid = sc.sid
JOIN course c ON sc.cid = c.cid;

-- 6. NTILE(n) — divide rows into n roughly equal groups
-- Quartile ranking of students by grade
SELECT s.sname, sc.cid, sc.grade,
       NTILE(4) OVER (PARTITION BY sc.cid ORDER BY sc.grade DESC) AS quartile
FROM student s
JOIN sc ON s.sid = sc.sid;

-- 7. Window frame specification
-- Rolling 3-row average (current + 2 preceding)
SELECT s.sname, sc.cid, sc.grade,
       AVG(sc.grade) OVER (
           PARTITION BY sc.cid
           ORDER BY sc.grade
           ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
       ) AS rolling_avg
FROM student s
JOIN sc ON s.sid = sc.sid;

-- ============================================================
-- Practice questions
-- ============================================================

-- Q1: Find the student with the second-highest grade in course 101.
-- WITH ranked AS (
--     SELECT s.sname, sc.grade,
--            ROW_NUMBER() OVER (ORDER BY sc.grade DESC) AS rn
--     FROM student s JOIN sc ON s.sid = sc.sid
--     WHERE sc.cid = 101
-- )
-- SELECT sname, grade FROM ranked WHERE rn = 2;

-- Q2: For each student, show their grade and the difference from
--     the course average.
-- SELECT s.sname, c.cname, sc.grade,
--        sc.grade - AVG(sc.grade) OVER (PARTITION BY sc.cid) AS diff
-- FROM student s
-- JOIN sc ON s.sid = sc.sid
-- JOIN course c ON sc.cid = c.cid;

-- Q3: Rank all students by total credits taken (descending).
-- WITH credits AS (
--     SELECT s.sname, SUM(c.credit) AS total_credits
--     FROM student s
--     JOIN sc ON s.sid = sc.sid
--     JOIN course c ON sc.cid = c.cid
--     GROUP BY s.sname
-- )
-- SELECT sname, total_credits,
--        RANK() OVER (ORDER BY total_credits DESC) AS rnk
-- FROM credits;

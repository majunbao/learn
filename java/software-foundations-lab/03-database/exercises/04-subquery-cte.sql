-- ============================================================
-- 04-subquery-cte.sql — Scalar, IN, EXISTS, correlated, CTE
-- Prerequisites: schema.sql + seed.sql
-- ============================================================

-- 1. Scalar subquery (returns exactly one value)
-- Students older than the average age
SELECT sname, age
FROM student
WHERE age > (SELECT AVG(age) FROM student);

-- 2. IN subquery
-- Students who have taken course 101
SELECT sname
FROM student
WHERE sid IN (
    SELECT sid FROM sc WHERE cid = 101
);

-- 3. NOT IN subquery
-- Students who have NOT taken course 101
SELECT sname
FROM student
WHERE sid NOT IN (
    SELECT sid FROM sc WHERE cid = 101
);

-- 4. EXISTS / NOT EXISTS (correlated subquery)
-- Students who have taken at least one Math course
SELECT s.sname
FROM student s
WHERE EXISTS (
    SELECT 1 FROM sc
    JOIN course c ON sc.cid = c.cid
    WHERE sc.sid = s.sid AND c.dept = 'Math'
);

-- Students who have NOT taken any Math course
SELECT s.sname
FROM student s
WHERE NOT EXISTS (
    SELECT 1 FROM sc
    JOIN course c ON sc.cid = c.cid
    WHERE sc.sid = s.sid AND c.dept = 'Math'
);

-- 5. Correlated subquery in SELECT
-- Each student's grade vs the course average
SELECT s.sname, c.cname, sc.grade,
       (SELECT AVG(sc2.grade) FROM sc sc2 WHERE sc2.cid = sc.cid) AS course_avg
FROM student s
JOIN sc ON s.sid = sc.sid
JOIN course c ON sc.cid = c.cid;

-- 6. Subquery in FROM (derived table)
-- Average grade per student, then filter
SELECT sname, avg_grade
FROM (
    SELECT s.sname, AVG(sc.grade) AS avg_grade
    FROM student s
    JOIN sc ON s.sid = sc.sid
    GROUP BY s.sname
) AS student_avg
WHERE avg_grade > 85;

-- 7. ANY / ALL
-- Students whose grade in ANY course is above 90
SELECT DISTINCT s.sname
FROM student s
JOIN sc ON s.sid = sc.sid
WHERE sc.grade > ANY (
    SELECT grade FROM sc WHERE cid = 101
);

-- Students whose grade in ALL courses is above 70
SELECT s.sname
FROM student s
WHERE 70 < ALL (
    SELECT grade FROM sc WHERE sc.sid = s.sid
);

-- 8. CTE (Common Table Expression) — WITH clause
-- More readable than nested subqueries
WITH course_avg AS (
    SELECT cid, AVG(grade) AS avg_grade
    FROM sc
    GROUP BY cid
)
SELECT c.cname, ca.avg_grade
FROM course c
JOIN course_avg ca ON c.cid = ca.cid
ORDER BY ca.avg_grade DESC;

-- 9. Recursive CTE (generate a number series)
WITH RECURSIVE nums AS (
    SELECT 1 AS n
    UNION ALL
    SELECT n + 1 FROM nums WHERE n < 10
)
SELECT * FROM nums;

-- ============================================================
-- Practice questions
-- ============================================================

-- Q1: Find students whose grade in course 101 is higher than
--     their average grade across all courses.
-- WITH student_avg AS (
--     SELECT sid, AVG(grade) AS avg_grade FROM sc GROUP BY sid
-- )
-- SELECT s.sname, sc.grade, sa.avg_grade
-- FROM student s
-- JOIN sc ON s.sid = sc.sid
-- JOIN student_avg sa ON s.sid = sa.sid
-- WHERE sc.cid = 101 AND sc.grade > sa.avg_grade;

-- Q2: Find courses that no EE student has taken.
-- SELECT c.cname FROM course c
-- WHERE NOT EXISTS (
--     SELECT 1 FROM sc
--     JOIN student s ON sc.sid = s.sid
--     WHERE sc.cid = c.cid AND s.dept = 'EE'
-- );

-- Q3: Find the student with the highest grade in each course.
-- WITH ranked AS (
--     SELECT sid, cid, grade,
--            ROW_NUMBER() OVER (PARTITION BY cid ORDER BY grade DESC) AS rn
--     FROM sc
-- )
-- SELECT s.sname, c.cname, r.grade
-- FROM ranked r
-- JOIN student s ON r.sid = s.sid
-- JOIN course c ON r.cid = c.cid
-- WHERE r.rn = 1;

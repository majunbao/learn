-- ============================================================
-- 01-select-where.sql — SELECT, WHERE, BETWEEN, IN, LIKE
-- Prerequisites: schema.sql + seed.sql
-- ============================================================

-- 1. Basic SELECT
-- All columns, all rows
SELECT * FROM student;

-- Specific columns
SELECT sname, dept, age FROM student;

-- Aliases
SELECT sname AS name, dept AS department FROM student;

-- DISTINCT
SELECT DISTINCT dept FROM student;

-- 2. WHERE — filtering rows

-- Exact match
SELECT * FROM student WHERE dept = 'CS';

-- Comparison operators: =, <>, <, <=, >, >=
SELECT sname, age FROM student WHERE age >= 21;

-- AND / OR / NOT
SELECT sname FROM student WHERE dept = 'CS' AND age >= 21;

SELECT sname FROM student WHERE dept = 'CS' OR dept = 'Math';

SELECT sname FROM student WHERE dept NOT IN ('CS');

-- 3. BETWEEN (inclusive)
SELECT sname, age FROM student WHERE age BETWEEN 20 AND 22;
-- Equivalent to: age >= 20 AND age <= 22

-- 4. IN
SELECT sname, dept FROM student WHERE dept IN ('CS', 'Math');

SELECT * FROM course WHERE credit IN (3, 4);

-- 5. LIKE — pattern matching
-- % = any sequence of characters (0 or more)
-- _ = exactly one character

-- Names starting with 'A'
SELECT sname FROM student WHERE sname LIKE 'A%';

-- Names ending with 'e'
SELECT sname FROM student WHERE sname LIKE '%e';

-- Names with 'a' anywhere
SELECT sname FROM student WHERE sname LIKE '%a%';

-- Exactly 3-letter names
SELECT sname FROM student WHERE sname LIKE '___';

-- NOT LIKE
SELECT sname FROM student WHERE sname NOT LIKE 'A%';

-- 6. IS NULL / IS NOT NULL
-- Students without email
-- (none in seed data, but the pattern is important)
SELECT sname FROM student WHERE email IS NULL;

SELECT sname FROM student WHERE email IS NOT NULL;

-- 7. ORDER BY
SELECT sname, age FROM student ORDER BY age ASC;

SELECT sname, age FROM student ORDER BY age DESC;

-- Sort by dept first, then age
SELECT sname, dept, age FROM student ORDER BY dept, age DESC;

-- 8. LIMIT / TOP (MySQL / PostgreSQL)
SELECT sname, age FROM student ORDER BY age DESC LIMIT 3;

-- ============================================================
-- Practice questions (try before uncommenting)
-- ============================================================

-- Q1: Find all students in CS department who are older than 20
-- SELECT sname FROM student WHERE dept = 'CS' AND age > 20;

-- Q2: Find courses whose name contains 'Data'
-- SELECT cname FROM course WHERE cname LIKE '%Data%';

-- Q3: Find students whose age is NOT between 20 and 22
-- SELECT sname, age FROM student WHERE age NOT BETWEEN 20 AND 22;

-- Q4: Find the 3 youngest students
-- SELECT sname, age FROM student ORDER BY age ASC LIMIT 3;

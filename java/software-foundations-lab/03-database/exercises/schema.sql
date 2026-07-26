-- ============================================================
-- schema.sql — shared student / course / sc tables
-- Used by all exercise files in this directory.
-- Compatible with MySQL 8+ and PostgreSQL 14+.
-- ============================================================

DROP TABLE IF EXISTS sc;
DROP TABLE IF EXISTS course;
DROP TABLE IF EXISTS student;

-- -----------------------------------------------------------
-- student
-- -----------------------------------------------------------
CREATE TABLE student (
    sid     BIGINT       PRIMARY KEY,
    sname   VARCHAR(50)  NOT NULL,
    dept    VARCHAR(20)  DEFAULT 'CS',
    age     INT          CHECK (age BETWEEN 0 AND 150),
    email   VARCHAR(80)  UNIQUE
);

-- -----------------------------------------------------------
-- course
-- -----------------------------------------------------------
CREATE TABLE course (
    cid     BIGINT       PRIMARY KEY,
    cname   VARCHAR(80)  NOT NULL,
    credit  INT          NOT NULL CHECK (credit > 0),
    dept    VARCHAR(20)  DEFAULT 'CS'
);

-- -----------------------------------------------------------
-- sc  (student-course enrolment & grade)
-- -----------------------------------------------------------
CREATE TABLE sc (
    sid    BIGINT,
    cid    BIGINT,
    grade  DECIMAL(5,2),
    PRIMARY KEY (sid, cid),
    FOREIGN KEY (sid) REFERENCES student(sid)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (cid) REFERENCES course(cid)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

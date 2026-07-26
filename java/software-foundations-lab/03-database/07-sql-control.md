# 07 — SQL Control Statements (PL/SQL Basics)

> Syllabus reference: P57–P60
>
> SQL is a declarative language, but every commercial DBMS extends it
> with procedural constructs: variables, IF, LOOP, cursors, stored
> procedures, functions and triggers. The dialect names differ —
> **PL/SQL** (Oracle), **T-SQL** (SQL Server), **PL/pgSQL** (PostgreSQL),
> **MySQL routines** — but the exam treats them generically.

---

## 1. Why Procedural SQL?

Pure SQL can't easily express:

* loops with side effects ("for every overdue invoice, send a mail")
* complex business rules wrapped in a single DB call
* event-triggered behaviour ("after an insert, write to audit table")

That's what stored procedures, functions and triggers are for.

---

## 2. Anatomy of a Stored Routine (MySQL syntax used as the canonical form)

```sql
DELIMITER //

CREATE PROCEDURE transfer_funds(
    IN  p_from BIGINT,
    IN  p_to   BIGINT,
    IN  p_amount DECIMAL(12,2),
    OUT p_status VARCHAR(20)
)
BEGIN
    DECLARE v_balance DECIMAL(12,2);

    START TRANSACTION;

    SELECT balance INTO v_balance
    FROM   account
    WHERE  id = p_from
    FOR UPDATE;

    IF v_balance < p_amount THEN
        ROLLBACK;
        SET p_status = 'INSUFFICIENT_FUNDS';
    ELSE
        UPDATE account SET balance = balance - p_amount WHERE id = p_from;
        UPDATE account SET balance = balance + p_amount WHERE id = p_to;
        COMMIT;
        SET p_status = 'OK';
    END IF;
END //

DELIMITER ;
```

Call it:
```sql
CALL transfer_funds(1, 2, 100.00, @s);
SELECT @s;
```

### Parameter modes

| Mode    | Direction          | Notes                                  |
|---------|--------------------|----------------------------------------|
| `IN`    | caller → routine   | default                                |
| `OUT`   | routine → caller   | caller passes a session variable / host var |
| `INOUT` | both               | rare; usually replaced by two params   |

---

## 3. Control-Flow Building Blocks

### 3.1 Conditional
```sql
IF condition THEN
    ...
ELSEIF condition THEN
    ...
ELSE
    ...
END IF;

CASE x
    WHEN 1 THEN ...
    WHEN 2 THEN ...
    ELSE        ...
END CASE;
```

### 3.2 Loops
```sql
-- WHILE
WHILE condition DO
    ...
END WHILE;

-- REPEAT (post-test)
REPEAT
    ...
UNTIL condition END REPEAT;

-- LOOP + LEAVE / ITERATE
my_loop: LOOP
    SET i = i + 1;
    IF i >= 10 THEN LEAVE my_loop; END IF;
    IF i =  5 THEN ITERATE my_loop; END IF;
END LOOP my_loop;
```

### 3.3 Variables
```sql
DECLARE v_count INT DEFAULT 0;
SET v_count = v_count + 1;
SELECT COUNT(*) INTO v_count FROM student;
```

---

## 4. Cursors — Row-by-Row Processing

Cursors let you **walk through a query result set** one row at a time.
Use them sparingly — set-based SQL is almost always faster.

```sql
DECLARE done INT DEFAULT FALSE;
DECLARE v_sid BIGINT;
DECLARE v_name VARCHAR(50);

DECLARE c CURSOR FOR SELECT sid, sname FROM student WHERE dept = 'CS';
DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

OPEN c;
read_loop: LOOP
    FETCH c INTO v_sid, v_name;
    IF done THEN LEAVE read_loop; END IF;
    -- do something with v_sid, v_name
END LOOP;
CLOSE c;
```

The **5 steps of a cursor**: `DECLARE → OPEN → FETCH (loop) → CLOSE`.
The exam likes to ask the order.

---

## 5. Stored Functions

Return **exactly one** value; can be used inside a `SELECT`.

```sql
DELIMITER //
CREATE FUNCTION discounted_price(p DECIMAL(10,2), r DECIMAL(3,2))
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    RETURN p * (1 - r);
END //
DELIMITER ;

SELECT cname, discounted_price(price, 0.1) AS sale FROM product;
```

> Difference between **procedure** and **function**:
>
> | Aspect           | Procedure                 | Function                          |
> |------------------|---------------------------|-----------------------------------|
> | Return value     | Via OUT / INOUT params    | Single return via `RETURNS`       |
> | Invocation       | `CALL`                    | Inside SQL expressions            |
> | Can modify data? | Yes                       | Usually no (varies by DBMS)       |

---

## 6. Triggers — "Run This When Something Happens"

```sql
CREATE TRIGGER trg_student_audit
AFTER INSERT ON student
FOR EACH ROW
BEGIN
    INSERT INTO student_audit(sid, action, ts)
    VALUES (NEW.sid, 'INSERT', NOW());
END;
```

Components every trigger has:

* **Timing** — `BEFORE` or `AFTER` (some DBs also `INSTEAD OF` for views).
* **Event** — `INSERT`, `UPDATE`, `DELETE`.
* **Granularity** — `FOR EACH ROW` (row-level) or `FOR EACH STATEMENT`.
* **Pseudo-rows** — `NEW.*` (after value) and `OLD.*` (before value).

Use cases: audit logs, denormalised aggregates, enforcing complex
constraints. Beware: triggers are invisible side effects; overuse hurts
maintainability.

---

## 7. Exception Handling

```sql
DECLARE CONTINUE HANDLER FOR SQLEXCEPTION
BEGIN
    ROLLBACK;
    -- log the error, set OUT params, etc.
END;

-- Specific SQLSTATE
DECLARE EXIT HANDLER FOR SQLSTATE '23000'
    SET p_status = 'DUPLICATE_KEY';

-- Raise an error
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Negative amount not allowed';
```

---

## 8. Exam-Style Questions

**Q1.** The order of cursor operations is:
> `DECLARE → OPEN → FETCH (in a loop) → CLOSE`.

**Q2.** Which DBMS object runs automatically in response to a DML event?
A. procedure  B. function  C. trigger  D. view
> Answer: C.

**Q3.** Which timing point sees both `OLD` and `NEW` for an `UPDATE`?
A. `BEFORE INSERT`  B. `AFTER DELETE`  C. `BEFORE UPDATE`  D. `AFTER INSERT`
> Answer: C (so does `AFTER UPDATE`).

**Q4.** Functions differ from procedures mainly in:
A. They cannot have parameters
B. They must return a value and can be used in SQL expressions
C. They cannot modify data
D. They run without being called
> Answer: B.

**Q5.** Inside a transaction, after `SIGNAL SQLSTATE '45000'` is raised,
what happens to the previous uncommitted updates?
> Depends on whether a handler intercepts it. With an `EXIT HANDLER` doing
> `ROLLBACK`, they are undone. Otherwise the statement-level rollback
> applies (only the failing statement is undone).

---

## 9. Further Reading

* MySQL Reference Manual — Stored Programs.
* Oracle PL/SQL Language Reference.
* PostgreSQL — Server Programming → PL/pgSQL.

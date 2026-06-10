# Basic Java Tutorial 01: Connect MySQL with JDBC (No Frameworks)

## Goal
Write Java code from scratch, use **only Java standard library + JDBC** to:
1. Connect to MySQL
2. Execute a simple SELECT query
3. Print the result in console

---

## Prerequisites
1. MySQL container running: `docker start mysql-vhr`
2. Database `vhr` created
3. Table `menu` has data

---

## Step 1: Create test class

Create a new class `BasicJdbcTest.java` in `src/main/java/com/vhr/`:

```java
package com.vhr;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.Statement;

public class BasicJdbcTest {

    public static void main(String[] args) {
        // 1. Database connection info
        String url = "jdbc:mysql://127.0.0.1:3306/vhr?characterEncoding=utf-8&useSSL=false&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true";
        String username = "root";
        String password = "123";

        Connection conn = null;
        Statement stmt = null;
        ResultSet rs = null;

        try {
            // 2. Load JDBC driver
            Class.forName("com.mysql.cj.jdbc.Driver");
            System.out.println("Driver loaded successfully");

            // 3. Connect to MySQL
            conn = DriverManager.getConnection(url, username, password);
            System.out.println("Database connected successfully");

            // 4. Create statement and execute SQL
            stmt = conn.createStatement();
            String sql = "SELECT * FROM menu WHERE enabled = 1";
            rs = stmt.executeQuery(sql);

            // 5. Print the result
            System.out.println("\nQuery results from menu table:");
            System.out.println("--------------------------------");
            while (rs.next()) {
                int id = rs.getInt("id");
                String name = rs.getString("name");
                String urlPath = rs.getString("url");
                System.out.println("ID: " + id + " | Name: " + name + " | URL: " + urlPath);
            }
            System.out.println("--------------------------------");

        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            // 6. Clean up resources
            try {
                if (rs != null) rs.close();
                if (stmt != null) stmt.close();
                if (conn != null) conn.close();
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }
}
```

---

## Step 2: Run it!
Right-click `BasicJdbcTest.java` → Run 'main()'

### What you should see:
```
Driver loaded successfully
Database connected successfully

Query results from menu table:
--------------------------------
ID: 1 | Name: 所有 | URL: /
ID: 2 | Name: 员工资料 | URL: /
ID: 3 | Name: 人事管理 | URL: /
... (more rows)
--------------------------------
```

---

## What does each part do?

| Line | What it does |
|------|--------------|
| `Class.forName(...)` | Load MySQL JDBC driver |
| `DriverManager.getConnection(...)` | Connect to MySQL database |
| `conn.createStatement()` | Create a SQL statement object |
| `stmt.executeQuery(sql)` | Send SQL to MySQL and get result |
| `rs.next()` | Move to the next row of results |
| `rs.getInt("id")` | Get value from "id" column as integer |

---

## Next step
In `02-Map-Result-To-Java-Object.md`, we'll write code to automatically convert database rows to Java objects, just like MyBatis does for you, but we'll write it by hand.

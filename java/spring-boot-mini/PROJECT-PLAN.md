# Spring Boot Mini - Project Plan

## Overview
Build a **mini Spring Boot framework from scratch**, then use this framework to build a **real admin backend** (like vhr).

**Final Goal**: Write a framework, then build a real app with it.

---

## Total Structure

```
spring-boot-mini/
├── PROJECT-PLAN.md              (this file)
├── 01-framework-core/           (Spring core implementation - 10 files)
├── 02-data-access/              (Database & ORM - 7 files)
├── 03-web-layer/                (Web server & routing - 8 files)
├── 04-configuration/            (Configuration & properties - 4 files)
├── 05-advanced-features/        (Production features - 5 files)
├── 06-admin-app/                (Real app using our framework - 8 files)
└── source/                      (Actual code)
    └── src/main/java/com/miniboot/
```

---

## Phase 1: Framework Core (`01-framework-core/`) - 10 Files

| # | File | What you build | Spring Equivalent |
|---|------|---------------|-------------------|
| 01 | `01-create-custom-annotations.md` | `@MiniComponent`, `@MiniService`, `@MiniMapper`, `@MiniController` | Stereotype annotations |
| 02 | `02-classpath-scanner.md` | Scan classpath for annotated classes | `@ComponentScan` |
| 03 | `03-bean-definition.md` | Define bean metadata | BeanDefinition |
| 04 | `04-simple-bean-factory.md` | Create and store beans | BeanFactory |
| 05 | `05-application-context.md` | Full application context | ApplicationContext |
| 06 | `06-field-injection.md` | Inject dependencies via fields | `@Autowired` (field) |
| 07 | `07-constructor-injection.md` | Inject via constructor | Constructor injection |
| 08 | `08-setter-injection.md` | Inject via setters | Setter injection |
| 09 | `09-bean-lifecycle.md` | `@MiniPostConstruct`, init methods | Bean lifecycle |
| 10 | `10-singleton-prototype.md` | Bean scopes | Singleton / Prototype |

---

## Phase 2: Data Access (`02-data-access/`) - 7 Files

| # | File | What you build | Spring/MyBatis Equivalent |
|---|------|---------------|--------------------------|
| 01 | `01-raw-jdbc-connection.md` | Database connection pool | DataSource |
| 02 | `02-manual-row-mapping.md` | ResultSet → Object | RowMapper / ResultMap |
| 03 | `03-mapper-interface.md` | Mapper pattern | MyBatis Mapper |
| 04 | `04-jdbc-template.md` | Helper class for JDBC | JdbcTemplate |
| 05 | `05-transaction-interceptor.md` | Open/close connection around method | `@Transactional` |
| 06 | `06-pagination-helper.md` | Page & pageable support | PageHelper / Pageable |
| 07 | `07-foreign-key-join.md` | One-to-many result mapping | Complex ResultMap |

---

## Phase 3: Web Layer (`03-web-layer/`) - 8 Files

| # | File | What you build | Spring Equivalent |
|---|------|---------------|-------------------|
| 01 | `01-embedded-http-server.md` | Java HttpServer startup | Embedded Tomcat |
| 02 | `02-request-handler.md` | Handle HTTP request/response | Servlet |
| 03 | `03-url-router.md` | Map URL to method | `@RequestMapping` |
| 04 | `04-http-method-annotations.md` | GET/POST/PUT/DELETE | `@GetMapping` etc. |
| 05 | `05-request-param-extractor.md` | Extract query params | `@RequestParam` |
| 06 | `06-request-body-parser.md` | Parse JSON body | `@RequestBody` |
| 07 | `07-json-serializer.md` | Object ↔ JSON | Jackson |
| 08 | `08-exception-handler.md` | Global exception handling | `@ExceptionHandler` |

---

## Phase 4: Configuration (`04-configuration/`) - 4 Files

| # | File | What you build | Spring Equivalent |
|---|------|---------------|-------------------|
| 01 | `01-property-file-reader.md` | Read .properties | PropertySources |
| 02 | `02-value-annotation.md` | Inject property values | `@Value` |
| 03 | `03-configuration-class.md` | Configuration beans | `@Configuration` |
| 04 | `04-profile-support.md` | Env-specific config | `@Profile` |

---

## Phase 5: Advanced Features (`05-advanced-features/`) - 5 Files

| # | File | What you build | Spring Equivalent |
|---|------|---------------|-------------------|
| 01 | `01-aop-dynamic-proxy.md` | Method interception | Spring AOP |
| 02 | `02-logging-aspect.md` | Log method calls around methods | Logging aspect |
| 03 | `03-bean-post-processor.md` | Modify beans after creation | BeanPostProcessor |
| 04 | `04-application-listener.md` | Event publishing | ApplicationEvent |
| 05 | `05-startup-banner.md` | Print banner on startup | Spring Boot banner |

---

## Phase 6: Admin App (THE REAL THING!) (`06-admin-app/`) - 8 Files

**Now use our mini framework to build a real admin backend!**

| # | File | Feature |
|---|------|---------|
| 01 | `01-boot-annotation.md` | `@MiniSpringBootApplication` |
| 02 | `02-application-runner.md` | `MiniApplication.run()` - starts everything |
| 03 | `03-database-schema.md` | HR database tables (employee, department, role) |
| 04 | `04-employee-crud.md` | Employee CRUD API |
| 05 | `05-department-tree.md` | Department tree API |
| 06 | `06-role-permission.md` | Role & permission management |
| 07 | `07-user-login.md` | Simple login API |
| 08 | `08-compare-side-by-side.md` | Compare mini code with real Spring Boot code |

---

## Total: 42 Files

---

## Full Project Roadmap

### Month 1: Foundation
- Phase 1 (10 files): Core IoC container
- You'll understand: beans, injection, scopes

### Month 2: Database
- Phase 2 (7 files): Data access layer
- You'll understand: transactions, pagination, ORM

### Month 3: Web
- Phase 3 (8 files): Web server
- You'll understand: routing, params, JSON, exceptions

### Month 4: Polish
- Phase 4 & 5 (9 files): Config + advanced
- You'll understand: AOP, events, profiles

### Month 5: Real App
- Phase 6 (8 files): Build admin backend
- You'll have: A working app using YOUR framework

---

## What you'll have by the end

1. ✅ A mini Spring Boot framework you wrote
2. ✅ Complete understanding of how Spring works
3. ✅ A real admin backend built with YOUR framework
4. ✅ Side-by-side comparison with real Spring Boot

---

## Prerequisites
1. MySQL container running (`docker start mysql-vhr`)
2. Java 11
3. IDEA
4. Patience (42 files worth!)

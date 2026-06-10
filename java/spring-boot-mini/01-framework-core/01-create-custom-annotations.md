# 01 Framework Core: Create Custom Annotations

## Goal
Create our first custom annotations, just like Spring's `@Service`, `@Controller`, etc.

---

## What are annotations?
Annotations are like "labels" you put on classes.
Later, our framework will scan for these labels and treat those classes specially.

---

## Step 1: Create the base annotation

Create `MiniComponent.java`:

```java
package com.miniboot.framework.annotations;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
public @interface MiniComponent {
    String value() default "";
}
```

### What this means:
- `@Target(ElementType.TYPE)`: Can only be used on classes
- `@Retention(RetentionPolicy.RUNTIME)`: Visible at runtime (so our framework can find it)
- `value()`: Optional bean name

---

## Step 2: Create stereotype annotations

These are "specialized" components for different layers.

### @MiniService (for service layer)
```java
package com.miniboot.framework.annotations;

import java.lang.annotation.*;

@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
public @interface MiniService {
    String value() default "";
}
```

### @MiniMapper (for database layer)
```java
package com.miniboot.framework.annotations;

import java.lang.annotation.*;

@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
public @interface MiniMapper {
    String value() default "";
}
```

### @MiniController (for web layer)
```java
package com.miniboot.framework.annotations;

import java.lang.annotation.*;

@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
public @interface MiniController {
    String value() default "";
}
```

---

## Step 3: Test annotations

Let's create a test class to see if annotations work:

```java
package com.miniboot.test;

import com.miniboot.framework.annotations.MiniService;

@MiniService
public class UserService {
    public String hello() {
        return "Hello from UserService!";
    }
}
```

---

## Step 4: Verify annotation is present

Create a simple test to check if the class has our annotation:

```java
package com.miniboot.test;

public class AnnotationTest {
    public static void main(String[] args) {
        // Check if UserService has @MiniService annotation
        boolean hasAnnotation = UserService.class.isAnnotationPresent(MiniService.class);
        System.out.println("UserService has @MiniService: " + hasAnnotation);
        // Should print: UserService has @MiniService: true
    }
}
```

---

## What you just built

| Our annotation | Spring equivalent |
|----------------|-------------------|
| `@MiniComponent` | `@Component` |
| `@MiniService` | `@Service` |
| `@MiniMapper` | `@Mapper` / `@Repository` |
| `@MiniController` | `@Controller` |

---

## Key understanding
1. Annotations are just "markers" on classes
2. They don't do anything by themselves
3. Later, our framework will scan for these markers and handle the classes accordingly

---

## Next tutorial
In `02-classpath-scanner.md`, we'll write code to find all classes with these annotations in the classpath.

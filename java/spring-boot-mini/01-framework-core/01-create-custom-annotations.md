# 01 Framework Core: Create Custom Annotations

## Goal
Create our first custom annotations, just like Spring's `@Service`, `@Controller`, etc.

---

## What are annotations?
Annotations are like "labels" you put on classes.
Later, our framework will scan for these labels and treat those classes specially.

---

## Step 1: Create the base annotation

**File**: `src/main/java/com/miniboot/framework/annotations/MiniComponent.java`

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

#### @Target(ElementType.TYPE)
```java
@Target(ElementType.TYPE)
```
- **Purpose**: Restricts where this annotation can be used
- **ElementType.TYPE**: Only on classes, interfaces, or enums
- **Other options**: `FIELD`, `METHOD`, `CONSTRUCTOR`, `PARAMETER`, etc.

#### @Retention(RetentionPolicy.RUNTIME)
```java
@Retention(RetentionPolicy.RUNTIME)
```
- **Purpose**: Controls how long the annotation is kept
- **RetentionPolicy.RUNTIME**: Annotation is visible at runtime (via reflection)
- **Other options**: 
  - `SOURCE`: Only in source code, discarded by compiler
  - `CLASS`: In .class file, but not accessible at runtime

#### value() default ""
```java
String value() default "";
```
- **Purpose**: Optional attribute for custom bean name
- **`value()`**: Special attribute name - can be omitted when used
- **`default ""`**: If not specified, defaults to empty string

---

## Key Annotation Concepts

| Concept | Explanation |
|---------|-------------|
| `@interface` | Declares an annotation type (special kind of interface) |
| `@Target` | Where the annotation can be applied |
| `@Retention` | How long the annotation persists |
| `value()` | Default attribute name |
| `default` | Default value if not specified |

---

## Step 2: Create stereotype annotations

These are "specialized" components for different layers.

### @MiniService (for service layer)

**File**: `src/main/java/com/miniboot/framework/annotations/MiniService.java`

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

**File**: `src/main/java/com/miniboot/framework/annotations/MiniMapper.java`

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

**File**: `src/main/java/com/miniboot/framework/annotations/MiniController.java`

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

**File**: `src/main/java/com/miniboot/demo/UserService.java`

```java
package com.miniboot.demo;

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

**File**: `src/main/java/com/miniboot/demo/AnnotationTest.java`

```java
package com.miniboot.demo;

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

## How to Run

### Option 1: Use Maven (recommended)

```bash
# In project root directory (where pom.xml is)
mvn -q compile exec:java -Dexec.mainClass="com.miniboot.demo.AnnotationTest"
```

### Option 2: Use IDE (IntelliJ IDEA)

1. Open `AnnotationTest.java` in IDEA
2. Click the green ▶️ play button next to `main` method
3. Or right-click → Run 'AnnotationTest.main()'

### Option 3: Use javac + java (manual)

```bash
# 1. Go to source directory
cd src/main/java

# 2. Compile all needed files
javac com/miniboot/framework/annotations/*.java com/miniboot/framework/beans/*.java com/miniboot/demo/*.java

# 3. Run
java com.miniboot.demo.AnnotationTest
```

### Expected Output

```
UserService has @MiniService: true
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

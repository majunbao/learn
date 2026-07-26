# 02 Framework Core: Classpath Scanner

## Goal
Write code to scan the classpath and find all classes with our annotations (@MiniService, @MiniController, etc.).

This is what Spring's `@ComponentScan` under the hood.

---

## What is classpath scanning?
When our framework starts, it needs to:
1. Look through all .class files in the package
2. Check which classes have our annotations
3. Collect those classes to create beans later

---

## Step 1: Create ClassScanner class

**File**: `src/main/java/com/miniboot/framework/scanner/ClassScanner.java`

```java
package com.miniboot.framework.scanner;

import com.miniboot.framework.annotations.MiniComponent;
import com.miniboot.framework.annotations.MiniController;
import com.miniboot.framework.annotations.MiniMapper;
import com.miniboot.framework.annotations.MiniService;

import java.io.File;
import java.io.IOException;
import java.net.URL;
import java.net.URLDecoder;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.List;

public class ClassScanner {

    /**
     * Scan a package and return all classes with our annotations
     */
    public static List<Class<?>> scanPackage(String packageName) {
        List<Class<?>> classes = new ArrayList<>();
        String packagePath = packageName.replace('.', '/');
        
        try {
            Enumeration<URL> resources = Thread.currentThread()
                    .getContextClassLoader()
                    .getResources(packagePath);
            
            while (resources.hasMoreElements()) {
                URL resource = resources.nextElement();
                String filePath = URLDecoder.decode(resource.getFile(), "UTF-8");
                findClasses(new File(filePath), packageName, classes);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        
        return classes;
    }

    /**
     * Recursively find classes in directory and subdirectories
     */
    private static void findClasses(File directory, String packageName, List<Class<?>> classes) {
        if (!directory.exists()) {
            return;
        }
        
        File[] files = directory.listFiles();
        if (files == null) {
            return;
        }
        
        for (File file : files) {
            if (file.isDirectory()) {
                // Recurse into subdirectory
                findClasses(file, packageName + "." + file.getName(), classes);
            } else if (file.getName().endsWith(".class")) {
                // Found a .class file, load it and check annotations
                String className = packageName + '.' + 
                        file.getName().substring(0, file.getName().length() - 6);
                try {
                    Class<?> clazz = Class.forName(className);
                    
                    // Check if class has any of our annotations
                    if (isComponentClass(clazz)) {
                        classes.add(clazz);
                    }
                } catch (ClassNotFoundException e) {
                    e.printStackTrace();
                }
            }
        }
    }

    /**
     * Check if class has any of our component annotations
     */
    private static boolean isComponentClass(Class<?> clazz) {
        return clazz.isAnnotationPresent(MiniComponent.class) ||
               clazz.isAnnotationPresent(MiniService.class) ||
               clazz.isAnnotationPresent(MiniMapper.class) ||
               clazz.isAnnotationPresent(MiniController.class);
    }
}
```

---

## Step 2: Create test classes

Let's create some test classes to scan:

**File**: `src/main/java/com/miniboot/demo/OrderService.java`

```java
package com.miniboot.demo;

import com.miniboot.framework.annotations.MiniService;

@MiniService
public class OrderService {
    public String getOrder() {
        return "Order 123";
    }
}
```

**File**: `src/main/java/com/miniboot/demo/UserController.java`

```java
package com.miniboot.demo;

import com.miniboot.framework.annotations.MiniController;

@MiniController
public class UserController {
    public String getUser() {
        return "User John";
    }
}
```

---

## Step 3: Test the scanner

**File**: `src/main/java/com/miniboot/demo/ScannerTest.java`

```java
package com.miniboot.demo;

import com.miniboot.framework.scanner.ClassScanner;
import java.util.List;

public class ScannerTest {
    public static void main(String[] args) {
        List<Class<?>> classes = ClassScanner.scanPackage("com.miniboot.demo");
        
        System.out.println("Found " + classes.size() + " component classes:");
        for (Class<?> clazz : classes) {
            System.out.println("- " + clazz.getName());
        }
        
        // Should print:
        // Found 3 component classes:
        // - com.miniboot.demo.OrderService
        // - com.miniboot.demo.UserController
        // - com.miniboot.demo.UserService
    }
}
```

---

## How to Run

### Option 1: Use Maven (recommended)

```bash
# In project root directory (where pom.xml is)
mvn -q compile exec:java -Dexec.mainClass="com.miniboot.demo.ScannerTest"
```

### Option 2: Use IDE (IntelliJ IDEA)

1. Open `ScannerTest.java` in IDEA
2. Click the green ▶️ play button next to `main` method
3. Or right-click → Run 'ScannerTest.main()'

### Option 3: Use javac + java (manual)

```bash
# 1. Go to source directory
cd src/main/java

# 2. Compile all files
javac com/miniboot/framework/annotations/*.java com/miniboot/framework/scanner/*.java com/miniboot/demo/*.java

# 3. Run
java com.miniboot.demo.ScannerTest
```

### Expected Output

```
Found 3 component classes:
- com.miniboot.demo.OrderService
- com.miniboot.demo.UserController
- com.miniboot.demo.UserService
```

> **Note**: The exact number may vary depending on how many `@MiniService`/`@MiniController` classes you have in the `demo` package.

---

## How it works (step by step)

### Step 1: Convert package name to path
```java
String packagePath = packageName.replace('.', '/');
```
- **Purpose**: Convert package name `com.miniboot.test` to file path `com/miniboot/test`
- **Why**: Java package structure maps directly to directory structure on disk

### Step 2: Get package location on disk
```java
Enumeration<URL> resources = Thread.currentThread()
        .getContextClassLoader()
        .getResources(packagePath);
```
- **Purpose**: Find the actual location of the package on disk via classloader
- **ClassLoader**: The component responsible for loading `.class` files
- **Returns**: Multiple URLs possible (if package is split across multiple JARs)

### Step 3: Recursively traverse directories
```java
private static void findClasses(File directory, String packageName, List<Class<?>> classes) {
    // Termination condition: directory doesn't exist
    if (!directory.exists()) {
        return;
    }
    
    // Get all files in directory
    File[] files = directory.listFiles();
    
    for (File file : files) {
        if (file.isDirectory()) {
            // If directory, recurse into it
            findClasses(file, packageName + "." + file.getName(), classes);
        } else if (file.getName().endsWith(".class")) {
            // If .class file, load and check
            ...
        }
    }
}
```
- **Recursion**: Calling itself to traverse all subdirectories
- **Termination**: Stop when directory doesn't exist or is empty

### Step 4: Load .class file
```java
String className = packageName + '.' + 
        file.getName().substring(0, file.getName().length() - 6);
Class<?> clazz = Class.forName(className);
```
- **Purpose**: Convert file name to fully qualified class name, then load the class
- **Example**: `com/miniboot/test/OrderService.class` → `com.miniboot.test.OrderService`
- **`substring(0, length - 6)`**: Remove `.class` suffix (6 characters)

### Step 5: Check annotations
```java
if (isComponentClass(clazz)) {
    classes.add(clazz);
}
```
- **Purpose**: Check if class has `@MiniService`, `@MiniController`, etc.
- **`isComponentClass()`**: Uses reflection to check class annotations

### Step 6: Collect results
All matching classes are collected into `List<Class<?>>` and returned

---

## Key Code Explanation

| Code | Purpose | Technical Point |
|------|---------|-----------------|
| `packageName.replace('.', '/')` | Convert package to path | Java packages = directory structure |
| `getContextClassLoader()` | Get classloader | Responsible for loading bytecode |
| `getResources()` | Get resource location | Supports resources inside JARs |
| `findClasses()` | Recursive traversal | Depth-first directory search |
| `file.getName().endsWith(".class")` | Filter class files | Only process compiled classes |
| `Class.forName(className)` | Load class | Core reflection method |
| `isAnnotationPresent()` | Check annotation | Reflection inspects class metadata |

---

## What you just built

| Our code | Spring equivalent |
|----------|-------------------|
| `ClassScanner.scanPackage()` | `@ComponentScan` |

---

## Key understanding
1. Class scanning is the foundation of Spring Boot
2. Without scanning, Spring wouldn't know which classes to turn into beans

---

## Next tutorial
In `03-bean-definition.md`, we'll define metadata for each bean we found.

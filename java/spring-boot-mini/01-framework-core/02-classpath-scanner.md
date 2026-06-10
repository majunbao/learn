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

```java
package com.miniboot.test;

import com.miniboot.framework.annotations.MiniService;

@MiniService
public class OrderService {
    public String getOrder() {
        return "Order 123";
    }
}
```

```java
package com.miniboot.test;

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

```java
package com.miniboot.test;

import com.miniboot.framework.scanner.ClassScanner;
import java.util.List;

public class ScannerTest {
    public static void main(String[] args) {
        List<Class<?>> classes = ClassScanner.scanPackage("com.miniboot.test");
        
        System.out.println("Found " + classes.size() + " component classes:");
        for (Class<?> clazz : classes) {
            System.out.println("- " + clazz.getName());
        }
        
        // Should print:
        // Found 2 component classes:
        // - com.miniboot.test.OrderService
        // - com.miniboot.test.UserController
    }
}
```

---

## How it works (step by step

1. Convert package name (`com.miniboot.test`) to path (`com/miniboot/test`)
2. Get all resources from classloader for that path
3. Recursively walk through directories
4. For each `.class` file, load the class
5. Check if class has any of our annotations
6. Collect annotated classes

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

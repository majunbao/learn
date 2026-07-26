# 05 Framework Core: Application Context

## Goal
Create ApplicationContext that combines ClassScanner + SimpleBeanFactory.

This is what Spring's `ApplicationContext` does - a complete container.

---

## What is ApplicationContext?

ApplicationContext is a complete IoC container that:
1. Scans for annotated classes
2. Creates BeanDefinitions
3. Registers them with BeanFactory
4. Creates and manages beans

---

## Step 1: Create MiniApplicationContext class

**File**: `src/main/java/com/miniboot/framework/context/MiniApplicationContext.java`

```java
package com.miniboot.framework.context;

import com.miniboot.framework.annotations.MiniComponent;
import com.miniboot.framework.annotations.MiniController;
import com.miniboot.framework.annotations.MiniMapper;
import com.miniboot.framework.annotations.MiniService;
import com.miniboot.framework.beans.BeanDefinition;
import com.miniboot.framework.beans.SimpleBeanFactory;

import java.util.List;

public class MiniApplicationContext {
    
    private final SimpleBeanFactory beanFactory;
    private final String basePackage;
    
    public MiniApplicationContext(String basePackage) {
        this.basePackage = basePackage;
        this.beanFactory = new SimpleBeanFactory();
        
        // Step 1: Scan package
        List<Class<?>> componentClasses = ClassScanner.scanPackage(basePackage);
        
        // Step 2: Create BeanDefinitions
        for (Class<?> clazz : componentClasses) {
            String beanName = getBeanName(clazz);
            BeanDefinition bd = new BeanDefinition(clazz, beanName);
            beanFactory.registerBeanDefinition(beanName, bd);
        }
        
        // Step 3: Pre-instantiate singletons
        preInstantiateSingletons();
    }
    
    /**
     * Get bean name from annotation value or class name
     */
    private String getBeanName(Class<?> clazz) {
        // Check annotation value first
        String name = null;
        if (clazz.isAnnotationPresent(MiniComponent.class)) {
            name = clazz.getAnnotation(MiniComponent.class).value();
        } else if (clazz.isAnnotationPresent(MiniService.class)) {
            name = clazz.getAnnotation(MiniService.class).value();
        } else if (clazz.isAnnotationPresent(MiniMapper.class)) {
            name = clazz.getAnnotation(MiniMapper.class).value();
        } else if (clazz.isAnnotationPresent(MiniController.class)) {
            name = clazz.getAnnotation(MiniController.class).value();
        }
        
        // If annotation has no value, use class name (lowercase first letter)
        if (name == null || name.isEmpty()) {
            String simpleName = clazz.getSimpleName();
            name = Character.toLowerCase(simpleName.charAt(0)) + simpleName.substring(1);
        }
        
        return name;
    }
    
    /**
     * Create all singleton beans upfront (eager initialization)
     */
    private void preInstantiateSingletons() {
        for (String beanName : beanFactory.getBeanNames()) {
            BeanDefinition bd = getBeanDefinition(beanName);
            if (bd.isSingleton() && !bd.isLazyInit()) {
                beanFactory.getBean(beanName);
            }
        }
    }
    
    // Delegate methods to beanFactory
    public Object getBean(String beanName) {
        return beanFactory.getBean(beanName);
    }
    
    public <T> T getBean(Class<T> requiredType) {
        return beanFactory.getBean(requiredType);
    }
    
    public boolean containsBean(String beanName) {
        return beanFactory.containsBean(beanName);
    }
    
    public BeanDefinition getBeanDefinition(String beanName) {
        // In a real implementation, this would be in BeanFactory
        // For simplicity, we'll add a method to access definitions directly
        try {
            java.lang.reflect.Field field = SimpleBeanFactory.class.getDeclaredField("beanDefinitionMap");
            field.setAccessible(true);
            @SuppressWarnings("unchecked")
            java.util.Map<String, BeanDefinition> map = (java.util.Map<String, BeanDefinition>) field.get(beanFactory);
            return map.get(beanName);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
    
    public String[] getBeanNames() {
        return beanFactory.getBeanNames();
    }
}
```

---

## Step 2: Add missing ClassScanner reference

We need to make ClassScanner accessible from context package. Move it or add import:

*(Note: In your actual code, ensure ClassScanner is in the right package)*

---

## Step 3: Test ApplicationContext

**File**: `src/main/java/com/miniboot/demo/ApplicationContextTest.java`

```java
package com.miniboot.test;

import com.miniboot.framework.context.MiniApplicationContext;

public class ApplicationContextTest {
    public static void main(String[] args) {
        // 1. Create context - this automatically scans and creates beans!
        MiniApplicationContext context = new MiniApplicationContext("com.miniboot.test");
        
        // 2. List all beans
        System.out.println("Beans in context:");
        for (String beanName : context.getBeanNames()) {
            System.out.println("- " + beanName);
        }
        
        // 3. Get and use beans
        OrderService orderService = context.getBean(OrderService.class);
        System.out.println("\nOrderService result: " + orderService.getOrder());
        
        UserController userController = (UserController) context.getBean("userController");
        System.out.println("UserController result: " + userController.getUser());
        
        // 4. Verify singleton
        OrderService orderService2 = context.getBean(OrderService.class);
        System.out.println("\nSame instance (singleton): " + (orderService == orderService2));
    }
}
```

### Expected output:
```
Beans in context:
- orderService
- userController

OrderService result: Order 123
UserController result: User John

Same instance (singleton): true
```

---

## How to Run

### Option 1: Use Maven (recommended)

```bash
# In project root directory (where pom.xml is)
mvn compile exec:java -Dexec.mainClass="com.miniboot.demo.ApplicationContextTest"
```

### Option 2: Use IDE (IntelliJ IDEA)

1. Open `ApplicationContextTest.java` in IDEA
2. Click the green ▶️ play button next to `main` method
3. Or right-click → Run 'ApplicationContextTest.main()'

### Option 3: Use javac + java (manual)

```bash
# 1. Go to source directory
cd src/main/java

# 2. Compile all needed files
javac com/miniboot/framework/annotations/*.java com/miniboot/framework/beans/*.java com/miniboot/framework/context/*.java com/miniboot/framework/scanner/*.java com/miniboot/demo/*.java

# 3. Run
java com.miniboot.demo.ApplicationContextTest
```

### Expected Output

```
Beans in context:
- orderService
- userController

OrderService result: Order 123
UserController result: User John

Same instance (singleton): true
```

---

## How it works (step by step)

### Step 1: Create context and scan
```java
public MiniApplicationContext(String basePackage) {
    this.beanFactory = new SimpleBeanFactory();
    
    // Step 1: Scan package
    List<Class<?>> componentClasses = ClassScanner.scanPackage(basePackage);
}
```
- **Create BeanFactory**: Internal container for beans
- **Scan**: Find all classes with component annotations

### Step 2: Create BeanDefinitions
```java
for (Class<?> clazz : componentClasses) {
    String beanName = getBeanName(clazz);
    BeanDefinition bd = new BeanDefinition(clazz, beanName);
    beanFactory.registerBeanDefinition(beanName, bd);
}
```
- **Get bean name**: From annotation value or class name
- **Register**: Store metadata in BeanFactory

### Step 3: Get bean name logic
```java
private String getBeanName(Class<?> clazz) {
    String name = null;
    if (clazz.isAnnotationPresent(MiniComponent.class)) {
        name = clazz.getAnnotation(MiniComponent.class).value();
    } else if (clazz.isAnnotationPresent(MiniService.class)) {
        name = clazz.getAnnotation(MiniService.class).value();
    }
    // ... check other annotations
    
    if (name == null || name.isEmpty()) {
        String simpleName = clazz.getSimpleName();
        name = Character.toLowerCase(simpleName.charAt(0)) + simpleName.substring(1);
    }
    return name;
}
```
- **Priority**: Annotation value > default class name
- **Fallback**: `OrderService` → `orderService`

### Step 4: Pre-instantiate singletons
```java
private void preInstantiateSingletons() {
    for (String beanName : beanFactory.getBeanNames()) {
        BeanDefinition bd = getBeanDefinition(beanName);
        if (bd.isSingleton() && !bd.isLazyInit()) {
            beanFactory.getBean(beanName);
        }
    }
}
```
- **Eager loading**: Create all singletons upfront
- **Why**: Catch errors early during startup
- **Lazy init**: Skip if `lazyInit = true`

### Step 5: Get bean definition (hack)
```java
public BeanDefinition getBeanDefinition(String beanName) {
    java.lang.reflect.Field field = SimpleBeanFactory.class.getDeclaredField("beanDefinitionMap");
    field.setAccessible(true);
    java.util.Map<String, BeanDefinition> map = (java.util.Map<String, BeanDefinition>) field.get(beanFactory);
    return map.get(beanName);
}
```
- **Reflection hack**: Access private field
- **In real Spring**: BeanFactory has proper methods for this
- **Note**: This is simplified for learning

---

## Key Code Explanation

| Code | Purpose | Technical Point |
|------|---------|-----------------|
| `ClassScanner.scanPackage()` | Find annotated classes | Package scanning |
| `getBeanName()` | Resolve bean name | Annotation value or convention |
| `preInstantiateSingletons()` | Eager initialization | Create all singletons upfront |
| `getBeanDefinition()` | Access metadata | Reflection for private access |
| Delegation methods | Forward to BeanFactory | `getBean()`, `containsBean()` |

---

## What you just built

| Our code | Spring equivalent |
|----------|-------------------|
| `MiniApplicationContext` | `AnnotationConfigApplicationContext` |
| `new MiniApplicationContext("com.miniboot")` | `new AnnotationConfigApplicationContext("com.miniboot")` |

---

## Key understanding
1. ApplicationContext = Scanner + BeanFactory
2. Singleton beans are created eagerly by default
3. You only need to create context once, then get beans from it

---

## Next tutorial
In `06-field-injection.md`, we'll implement @MiniAutowired for dependency injection.

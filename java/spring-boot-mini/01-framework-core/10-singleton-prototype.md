# 10 Framework Core: Bean Scopes

## Goal
Implement singleton and prototype scopes, with @MiniScope annotation.

This is Spring's `@Scope` annotation.

---

## Bean Scopes Overview

| Scope | Behavior | Use Case |
|-------|----------|----------|
| **singleton** | One instance per container | Default, stateless beans |
| **prototype** | New instance every time | Stateful beans |
| request | One instance per HTTP request | Web apps |
| session | One instance per HTTP session | Web apps |

We'll implement singleton + prototype.

---

## Step 1: Create @MiniScope annotation

**File**: `src/main/java/com/miniboot/framework/annotations/MiniScope.java`

```java
package com.miniboot.framework.annotations;

import com.miniboot.framework.beans.BeanScope;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
public @interface MiniScope {
    BeanScope value() default BeanScope.SINGLETON;
}
```

---

## Step 2: Update ApplicationContext to read @MiniScope

```java
package com.miniboot.framework.context;

// ... (imports)

public class MiniApplicationContext {
    
    private final SimpleBeanFactory beanFactory;
    private final String basePackage;
    
    public MiniApplicationContext(String basePackage) {
        this.basePackage = basePackage;
        this.beanFactory = new SimpleBeanFactory();
        
        List<Class<?>> componentClasses = ClassScanner.scanPackage(basePackage);
        
        for (Class<?> clazz : componentClasses) {
            String beanName = getBeanName(clazz);
            BeanDefinition bd = new BeanDefinition(clazz, beanName);
            
            // NEW: Read @MiniScope annotation
            if (clazz.isAnnotationPresent(MiniScope.class)) {
                MiniScope scopeAnnotation = clazz.getAnnotation(MiniScope.class);
                bd.setScope(scopeAnnotation.value());
            }
            
            beanFactory.registerBeanDefinition(beanName, bd);
        }
        
        preInstantiateSingletons();
    }
    
    // ... (rest of class remains same)
}
```

---

## Step 3: Create test beans with different scopes

**File**: `src/main/java/com/miniboot/demo/CounterService.java`

```java
package com.miniboot.test;

import com.miniboot.framework.annotations.MiniService;
import com.miniboot.framework.annotations.MiniScope;
import com.miniboot.framework.beans.BeanScope;

@MiniService
@MiniScope(BeanScope.SINGLETON)  // Default, can omit
public class CounterService {
    private int count = 0;
    
    public int incrementAndGet() {
        return ++count;
    }
}
```

**File**: `src/main/java/com/miniboot/demo/RequestScopedProcessor.java`

```java
package com.miniboot.test;

import com.miniboot.framework.annotations.MiniService;
import com.miniboot.framework.annotations.MiniScope;
import com.miniboot.framework.beans.BeanScope;

@MiniService
@MiniScope(BeanScope.PROTOTYPE)  // New instance every time
public class RequestScopedProcessor {
    private int requestId;
    private static int idCounter = 0;
    
    public RequestScopedProcessor() {
        this.requestId = ++idCounter;  // Each instance gets unique ID
    }
    
    public int getRequestId() {
        return requestId;
    }
}
```

---

## Step 4: Test bean scopes

**File**: `src/main/java/com/miniboot/demo/ScopeTest.java`

```java
package com.miniboot.test;

import com.miniboot.framework.context.MiniApplicationContext;

public class ScopeTest {
    public static void main(String[] args) {
        MiniApplicationContext context = new MiniApplicationContext("com.miniboot.test");
        
        System.out.println("=== Testing SINGLETON scope ===");
        // Get singleton bean multiple times
        CounterService counter1 = context.getBean(CounterService.class);
        CounterService counter2 = context.getBean(CounterService.class);
        CounterService counter3 = context.getBean(CounterService.class);
        
        System.out.println("counter1.incrementAndGet(): " + counter1.incrementAndGet()); // 1
        System.out.println("counter2.incrementAndGet(): " + counter2.incrementAndGet()); // 2
        System.out.println("counter3.incrementAndGet(): " + counter3.incrementAndGet()); // 3
        
        System.out.println("Same instance: " + (counter1 == counter2)); // true
        System.out.println("Same instance: " + (counter2 == counter3)); // true
        
        System.out.println("\n=== Testing PROTOTYPE scope ===");
        // Get prototype bean multiple times
        RequestScopedProcessor processor1 = context.getBean(RequestScopedProcessor.class);
        RequestScopedProcessor processor2 = context.getBean(RequestScopedProcessor.class);
        RequestScopedProcessor processor3 = context.getBean(RequestScopedProcessor.class);
        
        System.out.println("processor1.getRequestId(): " + processor1.getRequestId()); // 1
        System.out.println("processor2.getRequestId(): " + processor2.getRequestId()); // 2
        System.out.println("processor3.getRequestId(): " + processor3.getRequestId()); // 3
        
        System.out.println("Different instances: " + (processor1 != processor2)); // true
        System.out.println("Different instances: " + (processor2 != processor3)); // true
        
        System.out.println("\n=== Scope behavior confirmed! ===");
        System.out.println("- SINGLETON: All getBean() return SAME instance");
        System.out.println("- PROTOTYPE: Each getBean() returns NEW instance");
    }
}
```

### Expected output:
```
=== Testing SINGLETON scope ===
counter1.incrementAndGet(): 1
counter2.incrementAndGet(): 2
counter3.incrementAndGet(): 3
Same instance: true
Same instance: true

=== Testing PROTOTYPE scope ===
processor1.getRequestId(): 1
processor2.getRequestId(): 2
processor3.getRequestId(): 3
Different instances: true
Different instances: true

=== Scope behavior confirmed! ===
- SINGLETON: All getBean() return SAME instance
- PROTOTYPE: Each getBean() returns NEW instance
```

---

## How to Run

### Option 1: Use Maven (recommended)

```bash
# In project root directory (where pom.xml is)
mvn compile exec:java -Dexec.mainClass="com.miniboot.demo.ScopeTest"
```

### Option 2: Use IDE (IntelliJ IDEA)

1. Open `ScopeTest.java` in IDEA
2. Click the green ▶️ play button next to `main` method
3. Or right-click → Run 'ScopeTest.main()'

### Option 3: Use javac + java (manual)

```bash
# 1. Go to source directory
cd src/main/java

# 2. Compile all needed files
javac com/miniboot/framework/annotations/*.java com/miniboot/framework/beans/*.java com/miniboot/framework/context/*.java com/miniboot/framework/scanner/*.java com/miniboot/demo/*.java

# 3. Run
java com.miniboot.demo.ScopeTest
```

### Expected Output

```
=== Testing SINGLETON scope ===
counter1.incrementAndGet(): 1
counter2.incrementAndGet(): 2
counter3.incrementAndGet(): 3
Same instance: true
Same instance: true

=== Testing PROTOTYPE scope ===
processor1.getRequestId(): 1
processor2.getRequestId(): 2
processor3.getRequestId(): 3
Different instances: true
Different instances: true

=== Scope behavior confirmed! ===
- SINGLETON: All getBean() return SAME instance
- PROTOTYPE: Each getBean() returns NEW instance
```

---

## How it works (bean scopes step by step)

### Step 1: Create @MiniScope annotation
```java
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
public @interface MiniScope {
    BeanScope value() default BeanScope.SINGLETON;
}
```
- **`value()`**: Returns `BeanScope` enum
- **Default**: `SINGLETON` if not specified

### Step 2: Read @MiniScope during context creation
```java
for (Class<?> clazz : componentClasses) {
    String beanName = getBeanName(clazz);
    BeanDefinition bd = new BeanDefinition(clazz, beanName);
    
    // NEW: Read @MiniScope annotation
    if (clazz.isAnnotationPresent(MiniScope.class)) {
        MiniScope scopeAnnotation = clazz.getAnnotation(MiniScope.class);
        bd.setScope(scopeAnnotation.value());
    }
    
    beanFactory.registerBeanDefinition(beanName, bd);
}
```
- **Check**: Does class have `@MiniScope`?
- **Set**: Update scope in BeanDefinition
- **Default**: If no annotation, scope is `SINGLETON`

### Step 3: Singleton behavior in BeanFactory
```java
if (bd.isSingleton()) {
    if (!singletonObjects.containsKey(beanName)) {
        Object bean = createBean(bd);
        singletonObjects.put(beanName, bean);
        injectDependencies(bean);
        callPostConstruct(bean);
    }
    return singletonObjects.get(beanName);
}
```
- **Cache check**: First time? Create and cache
- **Subsequent**: Return from cache
- **One instance**: Same object every time

### Step 4: Prototype behavior in BeanFactory
```java
// If prototype, create new instance every time
return createBean(bd);
```
- **No caching**: Always create new instance
- **No reuse**: Each call creates fresh object
- **Stateful**: Can have different state per instance

### Step 5: Pre-instantiate singletons only
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
- **Only singletons**: Prototypes are created on-demand
- **Eager loading**: Singletons created at startup

---

## Complete BeanFactory with scopes recap

```
getBean(beanName):
    ↓
Get BeanDefinition
    ↓
If SINGLETON:
    ↓
    In cache? → Yes → Return cached bean
        ↓
        No → Create bean → Cache → Return
    ↓
If PROTOTYPE:
    ↓
    Create bean → Return (NO CACHING!)
```

---

## Key Code Explanation

| Code | Purpose | Technical Point |
|------|---------|-----------------|
| `@MiniScope(BeanScope.SINGLETON)` | Set singleton scope | Default behavior |
| `@MiniScope(BeanScope.PROTOTYPE)` | Set prototype scope | New instance each time |
| `isSingleton()` / `isPrototype()` | Check scope | From BeanDefinition |
| `singletonObjects.containsKey()` | Cache lookup | Check if already created |
| `singletonObjects.put()` | Cache storage | Store singleton instance |

---

## What you just built

| Our code | Spring equivalent |
|----------|-------------------|
| `@MiniScope` | `@Scope` |
| `BeanScope.SINGLETON` | `ConfigurableBeanFactory.SCOPE_SINGLETON` |
| `BeanScope.PROTOTYPE` | `ConfigurableBeanFactory.SCOPE_PROTOTYPE` |

---

## Phase 1 COMPLETE!

You have built a complete core IoC container:
✅ 1. Custom annotations (@MiniService, etc.)
✅ 2. Classpath scanning
✅ 3. BeanDefinition metadata
✅ 4. BeanFactory
✅ 5. ApplicationContext
✅ 6. Field injection
✅ 7. Constructor injection
✅ 8. Setter injection
✅ 9. Bean lifecycle (@MiniPostConstruct)
✅ 10. Bean scopes (singleton/prototype)

---

## Next phase
Phase 2: Data Access (JDBC, ORM, Transactions)

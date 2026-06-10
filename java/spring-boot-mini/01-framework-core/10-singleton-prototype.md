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

## How it works

1. During scanning, check for `@MiniScope` annotation
2. Set scope in BeanDefinition
3. When getBean() is called:
   - **Singleton**: Check cache, create once, cache
   - **Prototype**: Always create new instance, no caching

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

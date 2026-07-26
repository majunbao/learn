# 07 Framework Core: Constructor Injection

## Goal
Implement constructor-based dependency injection.

This is the recommended injection method in Spring (instead of field injection).

---

## Why Constructor Injection?

Benefits over field injection:
1. Dependencies are explicit (can't forget them)
2. Easy to write unit tests
3. Fields can be final
4. Spring recommends it

---

## Step 1: Update @MiniAutowired for constructors

We already made `@MiniAutowired` work for constructors (TARGET includes CONSTRUCTOR).

Now update BeanFactory to use it.

---

## Step 2: Update SimpleBeanFactory with constructor injection

**File**: `src/main/java/com/miniboot/framework/beans/SimpleBeanFactory.java`

```java
package com.miniboot.framework.beans;

import com.miniboot.framework.annotations.MiniAutowired;

import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Parameter;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class SimpleBeanFactory {
    
    private final Map<String, BeanDefinition> beanDefinitionMap = new ConcurrentHashMap<>();
    private final Map<String, Object> singletonObjects = new ConcurrentHashMap<>();
    
    public void registerBeanDefinition(String beanName, BeanDefinition beanDefinition) {
        beanDefinitionMap.put(beanName, beanDefinition);
    }
    
    public Object getBean(String beanName) {
        BeanDefinition bd = beanDefinitionMap.get(beanName);
        if (bd == null) {
            throw new RuntimeException("No bean named '" + beanName + "' found");
        }
        
        if (bd.isSingleton()) {
            if (!singletonObjects.containsKey(beanName)) {
                Object bean = createBean(bd);
                singletonObjects.put(beanName, bean);
                injectFieldDependencies(bean);  // Field injection after creation
            }
            return singletonObjects.get(beanName);
        }
        
        Object bean = createBean(bd);
        injectFieldDependencies(bean);
        return bean;
    }
    
    @SuppressWarnings("unchecked")
    public <T> T getBean(Class<T> requiredType) {
        for (Map.Entry<String, BeanDefinition> entry : beanDefinitionMap.entrySet()) {
            if (requiredType.isAssignableFrom(entry.getValue().getBeanClass())) {
                return (T) getBean(entry.getKey());
            }
        }
        throw new RuntimeException("No bean of type '" + requiredType.getName() + "' found");
    }
    
    /**
     * Create bean using constructor injection (if @MiniAutowired on constructor)
     * or using no-arg constructor.
     */
    private Object createBean(BeanDefinition bd) {
        try {
            Class<?> clazz = bd.getBeanClass();
            
            // Find constructor with @MiniAutowired
            Constructor<?> autowiredConstructor = findAutowiredConstructor(clazz);
            
            if (autowiredConstructor != null) {
                // Use constructor injection
                Object[] args = resolveConstructorArguments(autowiredConstructor);
                return autowiredConstructor.newInstance(args);
            }
            
            // Fallback to no-arg constructor
            return clazz.getDeclaredConstructor().newInstance();
            
        } catch (Exception e) {
            throw new RuntimeException("Failed to create bean: " + bd.getBeanName(), e);
        }
    }
    
    /**
     * Find constructor with @MiniAutowired annotation
     */
    private Constructor<?> findAutowiredConstructor(Class<?> clazz) {
        for (Constructor<?> constructor : clazz.getDeclaredConstructors()) {
            if (constructor.isAnnotationPresent(MiniAutowired.class)) {
                return constructor;
            }
        }
        return null;
    }
    
    /**
     * Resolve constructor arguments by getting beans for each parameter type
     */
    private Object[] resolveConstructorArguments(Constructor<?> constructor) {
        Parameter[] parameters = constructor.getParameters();
        Object[] args = new Object[parameters.length];
        
        for (int i = 0; i < parameters.length; i++) {
            Class<?> paramType = parameters[i].getType();
            args[i] = getBean(paramType);  // Get bean for parameter type
        }
        
        return args;
    }
    
    /**
     * Field injection (from previous lesson)
     */
    private void injectFieldDependencies(Object bean) {
        Class<?> clazz = bean.getClass();
        
        for (Field field : clazz.getDeclaredFields()) {
            if (field.isAnnotationPresent(MiniAutowired.class)) {
                Object dependency = getBean(field.getType());
                try {
                    field.setAccessible(true);
                    field.set(bean, dependency);
                } catch (IllegalAccessException e) {
                    throw new RuntimeException("Failed to inject field: " + field.getName(), e);
                }
            }
        }
    }
    
    public boolean containsBean(String beanName) {
        return beanDefinitionMap.containsKey(beanName);
    }
    
    public String[] getBeanNames() {
        return beanDefinitionMap.keySet().toArray(new String[0]);
    }
}
```

---

## Step 3: Test classes with constructor injection

**File**: `src/main/java/com/miniboot/demo/OrderService.java`

```java
package com.miniboot.test;

import com.miniboot.framework.annotations.MiniAutowired;
import com.miniboot.framework.annotations.MiniService;

@MiniService
public class OrderService {
    
    private final UserDao userDao;  // Note: can be final!
    
    // Constructor with @MiniAutowired
    @MiniAutowired
    public OrderService(UserDao userDao) {
        this.userDao = userDao;
    }
    
    public String getOrder() {
        String user = userDao.findUserById(123L);
        return "Order for: " + user;
    }
}
```

---

## Step 4: Test constructor injection

**File**: `src/main/java/com/miniboot/demo/ConstructorInjectionTest.java`

```java
package com.miniboot.test;

import com.miniboot.framework.context.MiniApplicationContext;

public class ConstructorInjectionTest {
    public static void main(String[] args) {
        // Create context - this uses constructor injection now!
        MiniApplicationContext context = new MiniApplicationContext("com.miniboot.test");
        
        // Get service
        OrderService orderService = context.getBean(OrderService.class);
        
        // Test
        String result = orderService.getOrder();
        System.out.println("Result: " + result);
        // Should print: Result: Order for: User 123 from database
        
        System.out.println("\nConstructor injection successful!");
        System.out.println("Note: userDao field can be final (immutable!)");
    }
}
```

---

## How to Run

### Option 1: Use Maven (recommended)

```bash
# In project root directory (where pom.xml is)
mvn compile exec:java -Dexec.mainClass="com.miniboot.demo.ConstructorInjectionTest"
```

### Option 2: Use IDE (IntelliJ IDEA)

1. Open `ConstructorInjectionTest.java` in IDEA
2. Click the green ▶️ play button next to `main` method
3. Or right-click → Run 'ConstructorInjectionTest.main()'

### Option 3: Use javac + java (manual)

```bash
# 1. Go to source directory
cd src/main/java

# 2. Compile all needed files
javac com/miniboot/framework/annotations/*.java com/miniboot/framework/beans/*.java com/miniboot/framework/context/*.java com/miniboot/framework/scanner/*.java com/miniboot/demo/*.java

# 3. Run
java com.miniboot.demo.ConstructorInjectionTest
```

### Expected Output

```
Result: Order for: User 123 from database

Constructor injection successful!
Note: userDao field can be final (immutable!)
```

---

## How it works (constructor injection step by step)

### Step 1: Find autowired constructor
```java
private Constructor<?> findAutowiredConstructor(Class<?> clazz) {
    for (Constructor<?> constructor : clazz.getDeclaredConstructors()) {
        if (constructor.isAnnotationPresent(MiniAutowired.class)) {
            return constructor;
        }
    }
    return null;
}
```
- **`getDeclaredConstructors()`**: Get all constructors of the class
- **`isAnnotationPresent()`**: Check for `@MiniAutowired`
- **Return**: First matching constructor found

### Step 2: Resolve constructor arguments
```java
private Object[] resolveConstructorArguments(Constructor<?> constructor) {
    Parameter[] parameters = constructor.getParameters();
    Object[] args = new Object[parameters.length];
    
    for (int i = 0; i < parameters.length; i++) {
        Class<?> paramType = parameters[i].getType();
        args[i] = getBean(paramType);  // Get bean for parameter type
    }
    
    return args;
}
```
- **`getParameters()`**: Get all constructor parameters
- **Loop**: For each parameter, resolve dependency
- **`getBean(paramType)`**: Get bean by type

### Step 3: Create bean with constructor
```java
private Object createBean(BeanDefinition bd) {
    Class<?> clazz = bd.getBeanClass();
    
    // Find constructor with @MiniAutowired
    Constructor<?> autowiredConstructor = findAutowiredConstructor(clazz);
    
    if (autowiredConstructor != null) {
        // Use constructor injection
        Object[] args = resolveConstructorArguments(autowiredConstructor);
        return autowiredConstructor.newInstance(args);
    }
    
    // Fallback to no-arg constructor
    return clazz.getDeclaredConstructor().newInstance();
}
```
- **Priority**: Constructor injection > no-arg constructor
- **`newInstance(args)`**: Create instance with resolved dependencies
- **Fallback**: Use no-arg constructor if no `@MiniAutowired` constructor

### Step 4: Field injection after constructor
```java
Object bean = createBean(bd);
singletonObjects.put(beanName, bean);
injectFieldDependencies(bean);  // Field injection after creation
```
- **Order**: Constructor injection first, then field injection
- **Why**: Constructor sets mandatory dependencies, fields set optional

---

## Key Code Explanation

| Code | Purpose | Technical Point |
|------|---------|-----------------|
| `getDeclaredConstructors()` | Get all constructors | Including private |
| `isAnnotationPresent()` | Check constructor annotation | Look for `@MiniAutowired` |
| `getParameters()` | Get constructor parameters | For dependency resolution |
| `newInstance(args)` | Create instance with args | Constructor call |
| `resolveConstructorArguments()` | Get beans for all params | Recursive dependency resolution |

---

## Field Injection vs Constructor Injection

| Aspect | Field Injection | Constructor Injection |
|--------|-----------------|----------------------|
| Visibility | Dependencies hidden | Dependencies explicit |
| Testability | Harder (need reflection) | Easier (just pass args) |
| Immutability | Fields can't be final | Fields can be final |
| Circular dependencies | Might work | Clearly fails |
| Spring recommendation | Not recommended | **Recommended** |

---

## What you just built

| Our code | Spring equivalent |
|----------|-------------------|
| `@MiniAutowired` on constructor | `@Autowired` on constructor |
| Constructor argument resolution | Spring's ConstructorResolver |

---

## Key understanding
1. Constructor injection = dependencies are known at construction time
2. Fields can be `final` (immutable)
3. This is how Spring Boot apps should be written

---

## Next tutorial
In `08-setter-injection.md`, we'll implement setter-based injection.

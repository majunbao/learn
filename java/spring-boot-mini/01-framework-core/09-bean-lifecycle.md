# 09 Framework Core: Bean Lifecycle

## Goal
Implement bean lifecycle callbacks: @MiniPostConstruct.

This is what Spring's `@PostConstruct` does - run custom initialization after dependencies are injected.

---

## Bean Lifecycle Phases

1. Bean instantiation (constructor)
2. **Dependency injection** (fields/setters
3. **Initialization callbacks** (@PostConstruct) ← This lesson
4. Bean ready to use
5. Destroy callbacks (@PreDestroy)

---

## Step 1: Create @MiniPostConstruct annotation

```java
package com.miniboot.framework.annotations;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface MiniPostConstruct {
}
```

---

## Step 2: Update SimpleBeanFactory with lifecycle callbacks

```java
package com.miniboot.framework.beans;

import com.miniboot.framework.annotations.MiniAutowired;
import com.miniboot.framework.annotations.MiniPostConstruct;

import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.lang.reflect.Parameter;
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
                injectDependencies(bean);
                callPostConstruct(bean);  // NEW: Call init after injection
            }
            return singletonObjects.get(beanName);
        }
        
        Object bean = createBean(bd);
        injectDependencies(bean);
        callPostConstruct(bean);  // NEW: Call init after injection
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
    
    private Object createBean(BeanDefinition bd) {
        try {
            Class<?> clazz = bd.getBeanClass();
            Constructor<?> autowiredConstructor = findAutowiredConstructor(clazz);
            
            if (autowiredConstructor != null) {
                Object[] args = resolveConstructorArguments(autowiredConstructor);
                return autowiredConstructor.newInstance(args);
            }
            
            return clazz.getDeclaredConstructor().newInstance();
        } catch (Exception e) {
            throw new RuntimeException("Failed to create bean: " + bd.getBeanName(), e);
        }
    }
    
    private Constructor<?> findAutowiredConstructor(Class<?> clazz) {
        for (Constructor<?> constructor : clazz.getDeclaredConstructors()) {
            if (constructor.isAnnotationPresent(MiniAutowired.class)) {
                return constructor;
            }
        }
        return null;
    }
    
    private Object[] resolveConstructorArguments(Constructor<?> constructor) {
        Parameter[] parameters = constructor.getParameters();
        Object[] args = new Object[parameters.length];
        
        for (int i = 0; i < parameters.length; i++) {
            args[i] = getBean(parameters[i].getType());
        }
        
        return args;
    }
    
    private void injectDependencies(Object bean) {
        injectFieldDependencies(bean);
        injectSetterDependencies(bean);
    }
    
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
    
    private void injectSetterDependencies(Object bean) {
        Class<?> clazz = bean.getClass();
        
        for (Method method : clazz.getDeclaredMethods()) {
            if (method.isAnnotationPresent(MiniAutowired.class) && 
                method.getName().startsWith("set") &&
                method.getParameterCount() == 1) {
                
                Class<?> paramType = method.getParameterTypes()[0];
                Object dependency = getBean(paramType);
                
                try {
                    method.setAccessible(true);
                    method.invoke(bean, dependency);
                } catch (Exception e) {
                    throw new RuntimeException("Failed to inject via setter: " + method.getName(), e);
                }
            }
        }
    }
    
    /**
     * NEW: Call methods annotated with @MiniPostConstruct after all injections
     */
    private void callPostConstruct(Object bean) {
        Class<?> clazz = bean.getClass();
        
        for (Method method : clazz.getDeclaredMethods()) {
            if (method.isAnnotationPresent(MiniPostConstruct.class)) {
                // Must be no-arg method
                if (method.getParameterCount() != 0) {
                    throw new RuntimeException("@MiniPostConstruct method must have no arguments: " 
                            + method.getName());
                }
                
                try {
                    method.setAccessible(true);
                    method.invoke(bean);  // Call the init method
                } catch (Exception e) {
                    throw new RuntimeException("Failed to call @MiniPostConstruct method: " 
                            + method.getName(), e);
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

## Step 3: Test classes with @MiniPostConstruct

```java
package com.miniboot.test;

import com.miniboot.framework.annotations.MiniAutowired;
import com.miniboot.framework.annotations.MiniPostConstruct;
import com.miniboot.framework.annotations.MiniService;

@MiniService
public class OrderService {
    
    @MiniAutowired
    private UserDao userDao;
    
    private String initializedMessage;
    
    public OrderService() {
        // Constructor called - userDao is NULL here!
        System.out.println("Step 1: Constructor called");
        System.out.println("  userDao in constructor: " + userDao);  // null
    }
    
    @MiniPostConstruct
    public void init() {
        // Dependencies are injected NOW!
        System.out.println("Step 2: @MiniPostConstruct called");
        System.out.println("  userDao in init: " + userDao);  // NOT null!
        
        // Do initialization work here
        this.initializedMessage = userDao.findUserById(1L) + " is ready!";
    }
    
    public String getInitializedMessage() {
        return initializedMessage;
    }
}
```

---

## Step 4: Test bean lifecycle

```java
package com.miniboot.test;

import com.miniboot.framework.context.MiniApplicationContext;

public class LifecycleTest {
    public static void main(String[] args) {
        System.out.println("=== Starting context ===");
        
        MiniApplicationContext context = new MiniApplicationContext("com.miniboot.test");
        
        System.out.println("\n=== Context ready, getting bean ===");
        
        OrderService orderService = context.getBean(OrderService.class);
        
        System.out.println("\n=== Using bean ===");
        System.out.println("Result: " + orderService.getInitializedMessage());
        
        System.out.println("\n=== Lifecycle order observed:");
        System.out.println("1. Constructor called (dependencies null)");
        System.out.println("2. Dependencies injected");
        System.out.println("3. @MiniPostConstruct called (dependencies ready!)");
        System.out.println("4. Bean ready to use");
    }
}
```

### Expected output:
```
=== Starting context ===
Step 1: Constructor called
  userDao in constructor: null
Step 2: @MiniPostConstruct called
  userDao in init: com.miniboot.test.UserDao@...

=== Context ready, getting bean ===

=== Using bean ===
Result: User 1 from database is ready!

=== Lifecycle order observed:
1. Constructor called (dependencies null)
2. Dependencies injected
3. @MiniPostConstruct called (dependencies ready!)
4. Bean ready to use
```

---

## Complete Bean Lifecycle Flow

```
1. Constructor called
        ↓
2. Dependencies injected (fields + setters)
        ↓
3. @MiniPostConstruct called ← YOU CAN INIT HERE!
        ↓
4. Bean is READY
        ↓
5. Bean used by application
        ↓
6. @PreDestroy (not implemented yet)
```

---

## What you just built

| Our code | Spring equivalent |
|----------|-------------------|
| `@MiniPostConstruct` | `@PostConstruct` |
| `callPostConstruct()` | InitDestroyAnnotationBeanPostProcessor |

---

## Key understanding
1. Constructor = bean is created, but dependencies NOT injected yet
2. @MiniPostConstruct = ALL dependencies are injected
3. Always use @PostConstruct for initialization logic that needs dependencies

---

## Next tutorial
In `10-singleton-prototype.md`, we'll implement bean scopes.

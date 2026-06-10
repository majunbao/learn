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

## How it works (constructor injection step by step)

1. When creating bean, find constructor with `@MiniAutowired`
2. For each parameter in that constructor:
   - Get parameter type
   - Call `getBean(paramType)` to get the dependency bean
3. Pass all resolved beans to the constructor
4. Done! Bean is created with all dependencies injected

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

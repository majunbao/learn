# 06 Framework Core: Field Injection (@MiniAutowired)

## Goal
Create @MiniAutowired annotation and inject dependencies into bean fields.

This is what Spring's `@Autowired` does.

---

## What is Dependency Injection?

Instead of:
```java
public class OrderService {
    private UserDao userDao = new UserDao();  // Hardcoded dependency
}
```

We do:
```java
public class OrderService {
    @MiniAutowired
    private UserDao userDao;  // Injected by framework
}
```

---

## Step 1: Create @MiniAutowired annotation

```java
package com.miniboot.framework.annotations;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Target({ElementType.FIELD, ElementType.CONSTRUCTOR})
@Retention(RetentionPolicy.RUNTIME)
public @interface MiniAutowired {
}
```

---

## Step 2: Update SimpleBeanFactory with injection logic

```java
package com.miniboot.framework.beans;

import com.miniboot.framework.annotations.MiniAutowired;

import java.lang.reflect.Field;
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
                injectDependencies(bean);  // NEW: Inject after creation
            }
            return singletonObjects.get(beanName);
        }
        
        Object bean = createBean(bd);
        injectDependencies(bean);  // NEW: Inject for prototype too
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
            return bd.getBeanClass().getDeclaredConstructor().newInstance();
        } catch (Exception e) {
            throw new RuntimeException("Failed to create bean: " + bd.getBeanName(), e);
        }
    }
    
    /**
     * NEW: Inject dependencies into @MiniAutowired fields
     */
    private void injectDependencies(Object bean) {
        Class<?> clazz = bean.getClass();
        
        for (Field field : clazz.getDeclaredFields()) {
            if (field.isAnnotationPresent(MiniAutowired.class)) {
                // Find bean by field type
                Object dependency = getBean(field.getType());
                
                // Inject the dependency
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

## Step 3: Create test classes with dependencies

```java
package com.miniboot.test;

import com.miniboot.framework.annotations.MiniMapper;

@MiniMapper
public class UserDao {
    public String findUserById(Long id) {
        return "User " + id + " from database";
    }
}
```

```java
package com.miniboot.test;

import com.miniboot.framework.annotations.MiniAutowired;
import com.miniboot.framework.annotations.MiniService;

@MiniService
public class OrderService {
    
    @MiniAutowired
    private UserDao userDao;  // Will be injected!
    
    public String getOrder() {
        // Use injected dependency
        String user = userDao.findUserById(123L);
        return "Order for: " + user;
    }
}
```

---

## Step 4: Test injection

```java
package com.miniboot.test;

import com.miniboot.framework.context.MiniApplicationContext;

public class AutowiredTest {
    public static void main(String[] args) {
        // Create context - this scans, creates beans, and injects dependencies
        MiniApplicationContext context = new MiniApplicationContext("com.miniboot.test");
        
        // Get service
        OrderService orderService = context.getBean(OrderService.class);
        
        // Call method that uses injected dependency
        String result = orderService.getOrder();
        System.out.println("Result: " + result);
        // Should print: Result: Order for: User 123 from database
        
        System.out.println("\nInjection successful!");
    }
}
```

---

## How it works (step by step)

1. Bean is created via reflection
2. After creation, `injectDependencies()` is called
3. Scan all fields for `@MiniAutowired` annotation
4. For each annotated field:
   - Get field type
   - Call `getBean(fieldType)` to get dependency
   - Use reflection to set field value

---

## What you just built

| Our code | Spring equivalent |
|----------|-------------------|
| `@MiniAutowired` | `@Autowired` |
| `injectDependencies()` | AutowiredAnnotationBeanPostProcessor |

---

## Key understanding
1. Reflection is used to set private fields
2. This creates a "chain" of beans being created
3. Circular dependencies would be a problem (we'll handle later)

---

## Next tutorial
In `07-constructor-injection.md`, we'll implement constructor-based injection.

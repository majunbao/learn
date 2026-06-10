# 08 Framework Core: Setter Injection

## Goal
Implement setter-based dependency injection.

This is the third injection method in Spring (field, constructor, setter).

---

## What is Setter Injection?

Instead of injecting into fields or constructors, inject into setter methods:

```java
public class OrderService {
    private UserDao userDao;
    
    @MiniAutowired
    public void setUserDao(UserDao userDao) {
        this.userDao = userDao;
    }
}
```

---

## Step 1: Update @MiniAutowired for methods

```java
package com.miniboot.framework.annotations;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Target({ElementType.FIELD, ElementType.CONSTRUCTOR, ElementType.METHOD})
@Retention(RetentionPolicy.RUNTIME)
public @interface MiniAutowired {
}
```

---

## Step 2: Update SimpleBeanFactory with setter injection

```java
package com.miniboot.framework.beans;

import com.miniboot.framework.annotations.MiniAutowired;

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
                injectDependencies(bean);  // Inject after creation
            }
            return singletonObjects.get(beanName);
        }
        
        Object bean = createBean(bd);
        injectDependencies(bean);
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
    
    /**
     * Unified injection: fields + setters
     */
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
    
    /**
     * NEW: Setter injection
     */
    private void injectSetterDependencies(Object bean) {
        Class<?> clazz = bean.getClass();
        
        for (Method method : clazz.getDeclaredMethods()) {
            // Look for setter methods with @MiniAutowired
            if (method.isAnnotationPresent(MiniAutowired.class) && 
                method.getName().startsWith("set") &&
                method.getParameterCount() == 1) {
                
                // Get parameter type and resolve bean
                Class<?> paramType = method.getParameterTypes()[0];
                Object dependency = getBean(paramType);
                
                // Call setter method
                try {
                    method.setAccessible(true);
                    method.invoke(bean, dependency);
                } catch (Exception e) {
                    throw new RuntimeException("Failed to inject via setter: " + method.getName(), e);
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

## Step 3: Test classes with setter injection

```java
package com.miniboot.test;

import com.miniboot.framework.annotations.MiniAutowired;
import com.miniboot.framework.annotations.MiniService;

@MiniService
public class OrderService {
    
    private UserDao userDao;
    private OrderDao orderDao;
    
    // Field injection
    @MiniAutowired
    private PaymentService paymentService;
    
    // Setter injection
    @MiniAutowired
    public void setUserDao(UserDao userDao) {
        this.userDao = userDao;
    }
    
    @MiniAutowired
    public void setOrderDao(OrderDao orderDao) {
        this.orderDao = orderDao;
    }
    
    public String getCompleteOrder() {
        String user = userDao.findUserById(123L);
        String order = orderDao.findOrderById(456L);
        String payment = paymentService.processPayment(100.0);
        
        return user + " | " + order + " | " + payment;
    }
}

// Also create OrderDao and PaymentService as @MiniMapper/@MiniService
```

---

## Step 4: Test all injection methods together

```java
package com.miniboot.test;

import com.miniboot.framework.context.MiniApplicationContext;

public class SetterInjectionTest {
    public static void main(String[] args) {
        MiniApplicationContext context = new MiniApplicationContext("com.miniboot.test");
        
        OrderService orderService = context.getBean(OrderService.class);
        
        String result = orderService.getCompleteOrder();
        System.out.println("Result: " + result);
        
        System.out.println("\nAll injection methods working!");
        System.out.println("- Field injection (paymentService)");
        System.out.println("- Setter injection (userDao, orderDao)");
    }
}
```

---

## How it works (setter injection)

1. After bean is created, scan all methods
2. Find methods with `@MiniAutowired`, starting with `set`, one parameter
3. Get bean for parameter type
4. Call setter method via reflection, passing the dependency

---

## Three Injection Methods Summary

| Method | Annotation on | Use Case |
|--------|--------------|----------|
| **Field** | Field | Quick and simple, not recommended |
| **Constructor** | Constructor | **Recommended** - mandatory dependencies |
| **Setter** | Setter method | Optional dependencies, can re-inject |

---

## What you just built

| Our code | Spring equivalent |
|----------|-------------------|
| `@MiniAutowired` on setters | `@Autowired` on setters |
| `injectSetterDependencies()` | Part of AutowiredAnnotationBeanPostProcessor |

---

## Key understanding
1. Three injection methods: field, constructor, setter
2. Constructor injection = mandatory dependencies
3. Setter injection = optional dependencies
4. Field injection = convenience but less clean

---

## Next tutorial
In `09-bean-lifecycle.md`, we'll implement @MiniPostConstruct and bean lifecycle callbacks.

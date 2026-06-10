# 04 Framework Core: Simple Bean Factory

## Goal
Create a BeanFactory that creates beans from BeanDefinitions and stores them.

This is the core of Spring's IoC container.

---

## What is BeanFactory?

BeanFactory is responsible for:
1. Storing BeanDefinitions
2. Creating bean instances from definitions
3. Caching singleton beans
4. Returning beans when requested

---

## Step 1: Create SimpleBeanFactory class

```java
package com.miniboot.framework.beans;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class SimpleBeanFactory {
    
    // Store bean definitions
    private final Map<String, BeanDefinition> beanDefinitionMap = new ConcurrentHashMap<>();
    
    // Cache for singleton beans
    private final Map<String, Object> singletonObjects = new ConcurrentHashMap<>();
    
    /**
     * Register a bean definition
     */
    public void registerBeanDefinition(String beanName, BeanDefinition beanDefinition) {
        beanDefinitionMap.put(beanName, beanDefinition);
    }
    
    /**
     * Get a bean by name
     */
    public Object getBean(String beanName) {
        BeanDefinition bd = beanDefinitionMap.get(beanName);
        if (bd == null) {
            throw new RuntimeException("No bean named '" + beanName + "' found");
        }
        
        // If singleton, return from cache or create and cache
        if (bd.isSingleton()) {
            if (!singletonObjects.containsKey(beanName)) {
                Object bean = createBean(bd);
                singletonObjects.put(beanName, bean);
            }
            return singletonObjects.get(beanName);
        }
        
        // If prototype, create new instance every time
        return createBean(bd);
    }
    
    /**
     * Get bean by type
     */
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
     * Create bean instance using reflection
     */
    private Object createBean(BeanDefinition bd) {
        try {
            // Use no-arg constructor to create instance
            return bd.getBeanClass().getDeclaredConstructor().newInstance();
        } catch (Exception e) {
            throw new RuntimeException("Failed to create bean: " + bd.getBeanName(), e);
        }
    }
    
    /**
     * Check if bean exists
     */
    public boolean containsBean(String beanName) {
        return beanDefinitionMap.containsKey(beanName);
    }
    
    /**
     * Get all bean names
     */
    public String[] getBeanNames() {
        return beanDefinitionMap.keySet().toArray(new String[0]);
    }
}
```

---

## Step 2: Test the BeanFactory

```java
package com.miniboot.test;

import com.miniboot.framework.beans.BeanDefinition;
import com.miniboot.framework.beans.SimpleBeanFactory;

public class BeanFactoryTest {
    public static void main(String[] args) {
        // 1. Create bean factory
        SimpleBeanFactory beanFactory = new SimpleBeanFactory();
        
        // 2. Register bean definition
        BeanDefinition bd = new BeanDefinition(OrderService.class);
        beanFactory.registerBeanDefinition("orderService", bd);
        
        // 3. Get bean (twice to test singleton)
        OrderService service1 = (OrderService) beanFactory.getBean("orderService");
        OrderService service2 = (OrderService) beanFactory.getBean("orderService");
        
        // 4. Test singleton
        System.out.println("Service 1: " + service1);
        System.out.println("Service 2: " + service2);
        System.out.println("Same instance (singleton): " + (service1 == service2));
        // Should print: true
        
        // 5. Test get by type
        OrderService service3 = beanFactory.getBean(OrderService.class);
        System.out.println("Get by type works: " + (service3 != null));
        
        // 6. Call method on bean
        System.out.println("Method call: " + service1.getOrder());
    }
}
```

---

## How it works (step by step)

1. **Register**: Store BeanDefinition in a map
2. **Get by name**: Look up BeanDefinition
3. **Singleton check**: If singleton, check cache first
4. **Create bean**: Use reflection to call no-arg constructor
5. **Cache**: If singleton, store the created bean

---

## What you just built

| Our code | Spring equivalent |
|----------|-------------------|
| `SimpleBeanFactory` | `DefaultListableBeanFactory` |
| `singletonObjects` map | Singleton bean cache |
| `getBean(String)` | `BeanFactory.getBean(String)` |

---

## Key understanding
1. BeanFactory is the heart of IoC container
2. Singleton beans are created once and cached
3. Prototype beans are created every time getBean() is called
4. Reflection is used to create bean instances

---

## Next tutorial
In `05-application-context.md`, we'll build ApplicationContext which combines scanner + bean factory.

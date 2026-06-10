# 03 Framework Core: Bean Definition

## Goal
Create a BeanDefinition class to store metadata about each bean.

This is what Spring's `BeanDefinition` does - stores configuration and metadata about beans before they are created.

---

## What is BeanDefinition?

Before we create a bean, we need to store information about it:
- Bean class
- Bean name
- Scope (singleton/prototype)
- Whether it's lazy initialized
- Dependencies
- etc.

BeanDefinition is like a "recipe" for creating beans.

---

## Step 1: Create BeanScope enum

```java
package com.miniboot.framework.beans;

public enum BeanScope {
    SINGLETON,  // One instance per container (default)
    PROTOTYPE   // New instance every time requested
}
```

---

## Step 2: Create BeanDefinition class

```java
package com.miniboot.framework.beans;

public class BeanDefinition {
    
    private Class<?> beanClass;
    private String beanName;
    private BeanScope scope = BeanScope.SINGLETON;  // Default singleton
    private boolean lazyInit = false;
    
    // Constructors
    public BeanDefinition(Class<?> beanClass) {
        this.beanClass = beanClass;
        this.beanName = getDefaultBeanName(beanClass);
    }
    
    public BeanDefinition(Class<?> beanClass, String beanName) {
        this.beanClass = beanClass;
        this.beanName = beanName;
    }
    
    // Generate default bean name from class name (lowercase first letter)
    private String getDefaultBeanName(Class<?> clazz) {
        String simpleName = clazz.getSimpleName();
        return Character.toLowerCase(simpleName.charAt(0)) + simpleName.substring(1);
    }
    
    // Getters and Setters
    public Class<?> getBeanClass() {
        return beanClass;
    }
    
    public String getBeanName() {
        return beanName;
    }
    
    public void setBeanName(String beanName) {
        this.beanName = beanName;
    }
    
    public BeanScope getScope() {
        return scope;
    }
    
    public void setScope(BeanScope scope) {
        this.scope = scope;
    }
    
    public boolean isLazyInit() {
        return lazyInit;
    }
    
    public void setLazyInit(boolean lazyInit) {
        this.lazyInit = lazyInit;
    }
    
    public boolean isSingleton() {
        return scope == BeanScope.SINGLETON;
    }
    
    public boolean isPrototype() {
        return scope == BeanScope.PROTOTYPE;
    }
    
    @Override
    public String toString() {
        return "BeanDefinition{" +
                "beanClass=" + beanClass.getName() +
                ", beanName='" + beanName + '\'' +
                ", scope=" + scope +
                ", lazyInit=" + lazyInit +
                '}';
    }
}
```

---

## Step 3: Test BeanDefinition

```java
package com.miniboot.test;

import com.miniboot.framework.beans.BeanDefinition;
import com.miniboot.framework.beans.BeanScope;

public class BeanDefinitionTest {
    public static void main(String[] args) {
        // Test 1: Default bean name
        BeanDefinition bd1 = new BeanDefinition(OrderService.class);
        System.out.println("Bean 1: " + bd1);
        // Should print: Bean 1: BeanDefinition{beanClass=com.miniboot.test.OrderService, beanName='orderService', scope=SINGLETON, lazyInit=false}
        
        // Test 2: Custom bean name
        BeanDefinition bd2 = new BeanDefinition(OrderService.class, "myOrderService");
        System.out.println("Bean 2: " + bd2);
        
        // Test 3: Change scope to prototype
        bd2.setScope(BeanScope.PROTOTYPE);
        System.out.println("Bean 2 is prototype: " + bd2.isPrototype());
        System.out.println("Bean 2 is singleton: " + bd2.isSingleton());
    }
}
```

---

## How it works

1. BeanDefinition stores metadata about a bean, not the bean itself
2. Default bean name is class name with first letter lowercase
3. Default scope is singleton

---

## What you just built

| Our code | Spring equivalent |
|----------|-------------------|
| `BeanDefinition` | `BeanDefinition` |
| `BeanScope` | `ConfigurableBeanFactory.SCOPE_SINGLETON` etc. |

---

## Key understanding
1. BeanDefinition = the recipe for beans
2. Actual bean instances are created later from this recipe
3. This separation allows Spring to handle configuration before instantiation

---

## Next tutorial
In `04-simple-bean-factory.md`, we'll create the BeanFactory to create and store beans using these definitions.

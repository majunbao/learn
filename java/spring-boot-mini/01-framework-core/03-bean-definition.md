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

**File**: `src/main/java/com/miniboot/framework/beans/BeanScope.java`

```java
package com.miniboot.framework.beans;

public enum BeanScope {
    SINGLETON,  // One instance per container (default)
    PROTOTYPE   // New instance every time requested
}
```

---

## Step 2: Create BeanDefinition class

**File**: `src/main/java/com/miniboot/framework/beans/BeanDefinition.java`

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

**File**: `src/main/java/com/miniboot/demo/BeanDefinitionTest.java`

```java
package com.miniboot.demo;

import com.miniboot.framework.beans.BeanDefinition;
import com.miniboot.framework.beans.BeanScope;

public class BeanDefinitionTest {
    public static void main(String[] args) {
        // Test 1: Default bean name
        BeanDefinition bd1 = new BeanDefinition(OrderService.class);
        System.out.println("Bean 1: " + bd1);
        // Should print: Bean 1: BeanDefinition{beanClass=com.miniboot.demo.OrderService, beanName='orderService', scope=SINGLETON, lazyInit=false}
        
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

## How to Run

### Option 1: Use Maven (recommended)

```bash
# In project root directory (where pom.xml is)
mvn -q compile exec:java -Dexec.mainClass="com.miniboot.demo.BeanDefinitionTest"
```

### Option 2: Use IDE (IntelliJ IDEA)

1. Open `BeanDefinitionTest.java` in IDEA
2. Click the green ▶️ play button next to `main` method
3. Or right-click → Run 'BeanDefinitionTest.main()'

### Option 3: Use javac + java (manual)

```bash
# 1. Go to source directory
cd src/main/java

# 2. Compile all needed files
javac com/miniboot/framework/annotations/*.java com/miniboot/framework/beans/*.java com/miniboot/demo/*.java

# 3. Run
java com.miniboot.demo.BeanDefinitionTest
```

### Expected Output

```
Bean 1: BeanDefinition{beanClass=com.miniboot.demo.OrderService, beanName='orderService', scope=SINGLETON, lazyInit=false}
Bean 2: BeanDefinition{beanClass=com.miniboot.demo.OrderService, beanName='myOrderService', scope=SINGLETON, lazyInit=false}
Bean 2 is prototype: true
Bean 2 is singleton: false
```

---

## How it works (step by step)

### Step 1: BeanScope enum

**Code**:
```java
public enum BeanScope {
    SINGLETON,  // One instance per container (default)
    PROTOTYPE   // New instance every time requested
}
```

**What is an enum?**

An **enum** is a special Java type for a fixed set of constants. Safer than using strings because:
- Compiler catches typos
- IDE auto-completes all options
- Only valid values are allowed

**What do these two scopes mean?**

| Scope | Meaning | Analogy |
|-------|---------|---------|
| `SINGLETON` | Only ONE instance in the entire container | One water cooler — everyone shares the same one |
| `PROTOTYPE` | A NEW instance every time you request it | Everyone gets their own new bottle |

**Default**: `SINGLETON` (most beans in Spring are singletons)

---

### Step 2: BeanDefinition class

**What is BeanDefinition?**

It's a "recipe" for creating beans. Before we actually create a bean instance, we store all the information about it.

**Fields explained**:

| Field | Type | Purpose |
|-------|------|---------|
| `beanClass` | `Class<?>` | The actual class of the bean |
| `beanName` | `String` | Name used to look up the bean |
| `scope` | `BeanScope` | Singleton or prototype (default: singleton) |
| `lazyInit` | `boolean` | Whether to create on startup or on first request |

**Key methods**:

| Method | What it does |
|--------|-------------|
| `getDefaultBeanName()` | Converts `OrderService` → `orderService` (lowercase first letter — Spring naming convention) |
| `isSingleton()` | Shortcut for `scope == SINGLETON` |
| `isPrototype()` | Shortcut for `scope == PROTOTYPE` |
| `toString()` | Prints all metadata for debugging |

**Why separate definition from instance?**

This is the core of Spring's design:
1. First, collect all recipes (BeanDefinitions)
2. Then, create actual beans from those recipes
3. This lets Spring validate, configure, and process before instantiation

---

### Step 3: Test BeanDefinition

The test verifies all main features:

| Test | What it checks |
|------|---------------|
| Test 1 | Default bean name: `OrderService` → `orderService` |
| Test 2 | Custom bean name: `"myOrderService"` |
| Test 3 | Scope change: singleton → prototype |

---

## Key understanding

1. **BeanDefinition = recipe**, not the actual bean
2. We first collect all definitions, then create beans
3. This separation is why Spring can do so much magic (AOP, validation, etc.)
4. Default scope is singleton — most beans are singletons

---

## What you just built

| Our code | Spring equivalent |
|----------|-------------------|
| `BeanDefinition` | `BeanDefinition` |
| `BeanScope` | `ConfigurableBeanFactory.SCOPE_SINGLETON` / `SCOPE_PROTOTYPE` |

---

## Next tutorial
In `04-simple-bean-factory.md`, we'll create the BeanFactory that actually creates bean instances from these definitions.

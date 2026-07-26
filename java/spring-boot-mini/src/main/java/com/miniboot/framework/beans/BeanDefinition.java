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
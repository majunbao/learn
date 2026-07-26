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
package com.miniboot.demo;

import com.miniboot.framework.annotations.MiniService;

public class AnnotationTest {
    public static void main(String[] args) {
        // 检查 UserService 是否有 @MiniService 注解
        boolean hasAnnotation = UserService.class.isAnnotationPresent(MiniService.class);
        System.out.println("UserService has @MiniService: " + hasAnnotation);
        
        // 创建实例并调用方法
        UserService service = new UserService();
        System.out.println("Service method result: " + service.hello());
    }
}
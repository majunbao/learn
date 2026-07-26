// src/main/java/com/zhifei/lesson01/controller/HelloController.java

package com.zhifei.lesson01.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import java.util.HashMap;
import java.util.Map;

@RestController
public class HelloController {

    /**
     * 基础测试接口
     * 访问: http://localhost:8080/hello
     */
    @GetMapping("/hello")
    public String sayHello() {
        return "Hello, Spring Boot! 🎉 欢迎来到知飞课程！";
    }

    /**
     * 首页接口
     * 访问: http://localhost:8080/
     */
    @GetMapping("/")
    public String home() {
        return "🏠 知飞课程管理系统 - 首页";
    }

    /**
     * 返回 JSON 数据
     * 访问: http://localhost:8080/info
     */
    @GetMapping("/info")
    public Map<String, Object> getInfo() {
        Map<String, Object> info = new HashMap<>();
        info.put("name", "知飞课程");
        info.put("version", "1.0.0");
        info.put("status", "运行中");
        info.put("timestamp", System.currentTimeMillis());
        return info;
    }
}
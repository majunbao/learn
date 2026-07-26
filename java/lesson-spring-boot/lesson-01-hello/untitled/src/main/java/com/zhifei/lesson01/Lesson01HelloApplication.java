// src/main/java/com/zhifei/lesson01/Lesson01HelloApplication.java

package com.zhifei.lesson01;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class Lesson01HelloApplication {

    public static void main(String[] args) {
        SpringApplication.run(Lesson01HelloApplication.class, args);
        System.out.println("✅ 项目启动成功！");
        System.out.println("🌐 访问地址: http://localhost:8080");
        System.out.println("📝 测试接口: http://localhost:8080/hello");
    }

}
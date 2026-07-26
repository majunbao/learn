package com.miniboot.demo;

import com.miniboot.framework.scanner.ClassScanner;
import java.util.List;

public class ScannerTest {
    public static void main(String[] args) {
        List<Class<?>> classes = ClassScanner.scanPackage("com.miniboot.demo");
        
        System.out.println("Found " + classes.size() + " component classes:");
        for (Class<?> clazz : classes) {
            System.out.println("- " + clazz.getName());
        }
        
        // Should print:
        // Found 3 component classes:
        // - com.miniboot.demo.OrderService
        // - com.miniboot.demo.UserController
        // - com.miniboot.demo.UserService
    }
}
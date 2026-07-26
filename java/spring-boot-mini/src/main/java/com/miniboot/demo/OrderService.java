package com.miniboot.demo;

import com.miniboot.framework.annotations.MiniService;

@MiniService
public class OrderService {
    public String getOrder() {
        return "Order 123";
    }
}
package com.miniboot.demo;

import com.miniboot.framework.annotations.MiniService;

@MiniService
public class UserService {
    public String hello() {
        return "Hello from UserService!";
    }
}
package com.miniboot.demo;

import com.miniboot.framework.annotations.MiniController;

@MiniController
public class UserController {
    public String getUser() {
        return "User John";
    }
}
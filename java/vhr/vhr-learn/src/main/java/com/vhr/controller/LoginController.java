package com.vhr.controller;

import com.vhr.bean.Hr;
import com.vhr.security.JwtUtils;
import com.vhr.service.HrService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

@RestController
public class LoginController {

    @Autowired
    private HrService hrService;

    @PostMapping("/login")
    public Map<String, Object> login(@RequestBody Map<String, String> loginRequest) {
        String username = loginRequest.get("username");
        String password = loginRequest.get("password");

        Hr hr = hrService.authenticate(username, password);

        String token = JwtUtils.generateToken(username, hr.getRoles());

        Map<String, Object> result = new HashMap<>();
        result.put("status", 200);
        result.put("token", token);
        result.put("user", hr);
        return result;
    }
}

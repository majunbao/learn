package com.vhr.service.impl;

import com.vhr.bean.Hr;
import com.vhr.mapper.HrMapper;
import com.vhr.service.HrService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class HrServiceImpl implements HrService {

    @Autowired
    private HrMapper hrMapper;

    private final BCryptPasswordEncoder passwordEncoder = new BCryptPasswordEncoder();

    @Override
    public Hr authenticate(String username, String password) {
        Hr hr = hrMapper.loadUserByUsername(username);

        if (hr == null) {
            throw new RuntimeException("User not found: " + username);
        }

        if (hr.getEnabled() == null || !hr.getEnabled()) {
            throw new RuntimeException("Account is disabled: " + username);
        }

        if (!passwordEncoder.matches(password, hr.getPassword())) {
            throw new RuntimeException("Invalid password");
        }

        List<String> roles = hrMapper.getRoleNamesByHrId(hr.getId());
        hr.setRoles(roles);

        hr.setPassword(null);

        return hr;
    }
}

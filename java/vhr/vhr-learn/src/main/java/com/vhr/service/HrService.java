package com.vhr.service;

import com.vhr.bean.Hr;

public interface HrService {
    Hr authenticate(String username, String password);
}
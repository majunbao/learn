package com.vhr.service.impl;

import com.vhr.bean.Menu;
import com.vhr.mapper.MenuMapper;
import com.vhr.service.MenuService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class MenuServiceImpl implements MenuService {

    @Autowired
    private MenuMapper menuMapper;

    @Override
    public List<Menu> getAllMenus() {
        return menuMapper.getAllMenus();
    }

    @Override
    public List<Menu> getMenusByRoleNames(List<String> roleNames) {
        return menuMapper.getMenusByRoleNames(roleNames);
    }
}

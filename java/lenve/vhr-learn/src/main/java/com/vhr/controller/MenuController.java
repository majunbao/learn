package com.vhr.controller;

import com.vhr.bean.Menu;
import com.vhr.service.MenuService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
public class MenuController {

    @Autowired
    private MenuService menuService;

    @GetMapping("/menu/all")
    public List<Menu> getAllMenus() {
        return menuService.getAllMenus();
    }
}
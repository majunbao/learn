package com.vhr.controller;

import com.vhr.bean.Menu;
import com.vhr.service.MenuService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.stream.Collectors;

@RestController
public class MenuController {

    @Autowired
    private MenuService menuService;

    /**
     * GET /menu/my
     * Returns only the menus that the currently logged-in user's roles can access.
     */
    @GetMapping("/menu/my")
    public List<Menu> getMyMenus(Authentication authentication) {
        List<String> roleNames = authentication.getAuthorities().stream()
                .map(GrantedAuthority::getAuthority)
                .collect(Collectors.toList());

        return menuService.getMenusByRoleNames(roleNames);
    }

    /**
     * GET /menu/all
     * Returns all menus (admin-only in production; kept for learning).
     */
    @GetMapping("/menu/all")
    public List<Menu> getAllMenus() {
        return menuService.getAllMenus();
    }
}

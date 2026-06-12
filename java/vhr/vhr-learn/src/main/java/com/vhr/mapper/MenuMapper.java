package com.vhr.mapper;

import com.vhr.bean.Menu;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface MenuMapper {
    List<Menu> getAllMenus();
    List<Menu> getMenusByRoleNames(@Param("roleNames") List<String> roleNames);
}

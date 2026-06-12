package com.vhr.mapper;

import com.vhr.bean.Hr;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface HrMapper {
    Hr loadUserByUsername(String username);
    List<String> getRoleNamesByHrId(Integer hrId);
}

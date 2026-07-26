package com.miniboot.framework.beans;

public enum BeanScope {
    SINGLETON,  // One instance per container (default)
    PROTOTYPE   // New instance every time requested
}
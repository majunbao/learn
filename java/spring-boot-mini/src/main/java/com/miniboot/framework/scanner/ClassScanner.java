package com.miniboot.framework.scanner;

import com.miniboot.framework.annotations.MiniComponent;
import com.miniboot.framework.annotations.MiniController;
import com.miniboot.framework.annotations.MiniMapper;
import com.miniboot.framework.annotations.MiniService;

import java.io.File;
import java.io.IOException;
import java.net.URL;
import java.net.URLDecoder;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.List;

public class ClassScanner {

    /**
     * Scan a package and return all classes with our annotations
     */
    public static List<Class<?>> scanPackage(String packageName) {
        List<Class<?>> classes = new ArrayList<>();
        String packagePath = packageName.replace('.', '/');
        
        try {
            Enumeration<URL> resources = Thread.currentThread()
                    .getContextClassLoader()
                    .getResources(packagePath);
            
            while (resources.hasMoreElements()) {
                URL resource = resources.nextElement();
                String filePath = URLDecoder.decode(resource.getFile(), "UTF-8");
                findClasses(new File(filePath), packageName, classes);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        
        return classes;
    }

    /**
     * Recursively find classes in directory and subdirectories
     */
    private static void findClasses(File directory, String packageName, List<Class<?>> classes) {
        if (!directory.exists()) {
            return;
        }
        
        File[] files = directory.listFiles();
        if (files == null) {
            return;
        }
        
        for (File file : files) {
            if (file.isDirectory()) {
                // Recurse into subdirectory
                findClasses(file, packageName + "." + file.getName(), classes);
            } else if (file.getName().endsWith(".class")) {
                // Found a .class file, load it and check annotations
                String className = packageName + '.' + 
                        file.getName().substring(0, file.getName().length() - 6);
                try {
                    Class<?> clazz = Class.forName(className);
                    
                    // Check if class has any of our annotations
                    if (isComponentClass(clazz)) {
                        classes.add(clazz);
                    }
                } catch (ClassNotFoundException e) {
                    e.printStackTrace();
                }
            }
        }
    }

    /**
     * Check if class has any of our component annotations
     */
    private static boolean isComponentClass(Class<?> clazz) {
        return clazz.isAnnotationPresent(MiniComponent.class) ||
               clazz.isAnnotationPresent(MiniService.class) ||
               clazz.isAnnotationPresent(MiniMapper.class) ||
               clazz.isAnnotationPresent(MiniController.class);
    }
}
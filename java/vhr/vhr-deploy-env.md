# vhr 学习项目 · 容器化部署手册

> 适用场景：项目跑通后，把整套应用一键启动，给别人演示或上服务器部署。
>
> 架构：MySQL + Spring Boot 后端 + Nginx + Vue 前端，**全部**在 Docker 容器里跑，用 docker-compose 统一管理。
>
> ⚠️ **前置条件**：先完成《开发环境搭建手册》，确保代码在本地能跑通。

---

## 目录

1. [目标架构](#0-目标架构)
2. [目录结构](#1-目录结构)
3. [编写 Dockerfile（后端）](#2-编写-dockerfile后端)
4. [编写 Dockerfile + Nginx 配置（前端）](#3-编写-dockerfile--nginx-配置前端)
5. [编写 docker-compose.yml](#4-编写-docker-composeyml)
6. [启动整套环境](#5-启动整套环境)
7. [常用命令速查](#6-常用命令速查)
8. [常见问题排查](#7-常见问题排查)
9. [完成检查清单](#8-完成检查清单)

---

## 0. 目标架构

```
                         Docker
┌───────────────────────────────────────────────┐
│                                               │
│   ┌─────────────┐    ┌─────────────┐          │
│   │   Nginx     │    │ Spring Boot │          │
│   │   (Vue 前端) │───▶│   (后端)    │──┐       │
│   │  端口 80 → 外│    │  8082 内部 │  │       │
│   └─────────────┘    └─────────────┘  │       │
│                                        ▼       │
│                                  ┌──────────┐ │
│                                  │  MySQL   │ │
│                                  │  (vhr库) │ │
│                                  │  3306内部│ │
│                                  └──────────┘ │
│                                               │
│                docker-compose up -d           │
└───────────────────────────────────────────────┘
```

| 组件 | 运行位置 | 对外端口 | 对内通信地址 |
|------|---------|---------|-------------|
| MySQL | Docker 容器 | 3306（可选，开发调试时打开） | `mysql` |
| Spring Boot 应用 | Docker 容器 | 8082（可选，也可只让 Nginx 访问） | `vhr-web` |
| Nginx（托管 Vue 前端） | Docker 容器 | **80**（浏览器直接访问） | `nginx` |

> 外部访问路径：浏览器 → `http://localhost/` → Nginx 给前端页面 → 前端 JS 调后端接口 → Nginx 把 `/api` 请求转发给 Spring Boot 容器 → Spring Boot 调 MySQL

---

## 1. 目录结构（最终目标）

```
vhr-learn/
├── vhr-dev-env.md            ← 开发环境手册
├── vhr-deploy-env.md         ← 本文件（部署环境手册）
├── docker-compose.yml         ← 新建（第 5 节）
├── vhr.sql                    ← 数据库脚本
├── mysql-data/                ← Docker 自动生成（MySQL 数据持久化）
│
├── vhr-web/                   ← 你的 Spring Boot 项目（按 02 文档创建）
│   ├── src/
│   ├── pom.xml
│   ├── Dockerfile             ← 新建（第 2 节）
│   └── target/vhr-web.jar     ← 打包后自动生成
│
└── vuehr/                     ← 前端项目（Vue 2）
    ├── src/
    ├── package.json
    ├── Dockerfile             ← 新建（第 3 节）
    ├── nginx.conf             ← 新建（第 3 节）
    └── dist/                  ← npm run build 后自动生成
```

---

## 2. 编写 Dockerfile（后端）

> Dockerfile 的作用：把 Spring Boot 应用打包成一个 Docker 镜像。

在你的 **Spring Boot 项目根目录**（例如 `vhr-web/`）下创建文件 `Dockerfile`。

### 版本一：推荐（用本地已打包好的 jar）

先在本地用 Maven 打包一次，然后 Docker 直接用打包结果。这样最快，构建镜像几秒钟。

```dockerfile
# 使用轻量级的 JRE 11 镜像作为运行基础
FROM openjdk:11-jre-slim

# 设置工作目录
WORKDIR /app

# 把本地打包好的 jar 文件复制到镜像里
# 注意：jar 文件名按你实际项目来，通常是 {artifactId}-{version}.jar
COPY target/vhr-web.jar app.jar

# 设置时区，确保日志和数据库时间正确
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 对外暴露的端口（和 application.properties 里的 server.port 一致）
EXPOSE 8082

# 启动命令
ENTRYPOINT ["java", "-jar", "app.jar"]
```

**使用步骤**：

```bash
# 1. 先在 Spring Boot 项目目录下打包
cd vhr-web
mvn clean package -DskipTests

# 2. 确认 target 目录下有 jar 文件
ls target/*.jar
```

### 版本二：完整构建（在 Docker 内部打包）

不想在本地装 Maven？用多阶段构建，Docker 内部完成打包。镜像构建慢一些（要下载 Maven 依赖），但环境最干净。

```dockerfile
# ======== 第一阶段：构建 ========
FROM maven:3.8.6-openjdk-11 AS builder
WORKDIR /app

# 先复制 pom.xml，利用 Docker 缓存加速
COPY pom.xml .
RUN mvn dependency:go-offline -q

# 再复制源码并打包
COPY src ./src
RUN mvn clean package -DskipTests

# ======== 第二阶段：运行 ========
FROM openjdk:11-jre-slim
WORKDIR /app

# 从构建阶段把 jar 拿过来
COPY --from=builder /app/target/*.jar app.jar

ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

EXPOSE 8082
ENTRYPOINT ["java", "-jar", "app.jar"]
```

> **初学者建议用版本一**：先在本地 `mvn package` 打包成功，再做镜像。这样出问题好排查。

---

## 3. 编写 Dockerfile + Nginx 配置（前端）

> 思路：先在本地用 `npm run build` 把 Vue 编译成静态 HTML/JS/CSS 文件（生成 `dist/` 目录），然后让 Nginx 托管这些静态文件。Nginx 同时负责把 `/api` 请求转发给 Spring Boot 容器。

### 3.1 准备工作：先在本地构建前端

```bash
cd vuehr

# 1. 确保有依赖（首次）
npm install

# 2. 构建生产包
npm run build

# 3. 确认 dist 目录存在，里面有 index.html
ls dist/
```

> 成功后 `vuehr/dist/` 目录下会有 `index.html` 和一堆 `.js`、`.css` 文件。

### 3.2 在 vuehr/ 目录下创建 nginx.conf

这个配置告诉 Nginx 两件事：
1. 访问 `/`（根路径）时，把 `dist/` 里的前端文件给浏览器
2. 访问 `/api` 开头的路径时，转发给 Spring Boot 容器（`vhr-web:8082`）

```nginx
worker_processes auto;

events {
    worker_connections 1024;
}

http {
    include       mime.types;
    default_type  application/octet-stream;
    sendfile      on;
    keepalive_timeout 65;

    server {
        listen       80;
        server_name  localhost;

        # ---- 前端静态文件 ----
        location / {
            root   /usr/share/nginx/html;
            index  index.html index.htm;
            # Vue Router history 模式：所有 404 回退到 index.html
            try_files $uri $uri/ /index.html;
        }

        # ---- 把 /api 请求转发给 Spring Boot ----
        # 方式 A：前端请求的路径已经带 /api 前缀，直接转发
        location /api/ {
            proxy_pass         http://vhr-web:8082/;
            proxy_set_header   Host              $host;
            proxy_set_header   X-Real-IP         $remote_addr;
            proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Proto $scheme;
            proxy_connect_timeout 30s;
            proxy_read_timeout    30s;
        }

        # ---- 或者：前端请求的路径不带 /api，直接把所有非静态文件都转发后端 ----
        # 如果你前端代码里直接调的是 `/login`、`/hr` 这种（没前缀），
        # 把上面的 location /api/ 删掉，改用下面这个 location（但要放在 location / 之前）
        #
        # location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        #     root   /usr/share/nginx/html;
        # }
        #
        # location / {
        #     # 先尝试找静态文件，找不到就交给 index.html（前端路由）
        #     try_files $uri @backend;
        # }
        #
        # location @backend {
        #     proxy_pass         http://vhr-web:8082;
        #     proxy_set_header   Host              $host;
        #     proxy_set_header   X-Real-IP         $remote_addr;
        #     proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        # }

        # 错误页
        error_page   500 502 503 504  /50x.html;
        location = /50x.html {
            root   /usr/share/nginx/html;
        }
    }
}
```

**重点提示**：
- `proxy_pass http://vhr-web:8082/` 里的 `vhr-web` 是 docker-compose 里后端服务的名字（service 名），Nginx 容器用这个名字在 Docker 内部网络找到 Spring Boot 容器，**不是 `127.0.0.1`**。
- 用哪种转发方式取决于你的前端代码：看 `vuehr/src/` 里 axios 的 `baseURL` 写的是什么，有没有 `/api` 前缀。

### 3.3 在 vuehr/ 目录下创建 Dockerfile

```dockerfile
# 用 Nginx 镜像做基础
FROM nginx:1.25-alpine

# 把我们写的 nginx.conf 覆盖掉 Nginx 默认配置
COPY nginx.conf /etc/nginx/nginx.conf

# 把构建好的前端 dist/ 目录复制到 Nginx 的静态文件目录
COPY dist/ /usr/share/nginx/html/

# 对外暴露 80 端口
EXPOSE 80

# 启动 Nginx（容器默认命令就是这个，写出来是为了清晰）
CMD ["nginx", "-g", "daemon off;"]
```

### 3.4 此时前端目录结构应该是这样

```
vuehr/
├── src/
├── package.json
├── Dockerfile      ← 新创建
├── nginx.conf      ← 新创建
└── dist/           ← npm run build 后生成
    ├── index.html
    └── ...
```

---

## 4. 编写 docker-compose.yml

> docker-compose.yml 的作用：一句话启动 MySQL + Spring Boot + Nginx 三个容器，并且自动处理网络连接和请求转发。

在 `vhr-learn` **根目录**下创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  # ============== MySQL ==============
  mysql:
    image: mysql:5.7
    container_name: vhr-mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: "123"
      MYSQL_DATABASE: vhr
    ports:
      - "3306:3306"
    # 数据持久化：容器删掉，数据还在本机
    volumes:
      - ./mysql-data:/var/lib/mysql
      # 如果想让 MySQL 首次启动时自动导入 SQL，取消下一行注释
      # - ./vhr.sql:/docker-entrypoint-initdb.d/vhr.sql
    command:
      - --character-set-server=utf8mb4
      - --collation-server=utf8mb4_unicode_ci
    # 健康检查：确保 MySQL 真的启动完成后，应用才启动
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-uroot", "-p123"]
      interval: 5s
      timeout: 5s
      retries: 20

  # ============== Spring Boot 后端 ==============
  vhr-web:
    build:
      context: ./vhr-web     # ← 改成你实际的 Spring Boot 项目目录名
      dockerfile: Dockerfile
    container_name: vhr-web
    restart: unless-stopped
    # 注意：后端端口可以不暴露给外部，让 Nginx 来代理（更安全）
    # 如果你想直接访问后端接口（调试用），保留下面这行；否则删掉
    ports:
      - "8082:8082"
    environment:
      # 关键：容器内部访问 MySQL 时，地址是服务名 "mysql"，不是 127.0.0.1
      SPRING_DATASOURCE_URL: jdbc:mysql://mysql:3306/vhr?useUnicode=true&characterEncoding=UTF-8&useSSL=false&serverTimezone=Asia/Shanghai
      SPRING_DATASOURCE_USERNAME: root
      SPRING_DATASOURCE_PASSWORD: "123"
    depends_on:
      mysql:
        condition: service_healthy   # 等 MySQL 健康检查通过再启动

  # ============== Nginx + Vue 前端 ==============
  nginx:
    build:
      context: ./vuehr       # ← 改成你实际的前端项目目录名
      dockerfile: Dockerfile
    container_name: vhr-nginx
    restart: unless-stopped
    ports:
      - "80:80"              # 浏览器访问 http://localhost/ 即可看到前端
    depends_on:
      - vhr-web              # 等后端起来再启动前端
```

### 参数重点说明

| 配置项 | 为什么这么写 |
|--------|-------------|
| `context: ./vhr-web` | 构建后端镜像时去 `vhr-web/` 目录找文件。**改成你实际的项目目录名**。 |
| `context: ./vuehr` | 构建前端镜像时去 `vuehr/` 目录找文件。**改成你实际的前端目录名**。 |
| `SPRING_DATASOURCE_URL` 的主机是 `mysql` | 容器在同一个 Docker 网络里，用服务名互相访问，**不是 `127.0.0.1`**。 |
| `nginx` 的 `proxy_pass http://vhr-web:8082` | Nginx 把 API 请求转发给后端，用服务名 `vhr-web` 找到后端容器。这个配置写在 `vuehr/nginx.conf` 里。 |
| `depends_on` + `condition: service_healthy` | 防止应用启动太快，MySQL 还没准备好就去连数据库。 |
| `restart: unless-stopped` | 容器意外退出时自动重启；你手动停止的不会自动启动。 |
| `volumes: ./mysql-data:/var/lib/mysql` | 把 MySQL 数据写到本机的 `mysql-data/` 目录。删容器、重启容器，数据都不丢。 |
| `nginx` 暴露 `80:80` | 浏览器直接访问 `http://localhost/` 就能看到前端，不需要带端口。如果 80 端口被占用，改成 `8080:80`，访问 `http://localhost:8080/`。 |

### application.properties 建议

建议让 `application.properties` 里的数据库配置可以被环境变量覆盖，写成这样：

```properties
spring.datasource.url=${SPRING_DATASOURCE_URL:jdbc:mysql://127.0.0.1:3306/vhr?useUnicode=true&characterEncoding=UTF-8}
spring.datasource.username=${SPRING_DATASOURCE_USERNAME:root}
spring.datasource.password=${SPRING_DATASOURCE_PASSWORD:123}
```

含义：有环境变量就用环境变量（Docker 容器里会注入），没有就用默认值（本地开发时用 `127.0.0.1`）。

> **如果不想改配置**也没关系，docker-compose.yml 里注入的 `SPRING_DATASOURCE_*` 环境变量，Spring Boot 默认就会识别并覆盖 `application.properties` 里的同名配置。

---

## 5. 启动整套环境

### 5.1 准备工作

1. 打包 Spring Boot 后端：

   ```bash
   cd vhr-web
   mvn clean package -DskipTests
   cd ..
   ```

2. 构建 Vue 前端：

   ```bash
   cd vuehr
   npm install          # 首次需要
   npm run build        # 生成 dist/ 目录
   cd ..
   ```

3. 确认文件结构：

   ```
   vhr-learn/
   ├── docker-compose.yml
   ├── vhr.sql
   ├── vhr-web/
   │   ├── Dockerfile
   │   └── target/vhr-web.jar   ← 后端包
   └── vuehr/
       ├── Dockerfile
       ├── nginx.conf
       └── dist/                ← 前端构建产物
   ```

### 5.2 一键启动

```bash
# 进入 vhr-learn 目录
cd vhr-learn

# 启动全套（首次会自动构建后端和前端镜像，比较慢）
docker-compose up -d
```

### 5.3 查看启动情况

```bash
# 查看容器状态
docker-compose ps

# 查看实时日志（Ctrl + C 退出日志查看，不影响容器运行）
docker-compose logs -f

# 分别查看各容器日志
docker-compose logs -f mysql     # MySQL
docker-compose logs -f vhr-web   # 后端
docker-compose logs -f nginx     # 前端 Nginx
```

**成功标志**：`docker-compose ps` 看到 **三个** 容器 `STATE` 都是 `Up`：

```
NAME         IMAGE                COMMAND                  SERVICE     STATUS     PORTS
vhr-mysql    mysql:5.7            "docker-entrypoint.s…"   mysql       Up         0.0.0.0:3306->3306/tcp
vhr-web      vhr-learn_vhr-web    "java -jar app.jar"      vhr-web     Up         0.0.0.0:8082->8082/tcp
vhr-nginx    vhr-learn_nginx      "/docker-entrypoint.…"   nginx       Up         0.0.0.0:80->80/tcp
```

### 5.4 验证应用

1. **访问前端**：浏览器打开

   ```
   http://localhost/
   ```

   （如果改了端口是 `8080:80`，则访问 `http://localhost:8080/`）

2. **验证后端接口**（可选，如果你在 docker-compose 里暴露了 8082 端口）：

   ```bash
   curl http://localhost:8082/
   ```

3. **前后端联调**：在前端页面登录、查询数据，看是否正常。

### 5.5 停止整套服务

```bash
# 停止并删除容器（保留数据在 mysql-data/）
docker-compose down

# 或者，只停止不删除（下次 start 即可恢复）
docker-compose stop

# 启动已停止的容器（不会重新构建镜像）
docker-compose start
```

### 5.6 修改代码后重新部署

**后端改了代码**：

```bash
cd vhr-web
mvn clean package -DskipTests
cd ..
docker-compose up -d --build vhr-web   # 只重建后端容器，不动 MySQL 和 Nginx
```

**前端改了代码**：

```bash
cd vuehr
npm run build                           # 重新构建 dist/
cd ..
docker-compose up -d --build nginx      # 只重建 Nginx 容器
```

---

## 6. 常用命令速查

| 操作 | 命令 |
|------|------|
| **启动全套** | `docker-compose up -d` |
| **启动全套（强制重新构建所有镜像）** | `docker-compose up -d --build` |
| **停止全套（删除容器，保留数据）** | `docker-compose down` |
| **只停止不删容器** | `docker-compose stop` |
| **启动已停止的容器** | `docker-compose start` |
| **查看容器状态** | `docker-compose ps` |
| **查看所有日志** | `docker-compose logs -f` |
| **只看后端日志** | `docker-compose logs -f vhr-web` |
| **只看前端 Nginx 日志** | `docker-compose logs -f nginx` |
| **只看 MySQL 日志** | `docker-compose logs -f mysql` |
| **重新构建并重启后端** | `docker-compose up -d --build vhr-web` |
| **重新构建并重启前端** | `docker-compose up -d --build nginx` |
| **进入后端容器** | `docker exec -it vhr-web bash` |
| **进入前端 Nginx 容器** | `docker exec -it vhr-nginx sh` |
| **进入 MySQL 命令行** | `docker exec -it vhr-mysql mysql -uroot -p123` |
| **彻底清空（含镜像和数据）** | `docker-compose down -v --rmi local`（慎用！） |

---

## 7. 常见问题排查

### ❌ 问题 1：后端应用容器启动后立即退出

**诊断**：`docker-compose ps` 看到 `vhr-web` 的 `STATE` 是 `Exit`。

**看日志找原因**：

```bash
docker-compose logs vhr-web
```

**常见原因**：

| 日志关键词 | 原因 | 解决 |
|-----------|------|------|
| `Error: Unable to access jarfile app.jar` | jar 文件名不对，或没打包 | 确认 `target/` 下有 jar 文件，且 `Dockerfile` 里的 `COPY` 路径正确 |
| `Communications link failure` | 连不上 MySQL | 检查 `SPRING_DATASOURCE_URL` 是否写的是 `mysql:3306`（不是 `127.0.0.1`） |
| `Access denied for user 'root'@'...'` | 密码不对 | 确认 `SPRING_DATASOURCE_PASSWORD` 和 MySQL 的 `MYSQL_ROOT_PASSWORD` 都是 `123` |
| `Unknown database 'vhr'` | 数据库没创建 | 删除 `mysql-data/` 目录，重新 `docker-compose up -d`，让 MySQL 重新初始化 |

---

### ❌ 问题 2：连不上 MySQL（`Communications link failure`）

**关键点**：在 docker-compose 里，Spring Boot 应用访问 MySQL 的地址 **不是 `127.0.0.1`**，而是服务名 `mysql`。

**正确配置**（在 docker-compose.yml 的 `vhr-web` 服务里）：

```yaml
environment:
  SPRING_DATASOURCE_URL: jdbc:mysql://mysql:3306/vhr?useUnicode=true&characterEncoding=UTF-8&useSSL=false&serverTimezone=Asia/Shanghai
```

**诊断步骤**：

1. 确认 MySQL 容器在跑：`docker-compose ps` → `mysql` 是 `Up` 状态
2. 确认 MySQL 有 `vhr` 数据库：
   ```bash
   docker exec -it vhr-mysql mysql -uroot -p123 -e "SHOW DATABASES;"
   ```
3. 确认应用容器的环境变量注入正确：
   ```bash
   docker exec vhr-web env | grep SPRING_DATASOURCE
   ```
   应该能看到 `SPRING_DATASOURCE_URL=jdbc:mysql://mysql:3306/vhr?...`

---

### ❌ 问题 3：后端镜像构建失败（找不到 jar）

**报错**：`COPY failed: file not found: target/vhr-web.jar`

**解决**：

1. 先在本地打包：
   ```bash
   cd vhr-web
   mvn clean package -DskipTests
   ls target/*.jar   # 确认有 jar 文件
   ```

2. 确认 jar 文件名和 Dockerfile 里写的一致。如果不知道文件名，看 `mvn package` 的输出。

3. `docker-compose.yml` 里的 `context: ./vhr-web` 路径要对。

---

### ❌ 问题 4：前端 Nginx 镜像构建失败（找不到 dist）

**报错**：`COPY failed: file not found: dist`

**解决**：

```bash
cd vuehr
npm install
npm run build          # 必须执行，生成 dist/ 目录
ls dist/index.html     # 确认有 index.html
```

然后再执行 `docker-compose up -d --build nginx`。

---

### ❌ 问题 5：浏览器访问 `http://localhost/` 看到 404 或空白页

**诊断步骤**：

1. **确认 Nginx 容器在跑**：`docker-compose ps` → `nginx` 是 `Up`
2. **看 Nginx 日志**：`docker-compose logs nginx`
3. **确认前端构建产物复制成功了**：进入 Nginx 容器看一眼
   ```bash
   docker exec vhr-nginx ls /usr/share/nginx/html/
   ```
   应该能看到 `index.html`。如果没有，就是 `npm run build` 没成功。
4. **确认端口映射**：`docker-compose.yml` 里是 `80:80` 吗？如果是 `8080:80`，就访问 `http://localhost:8080/`。

---

### ❌ 问题 6：前端页面能看到，但调后端接口报错（404 / 502）

**症状**：前端页面正常显示，但登录、查询等操作失败。浏览器 DevTools 看到请求返回 404 或 502。

**原因**：Nginx 把前端请求转发给后端时，路径不匹配，或后端还没启动好。

**诊断**：

1. 先确认后端自己正常：
   ```bash
   # 如果后端端口暴露了（8082:8082），直接调后端
   curl http://localhost:8082/
   ```
   有响应说明后端 OK，问题在 Nginx 转发配置。

2. 确认 Nginx 里 `proxy_pass` 写对了：
   ```
   proxy_pass http://vhr-web:8082/;
   ```
   这里的 `vhr-web` 是 docker-compose.yml 里后端服务的 **service 名**，必须一致。

3. 看前端代码里接口 URL 怎么写的：
   - 如果前端写的是 `/api/login`、`/api/hr` → Nginx 要用 `location /api/` 方式
   - 如果前端写的是 `/login`、`/hr` → Nginx 要用"非静态文件走后端"方式

4. **最简单的检查方式**：进入 Nginx 容器，看它能不能访问到后端：
   ```bash
   docker exec vhr-nginx wget -qO- http://vhr-web:8082/
   ```
   有输出说明网络通，问题在 `location` 匹配规则；没输出说明网络/后端有问题。

---

### ❌ 问题 7：前端请求跨域（CORS error）

**症状**：浏览器 Console 报 `CORS policy` 相关错误。

**在容器部署模式下**（Nginx 代理后端）：前端和后端同源（都是 `http://localhost/`），正常不会有跨域问题。如果出现了，多半是前端代码里 `baseURL` 写死了 `http://localhost:8082` 之类的地址，改成相对路径即可。

---

### ❌ 问题 8：端口被占用（80 / 3306 / 8082）

**报错**：`Bind for 0.0.0.0:80 failed: port is already allocated`

**解决**：改 `docker-compose.yml` 的端口映射，例如：

```yaml
services:
  mysql:
    ports:
      - "3307:3306"   # 对外改成 3307
  vhr-web:
    ports:
      - "8083:8082"   # 对外改成 8083
  nginx:
    ports:
      - "8080:80"     # 对外改成 8080
```

然后访问 `http://localhost:8080/`。

---

### ❌ 问题 9：首次启动 MySQL 初始化太慢，后端启动报错

**解决**：本手册配置了健康检查 + `depends_on: service_healthy`，正常情况下不会有这个问题。如果仍然报错：

```bash
# 手动分步启动
docker-compose up -d mysql
# 等 30 秒
docker-compose up -d vhr-web
docker-compose up -d nginx
```

---

### ❌ 问题 10：彻底清理重来

容器状态混乱，想从零开始（⚠️ 会删掉数据）：

```bash
# 停止并删除所有容器、网络
docker-compose down

# 删构建好的镜像
docker rmi vhr-learn_vhr-web vhr-learn_nginx

# 删 MySQL 数据目录（⚠️ 所有表和数据都会丢掉！）
rm -rf mysql-data   # macOS / Linux
# 或 Windows: Remove-Item -Recurse mysql-data

# 重新开始
docker-compose up -d
```

---

## 8. 完成检查清单

- [ ] Spring Boot 项目在本地 `mvn clean package -DskipTests` 打包成功
- [ ] Vue 前端 `npm run build` 成功，`vuehr/dist/index.html` 存在
- [ ] `vhr-web/` 目录下有 `Dockerfile`
- [ ] `vuehr/` 目录下有 `Dockerfile` 和 `nginx.conf`
- [ ] `vhr-learn/` 根目录下有 `docker-compose.yml`
- [ ] `docker-compose up -d` 执行无报错
- [ ] `docker-compose ps` 三个容器 `STATE` 都是 `Up`
- [ ] 浏览器访问 `http://localhost/`（或自定义端口）能看到前端页面
- [ ] 前端页面操作（登录、查询等）能正常请求到后端
- [ ] 查看后端日志无 `Exception`、`ERROR`

**全部打勾，部署环境就跑通了！**

---

**文档版本**：v2.0
**适用项目**：vhr（Spring Boot 2.4.0 + MyBatis + Spring Security + Vue 2.6.10 + Nginx）
**最后更新**：2026-06

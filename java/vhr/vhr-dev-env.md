# vhr 学习项目 · 开发环境搭建手册

> 适用场景：在本地 IDEA 中写代码、打断点、调试学习。
>
> 架构：Docker 跑 MySQL，本地跑 Spring Boot 后端 + Vue 前端。

---

## 目录

1. [目标架构](#0-目标架构)
2. [创建项目目录](#1-创建项目目录)
3. [准备数据库脚本](#2-准备数据库脚本)
4. [Docker 启动 MySQL](#3-docker-启动-mysql)
5. [导入数据库脚本](#4-导入数据库脚本)
6. [本地 JDK + Maven 安装](#5-本地-jdk--maven-安装)
7. [本地 Node.js 安装 + Vue 前端启动](#6-本地-nodejs-安装--vue-前端启动)
8. [后端启动 + 前后端联调](#7-后端启动--前后端联调)
9. [常用命令速查](#8-常用命令速查)
10. [常见问题排查](#9-常见问题排查)
11. [完成检查清单](#10-完成检查清单)

---

## 0. 目标架构

```
        你电脑本地                              Docker 容器
┌──────────────────────────────┐          ┌─────────────────┐
│                              │          │                 │
│   Vue 前端 (端口 8080)        │  HTTP    │                 │
│   ┌──────────────────────┐   │──────────▶   MySQL 5.7     │
│   │  浏览器访问 8080      │   │  3306    │   (库名 vhr)    │
│   │                      │   │  JDBC    │                 │
│   │  调用后端接口 8082    │   │          │                 │
│   └──────────┬───────────┘   │          │                 │
│              │               │          │                 │
│              ▼               │          │                 │
│   Spring Boot 后端 (8082)    │──────────▶                 │
│                              │          │                 │
└──────────────────────────────┘          └─────────────────┘
```

| 组件 | 版本 | 运行位置 | 端口 |
|------|------|---------|------|
| JDK | 8 或 11 | 本地 | — |
| Maven | 3.6+ | 本地 | — |
| Node.js | 14.x 或 16.x | 本地 | — |
| MySQL | 5.7 | Docker | 3306 |
| Spring Boot 应用 | 随项目 | 本地 IDEA | 8082 |
| Vue 前端 | 2.6.10 | 本地 Node | 8080 |
| IDEA / VS Code | 任意 | 本地 | — |

---

## 1. 创建项目目录

**在哪执行都一样**，选你习惯的位置：

```bash
# macOS / Linux
cd ~/Documents/learn
mkdir vhr-learn
cd vhr-learn

# Windows PowerShell
cd C:\learn
mkdir vhr-learn
cd vhr-learn

# Windows CMD
cd C:\learn
md vhr-learn
cd vhr-learn
```

最终结构（目标）：

```
vhr-learn/
├── vhr-dev-env.md           ← 本文件
├── vhr.sql                  ← 数据库脚本
└── ... （后续放 Spring Boot 项目代码）
```

---

## 2. 准备数据库脚本

从原项目复制 SQL 脚本到你的工作目录：

```bash
# macOS / Linux
cp /path/to/vhr-master/resources/vhr.sql ./vhr.sql

# Windows PowerShell
Copy-Item "C:\path\to\vhr-master\resources\vhr.sql" ".\vhr.sql"

# Windows CMD
copy "C:\path\to\vhr-master\resources\vhr.sql" ".\vhr.sql"
```

> **没有原项目文件？** 先跳过此步，MySQL 容器启动后，再手动把建表语句执行进去也可以。

---

## 3. Docker 启动 MySQL

> **前置条件**：已安装并启动 Docker Desktop（macOS/Windows）或 Docker 服务（Linux）。
>
> 确认方法：`docker --version` 能输出版本号。

打开终端，**整段复制执行**：

**macOS / Linux（bash / zsh）：**

```bash
docker run -d \
  --name vhr-mysql \
  -e MYSQL_ROOT_PASSWORD=123 \
  -e MYSQL_DATABASE=vhr \
  -p 3306:3306 \
  mysql:5.7 \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_unicode_ci
```

**Windows PowerShell：**

```powershell
docker run -d `
  --name vhr-mysql `
  -e MYSQL_ROOT_PASSWORD=123 `
  -e MYSQL_DATABASE=vhr `
  -p 3306:3306 `
  mysql:5.7 `
  --character-set-server=utf8mb4 `
  --collation-server=utf8mb4_unicode_ci
```

**Windows CMD：**

```cmd
docker run -d ^
  --name vhr-mysql ^
  -e MYSQL_ROOT_PASSWORD=123 ^
  -e MYSQL_DATABASE=vhr ^
  -p 3306:3306 ^
  mysql:5.7 ^
  --character-set-server=utf8mb4 ^
  --collation-server=utf8mb4_unicode_ci
```

**参数解释**（了解即可，不用改）：

| 参数 | 含义 |
|------|------|
| `-d` | 后台运行（detach） |
| `--name vhr-mysql` | 给容器起名，方便管理 |
| `-e MYSQL_ROOT_PASSWORD=123` | 设置 root 密码为 `123` |
| `-e MYSQL_DATABASE=vhr` | 启动时自动创建 `vhr` 数据库 |
| `-p 3306:3306` | 把容器内 3306 映射到本机 3306 |
| `mysql:5.7` | 使用 MySQL 5.7 镜像（**推荐**，8.0 有额外认证配置） |
| `--character-set-server=utf8mb4` | 设置默认字符集为 utf8mb4 |
| `--collation-server=utf8mb4_unicode_ci` | 设置默认排序规则 |

**验证启动成功**：

等 15~30 秒（MySQL 首次启动需要初始化），然后执行：

```bash
# macOS / Linux
docker ps | grep vhr

# Windows PowerShell
docker ps | Select-String vhr

# Windows CMD
docker ps | findstr vhr
```

看到 `STATUS` 是 `Up xx seconds` 就是成功了，例如：

```
CONTAINER ID  IMAGE      COMMAND       STATUS         NAMES
a1b2c3d4e5f6  mysql:5.7  "docker-..."  Up 20 seconds  vhr-mysql
```

**验证数据库连接**：

```bash
docker exec -it vhr-mysql mysql -uroot -p123 -e "SHOW DATABASES;"
```

预期输出（看到 `vhr` 就是 OK）：

```
+--------------------+
| Database           |
+--------------------+
| information_schema |
| mysql              |
| performance_schema |
| sys                |
| vhr                |
+--------------------+
```

---

## 4. 导入数据库脚本

**在 `vhr-learn` 目录下执行**（本目录要有 `vhr.sql` 文件）：

**macOS / Linux：**

```bash
docker exec -i vhr-mysql mysql -uroot -p123 vhr < vhr.sql
```

**Windows PowerShell：**

```powershell
Get-Content vhr.sql | docker exec -i vhr-mysql mysql -uroot -p123 vhr
```

**Windows CMD：**

```cmd
docker exec -i vhr-mysql mysql -uroot -p123 vhr < vhr.sql
```

**验证表是否导入成功**：

```bash
docker exec -it vhr-mysql mysql -uroot -p123 -e "USE vhr; SHOW TABLES;"
```

能看到 `hr`、`role`、`menu`、`hr_role`、`menu_role` 等表就成功了。

---

## 5. 本地 JDK + Maven 安装

### 5.1 安装 JDK 11（推荐）

| 系统 | 安装方式 |
|------|---------|
| **macOS**（有 Homebrew） | `brew install openjdk@11` |
| **macOS**（无 Homebrew） | 去 [Oracle 官网](https://www.oracle.com/java/technologies/downloads/#java11) 下载 `.dmg` 安装 |
| **Windows** | [官网下载 JDK 11](https://www.oracle.com/java/technologies/downloads/#java11)，安装时勾选 "Set PATH" |
| **Linux（Ubuntu/Debian）** | `sudo apt update && sudo apt install openjdk-11-jdk` |
| **Linux（CentOS/RHEL）** | `sudo dnf install java-11-openjdk` |

**安装后验证**（所有系统命令一样）：

```bash
java -version
```

预期输出：

```
openjdk version "11.0.x" 202x-xx-xx
OpenJDK Runtime Environment ...
OpenJDK 64-Bit Server VM ...
```

> **关于 JDK 8**：Spring Boot 2.4.0 也支持 JDK 8，有就用，没有就装 11。两个版本都可以。

### 5.2 安装 Maven

| 系统 | 安装方式 |
|------|---------|
| **macOS**（有 Homebrew） | `brew install maven` |
| **Windows** | 去 [Maven 官网](https://maven.apache.org/download.cgi) 下载 `apache-maven-x.x.x-bin.zip`，解压后把 `bin` 目录加到系统 `PATH` |
| **Linux（Ubuntu/Debian）** | `sudo apt install maven` |
| **Linux（CentOS/RHEL）** | `sudo dnf install maven` |

**安装后验证**：

```bash
mvn -version
```

预期输出（前两行）：

```
Apache Maven 3.x.x ...
Java version: 11.0.x, vendor: ...
```

> 确保 `Java version` 那一行显示的是你刚装的 JDK 版本。

---

## 6. 本地 Node.js 安装 + Vue 前端启动

### 6.1 为什么要指定 Node.js 版本

这个项目的前端用的是 **Vue 2.6.10 + node-sass 4.13.0**，对 Node.js 版本有严格要求：

| Node.js 版本 | 能否用 | 说明 |
|-------------|--------|------|
| 14.x / 16.x | ✅ 推荐 | `node-sass` 编译正常 |
| 18.x | ⚠️ 可能有问题 | `node-sass` 预编译二进制可能缺失，需要换 `sass` |
| 20.x / 24.x | ❌ 不行 | 原生不兼容老版 `node-sass` |

**推荐用 Node.js 16.x**。

### 6.2 安装 Node.js

| 系统 | 安装方式 |
|------|---------|
| **macOS**（有 Homebrew） | `brew install node@16` |
| **macOS / Windows**（无 Homebrew） | 去 [Node.js 官网下载页](https://nodejs.org/download/release/v16.20.2/) 下载 `v16.20.2` 的安装包：<br>- macOS: `node-v16.20.2.pkg`<br>- Windows: `node-v16.20.2-x64.msi` |
| **Linux（Ubuntu/Debian）** | `curl -fsSL https://deb.nodesource.com/setup_16.x \| sudo -E bash - && sudo apt install -y nodejs` |

**安装后验证**（所有系统命令一样）：

```bash
node -v
# 预期输出：v16.20.2 或 v14.x.x

npm -v
# 预期输出：x.x.x（版本号不重要，有就行）
```

### 6.3 获取前端代码

把原项目里的前端代码复制到你的工作目录：

```bash
# macOS / Linux
cp -r /path/to/vhr-master/vuehr ./vuehr

# Windows PowerShell
Copy-Item -Recurse "C:\path\to\vhr-master\vuehr" ".\vuehr"

# Windows CMD
xcopy /e /i "C:\path\to\vhr-master\vuehr" ".\vuehr"
```

确认目录结构：

```
vhr-learn/
├── vhr.sql
├── vhr-web/        (后端项目，按 02 号文档创建)
└── vuehr/          (前端项目)
    ├── src/
    ├── package.json
    └── ...
```

### 6.4 安装前端依赖

进入前端项目目录，安装依赖：

```bash
cd vuehr

# 安装全部依赖（首次较慢，需要下载）
npm install
```

> **macOS 用 Homebrew 装的 node@16？** 如果 `node -v` 看到的不是 16.x，需要先让 shell 找到它：
>
> ```bash
> # macOS zsh
> echo 'export PATH="/usr/local/opt/node@16/bin:$PATH"' >> ~/.zshrc
> source ~/.zshrc
> node -v   # 应该是 v16.x
> ```

如果 `npm install` 报 `node-sass` 编译错误，用下面这个方式绕过：

```bash
# 先装镜像里预编译好的版本
npm install --unsafe-perm

# 或者，把 node-sass 换成 dart-sass（不需要编译二进制）
npm uninstall node-sass
npm install -D sass
```

### 6.5 查看前端的 API 地址配置

前端通过 HTTP 调后端接口。打开 `vuehr/src/utils/` 或者 `vuehr/config/` 之类的目录，找到 API 地址配置。

通常前端里写死了类似这样的配置：

```
http://localhost:8082/
```

或者在 `config/index.js` 里有 `proxyTable` 的代理配置。

**目标**：确保前端请求会打到 **后端的 8082 端口**。后面启动后端后验证。

### 6.6 启动前端开发服务器

```bash
# 仍在 vuehr/ 目录下
npm run dev
```

成功后会看到类似输出：

```
 DONE  Compiled successfully in xxxms

 I  Your application is running here: http://localhost:8080
```

浏览器访问 **http://localhost:8080/** 就能看到前端页面。

> 前端默认端口通常是 **8080**，后端是 **8082**，两个端口互不冲突。

---

## 7. 后端启动 + 前后端联调

### 7.1 启动后端

用 IDEA 打开你的 Spring Boot 项目（`vhr-web/`），找到主启动类（带 `@SpringBootApplication` 注解的类），点绿色 ▶ 运行。

或者在命令行启动：

```bash
cd vhr-web
mvn spring-boot:run
```

启动成功后会看到：

```
... Started xxxApplication in x.xxx seconds
```

端口号就是 `application.properties` 里配置的 `server.port=8082`。

### 7.2 验证后端能连上数据库

最简单的方法：去 MySQL 里看一眼有没有新建连接。

```bash
docker exec -it vhr-mysql mysql -uroot -p123 -e "SHOW PROCESSLIST;"
```

能看到 `Sleep` 状态的连接就是连上了。

### 7.3 前后端联调验证

1. 后端正在跑（端口 8082）
2. 前端正在跑（端口 8080）
3. 浏览器打开 `http://localhost:8080/`
4. 看到登录页面 → 用数据库里已有的账号登录（或按 03+ 号文档创建账号）

### 7.4 每日开发流程

```bash
# 第一步：启动 MySQL
docker start vhr-mysql

# 第二步：启动后端（IDEA 里点 ▶ 或命令行 mvn spring-boot:run）

# 第三步：启动前端
cd vuehr
npm run dev

# 浏览器打开 http://localhost:8080/
```

---

## 8. 常用命令速查

### 8.1 MySQL

| 操作 | 命令 |
|------|------|
| **启动 MySQL** | `docker start vhr-mysql` |
| **停止 MySQL** | `docker stop vhr-mysql` |
| **查看状态** | `docker ps \| grep vhr`（macOS/Linux）<br>`docker ps \| findstr vhr`（Windows） |
| **重启** | `docker restart vhr-mysql` |
| **进入 MySQL 命令行** | `docker exec -it vhr-mysql mysql -uroot -p123` |
| **删除容器（不删数据）** | `docker rm -f vhr-mysql` |
| **查看日志** | `docker logs vhr-mysql` |
| **实时看日志** | `docker logs -f vhr-mysql` |

### 8.2 后端（Spring Boot）

| 操作 | 命令 |
|------|------|
| **启动后端** | IDEA 里点 ▶，或 `cd vhr-web && mvn spring-boot:run` |
| **打包 jar** | `cd vhr-web && mvn clean package -DskipTests` |
| **查看端口占用** | `lsof -i:8082`（macOS/Linux）<br>`netstat -ano \| findstr 8082`（Windows） |

### 8.3 前端（Vue）

| 操作 | 命令 |
|------|------|
| **安装依赖** | `cd vuehr && npm install` |
| **启动前端开发服务器** | `cd vuehr && npm run dev` |
| **重新安装依赖** | `cd vuehr && rm -rf node_modules && npm install`（macOS/Linux）<br>`cd vuehr && Remove-Item -Recurse node_modules && npm install`（PowerShell） |
| **停止前端** | 终端里按 Ctrl + C |
| **查看 Node 版本** | `node -v` |

---

## 9. 常见问题排查

### ❌ 问题 1：3306 端口被占用

**报错**：
```
Error starting userland proxy: Bind for 0.0.0.0:3306 failed: port is already allocated.
```

**原因**：你本地已经装了 MySQL，或者其他程序占了 3306 端口。

**解决**：换一个端口，比如 `3307`：

```bash
docker run -d \
  --name vhr-mysql \
  -e MYSQL_ROOT_PASSWORD=123 \
  -e MYSQL_DATABASE=vhr \
  -p 3307:3306 \
  mysql:5.7 \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_unicode_ci
```

⚠️ **同时**，你的 `application.properties` 中的端口也要改成 `3307`：

```properties
spring.datasource.url=jdbc:mysql://127.0.0.1:3307/vhr?useUnicode=true&characterEncoding=UTF-8
```

---

### ❌ 问题 2：MySQL 容器启动后马上退出

执行 `docker ps` 看不到 `vhr-mysql`，或者 `STATUS` 显示 `Exited`。

**诊断**：看日志找原因

```bash
docker logs vhr-mysql
```

**常见原因 & 解决**：

| 日志关键词 | 原因 | 解决 |
|-----------|------|------|
| `port is already allocated` | 端口被占 | 参考问题 1，换端口 |
| `Initializing database` 卡住很久 | 首次启动初始化慢 | 等 30~60 秒，或删除容器重新创建 |
| `Permission denied` | 数据目录权限问题（Windows WSL2 常见） | 把 `volumes` 路径换一个位置，或去掉 volumes 先用着 |

**万能修复**：删了重来（不会影响本地其他容器）

```bash
docker rm -f vhr-mysql
# 然后重新执行 docker run ...
```

---

### ❌ 问题 3：导入 SQL 失败（编码 / 乱码问题）

**症状**：导入后表的数据是乱码，或导入时报错。

**解决**：先进入容器手动重建数据库并设置编码：

```bash
docker exec -it vhr-mysql mysql -uroot -p123
```

在 MySQL 命令行里执行：

```sql
DROP DATABASE IF EXISTS vhr;
CREATE DATABASE vhr DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

然后重新导入脚本。

---

### ❌ 问题 4：Docker 没启动

**报错**：
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?
```

**解决**：

| 系统 | 操作 |
|------|------|
| **macOS** | 启动 **Docker Desktop** 应用（在 Launchpad 里找） |
| **Windows** | 启动 **Docker Desktop** 应用（开始菜单里找） |
| **Linux** | `sudo systemctl start docker` |

---

### ❌ 问题 5：MySQL 8.0 密码认证问题

> **强烈建议直接用 MySQL 5.7**，省去麻烦。这个项目的依赖就是为 5.7 写的。

如果你非要用 MySQL 8.0，创建容器时要加认证插件参数：

```bash
docker run -d \
  --name vhr-mysql \
  -e MYSQL_ROOT_PASSWORD=123 \
  -e MYSQL_DATABASE=vhr \
  -p 3306:3306 \
  mysql:8.0 \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_unicode_ci \
  --default-authentication-plugin=mysql_native_password
```

同时 `application.properties` 的 JDBC URL 要加上时区参数：

```properties
spring.datasource.url=jdbc:mysql://127.0.0.1:3306/vhr?useUnicode=true&characterEncoding=UTF-8&useSSL=false&serverTimezone=Asia/Shanghai
```

---

### ❌ 问题 6：Spring Boot 应用连不上 MySQL

**报错关键字**：`Communications link failure`、`Connection refused`、`Access denied`

**诊断步骤**：

1. **确认 MySQL 容器在跑**：`docker ps | grep vhr` → 能看到 `vhr-mysql`
2. **手动验证能连**：`docker exec -it vhr-mysql mysql -uroot -p123 -e "SELECT 1;"` → 不报错
3. **检查 `application.properties` 配置**：

   ```properties
   spring.datasource.url=jdbc:mysql://127.0.0.1:3306/vhr?useUnicode=true&characterEncoding=UTF-8
   spring.datasource.username=root
   spring.datasource.password=123
   ```

4. **端口确认**：如果启动 MySQL 时用了 `3307:3306`，本地应用连接要写 `3307`

---

### ❌ 问题 7：Node.js 版本不对

**症状**：`npm install` 时报 `node-sass` 相关错误，或者 `npm run dev` 编译失败。

**原因**：Vue 2 老项目依赖 `node-sass@4.13.0`，需要 Node.js 14 或 16，**Node 18+ 不兼容**。

**验证**：
```bash
node -v
# 必须是 v14.x 或 v16.x
```

**解决**：装 Node.js 16。

| 系统 | 操作 |
|------|------|
| **macOS（Homebrew）** | `brew install node@16` |
| **Windows** | [官网下载 Node 16](https://nodejs.org/download/release/v16.20.2/) |
| **Linux** | `curl -fsSL https://deb.nodesource.com/setup_16.x \| sudo -E bash - && sudo apt install nodejs` |

---

### ❌ 问题 8：`npm install` 失败 / `node-sass` 报错

**报错示例**：
```
node-sass@4.13.0 postinstall: `node scripts/build.js`
```
或者
```
Cannot find module 'node-sass'
```

**方案 A（推荐，最简单）**：换成 `sass`（纯 JavaScript 实现，不需要编译）

```bash
cd vuehr
npm uninstall node-sass
npm install -D sass
npm run dev
```

**方案 B（顽固版本）**：清空 node_modules 重新安装：

```bash
cd vuehr
rm -rf node_modules package-lock.json     # macOS / Linux
# 或 PowerShell: Remove-Item -Recurse node_modules, package-lock.json

# 换国内镜像加速（可选）
npm config set registry https://registry.npmmirror.com

npm install
```

---

### ❌ 问题 9：前端启动后页面空白 / 404

**症状**：浏览器打开 `http://localhost:8080/` 看到空白页或 404。

**排查**：

1. **确认前端真的跑起来了**：看终端输出，应该有 `Your application is running here: http://localhost:8080`
2. **确认端口没被占**：关掉 8080 上的其他程序
3. **清缓存重启**：
   ```bash
   # Ctrl+C 停掉前端
   cd vuehr
   rm -rf node_modules/.cache   # macOS / Linux
   npm run dev
   ```

---

### ❌ 问题 10：前端请求后端接口报错（跨域 / 404）

**症状**：前端页面能显示，但是登录/请求数据时报错，浏览器 DevTools 里看到红色的请求。

**原因**：前端调后端接口时，后端地址或端口对不上。

**诊断步骤**：

1. **确认后端在跑**：浏览器访问 `http://localhost:8082/` 有响应
2. **看前端代码里的接口地址**：搜索 vuehr 目录下的 `localhost`、`8082`、`baseURL` 等关键词
3. **前端常见的配置方式**：

   **方式 A**：`src/utils/` 下的某个 js 文件里写死了：
   ```js
   const baseURL = 'http://localhost:8082/'
   ```

   **方式 B**：通过 `config/index.js` 里的 `proxyTable` 做了代理：
   ```js
   proxyTable: {
     '/': {
       target: 'http://localhost:8082',
       changeOrigin: true
     }
   }
   ```

4. **如果后端端口不是 8082**，把前端配置里的 `8082` 改成实际端口

**简单测试方法**：启动后端后，用 curl 直接调接口看能不能通：
```bash
curl http://localhost:8082/
# 或
curl http://localhost:8082/login
```

---

### ❌ 问题 11：前端 8080 端口被占

**报错**：`Port 8080 is already in use`

**解决**：

1. 找到占用 8080 的程序并关掉：
   ```bash
   # macOS / Linux
   lsof -i:8080
   kill <PID>

   # Windows
   netstat -ano | findstr 8080
   # 然后去任务管理器结束对应进程
   ```

2. 或者，改前端配置里的端口（如 `config/index.js` 里的 `port: 8080`）

---

## 10. 完成检查清单

### 10.1 环境检查

- [ ] `docker ps` 能看到 `vhr-mysql` 且 `STATUS` 是 `Up ...`
- [ ] `docker exec -it vhr-mysql mysql -uroot -p123 -e "USE vhr; SHOW TABLES;"` 能看到多张表
- [ ] `java -version` 输出 `1.8.x` 或 `11.0.x`
- [ ] `mvn -version` 能正常输出版本，且 Java 版本和上一步一致
- [ ] `node -v` 输出 `v14.x` 或 `v16.x`

### 10.2 应用启动检查

- [ ] Spring Boot 项目能在 IDEA 里启动，日志看到 `Started ...`
- [ ] 后端启动后 `curl http://localhost:8082/` 不报错
- [ ] 前端 `npm run dev` 启动成功，浏览器访问 `http://localhost:8080/` 能看到页面

### 10.3 联调检查

- [ ] 前端页面上的请求能打到后端（浏览器 DevTools 看网络请求）
- [ ] 后端能正常连 MySQL 取数据

**全部打勾之后，就可以开始按章节学习和写代码了！**

---

**文档版本**：v1.1
**适用项目**：vhr（Spring Boot 2.4.0 + MyBatis + Spring Security + Vue 2.6.10）
**最后更新**：2026-06

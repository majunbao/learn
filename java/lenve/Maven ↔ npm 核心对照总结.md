# Maven ↔ npm 核心对照总结

> 一份完全对等、直接抄到命令行就能用的对照表。
> 适用场景：你熟悉 npm，正在学 Maven；或反过来。

---

## 一、核心角色对照（一句话理解）

| 维度 | Maven（Java 生态） | npm（Node.js 生态） | 对应关系 |
| :--- | :--- | :--- | :--- |
| **是什么** | Java 项目的依赖管理和构建工具 | Node.js 项目的依赖管理和构建工具 | ✅ 完全对等 |
| **配置文件** | `pom.xml` | `package.json` | ✅ 1:1 对应 |
| **依赖来源** | Maven 中央仓库（Maven Central） | npm 公共仓库（npmjs.com） | ✅ 完全对等 |
| **本地仓库/缓存** | `~/.m2/repository/` | `~/.npm/`（缓存） + `node_modules/`（项目级） | 功能对等，位置不同 |
| **常用别名** | 无（统一叫 `mvn`） | `npm` / `cnpm` / `pnpm` / `yarn` | 都是包管理器，语法略有差异 |

---

## 二、配置文件对照（`pom.xml` ↔ `package.json`）

### 2.1 项目基本信息

| Maven (`pom.xml`) | npm (`package.json`) | 说明 |
| :--- | :--- | :--- |
| `<groupId>` | — | Java 项目的组织/包名标识，npm 没有对应概念 |
| `<artifactId>` | `"name"` | 项目/包名 |
| `<version>` | `"version"` | 版本号，都是 `主版本.次版本.修订号` |
| `<packaging>jar</packaging>` | — | **打包类型**（jar / war / pom），npm 没有此概念，默认省略即可 |
| `<mainClass>org.example.Main</mainClass>` | `"main": "index.js"` | **程序入口**：告诉运行时从哪个类/文件开始执行 |

**示例对比：**

```xml
<!-- pom.xml -->
<groupId>com.example</groupId>
<artifactId>vhr</artifactId>
<version>1.0.0</version>
<packaging>jar</packaging>
```

```xml
<!-- 入口主类写在打包插件里（完整 pom.xml 的一部分） -->
<build>
  <plugins>
    <plugin>
      <artifactId>maven-jar-plugin</artifactId>
      <configuration>
        <archive>
          <manifest>
            <mainClass>org.example.Main</mainClass>
          </manifest>
        </archive>
      </configuration>
    </plugin>
  </plugins>
</build>
```

```json
// package.json
{
  "name": "vuehr",
  "version": "1.0.0",
  "main": "index.js"
}
```

### 2.2 依赖声明

| Maven (`pom.xml`) | npm (`package.json`) | 说明 |
| :--- | :--- | :--- |
| `<dependencies>` | `"dependencies"` | 运行时需要的依赖 |
| `<dependency>` | 包名 + 版本号 | 单个依赖 |
| `<scope>test</scope>` | `"devDependencies"` | 仅开发/测试用的依赖 |
| `<version>` | `"^1.2.3"` / `"~1.2.3"` | 版本号（Maven 不支持 `^`/`~`，写死具体版本） |

**示例对比：**

```xml
<!-- pom.xml -->
<dependencies>
  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
    <version>2.4.0</version>
  </dependency>
  <dependency>
    <groupId>junit</groupId>
    <artifactId>junit</artifactId>
    <version>4.13</version>
    <scope>test</scope>              <!-- 仅测试用 -->
  </dependency>
</dependencies>
```

```json
// package.json
{
  "dependencies": {
    "vue": "^2.6.10"
  },
  "devDependencies": {                // 仅开发用
    "eslint": "^7.0.0"
  }
}
```

### 2.3 变量定义（`<properties>`）

| Maven (`pom.xml`) | npm (`package.json`) | 说明 |
| :--- | :--- | :--- |
| `<properties>` | — | **自定义变量**：集中定义版本号、路径等常量，在其他地方用 `${变量名}` 引用 |
| `<spring.version>5.3.0</spring.version>` | `"version"` / `"config"` | 定义一个具体变量；npm 没有专门的变量区，但可以用 `"config"` 或直接写在版本字段里 |
| `${spring.version}` | `$npm_package_version` | 引用变量（Maven 用 `${xxx}`，npm 用 `$npm_package_xxx`） |

**示例对比：**

```xml
<!-- pom.xml 里用 <properties> 集中管理版本号 -->
<properties>
  <spring.version>2.4.0</spring.version>
  <java.version>11</java.version>
  <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
</properties>

<!-- 下面用 ${变量名} 引用 -->
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-web</artifactId>
  <version>${spring.version}</version>        <!-- 引用上面的变量 -->
</dependency>
```

```json
// package.json 没有专门的变量区，版本号写死在各依赖里
// npm 脚本里可以用 $npm_package_xxx 引用 package.json 的字段
{
  "name": "vuehr",
  "version": "1.0.0",
  "config": {                          // 可选：用 config 存自定义变量
    "port": 8080
  }
}

// 在 npm script 里使用：npm run start → 会用 $npm_package_config_port
// "scripts": { "start": "node server.js --port $npm_package_config_port" }
```

### 2.4 构建配置（`<build>`）

| Maven (`pom.xml`) | npm (`package.json`) | 说明 |
| :--- | :--- | :--- |
| `<build>` | `"scripts"` + 构建工具配置 | 构建规则的根节点：Maven 所有打包/编译配置都写在这里 |
| `<finalName>xxx</finalName>` | — | 指定打包后的文件名（jar/war 名称），npm 中由构建工具（vite/webpack）控制 |
| `<plugins>` | `"scripts"` | 构建用的插件集合，对应 npm 的命令脚本定义 |
| `<plugin>` | 单个 `npm run xxx` 命令 | 一个插件完成一个构建任务（打包、编译、测试等） |

**示例对比：**

```xml
<!-- pom.xml 的 <build> 定义完整的构建规则 -->
<build>
  <finalName>vhr-web</finalName>                    <!-- 打包后叫 vhr-web.jar -->
  <plugins>
    <plugin>
      <groupId>org.apache.maven.plugins</groupId>
      <artifactId>maven-jar-plugin</artifactId>     <!-- 打 jar 包的插件 -->
      <configuration>
        <archive>
          <manifest>
            <mainClass>org.example.Main</mainClass>
          </manifest>
        </archive>
      </configuration>
    </plugin>
    <plugin>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-maven-plugin</artifactId>   <!-- Spring Boot 专属插件 -->
    </plugin>
  </plugins>
</build>
```

```json
// package.json 里用 "scripts" 定义构建命令
// 具体的构建逻辑由 vue-cli / vite / webpack 等工具的配置文件管理
{
  "main": "index.js",
  "scripts": {
    "dev": "vue-cli-service serve",
    "build": "vue-cli-service build",
    "start": "node index.js"
  }
}
// 注：npm 不像 Maven 把所有构建规则集中在一个文件里，
//     它把"命令"写在 scripts，把"怎么构建"写在 vite.config.js / vue.config.js 等文件中。
```

---

## 三、命令对照（直接照搬）

> 最常用的命令，按操作类型分组。

### 3.1 依赖安装

| 操作 | Maven 命令 | npm 命令 |
| :--- | :--- | :--- |
| **安装所有依赖**（首次拉项目必执行） | `mvn dependency:resolve` | `npm install` |
| **安装单个依赖并保存** | 手动在 `pom.xml` 加 `<dependency>` | `npm install <包名> --save` |
| **安装开发依赖并保存** | 手动加 `<dependency><scope>test</scope>` | `npm install <包名> --save-dev` |
| **全局安装工具** | 无对应概念 | `npm install -g <包名>` |
| **卸载依赖** | 从 `pom.xml` 删除 | `npm uninstall <包名>` |
| **查看已安装依赖树** | `mvn dependency:tree` | `npm ls` |

### 3.2 清理 / 构建 / 打包

| 操作 | Maven 命令 | npm 命令 |
| :--- | :--- | :--- |
| **清理旧构建产物** | `mvn clean` | `npm run clean`（手动定义）或手动删 `dist/` |
| **编译** | `mvn compile` | `tsc`（TypeScript 项目）或 Babel |
| **构建/打包**（最常用） | `mvn package` | `npm run build` |
| **清理 + 打包**（推荐一键命令） | `mvn clean package` | `npm run clean && npm run build` |
| **打包并安装到本地仓库**（多项目共享） | `mvn clean install` | `npm link` |

### 3.3 运行项目

| 操作 | Maven 命令 | npm 命令 |
| :--- | :--- | :--- |
| **运行测试** | `mvn test` | `npm test` |
| **启动开发服务**（Spring Boot / Node 应用） | `mvn spring-boot:run` | `npm run dev` 或 `npm start` |
| **执行打包后的产物** | `java -jar target/vhr-web.jar` | `node dist/index.js` |

---

## 四、产物目录对照

| Maven | npm | 说明 |
| :--- | :--- | :--- |
| `target/` | `dist/` | 构建/打包产物目录 |
| `target/xxx.jar` | `dist/index.html` + JS/CSS | 最终可部署的产物 |
| `~/.m2/repository/` | `~/.npm/`（缓存）+ `node_modules/`（本地依赖） | 依赖包存储位置 |

---

## 五、高频操作速查卡片

> 日常开发用得上的命令，按场景整理。

| 场景 | Maven | npm |
| :--- | :--- | :--- |
| **第一次拉项目** | `git clone ...` → `mvn clean package` | `git clone ...` → `npm install` |
| **日常开发启动** | `mvn spring-boot:run` | `npm run dev` |
| **打包部署** | `mvn clean package -DskipTests` | `npm run build` |
| **看依赖冲突** | `mvn dependency:tree` | `npm ls` |
| **跑测试** | `mvn test` | `npm test` |

---

**文档版本**：v2.0
**最后更新**：2026-06

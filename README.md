# LK & GLaDOS 自动签到

基于 [https://github.com/iszhangyt/lk-checkin](https://github.com/iszhangyt/lk-checkin) 开发的 GitHub Actions 自动签到工具，支持轻之国度（LK）和 GLaDOS 每日自动签到。

## 功能特性

- **轻之国度（LK）**
  - 自动完成每日签到任务
  - 支持 security_key 直接配置或账号密码登录
  - 自动完成阅读、收藏、点赞、分享、投币等任务

- **GLaDOS**
  - 自动每日签到获取积分
  - 支持自定义 API 地址
  - Cookie 方式认证，无需登录流程

## 使用方法

### 1. Fork 本仓库

点击右上角 **Fork** 按钮，将仓库复制到你的 GitHub 账号下。

### 2. 配置 Secrets

进入你 Fork 的仓库，点击 **Settings → Secrets and variables → Actions → New repository secret**，添加以下 Secrets：

#### LK 签到配置

| Secret 名称 | 说明 |
|-------------|------|
| `LK_SECURITY_KEY` | LK APP 的 security_key，格式如 `key:uid:timestamp` |
| `LK_USERNAME` | LK 用户名/邮箱（security_key 失效时作为备用登录） |
| `LK_PASSWORD` | LK 密码（security_key 失效时作为备用登录） |

> **获取 security_key 的方法**：通过抓包 LK APP 的登录请求，在请求体或响应中找到 `security_key` 字段。

#### GLaDOS 签到配置

| Secret 名称 | 说明 |
|-------------|------|
| `GLADOS_COOKIE` | GLaDOS 的 Cookie，需包含 `koa:sess` 和 `koa:sess.sig` |
| `GLADOS_BASE_URL` | API 基础地址，默认为 `https://glados.one` |

> **获取 Cookie 的方法**：
> 1. 浏览器登录 GLaDOS 网站
> 2. 按 F12 打开开发者工具 → Network（网络）
> 3. 刷新页面，找到任意请求
> 4. 在请求头中复制 `Cookie` 字段的值

### 3. 手动触发测试

配置完成后，可以手动触发工作流测试：

1. 进入仓库的 **Actions** 页面
2. 选择 **LK 签到** 或 **GLaDOS 签到**
3. 点击 **Run workflow** 按钮

### 4. 查看执行结果

工作流执行完成后，可以在 Actions 页面查看：
- 执行状态（成功/失败）
- 运行日志（点击具体工作流进入查看）

## 执行时间

- **LK 签到**：每天北京时间 08:00（UTC 00:00）
- **GLaDOS 签到**：每天北京时间 08:30（UTC 00:30）

如需修改执行时间，可编辑对应的工作流文件（`.github/workflows/*.yml`）中的 `cron` 表达式。

## 免责声明

本项目仅供学习交流使用，请遵守相关网站的服务条款。使用本项目产生的任何后果由使用者自行承担。

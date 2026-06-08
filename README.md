# LK & GLaDOS & Archive Bot & ESJ 自动签到

基于 [https://github.com/iszhangyt/lk-checkin](https://github.com/iszhangyt/lk-checkin) 开发的 GitHub Actions 自动签到工具，支持轻之国度（LK）、GLaDOS 每日自动签到。


## 功能特性

- **轻之国度（LK）**
  - 自动完成每日签到任务
  - 自动完成阅读、收藏、点赞、分享、投币任务

- **GLaDOS**
  - 自动每日签到获取积分

- **Archive Bot（归档机器人）**
  - 支持 EH-ArBot 和 Archive-at-Home 两种协议
  - 自动每日签到获取 GP
  - 支持多账号配置

- **ESJ论坛水经验**
  - 自动登录 ESJ 论坛
  - 每日自动发表评论水经验


## 使用方法

### 1. Fork 本仓库

点击右上角 **Fork** 按钮，将仓库复制到你的 GitHub 账号下。

### 2. 配置 Secrets

进入你 Fork 的仓库，点击 **Settings → Secrets and variables → Actions → New repository secret**，添加以下 Secrets：

#### LK 签到配置

| Secret 名称 | 说明 |
|-------------|------|
| `LK_USERNAME` | LK 用户名/邮箱 |
| `LK_PASSWORD` | LK 密码 |

#### GLaDOS 签到配置

| Secret 名称 | 说明 |
|-------------|------|
| `GLADOS_COOKIE` | GLaDOS 的 Cookie |
| `GLADOS_BASE_URL` | 默认为 `https://glados.one` |

#### Archive Bot 签到配置

| 类型 Secret | 说明 | API 地址 Secret | 说明 | API Key Secret | 说明 |
|-------------|------|-----------------|------|----------------|------|
| `ARCHIVE_BOT_TYPE` | 默认账号协议类型：`ehArBot` 或 `archiveAtHome`（默认 `ehArBot`） | `ARCHIVE_BOT_API_ADDRESS` | 默认账号 API 服务器地址（可选） | `ARCHIVE_BOT_API_KEY` | 默认账号 API Key |
| `ARCHIVE_BOT_TYPE_1` | 账号1 协议类型 | `ARCHIVE_BOT_API_ADDRESS_1` | 账号1 API 服务器地址 | `ARCHIVE_BOT_API_KEY_1` | 账号1 API Key |
| `ARCHIVE_BOT_TYPE_2` | 账号2 协议类型 | `ARCHIVE_BOT_API_ADDRESS_2` | 账号2 API 服务器地址 | `ARCHIVE_BOT_API_KEY_2` | 账号2 API Key |
| `ARCHIVE_BOT_TYPE_3` | 账号3 协议类型 | `ARCHIVE_BOT_API_ADDRESS_3` | 账号3 API 服务器地址 | `ARCHIVE_BOT_API_KEY_3` | 账号3 API Key |
| `ARCHIVE_BOT_TYPE_4` | 账号4 协议类型 | `ARCHIVE_BOT_API_ADDRESS_4` | 账号4 API 服务器地址 | `ARCHIVE_BOT_API_KEY_4` | 账号4 API Key |
| `ARCHIVE_BOT_TYPE_5` | 账号5 协议类型 | `ARCHIVE_BOT_API_ADDRESS_5` | 账号5 API 服务器地址 | `ARCHIVE_BOT_API_KEY_5` | 账号5 API Key |

> 支持最多 6 个账号，账号 0 使用基础 Secret，账号 1~5 使用带 `_1` ~ `_5` 后缀的 Secret。

#### ESJ 论坛水经验配置

| Secret 名称 | 说明 |
|-------------|------|
| `ESJ_USERNAME` | ESJ 论坛账号邮箱 |
| `ESJ_PASSWORD` | ESJ 论坛密码 |

### 3. 手动触发测试

配置完成后，可以手动触发工作流测试：

1. 进入仓库的 **Actions** 页面
2. 选择 **LK 签到**、**GLaDOS 签到**、**Archive Bot 签到** 或 **ESJ 论坛水经验**
3. 点击 **Run workflow** 按钮

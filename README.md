# 📋 HuChuan - 跨设备剪贴板同步工具

> 基于 WebDAV 的轻量级跨设备剪贴板同步解决方案，支持系统托盘运行，实现多设备间文本内容的实时同步。

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-brightgreen.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ 功能特点

- 🔄 **双向实时同步** - 自动检测本地剪贴板变化并上传，同时监听云端更新并下载
- 🔐 **安全传输** - 支持 HTTP Basic 认证，保护您的数据安全
- 💻 **系统托盘运行** - 后台静默运行，不干扰日常工作
- 📱 **多设备支持** - 通过设备 ID 区分不同设备，避免同步冲突
- 🔔 **推送通知** - 支持 Bark 等推送服务（作为iPhone触发信号）
- ⚡ **高效同步** - 使用 ETag 机制，只在内容变化时下载，节省带宽
- 🎨 **自定义配置** - 灵活的配置文件，可自定义同步间隔、webdav服务器地址等

## 📦 安装

### 环境要求

- Python 3.7+
- 支持 WebDAV 协议的云存储服务（如坚果云、Nextcloud 、infini等）

### 依赖安装

```bash
pip install requests pyperclip pillow pystray
```

## ⚙️ 配置

1. 复制配置文件模板：

```bash
cp config/exchange_data.example.json config/exchange_data.json
```

2. 编辑 `config/exchange_data.json`，填入您的配置：

```json
{
    "base_url": "https://webdav.example.com/dav/",
    "username": "your_username",
    "password": "your_password",
    "config_file": "SyncClipboard.json",
    "check_interval": 0.5,
    "device_id": "PC-001",
    "notification_url": "https://api.day.app/your_key/"
}
```

### 配置项说明

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `base_url` | WebDAV 服务器地址 | `https://dav.jianguoyun.com/dav/` |
| `username` | WebDAV 用户名 | `your_email@example.com` |
| `password` | WebDAV 密码或应用密钥 | `your_app_password` |
| `config_file` | 同步文件名 | `SyncClipboard.json` |
| `check_interval` | 检查间隔（秒） | `0.5` |
| `device_id` | 设备标识符 | `PC-001` |
| `notification_url` | 推送通知 URL（可选） | `https://api.day.app/your_key/` |

## 🚀 使用方法

### 直接运行

```bash
python huchuan.py
```

### 打包为可执行文件

```bash
pyinstaller -F -w -i exchange.ico huchuan.py
```

### 打包后目录结构

打包完成后，请确保文件按以下结构放置：

```
📁 程序目录/
├── 📄 huchuan.exe          # 主程序（打包生成）
├── 🖼️ exchange.ico         # 托盘图标文件
└── 📁 config/              # 配置文件夹
    └── 📄 exchange_data.json   # 配置文件
```

> ⚠️ **注意**：`config` 文件夹和 `exchange.ico` 必须与 `huchuan.exe` 位于同一目录下，否则程序将无法正常读取配置和显示图标。

## 🖥️ 系统托盘菜单

运行后，程序会在系统托盘显示图标，右键点击可见以下菜单：

- **状态：正在同步中 / 暂停同步中** - 点击切换同步状态
- **配置文件** - 打开配置文件进行编辑
- **退出** - 退出程序

## 📝 日志

程序会在运行目录下生成日志文件：`sync_YYYYMMDD.log`，记录同步状态和错误信息。

## 🔗 兼容性

本工具与 [SyncClipboard](https://github.com/Jeric-X/SyncClipboard) 项目兼容，可与其他支持该协议的客户端配合使用：

- Windows / macOS / Linux 桌面客户端
- iOS 客户端（如 Clip 等）

## ❓ 常见问题

### Q: 如何获取坚果云的 WebDAV 地址？

A: 登录坚果云网页版 → 账户信息 → 安全选项 → 第三方应用管理 → 添加应用密码

### Q: 同步延迟较高怎么办？

A: 可以减小 `check_interval` 的值，但建议不要低于 0.3 秒，以避免请求过于频繁。

## 📄 许可证

本项目采用 MIT 许可证开源。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

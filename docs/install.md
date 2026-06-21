# Hermes Connector 安装指南

## 前置条件

1. **Hermes Agent** 已安装并可正常运行
   - 验证: 在终端运行 `hermes --version` 应显示版本号

2. **AstrBot** v3.4+ 已安装并可正常运行

## 安装方法

### 方法一：手动安装

1. 将 `astrbot_plugin_hermes_connector` 目录复制到 AstrBot 的 `data/plugins/` 目录下
2. 重启 AstrBot
3. 在 AstrBot WebUI 管理面板中启用该插件
4. 配置插件参数（见下方说明）

### 方法二：通过插件市场安装（即将支持）

```bash
# 待上架后可通过插件市场一键安装
```

## 配置说明

在 AstrBot 管理面板的插件配置页填写：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `hermes_command` | Hermes CLI 命令路径 | `hermes` |
| `hermes_workdir` | Hermes 工作目录 | 空（使用默认） |
| `hermes_model` | 创建新会话默认模型 | 空（使用默认） |
| `max_timeout` | 命令超时时间（秒） | 120 |
| `quick_prefix` | 快捷发送前缀 | `>` |
| `output_mode` | 输出模式 | `simple` |
| `auto_create_session` | 自动创建会话 | true |

## 使用说明

### 基础命令

```
/hermes help           — 显示帮助信息
/hermes health         — 检查 Hermes 连接状态
/hermes list           — 列出所有会话
/hermes status [序号]  — 查看会话状态
```

### 消息发送

```
/hermes to 1 你好      — 发送消息到第 1 个会话
/hermes send 你好      — 发送到当前会话
> 你好                 — 快捷发送到当前会话
>1 你好                — 快捷发送到第 1 个会话
```

### 会话管理

```
/hermes create 写一个爬虫  — 创建新会话
/hermes sw 1             — 切换到第 1 个会话
/hermes msg              — 查看最近消息
/hermes abort            — 中断当前会话
/hermes files /tmp       — 浏览文件
```

## 架构说明

```
QQ/微信/Telegram
      ↕  （消息事件）
    AstrBot
      ↕  （Hermes Connector 插件）
 Hermes CLI (subprocess)
      ↕
  Hermes Agent
```

插件通过 subprocess 调用 Hermes CLI，解析 stdout 获取回复内容。
所有会话状态通过 Hermes 的内置会话管理机制维护。

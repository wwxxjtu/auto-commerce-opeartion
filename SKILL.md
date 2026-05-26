# SMS Receiver Skill

一个用于接收、管理和查询短信的OpenClaw技能，与SmsForwarder集成。

## 功能特性

- 管理短信webhook服务器
- 查看和搜索短信记录
- 与MCP服务器集成
- 提供友好的命令界面

## 命令列表

### 启动服务
- `start-webhook` - 启动短信webhook服务器
- `start-mcp` - 启动MCP服务器
- `start-all` - 启动所有服务

### 停止服务
- `stop-webhook` - 停止短信webhook服务器
- `stop-mcp` - 停止MCP服务器
- `stop-all` - 停止所有服务

### 短信管理
- `list-sms` - 查看最新短信
- `search-sms` - 搜索短信
- `clear-sms` - 清空所有短信

### 系统管理
- `status` - 查看服务状态
- `help` - 显示帮助信息

## 配置说明

### 环境变量
- `SMS_SERVER_DIR` - 短信服务器安装目录
- `SMS_SERVER_HOST` - 服务器主机地址
- `SMS_SERVER_PORT` - 服务器端口

### 默认配置
- 服务器地址: http://localhost:8000
- Webhook路径: /webhook/sms
- 存储文件: sms_data.json

## 依赖项

- Python 3.8+
- 已安装的短信服务器组件

## 使用示例

```bash
# 启动所有服务
openclaw skill run sms-receiver --action start-all

# 查看最新短信
openclaw skill run sms-receiver --action list-sms

# 搜索短信
openclaw skill run sms-receiver --action search-sms --keyword "验证码"

# 停止所有服务
openclaw skill run sms-receiver --action stop-all
```

## 注意事项

1. 确保SmsForwarder已正确配置指向webhook地址
2. 首次使用前请运行安装脚本
3. 服务默认在后台运行

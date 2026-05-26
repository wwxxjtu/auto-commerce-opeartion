# SMS Receiver Skill for OpenClaw

一个用于接收、管理和查询短信的OpenClaw技能，与SmsForwarder集成。

## 功能特性

- 管理短信webhook服务器
- 查看和搜索短信记录
- 与MCP服务器集成
- 提供友好的命令界面
- 支持Windows和Linux平台

## 安装方法

### 方法1：直接安装

1. 下载技能包到OpenClaw的skills目录
2. 运行安装脚本：
   ```bash
   # Windows
   install.bat
   
   # Linux/Mac
   bash install.sh
   ```

### 方法2：通过OpenClaw命令安装

```bash
openclaw skill install sms-receiver
```

## 快速开始

### 1. 启动所有服务

```bash
openclaw skill run sms-receiver --action start-all
```

### 2. 配置SmsForwarder

1. 在Android手机上安装SmsForwarder
2. 添加Webhook发送方
3. URL设置为：`http://your-ip:8000/webhook/sms`
4. 配置转发规则

### 3. 测试服务

```bash
# 查看服务状态
openclaw skill run sms-receiver --action status

# 查看最新短信
openclaw skill run sms-receiver --action list-sms

# 搜索短信
openclaw skill run sms-receiver --action search-sms --keyword "验证码"
```

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
在 `.env` 文件中配置：

- `SMS_SERVER_HOST` - 服务器主机地址（默认：0.0.0.0）
- `SMS_SERVER_PORT` - 服务器端口（默认：8000）
- `SMS_WEBHOOK_PATH` - Webhook路径（默认：/webhook/sms）
- `SMS_STORAGE_FILE` - 存储文件（默认：sms_data.json）

### 默认配置
- 服务器地址: http://localhost:8000
- Webhook路径: /webhook/sms
- 存储文件: sms_data.json

## 使用示例

### 启动服务
```bash
openclaw skill run sms-receiver --action start-all
```

### 查看短信
```bash
# 查看最新10条短信
openclaw skill run sms-receiver --action list-sms

# 查看最新20条短信
openclaw skill run sms-receiver --action list-sms --count 20
```

### 搜索短信
```bash
# 搜索包含"验证码"的短信
openclaw skill run sms-receiver --action search-sms --keyword "验证码"

# 搜索包含"余额"的短信
openclaw skill run sms-receiver --action search-sms --keyword "余额"
```

### 管理服务
```bash
# 停止所有服务
openclaw skill run sms-receiver --action stop-all

# 查看服务状态
openclaw skill run sms-receiver --action status

# 显示帮助信息
openclaw skill run sms-receiver --action help
```

## 技术架构

### 核心组件
- **Webhook服务器** - 接收SmsForwarder转发的短信
- **MCP服务器** - 与OpenClaw集成，提供短信查询工具
- **存储系统** - 管理短信数据
- **技能接口** - 提供命令行界面

### 数据流程
1. SmsForwarder发送短信到Webhook服务器
2. Webhook服务器存储短信到JSON文件
3. MCP服务器提供工具查询短信
4. Skill命令提供管理界面

## 故障排除

### 常见问题

1. **Webhook服务器启动失败**
   - 检查端口是否被占用
   - 检查Python依赖是否安装

2. **SmsForwarder无法连接**
   - 检查网络连接
   - 检查防火墙设置
   - 确保服务器地址正确

3. **MCP服务器无法启动**
   - 检查Python环境
   - 检查端口冲突

4. **短信不显示**
   - 检查SmsForwarder配置
   - 检查Webhook服务器日志
   - 检查存储文件权限

### 日志查看

- Webhook服务器日志：运行时控制台输出
- MCP服务器日志：运行时控制台输出
- 技能日志：OpenClaw控制台输出

## 系统要求

- Python 3.8+
- OpenClaw最新版本
- SmsForwarder（Android应用）
- 网络连接

## 注意事项

1. 确保SmsForwarder已正确配置指向webhook地址
2. 首次使用前请运行安装脚本
3. 服务默认在后台运行
4. 定期备份短信数据文件
5. 短信数据可能包含敏感信息，请妥善保管

## 许可证

BSD 2-Clause License

# SMS Webhook Server with MCP

一个与SmsForwarder集成的短信webhook服务器，封装为MCP服务器供OpenClaw使用。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动Webhook服务器

```bash
python webhook_server.py
```

服务器将在 `http://localhost:8000` 启动

### 3. 配置SmsForwarder

1. 在Android手机上安装SmsForwarder
2. 添加Webhook发送方，URL设置为：`http://your-ip:8000/webhook/sms`
3. 配置转发规则

### 4. 启动MCP服务器（供OpenClaw使用）

```bash
python mcp_server.py
```

### 5. 测试

```bash
python test_server.py    # 测试Webhook服务器
python test_mcp.py       # 测试MCP服务器
```

## 功能特性

- 接收SmsForwarder转发的短信
- 存储和管理短信记录
- 提供RESTful API接口
- 封装为MCP服务器，提供以下工具：
  - `get_latest_sms`: 获取最新短信
  - `search_sms`: 搜索短信
  - `get_sms_by_id`: 根据ID获取短信
  - `get_all_sms`: 获取所有短信
  - `clear_all_sms`: 清空所有短信

## 安装

### 前置要求

- Python 3.8+
- SmsForwarder Android应用

### 安装步骤

1. 克隆或下载本项目

2. 安装依赖：
```bash
pip install -r requirements.txt
```

或者在Windows上运行：
```bash
install.bat
```

3. 配置环境变量（可选）：
```bash
cp .env.example .env
```

编辑 `.env` 文件根据需要修改配置。

## 使用方法

### 启动Webhook服务器

Webhook服务器用于接收SmsForwarder转发的短信。

**Windows:**
```bash
start_webhook.bat
```

**Linux/Mac:**
```bash
python webhook_server.py
```

服务器默认运行在 `http://localhost:8000`

### 配置SmsForwarder

1. 在Android手机上安装SmsForwarder
2. 打开应用，进入"发送方设置"
3. 添加"Webhook"发送方
4. 设置Webhook URL为：`http://your-server-ip:8000/webhook/sms`
5. 配置转发规则，选择刚才创建的Webhook发送方
6. 测试配置是否正确

### 启动MCP服务器

MCP服务器用于向OpenClaw提供短信数据访问能力。

**Windows:**
```bash
start_mcp.bat
```

**Linux/Mac:**
```bash
python mcp_server.py
```

### 在OpenClaw中配置MCP服务器

在OpenClaw的配置文件中添加：

```json
{
  "mcpServers": {
    "sms-webhook": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "/path/to/sms-auto"
    }
  }
}
```

## API接口

### Webhook接口

- `POST /webhook/sms` - 接收SmsForwarder转发的短信

### RESTful API接口

- `GET /` - 服务器状态
- `GET /health` - 健康检查
- `GET /api/sms` - 获取所有短信
- `GET /api/sms/latest?count=10` - 获取最新N条短信
- `GET /api/sms/{sms_id}` - 根据ID获取短信
- `GET /api/sms/search/{keyword}` - 搜索短信
- `DELETE /api/sms` - 清空所有短信

## MCP工具说明

### get_latest_sms
获取最新的短信记录。

参数：
- `count` (可选): 获取的短信数量，默认10条，范围1-100

### search_sms
搜索短信内容。

参数：
- `keyword` (必需): 搜索关键词，匹配发送者号码或短信内容

### get_sms_by_id
根据ID获取特定短信。

参数：
- `sms_id` (必需): 短信ID

### get_all_sms
获取所有短信记录。

### clear_all_sms
清空所有短信记录。

## 数据存储

短信数据存储在 `sms_data.json` 文件中，格式如下：

```json
[
  {
    "id": "sms_1234567890",
    "sender": "10086",
    "content": "您的验证码是123456",
    "timestamp": "2024-01-01T12:00:00",
    "sim_slot": "SIM1",
    "device_name": "MyPhone",
    "extra": {}
  }
]
```

## 配置说明

环境变量配置（`.env` 文件）：

- `HOST`: 服务器监听地址，默认 `0.0.0.0`
- `PORT`: 服务器端口，默认 `8000`
- `WEBHOOK_PATH`: Webhook路径，默认 `/webhook/sms`
- `STORAGE_FILE`: 存储文件路径，默认 `sms_data.json`
- `MAX_SMS_COUNT`: 最大存储短信数量，默认 `1000`
- `MCP_SERVER_NAME`: MCP服务器名称，默认 `sms-webhook`
- `MCP_SERVER_VERSION`: MCP服务器版本，默认 `1.0.0`

## 项目结构

```
sms-auto/
├── config.py           # 配置管理
├── models.py           # 数据模型
├── storage.py          # 数据存储
├── webhook_server.py   # Webhook服务器
├── mcp_server.py       # MCP服务器
├── requirements.txt    # Python依赖
├── .env.example       # 环境变量示例
├── .gitignore         # Git忽略文件
├── install.bat        # Windows安装脚本
├── start_webhook.bat  # Windows启动Webhook服务器
├── start_mcp.bat      # Windows启动MCP服务器
└── README.md          # 本文件
```

## 注意事项

1. 确保服务器可以从SmsForwarder访问（考虑防火墙和网络配置）
2. 定期备份 `sms_data.json` 文件
3. 短信数据可能包含敏感信息，请妥善保管
4. 建议在生产环境中使用HTTPS

## 故障排除

### Webhook无法接收短信

- 检查SmsForwarder的Webhook URL配置是否正确
- 确认服务器正在运行且端口可访问
- 查看服务器日志获取错误信息

### MCP服务器无法连接

- 确认MCP服务器正在运行
- 检查OpenClaw配置文件中的路径是否正确
- 查看MCP服务器日志

## 许可证

BSD 2-Clause License

## 相关链接

- [SmsForwarder GitHub](https://github.com/pppscn/SmsForwarder)
- [SmsForwarder Gitee](https://gitee.com/pp/SmsForwarder)
- [MCP协议文档](https://modelcontextprotocol.io/)

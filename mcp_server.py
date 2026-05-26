#!/usr/bin/env python3
"""
MCP Server Implementation
Pure Python implementation of MCP (Model Context Protocol) server

This server provides tools for accessing SMS data and communicates over stdio
using the MCP protocol.
"""
import json
import sys
import logging
from typing import Dict, Any, List, Optional
from storage import storage
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPMessage:
    """MCP message structure"""
    def __init__(self, **kwargs):
        self.type = kwargs.get('type')
        self.data = kwargs.get('data')
        self.id = kwargs.get('id')
    
    def to_json(self) -> str:
        return json.dumps({
            'type': self.type,
            'data': self.data,
            'id': self.id
        }, ensure_ascii=False) + '\n'


class MCPResponse:
    """MCP response structure"""
    def __init__(self, content: List[Dict[str, Any]]):
        self.content = content
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'content': self.content
        }


class MCPTool:
    """MCP tool definition"""
    def __init__(self, name: str, description: str, input_schema: Dict[str, Any]):
        self.name = name
        self.description = description
        self.input_schema = input_schema
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'inputSchema': self.input_schema
        }


class MCPServer:
    """MCP Server implementation"""
    
    def __init__(self):
        self.tools = [
            MCPTool(
                name="get_latest_sms",
                description="获取最新的短信记录",
                input_schema={
                    "type": "object",
                    "properties": {
                        "count": {
                            "type": "integer",
                            "description": "获取的短信数量，默认10条",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 100
                        }
                    }
                }
            ),
            MCPTool(
                name="search_sms",
                description="搜索短信内容",
                input_schema={
                    "type": "object",
                    "properties": {
                        "keyword": {
                            "type": "string",
                            "description": "搜索关键词，匹配发送者号码或短信内容"
                        }
                    },
                    "required": ["keyword"]
                }
            ),
            MCPTool(
                name="get_sms_by_id",
                description="根据ID获取特定短信",
                input_schema={
                    "type": "object",
                    "properties": {
                        "sms_id": {
                            "type": "string",
                            "description": "短信ID"
                        }
                    },
                    "required": ["sms_id"]
                }
            ),
            MCPTool(
                name="get_all_sms",
                description="获取所有短信记录",
                input_schema={
                    "type": "object",
                    "properties": {}
                }
            ),
            MCPTool(
                name="clear_all_sms",
                description="清空所有短信记录",
                input_schema={
                    "type": "object",
                    "properties": {}
                }
            )
        ]
    
    def handle_message(self, message: MCPMessage) -> Optional[MCPResponse]:
        """Handle MCP messages"""
        if message.type == 'list_tools':
            return MCPResponse([{
                'type': 'tool_list',
                'tools': [tool.to_dict() for tool in self.tools]
            }])
        
        elif message.type == 'call_tool':
            tool_call = message.data
            tool_name = tool_call.get('name')
            arguments = tool_call.get('arguments', {})
            
            try:
                if tool_name == "get_latest_sms":
                    return self.get_latest_sms(arguments)
                elif tool_name == "search_sms":
                    return self.search_sms(arguments)
                elif tool_name == "get_sms_by_id":
                    return self.get_sms_by_id(arguments)
                elif tool_name == "get_all_sms":
                    return self.get_all_sms()
                elif tool_name == "clear_all_sms":
                    return self.clear_all_sms()
                else:
                    return MCPResponse([{
                        'type': 'text',
                        'text': f"未知的工具: {tool_name}"
                    }])
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}")
                return MCPResponse([{
                    'type': 'text',
                    'text': f"执行工具时出错: {str(e)}"
                }])
        
        return None
    
    def get_latest_sms(self, arguments: Dict[str, Any]) -> MCPResponse:
        """Get latest SMS messages"""
        import asyncio
        count = arguments.get("count", 10)
        sms_list = asyncio.run(storage.get_latest_sms(count))
        
        if not sms_list:
            return MCPResponse([{
                'type': 'text',
                'text': "暂无短信记录"
            }])
        
        result = []
        for sms in sms_list:
            result.append(f"【{sms.timestamp}】{sms.sender}: {sms.content}")
        
        return MCPResponse([{
            'type': 'text',
            'text': "\n\n".join(result)
        }])
    
    def search_sms(self, arguments: Dict[str, Any]) -> MCPResponse:
        """Search SMS messages"""
        import asyncio
        keyword = arguments.get("keyword", "")
        if not keyword:
            return MCPResponse([{
                'type': 'text',
                'text': "请提供搜索关键词"
            }])
        
        sms_list = asyncio.run(storage.search_sms(keyword))
        
        if not sms_list:
            return MCPResponse([{
                'type': 'text',
                'text': f"未找到包含关键词 '{keyword}' 的短信"
            }])
        
        result = []
        for sms in sms_list:
            result.append(f"【{sms.timestamp}】{sms.sender}: {sms.content}")
        
        return MCPResponse([{
            'type': 'text',
            'text': f"找到 {len(sms_list)} 条匹配的短信:\n\n" + "\n\n".join(result)
        }])
    
    def get_sms_by_id(self, arguments: Dict[str, Any]) -> MCPResponse:
        """Get SMS by ID"""
        import asyncio
        sms_id = arguments.get("sms_id", "")
        if not sms_id:
            return MCPResponse([{
                'type': 'text',
                'text': "请提供短信ID"
            }])
        
        sms = asyncio.run(storage.get_sms_by_id(sms_id))
        
        if not sms:
            return MCPResponse([{
                'type': 'text',
                'text': f"未找到ID为 '{sms_id}' 的短信"
            }])
        
        result = f"短信ID: {sms.id}\n"
        result += f"发送者: {sms.sender}\n"
        result += f"时间: {sms.timestamp}\n"
        result += f"内容: {sms.content}\n"
        if sms.sim_slot:
            result += f"卡槽: {sms.sim_slot}\n"
        if sms.device_name:
            result += f"设备: {sms.device_name}\n"
        
        return MCPResponse([{
            'type': 'text',
            'text': result
        }])
    
    def get_all_sms(self) -> MCPResponse:
        """Get all SMS messages"""
        import asyncio
        sms_list = asyncio.run(storage.get_all_sms())
        
        if not sms_list:
            return MCPResponse([{
                'type': 'text',
                'text': "暂无短信记录"
            }])
        
        result = []
        for sms in sms_list:
            result.append(f"【{sms.timestamp}】{sms.sender}: {sms.content}")
        
        return MCPResponse([{
            'type': 'text',
            'text': f"共有 {len(sms_list)} 条短信:\n\n" + "\n\n".join(result)
        }])
    
    def clear_all_sms(self) -> MCPResponse:
        """Clear all SMS messages"""
        import asyncio
        asyncio.run(storage.clear_all())
        return MCPResponse([{
            'type': 'text',
            'text': "已清空所有短信记录"
        }])


def read_message() -> Optional[MCPMessage]:
    """Read MCP message from stdin"""
    try:
        line = sys.stdin.readline()
        if not line:
            return None
        
        line = line.strip()
        if not line:
            return None
        
        data = json.loads(line)
        return MCPMessage(**data)
    except Exception as e:
        logger.error(f"Error reading message: {e}")
        return None


def write_response(response: MCPResponse, message_id: str):
    """Write MCP response to stdout"""
    try:
        resp_message = MCPMessage(
            type='tool_response',
            data=response.to_dict(),
            id=message_id
        )
        sys.stdout.write(resp_message.to_json())
        sys.stdout.flush()
    except Exception as e:
        logger.error(f"Error writing response: {e}")


def main():
    """Main MCP server loop"""
    logger.info("Starting MCP server...")
    
    server = MCPServer()
    
    try:
        while True:
            message = read_message()
            if message is None:
                break
            
            logger.info(f"Received message: {message.type}")
            
            response = server.handle_message(message)
            if response:
                write_response(response, message.id)
    
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")


if __name__ == "__main__":
    main()

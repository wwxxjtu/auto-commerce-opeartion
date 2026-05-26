#!/usr/bin/env python3
"""
SMS Receiver Skill Main Script

This script handles the SMS receiver skill commands for OpenClaw.
"""
import os
import sys
import json
import subprocess
import time
import argparse
from datetime import datetime


class SMSReceiverSkill:
    """SMS Receiver Skill class"""
    
    def __init__(self):
        self.skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_file = os.path.join(self.skill_dir, '.env')
        self.config = self._load_config()
        self.processes = {}
    
    def _load_config(self):
        """Load configuration"""
        config = {
            'SMS_SERVER_DIR': self.skill_dir,
            'SMS_SERVER_HOST': '0.0.0.0',
            'SMS_SERVER_PORT': 8000,
            'SMS_WEBHOOK_PATH': '/webhook/sms',
            'SMS_STORAGE_FILE': 'sms_data.json'
        }
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        config[key] = value
        
        return config
    
    def _run_command(self, command, cwd=None, shell=True, wait=True):
        """Run system command"""
        try:
            if wait:
                result = subprocess.run(
                    command,
                    cwd=cwd or self.config['SMS_SERVER_DIR'],
                    shell=shell,
                    capture_output=True,
                    text=True
                )
                return result.returncode, result.stdout, result.stderr
            else:
                process = subprocess.Popen(
                    command,
                    cwd=cwd or self.config['SMS_SERVER_DIR'],
                    shell=shell,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                return 0, process, None
        except Exception as e:
            return 1, None, str(e)
    
    def start_webhook(self):
        """Start webhook server"""
        print("Starting SMS Webhook Server...")
        
        # Check if already running
        if 'webhook' in self.processes:
            print("Webhook server is already running.")
            return {
                "success": True,
                "message": "Webhook server is already running"
            }
        
        # Start server
        cmd = 'python webhook_server.py'
        code, process, error = self._run_command(cmd, wait=False)
        
        if code == 0:
            self.processes['webhook'] = process
            time.sleep(2)  # Give it time to start
            
            # Check if it's running
            host = self.config['SMS_SERVER_HOST']
            port = self.config['SMS_SERVER_PORT']
            webhook_path = self.config['SMS_WEBHOOK_PATH']
            
            print(f"Webhook server started successfully!")
            print(f"Server address: http://{host}:{port}")
            print(f"Webhook endpoint: http://{host}:{port}{webhook_path}")
            
            return {
                "success": True,
                "message": f"Webhook server started at http://{host}:{port}",
                "endpoint": f"http://{host}:{port}{webhook_path}"
            }
        else:
            return {
                "success": False,
                "message": f"Failed to start webhook server: {error}"
            }
    
    def start_mcp(self):
        """Start MCP server"""
        print("Starting SMS MCP Server...")
        
        # Check if already running
        if 'mcp' in self.processes:
            print("MCP server is already running.")
            return {
                "success": True,
                "message": "MCP server is already running"
            }
        
        # Start server
        cmd = 'python mcp_server.py'
        code, process, error = self._run_command(cmd, wait=False)
        
        if code == 0:
            self.processes['mcp'] = process
            time.sleep(2)  # Give it time to start
            
            print("MCP server started successfully!")
            print("Server is ready for OpenClaw connections")
            
            return {
                "success": True,
                "message": "MCP server started successfully",
                "status": "ready"
            }
        else:
            return {
                "success": False,
                "message": f"Failed to start MCP server: {error}"
            }
    
    def start_all(self):
        """Start all servers"""
        print("Starting all SMS servers...")
        
        results = []
        
        # Start webhook server
        webhook_result = self.start_webhook()
        results.append(webhook_result)
        
        # Start MCP server
        mcp_result = self.start_mcp()
        results.append(mcp_result)
        
        all_success = all(r['success'] for r in results)
        
        return {
            "success": all_success,
            "message": "All servers started" if all_success else "Some servers failed to start",
            "results": results
        }
    
    def stop_webhook(self):
        """Stop webhook server"""
        print("Stopping SMS Webhook Server...")
        
        if 'webhook' in self.processes:
            process = self.processes['webhook']
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            del self.processes['webhook']
            
            return {
                "success": True,
                "message": "Webhook server stopped"
            }
        else:
            return {
                "success": True,
                "message": "Webhook server is not running"
            }
    
    def stop_mcp(self):
        """Stop MCP server"""
        print("Stopping SMS MCP Server...")
        
        if 'mcp' in self.processes:
            process = self.processes['mcp']
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            del self.processes['mcp']
            
            return {
                "success": True,
                "message": "MCP server stopped"
            }
        else:
            return {
                "success": True,
                "message": "MCP server is not running"
            }
    
    def stop_all(self):
        """Stop all servers"""
        print("Stopping all SMS servers...")
        
        results = []
        
        # Stop webhook server
        webhook_result = self.stop_webhook()
        results.append(webhook_result)
        
        # Stop MCP server
        mcp_result = self.stop_mcp()
        results.append(mcp_result)
        
        return {
            "success": True,
            "message": "All servers stopped",
            "results": results
        }
    
    def list_sms(self, count=10):
        """List latest SMS"""
        print(f"Listing latest {count} SMS messages...")
        
        # Check if storage file exists
        storage_file = os.path.join(self.config['SMS_SERVER_DIR'], self.config.get('SMS_STORAGE_FILE', 'sms_data.json'))
        
        if not os.path.exists(storage_file):
            return {
                "success": True,
                "message": "No SMS messages found",
                "data": []
            }
        
        try:
            with open(storage_file, 'r', encoding='utf-8') as f:
                sms_data = json.load(f)
            
            # Get latest SMS
            latest_sms = sms_data[:count]
            
            # Format response
            formatted_sms = []
            for sms in latest_sms:
                formatted_sms.append({
                    "id": sms.get('id'),
                    "sender": sms.get('sender'),
                    "content": sms.get('content'),
                    "timestamp": sms.get('timestamp'),
                    "sim_slot": sms.get('sim_slot'),
                    "device_name": sms.get('device_name')
                })
            
            return {
                "success": True,
                "message": f"Found {len(formatted_sms)} SMS messages",
                "data": formatted_sms
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error reading SMS data: {str(e)}"
            }
    
    def search_sms(self, keyword):
        """Search SMS by keyword"""
        print(f"Searching SMS for keyword: {keyword}")
        
        # Check if storage file exists
        storage_file = os.path.join(self.config['SMS_SERVER_DIR'], self.config.get('SMS_STORAGE_FILE', 'sms_data.json'))
        
        if not os.path.exists(storage_file):
            return {
                "success": True,
                "message": "No SMS messages found",
                "data": []
            }
        
        try:
            with open(storage_file, 'r', encoding='utf-8') as f:
                sms_data = json.load(f)
            
            # Search SMS
            keyword_lower = keyword.lower()
            matched_sms = []
            
            for sms in sms_data:
                sender = sms.get('sender', '').lower()
                content = sms.get('content', '').lower()
                
                if keyword_lower in sender or keyword_lower in content:
                    matched_sms.append({
                        "id": sms.get('id'),
                        "sender": sms.get('sender'),
                        "content": sms.get('content'),
                        "timestamp": sms.get('timestamp'),
                        "sim_slot": sms.get('sim_slot'),
                        "device_name": sms.get('device_name')
                    })
            
            return {
                "success": True,
                "message": f"Found {len(matched_sms)} matching SMS messages",
                "data": matched_sms
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error searching SMS: {str(e)}"
            }
    
    def clear_sms(self):
        """Clear all SMS"""
        print("Clearing all SMS messages...")
        
        # Check if storage file exists
        storage_file = os.path.join(self.config['SMS_SERVER_DIR'], self.config.get('SMS_STORAGE_FILE', 'sms_data.json'))
        
        try:
            # Write empty list
            with open(storage_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "message": "All SMS messages cleared"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error clearing SMS: {str(e)}"
            }
    
    def status(self):
        """Check service status"""
        print("Checking SMS server status...")
        
        status = {
            "webhook": "running" if 'webhook' in self.processes else "stopped",
            "mcp": "running" if 'mcp' in self.processes else "stopped",
            "storage": "available" if os.path.exists(os.path.join(self.config['SMS_SERVER_DIR'], self.config.get('SMS_STORAGE_FILE', 'sms_data.json'))) else "not_found",
            "config": self.config,
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "message": "Status check completed",
            "data": status
        }
    
    def help(self):
        """Show help information"""
        help_text = """
SMS Receiver Skill Help

Available commands:

  start-webhook   - Start SMS webhook server
  start-mcp       - Start MCP server
  start-all       - Start all servers
  stop-webhook    - Stop SMS webhook server
  stop-mcp        - Stop MCP server
  stop-all        - Stop all servers
  list-sms        - List latest SMS messages
  search-sms      - Search SMS by keyword
  clear-sms       - Clear all SMS messages
  status          - Check service status
  help            - Show this help

Usage examples:
  openclaw skill run sms-receiver --action start-all
  openclaw skill run sms-receiver --action list-sms
  openclaw skill run sms-receiver --action search-sms --keyword "验证码"
        """
        
        print(help_text)
        
        return {
            "success": True,
            "message": "Help information displayed",
            "data": {
                "commands": [
                    "start-webhook", "start-mcp", "start-all",
                    "stop-webhook", "stop-mcp", "stop-all",
                    "list-sms", "search-sms", "clear-sms",
                    "status", "help"
                ]
            }
        }


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='SMS Receiver Skill')
    parser.add_argument('--action', type=str, required=True, help='Action to perform')
    parser.add_argument('--keyword', type=str, help='Search keyword')
    parser.add_argument('--count', type=int, default=10, help='Number of SMS to list')
    
    args = parser.parse_args()
    
    skill = SMSReceiverSkill()
    
    actions = {
        'start-webhook': skill.start_webhook,
        'start-mcp': skill.start_mcp,
        'start-all': skill.start_all,
        'stop-webhook': skill.stop_webhook,
        'stop-mcp': skill.stop_mcp,
        'stop-all': skill.stop_all,
        'list-sms': lambda: skill.list_sms(args.count),
        'search-sms': lambda: skill.search_sms(args.keyword) if args.keyword else {"success": False, "message": "Keyword is required"},
        'clear-sms': skill.clear_sms,
        'status': skill.status,
        'help': skill.help
    }
    
    if args.action in actions:
        result = actions[args.action]()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        result = {
            "success": False,
            "message": f"Unknown action: {args.action}"
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

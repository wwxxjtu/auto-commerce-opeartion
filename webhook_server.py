#!/usr/bin/env python3
"""
SMS Webhook Server
Simple HTTP server to receive SMS from SmsForwarder
"""
import http.server
import json
import logging
from urllib.parse import parse_qs
from datetime import datetime
from storage import storage
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SMSWebhookHandler(http.server.BaseHTTPRequestHandler):
    """Webhook handler for SMS messages"""
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == settings.webhook_path:
            try:
                # Read request body
                content_length = int(self.headers['Content-Length'])
                body = self.rfile.read(content_length)
                
                # Parse request data
                content_type = self.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    data = json.loads(body.decode('utf-8'))
                else:
                    # Parse form data
                    form_data = parse_qs(body.decode('utf-8'))
                    data = {k: v[0] for k, v in form_data.items()}
                
                logger.info(f"Received webhook data: {data}")
                
                # Create SMS message
                from models import SMSMessage
                sms = SMSMessage(
                    sender=data.get("sender", data.get("from", data.get("phone", ""))),
                    content=data.get("content", data.get("message", data.get("text", ""))),
                    sim_slot=data.get("sim_slot", data.get("sim", None)),
                    device_name=data.get("device_name", data.get("device", None)),
                    extra=data
                )
                
                # Save SMS
                import asyncio
                asyncio.run(storage.add_sms(sms))
                logger.info(f"SMS saved: {sms.sender} - {sms.content[:50]}...")
                
                # Send response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {"success": True, "message": "Received"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except Exception as e:
                logger.error(f"Error processing webhook: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {"success": False, "message": str(e)}
                self.wfile.write(json.dumps(response).encode('utf-8'))
        
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"success": False, "message": "Not found"}
            self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "name": settings.app_name,
                "version": settings.app_version,
                "status": "running"
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
        
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"status": "healthy"}
            self.wfile.write(json.dumps(response).encode('utf-8'))
        
        elif self.path.startswith('/api/sms'):
            self._handle_api_request()
        
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"success": False, "message": "Not found"}
            self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def _handle_api_request(self):
        """Handle API requests"""
        import asyncio
        
        try:
            if self.path == '/api/sms':
                # Get all SMS
                sms_list = asyncio.run(storage.get_all_sms())
                self._send_json_response({"count": len(sms_list), "data": [s.dict() for s in sms_list]})
            
            elif self.path.startswith('/api/sms/latest'):
                # Get latest SMS
                import urllib.parse
                parsed = urllib.parse.urlparse(self.path)
                query = urllib.parse.parse_qs(parsed.query)
                count = int(query.get('count', ['10'])[0])
                sms_list = asyncio.run(storage.get_latest_sms(count))
                self._send_json_response({"count": len(sms_list), "data": [s.dict() for s in sms_list]})
            
            elif self.path.startswith('/api/sms/'):
                # Get SMS by ID or search
                parts = self.path.split('/')
                if len(parts) == 4:
                    sms_id = parts[3]
                    sms = asyncio.run(storage.get_sms_by_id(sms_id))
                    if sms:
                        self._send_json_response(sms.dict())
                    else:
                        self.send_response(404)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        response = {"success": False, "message": "SMS not found"}
                        self.wfile.write(json.dumps(response).encode('utf-8'))
                elif len(parts) == 5 and parts[3] == 'search':
                    keyword = parts[4]
                    sms_list = asyncio.run(storage.search_sms(keyword))
                    self._send_json_response({"count": len(sms_list), "data": [s.dict() for s in sms_list]})
            
            else:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {"success": False, "message": "Not found"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
        except Exception as e:
            logger.error(f"Error handling API request: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"success": False, "message": str(e)}
            self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def _send_json_response(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        # Handle datetime objects
        def serialize(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
        self.wfile.write(json.dumps(data, default=serialize).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Custom log message"""
        logger.info(f"{self.client_address[0]} - {format % args}")


def run_server():
    """Run the webhook server"""
    server_address = (settings.host, settings.port)
    httpd = http.server.HTTPServer(server_address, SMSWebhookHandler)
    logger.info(f"Starting SMS Webhook Server on http://{settings.host}:{settings.port}")
    logger.info(f"Webhook endpoint: http://{settings.host}:{settings.port}{settings.webhook_path}")
    logger.info("Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    finally:
        httpd.server_close()


if __name__ == '__main__':
    run_server()

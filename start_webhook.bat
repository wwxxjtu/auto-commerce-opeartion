@echo off
echo Starting SMS Webhook Server...
echo.
echo Server will be available at: http://localhost:8000
echo Webhook endpoint: http://localhost:8000/webhook/sms
echo.
echo Press Ctrl+C to stop the server
echo.

python webhook_server.py

@echo off
echo Running Webhook Server Tests...
echo.
echo Make sure the webhook server is running first!
echo Start it with: start_webhook.bat
echo.

python test_server.py
pause

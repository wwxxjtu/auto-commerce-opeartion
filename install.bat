@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Installation completed!
echo.
echo To start the webhook server, run: start_webhook.bat
echo To start the MCP server, run: start_mcp.bat
pause

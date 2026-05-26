from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()


class Settings(BaseSettings):
    app_name: str = "SMS Webhook Server"
    app_version: str = "1.0.0"
    
    host: str = "0.0.0.0"
    port: int = 8000
    
    webhook_path: str = "/webhook/sms"
    
    storage_file: str = "sms_data.json"
    max_sms_count: int = 1000
    
    mcp_server_name: str = "sms-webhook"
    mcp_server_version: str = "1.0.0"
    mcp_port: int = 8080
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime


class SMSMessage(BaseModel):
    id: Optional[str] = None
    sender: str = Field(..., description="发送者号码")
    content: str = Field(..., description="短信内容")
    timestamp: datetime = Field(default_factory=datetime.now, description="接收时间")
    sim_slot: Optional[str] = Field(None, description="卡槽标识 (SIM1/SIM2)")
    device_name: Optional[str] = Field(None, description="设备名称")
    extra: Optional[Dict[str, Any]] = Field(default_factory=dict, description="额外信息")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookResponse(BaseModel):
    success: bool = True
    message: str = "Received"

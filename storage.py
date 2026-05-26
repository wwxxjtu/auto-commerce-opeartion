import json
import asyncio
from typing import List, Optional
from datetime import datetime
from pathlib import Path
from models import SMSMessage
from config import settings


class SMSStorage:
    def __init__(self):
        self.storage_file = Path(settings.storage_file)
        self._lock = asyncio.Lock()
        self._ensure_storage_file()
    
    def _ensure_storage_file(self):
        if not self.storage_file.exists():
            self.storage_file.write_text("[]", encoding="utf-8")
    
    async def add_sms(self, sms: SMSMessage) -> SMSMessage:
        async with self._lock:
            sms_list = await self._load_sms_list()
            
            if not sms.id:
                sms.id = f"sms_{int(datetime.now().timestamp() * 1000)}"
            
            sms_list.insert(0, sms)
            
            if len(sms_list) > settings.max_sms_count:
                sms_list = sms_list[:settings.max_sms_count]
            
            await self._save_sms_list(sms_list)
            return sms
    
    async def get_all_sms(self) -> List[SMSMessage]:
        async with self._lock:
            return await self._load_sms_list()
    
    async def get_sms_by_id(self, sms_id: str) -> Optional[SMSMessage]:
        sms_list = await self.get_all_sms()
        for sms in sms_list:
            if sms.id == sms_id:
                return sms
        return None
    
    async def get_latest_sms(self, count: int = 10) -> List[SMSMessage]:
        sms_list = await self.get_all_sms()
        return sms_list[:count]
    
    async def search_sms(self, keyword: str) -> List[SMSMessage]:
        sms_list = await self.get_all_sms()
        keyword_lower = keyword.lower()
        return [
            sms for sms in sms_list
            if keyword_lower in sms.sender.lower() or keyword_lower in sms.content.lower()
        ]
    
    async def clear_all(self):
        async with self._lock:
            await self._save_sms_list([])
    
    async def _load_sms_list(self) -> List[SMSMessage]:
        try:
            content = self.storage_file.read_text(encoding="utf-8")
            data = json.loads(content)
            return [SMSMessage(**item) for item in data]
        except Exception:
            return []
    
    async def _save_sms_list(self, sms_list: List[SMSMessage]):
        data = []
        for sms in sms_list:
            sms_dict = sms.dict()
            # 处理datetime对象
            if isinstance(sms_dict.get('timestamp'), datetime):
                sms_dict['timestamp'] = sms_dict['timestamp'].isoformat()
            data.append(sms_dict)
        self.storage_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


storage = SMSStorage()

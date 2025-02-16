# core/telegram.py

from telethon import TelegramClient, events
from telethon.tl.types import InputPeerChannel, InputPeerUser
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.errors import SessionPasswordNeededError
import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime
from config.settings import settings

logger = logging.getLogger(__name__)

class TelegramManager:
    def __init__(self):
        self.clients: Dict[str, TelegramClient] = {}
        self.active_client: Optional[TelegramClient] = None
        self._load_accounts()
        
    def _load_accounts(self):
        """加载所有保存的账号"""
        accounts = settings.get_telegram_accounts()
        for account in accounts:
            self.add_client(
                phone=account['phone'],
                api_id=account['api_id'],
                api_hash=account['api_hash']
            )
            
    def add_client(self, phone: str, api_id: str, api_hash: str) -> TelegramClient:
        """添加新的客户端"""
        try:
            # 创建会话名称
            session_name = f"sessions/{phone}"
            
            # 创建客户端
            client = TelegramClient(
                session_name,
                api_id,
                api_hash,
                device_model="Desktop",
                system_version="Windows 10",
                app_version="1.0",
                lang_code="en"
            )
            
            self.clients[phone] = client
            return client
        except Exception as e:
            logger.error(f"添加Telegram客户端失败: {str(e)}")
            raise
            
    async def start_client(self, phone: str, code_callback=None) -> bool:
        """启动指定的客户端"""
        try:
            client = self.clients.get(phone)
            if not client:
                raise ValueError(f"未找到手机号为 {phone} 的客户端")
                
            # 如果已经连接，先断开
            if client.is_connected():
                await client.disconnect()
                
            # 启动客户端
            await client.connect()
            
            # 如果需要登录
            if not await client.is_user_authorized():
                # 发送验证码
                await client.send_code_request(phone)
                
                # 如果提供了回调函数，使用它获取验证码
                if code_callback:
                    code = await code_callback()
                    try:
                        await client.sign_in(phone, code)
                    except SessionPasswordNeededError:
                        # 如果启用了两步验证，需要输入密码
                        password = await code_callback(password=True)
                        await client.sign_in(password=password)
                        
            self.active_client = client
            logger.info(f"Telegram客户端 {phone} 启动成功")
            return True
            
        except Exception as e:
            logger.error(f"启动Telegram客户端失败: {str(e)}")
            return False
            
    async def get_dialogs(self) -> List[Dict]:
        """获取所有对话（群组/频道）"""
        if not self.active_client:
            raise ValueError("没有活动的客户端")
            
        try:
            dialog_list = []
            async for dialog in self.active_client.iter_dialogs():
                if dialog.is_channel or dialog.is_group:
                    dialog_list.append({
                        'id': dialog.id,
                        'title': dialog.title,
                        'type': 'channel' if dialog.is_channel else 'group',
                        'members_count': dialog.entity.participants_count if hasattr(dialog.entity, 'participants_count') else None
                    })
            return dialog_list
        except Exception as e:
            logger.error(f"获取对话列表失败: {str(e)}")
            raise
            
    async def join_channel(self, channel_link: str) -> bool:
        """加入频道"""
        if not self.active_client:
            raise ValueError("没有活动的客户端")
            
        try:
            await self.active_client(JoinChannelRequest(channel_link))
            return True
        except Exception as e:
            logger.error(f"加入频道失败: {str(e)}")
            return False
            
    async def forward_message(self, message, target_chat_id: int) -> bool:
        """转发消息到目标群组"""
        if not self.active_client:
            raise ValueError("没有活动的客户端")
            
        try:
            # 转发消息
            await self.active_client.forward_messages(
                target_chat_id,
                message
            )
            return True
        except Exception as e:
            logger.error(f"转发消息失败: {str(e)}")
            return False
            
    async def send_message(self, chat_id: int, text: str, file=None) -> bool:
        """发送消息到指定群组"""
        if not self.active_client:
            raise ValueError("没有活动的客户端")
            
        try:
            if file:
                await self.active_client.send_file(
                    chat_id,
                    file,
                    caption=text
                )
            else:
                await self.active_client.send_message(
                    chat_id,
                    text
                )
            return True
        except Exception as e:
            logger.error(f"发送消息失败: {str(e)}")
            return False
            
    def start_message_handler(self, source_groups: List[str], callback):
        """启动消息处理器"""
        if not self.active_client:
            raise ValueError("没有活动的客户端")
            
        @self.active_client.on(events.NewMessage(chats=source_groups))
        async def handler(event):
            try:
                await callback(event)
            except Exception as e:
                logger.error(f"处理消息失败: {str(e)}")
                
    async def stop_client(self, phone: str):
        """停止指定的客户端"""
        try:
            client = self.clients.get(phone)
            if client and client.is_connected():
                await client.disconnect()
                if client == self.active_client:
                    self.active_client = None
        except Exception as e:
            logger.error(f"停止客户端失败: {str(e)}")
            
    async def stop_all_clients(self):
        """停止所有客户端"""
        for phone in self.clients:
            await self.stop_client(phone)
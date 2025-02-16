# core/twitter.py

import tweepy
import logging
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
import tempfile
import os
from config.settings import settings

logger = logging.getLogger(__name__)

class TwitterManager:
    def __init__(self):
        self.clients: Dict[str, tweepy.API] = {}
        self.active_client: Optional[tweepy.API] = None
        self._load_accounts()
        
    def _load_accounts(self):
        """加载所有保存的账号"""
        accounts = settings.get_twitter_accounts()
        for account in accounts:
            self.add_client(
                username=account['username'],
                api_key=account['api_key'],
                api_secret=account['api_secret'],
                access_token=account['access_token'],
                access_secret=account['access_secret']
            )
            
    def add_client(self, username: str, api_key: str, api_secret: str,
                  access_token: str, access_secret: str) -> tweepy.API:
        """添加新的客户端"""
        try:
            # 创建认证对象
            auth = tweepy.OAuthHandler(api_key, api_secret)
            auth.set_access_token(access_token, access_secret)
            
            # 创建API对象
            api = tweepy.API(auth, wait_on_rate_limit=True)
            
            # 验证凭据
            api.verify_credentials()
            
            self.clients[username] = api
            return api
        except Exception as e:
            logger.error(f"添加Twitter客户端失败: {str(e)}")
            raise
            
    def set_active_client(self, username: str) -> bool:
        """设置活动客户端"""
        if username in self.clients:
            self.active_client = self.clients[username]
            return True
        return False
        
    async def send_tweet(self, text: str, media_paths: List[str] = None) -> bool:
        """发送推文"""
        if not self.active_client:
            raise ValueError("没有活动的客户端")
            
        try:
            # 处理文本长度
            if len(text) > 280:
                text = text[:277] + "..."
                
            media_ids = []
            # 上传媒体文件
            if media_paths:
                for media_path in media_paths[:4]:  # Twitter限制最多4个媒体文件
                    media = self.active_client.media_upload(media_path)
                    media_ids.append(media.media_id)
                    
            # 发送推文
            if media_ids:
                self.active_client.update_status(
                    status=text,
                    media_ids=media_ids
                )
            else:
                self.active_client.update_status(text)
                
            return True
            
        except Exception as e:
            logger.error(f"发送推文失败: {str(e)}")
            return False
            
    async def download_media(self, url: str) -> Optional[str]:
        """下载媒体文件"""
        try:
            import requests
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                # 下载文件
                response = requests.get(url, stream=True)
                response.raise_for_status()
                
                # 写入临时文件
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        tmp_file.write(chunk)
                        
                return tmp_file.name
                
        except Exception as e:
            logger.error(f"下载媒体文件失败: {str(e)}")
            return None
            
    def cleanup_media(self, file_path: str):
        """清理临时媒体文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.error(f"清理媒体文件失败: {str(e)}")
            
    def get_client_info(self, username: str) -> Optional[Dict]:
        """获取客户端信息"""
        try:
            client = self.clients.get(username)
            if client:
                user = client.verify_credentials()
                return {
                    'username': username,
                    'name': user.name,
                    'followers_count': user.followers_count,
                    'tweets_count': user.statuses_count,
                    'profile_image': user.profile_image_url_https
                }
        except Exception as e:
            logger.error(f"获取客户端信息失败: {str(e)}")
        return None
        
    def remove_client(self, username: str):
        """移除客户端"""
        if username in self.clients:
            if self.active_client == self.clients[username]:
                self.active_client = None
            del self.clients[username]
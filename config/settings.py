# config/settings.py

import os
from dataclasses import dataclass
from typing import List, Dict, Optional
from models.database import DatabaseManager

@dataclass
class DatabaseConfig:
    db_file: str = "forward.db"
    
@dataclass
class AppConfig:
    app_name: str = "Telegram Forward"
    version: str = "1.0.0"
    data_dir: str = os.path.expanduser("~/.tg_forward")
    log_file: str = "forward.log"
    database: DatabaseConfig = DatabaseConfig()
    
    def __post_init__(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
class Settings:
    def __init__(self):
        self.config = AppConfig()
        self.db = DatabaseManager(
            os.path.join(self.config.data_dir, self.config.database.db_file)
        )
        
    def save_telegram_account(self, phone: str, api_id: str, api_hash: str):
        """保存Telegram账号信息"""
        return self.db.save_telegram_account(phone, api_id, api_hash)
        
    def get_telegram_accounts(self) -> List[Dict]:
        """获取所有保存的Telegram账号"""
        accounts = self.db.get_accounts('telegram')
        return [{
            'phone': account.username,
            'api_id': account.api_id,
            'api_hash': account.api_hash
        } for account in accounts]
        
    def save_twitter_account(self, username: str, api_key: str, api_secret: str,
                           access_token: str, access_secret: str):
        """保存Twitter账号信息"""
        return self.db.save_twitter_account(
            username, api_key, api_secret,
            access_token, access_secret
        )
        
    def get_twitter_accounts(self) -> List[Dict]:
        """获取所有保存的Twitter账号"""
        accounts = self.db.get_accounts('twitter')
        return [{
            'username': account.username,
            'api_key': account.api_id,
            'api_secret': account.api_hash,
            'access_token': account.access_token,
            'access_secret': account.access_secret
        } for account in accounts]
        
    def save_forward_rule(self, rule_name: str, rule_data: dict):
        """保存转发规则"""
        source_group = self.db.save_group(
            group_id=rule_data['source_group']['id'],
            title=rule_data['source_group']['title'],
            type='source',
            group_type='group'
        )
        
        target_group = self.db.save_group(
            group_id=rule_data['target']['id'],
            title=rule_data['target']['title'],
            type='target',
            group_type='group' if rule_data['target_type'] == 'Telegram群组' else 'twitter'
        )
        
        return self.db.save_rule(
            name=rule_name,
            source_group_id=source_group.id,
            target_type=rule_data['target_type'],
            target_id=target_group.id,
            filters=rule_data['filters'],
            options=rule_data['options'],
            twitter_config=rule_data.get('twitter_config')
        )
        
    def get_forward_rules(self) -> List[Dict]:
        """获取所有转发规则"""
        rules = self.db.get_rules()
        result = []
        for rule in rules:
            source_group = self.db.get_group_by_id(rule.source_group_id)
            target_group = self.db.get_group_by_id(rule.target_id)
            
            if source_group and target_group:
                result.append({
                    'name': rule.name,
                    'source_group': {
                        'id': source_group.group_id,
                        'title': source_group.title,
                        'type': source_group.group_type
                    },
                    'target_type': rule.target_type,
                    'target': {
                        'id': target_group.group_id,
                        'title': target_group.title
                    },
                    'filters': rule.filters,
                    'options': rule.options,
                    'twitter_config': rule.twitter_config,
                    'disabled': not rule.is_enabled
                })
        return result
        
    def get_statistics(self, start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> Dict:
        """获取统计数据"""
        return self.db.get_statistics(start_date=start_date, end_date=end_date)
        
    def log_forward(self, rule_id: int, message: str, success: bool,
                   error_message: Optional[str] = None):
        """记录转发日志"""
        self.db.add_forward_log(
            rule_id=rule_id,
            message_text=message,
            status='success' if success else 'failed',
            error_message=error_message
        )
        
    def get_forward_logs(self, rule_id: Optional[int] = None,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None) -> List[Dict]:
        """获取转发日志"""
        return self.db.get_forward_logs(
            rule_id=rule_id,
            start_date=start_date,
            end_date=end_date
        )
        
# 创建全局设置实例
settings = Settings()
import os
from dataclasses import dataclass
from typing import List
from PyQt6.QtCore import QSettings

@dataclass
class DatabaseConfig:
    db_file: str = "forward.db"
    
@dataclass
class AppConfig:
    # 应用程序配置
    app_name: str = "Telegram Forward"
    version: str = "1.0.0"
    data_dir: str = os.path.expanduser("~/.tg_forward")
    log_file: str = "forward.log"
    
    # 数据库配置
    database: DatabaseConfig = DatabaseConfig()
    
    def __post_init__(self):
        # 确保数据目录存在
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
class Settings:
    def __init__(self):
        self.config = AppConfig()
        self.settings = QSettings()
        
    def save_telegram_account(self, phone: str, api_id: str, api_hash: str):
        """保存Telegram账号信息"""
        self.settings.beginGroup("telegram_accounts")
        self.settings.setValue(phone, {
            "api_id": api_id,
            "api_hash": api_hash
        })
        self.settings.endGroup()
        
    def get_telegram_accounts(self) -> List[dict]:
        """获取所有保存的Telegram账号"""
        accounts = []
        self.settings.beginGroup("telegram_accounts")
        for phone in self.settings.childKeys():
            account_data = self.settings.value(phone)
            account_data['phone'] = phone
            accounts.append(account_data)
        self.settings.endGroup()
        return accounts
        
    def save_twitter_account(self, username: str, api_key: str, api_secret: str,
                           access_token: str, access_secret: str):
        """保存Twitter账号信息"""
        self.settings.beginGroup("twitter_accounts")
        self.settings.setValue(username, {
            "api_key": api_key,
            "api_secret": api_secret,
            "access_token": access_token,
            "access_secret": access_secret
        })
        self.settings.endGroup()
        
    def get_twitter_accounts(self) -> List[dict]:
        """获取所有保存的Twitter账号"""
        accounts = []
        self.settings.beginGroup("twitter_accounts")
        for username in self.settings.childKeys():
            account_data = self.settings.value(username)
            account_data['username'] = username
            accounts.append(account_data)
        self.settings.endGroup()
        return accounts
        
    def save_forward_rule(self, rule_name: str, rule_data: dict):
        """保存转发规则"""
        self.settings.beginGroup("forward_rules")
        self.settings.setValue(rule_name, rule_data)
        self.settings.endGroup()
        
    def get_forward_rules(self) -> List[dict]:
        """获取所有转发规则"""
        rules = []
        self.settings.beginGroup("forward_rules")
        for rule_name in self.settings.childKeys():
            rule_data = self.settings.value(rule_name)
            rule_data['name'] = rule_name
            rules.append(rule_data)
        self.settings.endGroup()
        return rules
        
# 创建全局设置实例
settings = Settings()
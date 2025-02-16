# models/database.py

import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class Account:
    id: int
    type: str  # 'telegram' or 'twitter'
    username: str
    api_id: str
    api_hash: str
    access_token: Optional[str] = None
    access_secret: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None

@dataclass
class Group:
    id: int
    group_id: str
    title: str
    type: str  # 'source' or 'target'
    group_type: str  # 'channel' or 'group'
    members_count: Optional[int] = None
    created_at: datetime = None
    updated_at: datetime = None

@dataclass
class ForwardRule:
    id: int
    name: str
    source_group_id: int
    target_type: str  # 'telegram' or 'twitter'
    target_id: int
    filters: Dict
    options: Dict
    twitter_config: Optional[Dict] = None
    is_enabled: bool = True
    created_at: datetime = None
    updated_at: datetime = None

@dataclass
class ForwardLog:
    id: int
    rule_id: int
    message_text: str
    status: str
    error_message: Optional[str] = None
    created_at: datetime = None

class DatabaseManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, db_path: str = None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
            
    def __init__(self, db_path: str = None):
        if not hasattr(self, '_initialized'):
            self.db_path = db_path or str(Path.home() / '.tg_forward' / 'forward.db')
            self._initialized = True
            self._create_tables()
            
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
        
    def _create_tables(self):
        """创建数据库表"""
        with self._get_connection() as conn:
            conn.executescript('''
                -- 账号表
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    username TEXT NOT NULL,
                    api_id TEXT,
                    api_hash TEXT,
                    access_token TEXT,
                    access_secret TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- 群组表
                CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    type TEXT NOT NULL,
                    group_type TEXT NOT NULL,
                    members_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- 转发规则表
                CREATE TABLE IF NOT EXISTS forward_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    source_group_id INTEGER NOT NULL,
                    target_type TEXT NOT NULL,
                    target_id INTEGER NOT NULL,
                    filters TEXT NOT NULL,
                    options TEXT NOT NULL,
                    twitter_config TEXT,
                    is_enabled BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_group_id) REFERENCES groups (id),
                    FOREIGN KEY (target_id) REFERENCES groups (id)
                );
                
                -- 转发日志表
                CREATE TABLE IF NOT EXISTS forward_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_id INTEGER NOT NULL,
                    message_text TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (rule_id) REFERENCES forward_rules (id)
                );
                
                -- 统计数据表
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_id INTEGER,
                    date DATE NOT NULL,
                    total_messages INTEGER DEFAULT 0,
                    success_messages INTEGER DEFAULT 0,
                    avg_delay REAL DEFAULT 0,
                    FOREIGN KEY (rule_id) REFERENCES forward_rules (id)
                );
                
                -- 创建索引
                CREATE INDEX IF NOT EXISTS idx_accounts_type ON accounts(type);
                CREATE INDEX IF NOT EXISTS idx_groups_type ON groups(type);
                CREATE INDEX IF NOT EXISTS idx_forward_rules_enabled ON forward_rules(is_enabled);
                CREATE INDEX IF NOT EXISTS idx_forward_logs_rule_id ON forward_logs(rule_id);
                CREATE INDEX IF NOT EXISTS idx_forward_logs_created_at ON forward_logs(created_at);
                CREATE INDEX IF NOT EXISTS idx_statistics_date ON statistics(date);
            ''')
            
    # Account 相关方法
    def save_telegram_account(self, phone: str, api_id: str, api_hash: str) -> Account:
        """保存Telegram账号"""
        with self._get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO accounts (type, username, api_id, api_hash)
                VALUES (?, ?, ?, ?)
                RETURNING *
            ''', ('telegram', phone, api_id, api_hash))
            row = cursor.fetchone()
            return self._row_to_account(row)
            
    def save_twitter_account(self, username: str, api_key: str, api_secret: str,
                           access_token: str, access_secret: str) -> Account:
        """保存Twitter账号"""
        with self._get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO accounts (type, username, api_id, api_hash, 
                                   access_token, access_secret)
                VALUES (?, ?, ?, ?, ?, ?)
                RETURNING *
            ''', ('twitter', username, api_key, api_secret, 
                 access_token, access_secret))
            row = cursor.fetchone()
            return self._row_to_account(row)
            
    def get_accounts(self, account_type: str = None) -> List[Account]:
        """获取账号列表"""
        with self._get_connection() as conn:
            if account_type:
                cursor = conn.execute(
                    'SELECT * FROM accounts WHERE type = ?',
                    (account_type,)
                )
            else:
                cursor = conn.execute('SELECT * FROM accounts')
            return [self._row_to_account(row) for row in cursor.fetchall()]
            
    def delete_account(self, account_id: int):
        """删除账号"""
        with self._get_connection() as conn:
            conn.execute('DELETE FROM accounts WHERE id = ?', (account_id,))
            
    # Group 相关方法
    def save_group(self, group_id: str, title: str, type: str,
                  group_type: str, members_count: int = None) -> Group:
        """保存群组信息"""
        with self._get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO groups (group_id, title, type, group_type, members_count)
                VALUES (?, ?, ?, ?, ?)
                RETURNING *
            ''', (group_id, title, type, group_type, members_count))
            row = cursor.fetchone()
            return self._row_to_group(row)
            
    def get_groups(self, group_type: str = None) -> List[Group]:
        """获取群组列表"""
        with self._get_connection() as conn:
            if group_type:
                cursor = conn.execute(
                    'SELECT * FROM groups WHERE type = ?',
                    (group_type,)
                )
            else:
                cursor = conn.execute('SELECT * FROM groups')
            return [self._row_to_group(row) for row in cursor.fetchall()]
            
    def delete_group(self, group_id: int):
        """删除群组"""
        with self._get_connection() as conn:
            conn.execute('DELETE FROM groups WHERE id = ?', (group_id,))
            
    # ForwardRule 相关方法
    def save_rule(self, name: str, source_group_id: int, target_type: str,
                 target_id: int, filters: Dict, options: Dict,
                 twitter_config: Dict = None) -> ForwardRule:
        """保存转发规则"""
        with self._get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO forward_rules (name, source_group_id, target_type,
                                        target_id, filters, options, twitter_config)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                RETURNING *
            ''', (name, source_group_id, target_type, target_id,
                 json.dumps(filters), json.dumps(options),
                 json.dumps(twitter_config) if twitter_config else None))
            row = cursor.fetchone()
            return self._row_to_rule(row)
            
    def get_rules(self, enabled_only: bool = False) -> List[ForwardRule]:
        """获取转发规则列表"""
        with self._get_connection() as conn:
            if enabled_only:
                cursor = conn.execute(
                    'SELECT * FROM forward_rules WHERE is_enabled = 1'
                )
            else:
                cursor = conn.execute('SELECT * FROM forward_rules')
            return [self._row_to_rule(row) for row in cursor.fetchall()]
            
    def update_rule_status(self, rule_id: int, is_enabled: bool):
        """更新规则状态"""
        with self._get_connection() as conn:
            conn.execute('''
                UPDATE forward_rules 
                SET is_enabled = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (is_enabled, rule_id))
            
    def delete_rule(self, rule_id: int):
        """删除转发规则"""
        with self._get_connection() as conn:
            conn.execute('DELETE FROM forward_rules WHERE id = ?', (rule_id,))
            
    # ForwardLog 相关方法
    def add_forward_log(self, rule_id: int, message_text: str,
                       status: str, error_message: str = None) -> ForwardLog:
        """添加转发日志"""
        with self._get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO forward_logs (rule_id, message_text, status, error_message)
                VALUES (?, ?, ?, ?)
                RETURNING *
            ''', (rule_id, message_text, status, error_message))
            row = cursor.fetchone()
            return self._row_to_log(row)
            
    def get_forward_logs(self, rule_id: int = None,
                        start_date: datetime = None,
                        end_date: datetime = None) -> List[ForwardLog]:
        """获取转发日志"""
        with self._get_connection() as conn:
            query = ['SELECT * FROM forward_logs']
            params = []
            
            conditions = []
            if rule_id:
                conditions.append('rule_id = ?')
                params.append(rule_id)
            if start_date:
                conditions.append('created_at >= ?')
                params.append(start_date)
            if end_date:
                conditions.append('created_at <= ?')
                params.append(end_date)
                
            if conditions:
                query.append('WHERE ' + ' AND '.join(conditions))
                
            query.append('ORDER BY created_at DESC')
            cursor = conn.execute(' '.join(query), params)
            return [self._row_to_log(row) for row in cursor.fetchall()]
            
    # Statistics 相关方法
    def update_statistics(self, rule_id: int, date: datetime,
                         total_messages: int, success_messages: int,
                         avg_delay: float):
        """更新统计数据"""
        with self._get_connection() as conn:
            conn.execute('''
                INSERT INTO statistics 
                    (rule_id, date, total_messages, success_messages, avg_delay)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (rule_id, date) DO UPDATE SET
                    total_messages = excluded.total_messages,
                    success_messages = excluded.success_messages,
                    avg_delay = excluded.avg_delay
            ''', (rule_id, date, total_messages, success_messages, avg_delay))
            
    def get_statistics(self, rule_id: int = None,
                      start_date: datetime = None,
                      end_date: datetime = None) -> List[Dict]:
        """获取统计数据"""
        with self._get_connection() as conn:
            query = ['SELECT * FROM statistics']
            params = []
            
            conditions = []
            if rule_id:
                conditions.append('rule_id = ?')
                params.append(rule_id)
            if start_date:
                conditions.append('date >= ?')
                params.append(start_date)
            if end_date:
                conditions.append('date <= ?')
                params.append(end_date)
                
            if conditions:
                query.append('WHERE ' + ' AND '.join(conditions))
                
            query.append('ORDER BY date DESC')
            return [dict(row) for row in conn.execute(' '.join(query), params)]
            
    # 数据转换方法
    def _row_to_account(self, row: sqlite3.Row) -> Account:
        return Account(
            id=row['id'],
            type=row['type'],
            username=row['username'],
            api_id=row['api_id'],
            api_hash=row['api_hash'],
            access_token=row['access_token'],
            access_secret=row['access_secret'],
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )
        
    def _row_to_group(self, row: sqlite3.Row) -> Group:
        return Group(
            id=row['id'],
            group_id=row['group_id'],
            title=row['title'],
            type=row['type'],
            group_type=row['group_type'],
            members_count=row['members_count'],
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )
        
    def _row_to_rule(self, row: sqlite3.Row) -> ForwardRule:
        return ForwardRule(
            id=row['id'],
            name=row['name'],
            source_group_id=row['source_group_id'],
            target_type=row['target_type'],
            target_id=row['target_id'],
            filters=json.loads(row['filters']),
            options=json.loads(row['options']),
            twitter_config=json.loads(row['twitter_config']) if row['twitter_config'] else None,
            is_enabled=bool(row['is_enabled']),
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )
        
    def _row_to_log(self, row: sqlite3.Row) -> ForwardLog:
        return ForwardLog(
            id=row['id'],
            rule_id=row['rule_id'],
            message_text=row['message_text'],
            status=row['status'],
            error_message=row['error_message'],
            created_at=datetime.fromisoformat(row['created_at'])
        )
        
    # 数据库备份和恢复
    def backup_database(self, backup_path: str):
        """备份数据库"""
        with self._get_connection() as conn:
            backup = sqlite3.connect(backup_path)
            conn.backup(backup)
            backup.close()
            
    def restore_database(self, backup_path: str):
        """从备份恢复数据库"""
        backup = sqlite3.connect(backup_path)
        with self._get_connection() as conn:
            backup.backup(conn)
        backup.close()
        
    # 数据迁移
    def migrate_from_qsettings(self, settings):
        """从QSettings迁移数据到SQLite"""
        try:
            # 迁移Telegram账号
            settings.settings.beginGroup("telegram_accounts")
            for phone in settings.settings.childKeys():
                account_data = settings.settings.value(phone)
                self.save_telegram_account(
                    phone=phone,
                    api_id=account_data['api_id'],
                    api_hash=account_data['api_hash']
                )
            settings.settings.endGroup()
            
            # 迁移Twitter账号
            settings.settings.beginGroup("twitter_accounts")
            for username in settings.settings.childKeys():
                account_data = settings.settings.value(username)
                self.save_twitter_account(
                    username=username,
                    api_key=account_data['api_key'],
                    api_secret=account_data['api_secret'],
                    access_token=account_data['access_token'],
                    access_secret=account_data['access_secret']
                )
            settings.settings.endGroup()
            
            # 迁移群组信息
            settings.settings.beginGroup("source_groups")
            for group_id in settings.settings.childKeys():
                group_data = settings.settings.value(group_id)
                self.save_group(
                    group_id=group_id,
                    title=group_data['title'],
                    type='source',
                    group_type=group_data['type']
                )
            settings.settings.endGroup()
            
            settings.settings.beginGroup("target_groups")
            for group_id in settings.settings.childKeys():
                group_data = settings.settings.value(group_id)
                self.save_group(
                    group_id=group_id,
                    title=group_data['title'],
                    type='target',
                    group_type=group_data['type']
                )
            settings.settings.endGroup()
            
            # 迁移转发规则
            settings.settings.beginGroup("forward_rules")
            for rule_name in settings.settings.childKeys():
                rule_data = settings.settings.value(rule_name)
                # 需要先获取对应的group_id
                source_group = self.get_group_by_external_id(rule_data['source_group']['id'])
                target_group = self.get_group_by_external_id(rule_data['target']['id'])
                
                if source_group and target_group:
                    self.save_rule(
                        name=rule_name,
                        source_group_id=source_group.id,
                        target_type=rule_data['target_type'],
                        target_id=target_group.id,
                        filters=rule_data['filters'],
                        options=rule_data['options'],
                        twitter_config=rule_data.get('twitter_config')
                    )
            settings.settings.endGroup()
            
            return True
        except Exception as e:
            logger.error(f"数据迁移失败: {str(e)}")
            return False
            
    def get_rule_by_name(self, rule_name: str) -> Optional[ForwardRule]:
        """通过规则名称查找规则"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                'SELECT * FROM forward_rules WHERE name = ?',
                (rule_name,)
            )
            row = cursor.fetchone()
            return self._row_to_rule(row) if row else None
            
    def get_group_by_id(self, group_id: int) -> Optional[Group]:
        """通过ID查找群组"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                'SELECT * FROM groups WHERE id = ?',
                (group_id,)
            )
            row = cursor.fetchone()
            return self._row_to_group(row) if row else None
            
    def get_group_by_external_id(self, external_id: str) -> Optional[Group]:
        """通过外部ID查找群组"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                'SELECT * FROM groups WHERE group_id = ?',
                (external_id,)
            )
            row = cursor.fetchone()
            return self._row_to_group(row) if row else None

    def get_rule_by_id(self, rule_id: int) -> Optional[ForwardRule]:
        """通过ID查找规则"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                'SELECT * FROM forward_rules WHERE id = ?',
                (rule_id,)
            )
            row = cursor.fetchone()
            return self._row_to_rule(row) if row else None
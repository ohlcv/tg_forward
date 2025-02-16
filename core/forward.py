# core/forward.py

import asyncio
import logging
import re
from datetime import datetime
from typing import List, Dict, Optional
from telethon import events
from config.settings import settings
from .telegram import TelegramManager
from .twitter import TwitterManager

logger = logging.getLogger(__name__)

class ForwardEngine:
    def __init__(self):
        self.telegram = TelegramManager()
        self.twitter = TwitterManager()
        self.rules = []
        self.running = False
        self.stats = {}
        self.load_rules()
        
    def load_rules(self):
        """加载转发规则"""
        try:
            self.rules = settings.get_forward_rules()
            # 过滤出启用的规则
            self.rules = [r for r in self.rules if not r.get('disabled', False)]
            logger.info(f"已加载 {len(self.rules)} 条规则")
        except Exception as e:
            logger.error(f"加载规则失败: {str(e)}")
            
    async def start(self):
        """启动转发引擎"""
        if self.running:
            return
            
        try:
            self.running = True
            logger.info("转发引擎启动")
            
            # 获取所有源群组
            source_groups = set()
            for rule in self.rules:
                source_groups.add(rule['source_group']['id'])
            
            # 为每个Telegram账号注册消息处理器
            for phone, client in self.telegram.clients.items():
                if not client.is_connected():
                    await self.telegram.start_client(phone)
                    
                @client.on(events.NewMessage(chats=list(source_groups)))
                async def message_handler(event):
                    await self.handle_message(event)
                    
        except Exception as e:
            self.running = False
            logger.error(f"启动转发引擎失败: {str(e)}")
            raise
            
    async def stop(self):
        """停止转发引擎"""
        if not self.running:
            return
            
        try:
            self.running = False
            # 停止所有客户端
            await self.telegram.stop_all_clients()
            logger.info("转发引擎已停止")
        except Exception as e:
            logger.error(f"停止转发引擎失败: {str(e)}")
            
    async def handle_message(self, event):
        """处理新消息"""
        try:
            # 获取消息源群组ID
            source_id = str(event.chat_id)
            
            # 查找匹配的规则
            matching_rules = [
                r for r in self.rules 
                if r['source_group']['id'] == source_id
            ]
            
            for rule in matching_rules:
                await self.process_rule(rule, event)
                
        except Exception as e:
            logger.error(f"处理消息失败: {str(e)}")
            self.log_error(None, "消息处理", str(e))
            
    async def process_rule(self, rule: dict, event):
        """处理单个规则的转发"""
        try:
            # 检查消息是否匹配过滤规则
            if not self.check_filters(rule, event.message):
                return
                
            # 应用延迟
            if rule['options']['delay']['enabled']:
                await asyncio.sleep(rule['options']['delay']['value'])
                
            # 根据目标类型转发
            start_time = datetime.now()
            success = False
            
            if rule['target_type'] == "Telegram群组":
                success = await self.forward_to_telegram(rule, event.message)
            else:  # Twitter
                success = await self.forward_to_twitter(rule, event.message)
                
            # 更新统计
            self.update_stats(rule, success, (datetime.now() - start_time).total_seconds())
            
            # 记录日志
            self.log_forward(rule, event.message, success)
            
        except Exception as e:
            logger.error(f"处理规则失败: {str(e)}")
            self.log_error(rule['name'], "规则处理", str(e))
            
    def check_filters(self, rule: dict, message) -> bool:
        """检查消息是否匹配过滤规则"""
        try:
            text = message.text or message.caption or ""
            
            # 关键词过滤
            if rule['filters']['keywords']:
                if not any(k in text for k in rule['filters']['keywords']):
                    return False
                    
            # 正则过滤
            if rule['filters']['regex']:
                if not re.search(rule['filters']['regex'], text):
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"检查过滤规则失败: {str(e)}")
            return False
            
    async def forward_to_telegram(self, rule: dict, message) -> bool:
        """转发到Telegram群组"""
        try:
            target_id = int(rule['target']['id'])
            
            # 检查是否需要转发媒体
            if rule['options']['media_forward'] and message.media:
                await self.telegram.active_client.send_file(
                    target_id,
                    message.media,
                    caption=message.text
                )
            else:
                await self.telegram.active_client.send_message(
                    target_id,
                    message.text
                )
                
            return True
            
        except Exception as e:
            logger.error(f"转发到Telegram失败: {str(e)}")
            return False
            
    async def forward_to_twitter(self, rule: dict, message) -> bool:
        """转发到Twitter"""
        try:
            # 设置活动Twitter客户端
            if not self.twitter.set_active_client(rule['target']['id']):
                raise ValueError(f"Twitter账号 {rule['target']['id']} 未找到")
                
            # 处理文本
            text = message.text or message.caption or ""
            
            # 应用推文模板
            if rule['twitter_config']['template']:
                text = rule['twitter_config']['template'].format(
                    text=text,
                    link="https://t.me/" + str(message.chat_id)
                )
                
            # 添加话题标签
            if rule['twitter_config']['hashtags']:
                text = f"{text}\n\n{rule['twitter_config']['hashtags']}"
                
            # 处理媒体文件
            media_paths = []
            if rule['options']['media_forward'] and message.media:
                path = await self.telegram.active_client.download_media(message.media)
                if path:
                    media_paths.append(path)
                    
            # 发送推文
            success = await self.twitter.send_tweet(text, media_paths)
            
            # 清理临时文件
            for path in media_paths:
                self.twitter.cleanup_media(path)
                
            return success
            
        except Exception as e:
            logger.error(f"转发到Twitter失败: {str(e)}")
            return False
            
    def update_stats(self, rule: dict, success: bool, delay: float):
        """更新统计数据"""
        try:
            # 更新总计数
            total = settings.settings.value("stats/total_messages", 0)
            settings.settings.setValue("stats/total_messages", total + 1)
            
            if success:
                total_success = settings.settings.value("stats/total_success", 0)
                settings.settings.setValue("stats/total_success", total_success + 1)
                
            # 更新今日统计
            today = datetime.now().strftime("%Y-%m-%d")
            daily = settings.settings.value(f"stats/daily/{today}", 0)
            settings.settings.setValue(f"stats/daily/{today}", daily + 1)
            
            # 更新规则统计
            rule_stats = settings.settings.value(f"stats/rules/{rule['name']}", {})
            rule_stats['total'] = rule_stats.get('total', 0) + 1
            rule_stats['today'] = rule_stats.get('today', 0) + 1
            if success:
                rule_stats['success'] = rule_stats.get('success', 0) + 1
            rule_stats['success_rate'] = (rule_stats.get('success', 0) / rule_stats['total']) * 100
            
            # 更新平均延迟
            delays = rule_stats.get('delays', [])
            delays.append(delay)
            rule_stats['delays'] = delays[-100:]  # 只保留最近100条记录
            rule_stats['avg_delay'] = sum(delays) / len(delays)
            
            settings.settings.setValue(f"stats/rules/{rule['name']}", rule_stats)
            
        except Exception as e:
            logger.error(f"更新统计数据失败: {str(e)}")
            
    def log_forward(self, rule: dict, message, success: bool):
        """记录转发日志"""
        try:
            log_entry = {
                'time': datetime.now().isoformat(),
                'rule': rule['name'],
                'source': rule['source_group']['title'],
                'target': f"{rule['target_type']}: {rule['target']['title']}",
                'status': 'success' if success else 'failed',
                'message': message.text[:100] if message.text else ''
            }
            
            logs = settings.settings.value("logs/forwards", [])
            logs.append(log_entry)
            
            # 只保留最近1000条记录
            if len(logs) > 1000:
                logs = logs[-1000:]
                
            settings.settings.setValue("logs/forwards", logs)
            
        except Exception as e:
            logger.error(f"记录转发日志失败: {str(e)}")
            
    def log_error(self, rule_name: Optional[str], error_type: str, error_msg: str):
        """记录错误日志"""
        try:
            log_entry = {
                'time': datetime.now().isoformat(),
                'rule': rule_name,
                'type': error_type,
                'message': error_msg
            }
            
            logs = settings.settings.value("logs/errors", [])
            logs.append(log_entry)
            
            # 只保留最近500条错误记录
            if len(logs) > 500:
                logs = logs[-500:]
                
            settings.settings.setValue("logs/errors", logs)
            
        except Exception as e:
            logger.error(f"记录错误日志失败: {str(e)}")
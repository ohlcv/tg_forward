# ui/rules.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QComboBox, QSpinBox, QCheckBox,
    QGroupBox, QScrollArea
)
from PyQt6.QtCore import Qt
from config.settings import settings
import json
import logging

logger = logging.getLogger(__name__)

class RulesWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_rules()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 规则列表
        list_group = QGroupBox("现有规则")
        list_layout = QVBoxLayout(list_group)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["规则名称", "源群组", "目标", "状态", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        list_layout.addWidget(self.table)
        
        layout.addWidget(list_group)
        
        # 规则配置区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.create_rule_config())
        layout.addWidget(scroll)
        
    def create_rule_config(self):
        """创建规则配置部分"""
        config_group = QGroupBox("规则配置")
        config_layout = QVBoxLayout(config_group)
        
        # 基本信息
        form = QFormLayout()
        
        self.rule_name = QLineEdit()
        form.addRow("规则名称:", self.rule_name)
        
        # 源群组选择
        self.source_combo = QComboBox()
        self.update_source_groups()
        form.addRow("源群组:", self.source_combo)
        
        # 目标类型选择
        self.target_type = QComboBox()
        self.target_type.addItems(["Telegram群组", "Twitter"])
        self.target_type.currentTextChanged.connect(self.on_target_type_changed)
        form.addRow("目标类型:", self.target_type)
        
        # 目标选择（动态变化）
        self.target_stack = QWidget()
        self.target_layout = QVBoxLayout(self.target_stack)
        self.update_target_selection()
        form.addRow("目标:", self.target_stack)
        
        config_layout.addLayout(form)
        
        # 消息过滤配置
        filter_group = QGroupBox("消息过滤")
        filter_layout = QVBoxLayout(filter_group)
        
        self.keyword_filter = QTextEdit()
        self.keyword_filter.setPlaceholderText("每行一个关键词，留空表示不过滤")
        self.keyword_filter.setMaximumHeight(100)
        filter_layout.addWidget(QLabel("关键词过滤:"))
        filter_layout.addWidget(self.keyword_filter)
        
        self.regex_filter = QLineEdit()
        self.regex_filter.setPlaceholderText("正则表达式，留空表示不过滤")
        filter_layout.addWidget(QLabel("正则过滤:"))
        filter_layout.addWidget(self.regex_filter)
        
        config_layout.addWidget(filter_group)
        
        # Twitter 特殊配置
        self.twitter_config = QGroupBox("Twitter配置")
        self.twitter_config.setVisible(False)
        twitter_layout = QVBoxLayout(self.twitter_config)
        
        self.tweet_template = QTextEdit()
        self.tweet_template.setPlaceholderText("推文模板，使用{text}表示原文，{link}表示链接")
        self.tweet_template.setMaximumHeight(100)
        twitter_layout.addWidget(QLabel("推文模板:"))
        twitter_layout.addWidget(self.tweet_template)
        
        self.hashtags = QLineEdit()
        self.hashtags.setPlaceholderText("#标签1 #标签2")
        twitter_layout.addWidget(QLabel("话题标签:"))
        twitter_layout.addWidget(self.hashtags)
        
        config_layout.addWidget(self.twitter_config)
        
        # 转发选项
        options_group = QGroupBox("转发选项")
        options_layout = QVBoxLayout(options_group)
        
        delay_layout = QHBoxLayout()
        self.delay_enabled = QCheckBox("启用延迟")
        self.delay_value = QSpinBox()
        self.delay_value.setRange(1, 3600)
        self.delay_value.setValue(30)
        self.delay_value.setSuffix(" 秒")
        delay_layout.addWidget(self.delay_enabled)
        delay_layout.addWidget(self.delay_value)
        options_layout.addLayout(delay_layout)
        
        self.media_forward = QCheckBox("转发媒体文件")
        self.media_forward.setChecked(True)
        options_layout.addWidget(self.media_forward)
        
        config_layout.addWidget(options_group)
        
        # 按钮
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存规则")
        save_btn.clicked.connect(self.save_rule)
        btn_layout.addWidget(save_btn)
        
        test_btn = QPushButton("测试规则")
        test_btn.clicked.connect(self.test_rule)
        btn_layout.addWidget(test_btn)
        
        config_layout.addLayout(btn_layout)
        
        return config_group
        
    def update_source_groups(self):
        """更新源群组下拉列表"""
        self.source_combo.clear()
        settings.settings.beginGroup("source_groups")
        for group_id in settings.settings.childKeys():
            group_data = settings.settings.value(group_id)
            self.source_combo.addItem(group_data['title'], group_id)
        settings.settings.endGroup()
        
    def update_target_selection(self):
        """根据目标类型更新目标选择界面"""
        # 清除现有内容
        for i in reversed(range(self.target_layout.count())): 
            self.target_layout.itemAt(i).widget().setParent(None)
            
        if self.target_type.currentText() == "Telegram群组":
            # 添加Telegram群组选择
            self.target_combo = QComboBox()
            settings.settings.beginGroup("target_groups")
            for group_id in settings.settings.childKeys():
                group_data = settings.settings.value(group_id)
                self.target_combo.addItem(group_data['title'], group_id)
            settings.settings.endGroup()
            self.target_layout.addWidget(self.target_combo)
            
        else:
            # 添加Twitter账号选择
            self.target_combo = QComboBox()
            accounts = settings.get_twitter_accounts()
            for account in accounts:
                self.target_combo.addItem(account['username'])
            self.target_layout.addWidget(self.target_combo)
            
    def on_target_type_changed(self, target_type):
        """目标类型改变时的处理"""
        self.update_target_selection()
        self.twitter_config.setVisible(target_type == "Twitter")
        
    def save_rule(self):
        """保存规则"""
        try:
            rule_name = self.rule_name.text().strip()
            if not rule_name:
                raise ValueError("请输入规则名称")
                
            # 构建规则数据
            rule_data = {
                'source_group': {
                    'id': self.source_combo.currentData(),
                    'title': self.source_combo.currentText()
                },
                'target_type': self.target_type.currentText(),
                'target': {
                    'id': self.target_combo.currentData() if self.target_type.currentText() == "Telegram群组" else self.target_combo.currentText(),
                    'title': self.target_combo.currentText()
                },
                'filters': {
                    'keywords': [k.strip() for k in self.keyword_filter.toPlainText().split('\n') if k.strip()],
                    'regex': self.regex_filter.text().strip()
                },
                'twitter_config': {
                    'template': self.tweet_template.toPlainText().strip(),
                    'hashtags': self.hashtags.text().strip()
                } if self.target_type.currentText() == "Twitter" else None,
                'options': {
                    'delay': {
                        'enabled': self.delay_enabled.isChecked(),
                        'value': self.delay_value.value()
                    },
                    'media_forward': self.media_forward.isChecked()
                }
            }
            
            # 保存规则
            settings.save_forward_rule(rule_name, rule_data)
            
            # 刷新规则列表
            self.load_rules()
            
            # 清空表单
            self.rule_name.clear()
            self.keyword_filter.clear()
            self.regex_filter.clear()
            self.tweet_template.clear()
            self.hashtags.clear()
            
            QMessageBox.information(self, "成功", "规则保存成功")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存规则失败: {str(e)}")
            
    def load_rules(self):
        """加载规则列表"""
        rules = settings.get_forward_rules()
        self.table.setRowCount(len(rules))
        
        for i, rule in enumerate(rules):
            self.table.setItem(i, 0, QTableWidgetItem(rule['name']))
            self.table.setItem(i, 1, QTableWidgetItem(rule['source_group']['title']))
            self.table.setItem(i, 2, QTableWidgetItem(f"{rule['target_type']}: {rule['target']['title']}"))
            
            # 状态切换按钮
            status_btn = QPushButton("启用" if rule.get('disabled') else "禁用")
            status_btn.clicked.connect(lambda checked, r=rule: self.toggle_rule_status(r))
            self.table.setCellWidget(i, 3, status_btn)
            
            # 操作按钮
            op_widget = QWidget()
            op_layout = QHBoxLayout(op_widget)
            op_layout.setContentsMargins(0, 0, 0, 0)
            
            edit_btn = QPushButton("编辑")
            edit_btn.clicked.connect(lambda checked, r=rule: self.edit_rule(r))
            op_layout.addWidget(edit_btn)
            
            delete_btn = QPushButton("删除")
            delete_btn.clicked.connect(lambda checked, r=rule: self.delete_rule(r))
            op_layout.addWidget(delete_btn)
            
            self.table.setCellWidget(i, 4, op_widget)
            
    def toggle_rule_status(self, rule):
        """切换规则状态"""
        try:
            rule['disabled'] = not rule.get('disabled', False)
            settings.save_forward_rule(rule['name'], rule)
            self.load_rules()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"切换规则状态失败: {str(e)}")
            
    def edit_rule(self, rule):
        """编辑规则"""
        try:
            # 填充表单
            self.rule_name.setText(rule['name'])
            
            # 设置源群组
            index = self.source_combo.findData(rule['source_group']['id'])
            if index >= 0:
                self.source_combo.setCurrentIndex(index)
                
            # 设置目标类型和目标
            self.target_type.setCurrentText(rule['target_type'])
            index = self.target_combo.findText(rule['target']['title'])
            if index >= 0:
                self.target_combo.setCurrentIndex(index)
                
            # 设置过滤器
            self.keyword_filter.setPlainText('\n'.join(rule['filters']['keywords']))
            self.regex_filter.setText(rule['filters']['regex'])
            
            # 设置Twitter配置
            if rule['twitter_config']:
                self.tweet_template.setPlainText(rule['twitter_config']['template'])
                self.hashtags.setText(rule['twitter_config']['hashtags'])
                
            # 设置选项
            self.delay_enabled.setChecked(rule['options']['delay']['enabled'])
            self.delay_value.setValue(rule['options']['delay']['value'])
            self.media_forward.setChecked(rule['options']['media_forward'])
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载规则失败: {str(e)}")
            
    def delete_rule(self, rule):
        """删除规则"""
        reply = QMessageBox.question(self, "确认", 
                                   f"确定要删除规则 {rule['name']} 吗？",
                                   QMessageBox.StandardButton.Yes | 
                                   QMessageBox.StandardButton.No)
                                   
        if reply == QMessageBox.StandardButton.Yes:
            try:
                settings.settings.beginGroup("forward_rules")
                settings.settings.remove(rule['name'])
                settings.settings.endGroup()
                self.load_rules()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除规则失败: {str(e)}")
                
    def test_rule(self):
        """测试规则"""
        QMessageBox.information(self, "提示", "测试功能待实现")
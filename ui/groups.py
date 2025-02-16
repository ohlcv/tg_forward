# ui/groups.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QLineEdit, QFormLayout,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QComboBox, QProgressDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from config.settings import settings
from core.telegram import TelegramManager
import asyncio
import logging

logger = logging.getLogger(__name__)

class LoadGroupsWorker(QThread):
    """加载群组的工作线程"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, telegram_manager):
        super().__init__()
        self.telegram_manager = telegram_manager
        
    def run(self):
        try:
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            # 获取群组列表
            groups = loop.run_until_complete(self.telegram_manager.get_dialogs())
            self.finished.emit(groups)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            loop.close()

class GroupsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.telegram_manager = TelegramManager()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 账号选择
        account_layout = QHBoxLayout()
        self.account_combo = QComboBox()
        self.account_combo.addItems(self.telegram_manager.clients.keys())
        self.account_combo.currentTextChanged.connect(self.on_account_changed)
        account_layout.addWidget(QLabel("选择账号:"))
        account_layout.addWidget(self.account_combo)
        account_layout.addStretch()
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新群组列表")
        refresh_btn.clicked.connect(self.load_groups)
        account_layout.addWidget(refresh_btn)
        
        layout.addLayout(account_layout)
        
        # 创建标签页
        tab_widget = QTabWidget()
        tab_widget.addTab(SourceGroupsTab(self.telegram_manager), "源群组")
        tab_widget.addTab(TargetGroupsTab(self.telegram_manager), "目标群组")
        
        layout.addWidget(tab_widget)
        
    def on_account_changed(self, phone):
        """切换当前账号"""
        if phone:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.telegram_manager.start_client(phone))
            except Exception as e:
                QMessageBox.critical(self, "错误", f"切换账号失败: {str(e)}")
            finally:
                loop.close()

    def load_groups(self):
        """加载群组列表"""
        try:
            groups = self.telegram_manager.get_dialogs()
            self.update_groups(groups)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载群组失败: {str(e)}")
        
    def on_groups_loaded(self, groups):
        """群组加载完成的回调"""
        # 更新源群组和目标群组标签页
        for i in range(2):  # 0: 源群组, 1: 目标群组
            tab = self.findChild(QTabWidget).widget(i)
            if tab:
                tab.update_groups(groups)
                
    def on_load_error(self, error_msg):
        """加载失败的回调"""
        QMessageBox.critical(self, "错误", f"加载群组失败: {error_msg}")

class SourceGroupsTab(QWidget):
    def __init__(self, telegram_manager):
        super().__init__()
        self.telegram_manager = telegram_manager
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 群组列表
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "名称", "类型", "成员数", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        # 手动添加群组
        form_layout = QFormLayout()
        self.group_link_input = QLineEdit()
        form_layout.addRow("群组链接:", self.group_link_input)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("添加群组")
        add_btn.clicked.connect(self.add_group)
        btn_layout.addWidget(add_btn)
        
        layout.addLayout(form_layout)
        layout.addLayout(btn_layout)
        
    def update_groups(self, groups):
        """更新群组列表"""
        self.table.setRowCount(len(groups))
        for i, group in enumerate(groups):
            self.table.setItem(i, 0, QTableWidgetItem(str(group['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(group['title']))
            self.table.setItem(i, 2, QTableWidgetItem(group['type']))
            self.table.setItem(i, 3, QTableWidgetItem(str(group['members_count'])))
            
            # 添加操作按钮
            select_btn = QPushButton("选择为源")
            select_btn.clicked.connect(lambda checked, g=group: self.select_source(g))
            self.table.setCellWidget(i, 4, select_btn)
            
    def add_group(self):
        """手动添加群组"""
        link = self.group_link_input.text().strip()
        if not link:
            QMessageBox.warning(self, "警告", "请输入群组链接")
            return
            
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.telegram_manager.join_channel(link)
            )
            if result:
                QMessageBox.information(self, "成功", "成功加入群组")
                self.group_link_input.clear()
                # 重新加载群组列表
                self.parent().parent().parent().load_groups()
            else:
                QMessageBox.warning(self, "失败", "加入群组失败")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加入群组失败: {str(e)}")
        finally:
            loop.close()
            
    def select_source(self, group):
        """选择源群组"""
        try:
            settings.db.save_group(
                group_id=str(group['id']),
                title=group['title'],
                type='source',
                group_type=group['type'],
                members_count=group.get('members_count')
            )
            QMessageBox.information(self, "成功", f"已将 {group['title']} 设置为源群组")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"设置源群组失败: {str(e)}")

class TargetGroupsTab(QWidget):
    def __init__(self, telegram_manager):
        super().__init__()
        self.telegram_manager = telegram_manager
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 群组列表
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "名称", "类型", "成员数", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
    def update_groups(self, groups):
        """更新群组列表"""
        self.table.setRowCount(len(groups))
        for i, group in enumerate(groups):
            self.table.setItem(i, 0, QTableWidgetItem(str(group['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(group['title']))
            self.table.setItem(i, 2, QTableWidgetItem(group['type']))
            self.table.setItem(i, 3, QTableWidgetItem(str(group['members_count'])))
            
            # 添加操作按钮
            select_btn = QPushButton("选择为目标")
            select_btn.clicked.connect(lambda checked, g=group: self.select_target(g))
            self.table.setCellWidget(i, 4, select_btn)
            
    def select_target(self, group):
        """选择目标群组"""
        try:
            settings.db.save_group(
                group_id=str(group['id']),
                title=group['title'],
                type='target',
                group_type=group['type'],
                members_count=group.get('members_count')
            )
            QMessageBox.information(self, "成功", f"已将 {group['title']} 设置为目标群组")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"设置目标群组失败: {str(e)}")
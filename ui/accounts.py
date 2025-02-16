# ui/accounts.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QLineEdit, QFormLayout,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView
)
from PyQt6.QtCore import Qt
from config.settings import settings

class AccountsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 创建标签页
        tab_widget = QTabWidget()
        tab_widget.addTab(TelegramAccountTab(), "Telegram账号")
        tab_widget.addTab(TwitterAccountTab(), "Twitter账号")
        
        layout.addWidget(tab_widget)

class TelegramAccountTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_accounts()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 账号表格
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["手机号", "API ID", "API Hash", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        # 添加账号表单
        form_group = QWidget()
        form_layout = QFormLayout(form_group)
        
        self.phone_input = QLineEdit()
        self.api_id_input = QLineEdit()
        self.api_hash_input = QLineEdit()
        
        form_layout.addRow("手机号:", self.phone_input)
        form_layout.addRow("API ID:", self.api_id_input)
        form_layout.addRow("API Hash:", self.api_hash_input)
        
        # 添加按钮
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("添加账号")
        add_btn.clicked.connect(self.add_account)
        btn_layout.addWidget(add_btn)
        
        layout.addWidget(form_group)
        layout.addLayout(btn_layout)
        
    def load_accounts(self):
        """加载已保存的账号"""
        try:
            accounts = settings.get_telegram_accounts()
            self.table.setRowCount(len(accounts))
            
            for i, account in enumerate(accounts):
                self.table.setItem(i, 0, QTableWidgetItem(account['phone']))
                self.table.setItem(i, 1, QTableWidgetItem(account['api_id']))
                self.table.setItem(i, 2, QTableWidgetItem(account['api_hash']))
                
                # 删除按钮
                delete_btn = QPushButton("删除")
                delete_btn.clicked.connect(lambda checked, row=i: self.delete_account(row))
                self.table.setCellWidget(i, 3, delete_btn)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载账号失败: {str(e)}")
            
    def add_account(self):
        """添加新账号"""
        phone = self.phone_input.text().strip()
        api_id = self.api_id_input.text().strip()
        api_hash = self.api_hash_input.text().strip()
        
        if not all([phone, api_id, api_hash]):
            QMessageBox.warning(self, "错误", "请填写所有字段")
            return
            
        try:
            settings.save_telegram_account(phone, api_id, api_hash)
            self.load_accounts()
            
            # 清空输入框
            self.phone_input.clear()
            self.api_id_input.clear()
            self.api_hash_input.clear()
            
            QMessageBox.information(self, "成功", "账号添加成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加账号失败: {str(e)}")
            
    def delete_account(self, row):
        """删除账号"""
        phone = self.table.item(row, 0).text()
        reply = QMessageBox.question(
            self, "确认", 
            f"确定要删除账号 {phone} 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
                                   
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 获取账号并删除
                accounts = settings.get_telegram_accounts()
                for account in accounts:
                    if account['phone'] == phone:
                        settings.db.delete_account(account['id'])
                        break
                self.load_accounts()
                QMessageBox.information(self, "成功", "账号删除成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除账号失败: {str(e)}")

class TwitterAccountTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_accounts()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 账号表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "用户名", "API Key", "API Secret", 
            "Access Token", "Access Secret", "操作"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        # 添加账号表单
        form_group = QWidget()
        form_layout = QFormLayout(form_group)
        
        self.username_input = QLineEdit()
        self.api_key_input = QLineEdit()
        self.api_secret_input = QLineEdit()
        self.access_token_input = QLineEdit()
        self.access_secret_input = QLineEdit()
        
        form_layout.addRow("用户名:", self.username_input)
        form_layout.addRow("API Key:", self.api_key_input)
        form_layout.addRow("API Secret:", self.api_secret_input)
        form_layout.addRow("Access Token:", self.access_token_input)
        form_layout.addRow("Access Secret:", self.access_secret_input)
        
        # 添加按钮
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("添加账号")
        add_btn.clicked.connect(self.add_account)
        btn_layout.addWidget(add_btn)
        
        layout.addWidget(form_group)
        layout.addLayout(btn_layout)
        
    def load_accounts(self):
        """加载已保存的账号"""
        try:
            accounts = settings.get_twitter_accounts()
            self.table.setRowCount(len(accounts))
            
            for i, account in enumerate(accounts):
                self.table.setItem(i, 0, QTableWidgetItem(account['username']))
                self.table.setItem(i, 1, QTableWidgetItem(account['api_key']))
                self.table.setItem(i, 2, QTableWidgetItem(account['api_secret']))
                self.table.setItem(i, 3, QTableWidgetItem(account['access_token']))
                self.table.setItem(i, 4, QTableWidgetItem(account['access_secret']))
                
                # 删除按钮
                delete_btn = QPushButton("删除")
                delete_btn.clicked.connect(lambda checked, row=i: self.delete_account(row))
                self.table.setCellWidget(i, 5, delete_btn)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载账号失败: {str(e)}")
            
    def add_account(self):
        """添加新账号"""
        username = self.username_input.text().strip()
        api_key = self.api_key_input.text().strip()
        api_secret = self.api_secret_input.text().strip()
        access_token = self.access_token_input.text().strip()
        access_secret = self.access_secret_input.text().strip()
        
        if not all([username, api_key, api_secret, access_token, access_secret]):
            QMessageBox.warning(self, "错误", "请填写所有字段")
            return
            
        try:
            settings.save_twitter_account(
                username, api_key, api_secret,
                access_token, access_secret
            )
            self.load_accounts()
            
            # 清空输入框
            self.username_input.clear()
            self.api_key_input.clear()
            self.api_secret_input.clear()
            self.access_token_input.clear()
            self.access_secret_input.clear()
            
            QMessageBox.information(self, "成功", "账号添加成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加账号失败: {str(e)}")
            
    def delete_account(self, row):
        """删除账号"""
        username = self.table.item(row, 0).text()
        reply = QMessageBox.question(
            self, "确认", 
            f"确定要删除账号 {username} 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
                                   
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 获取账号并删除
                accounts = settings.get_twitter_accounts()
                for account in accounts:
                    if account['username'] == username:
                        settings.db.delete_account(account['id'])
                        break
                self.load_accounts()
                QMessageBox.information(self, "成功", "账号删除成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除账号失败: {str(e)}")
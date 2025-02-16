from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFont

from .accounts import AccountsWidget
from .groups import GroupsWidget
from .rules import RulesWidget
from .statistics import StatisticsWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Telegram 消息转发")
        self.setMinimumSize(1000, 600)
        
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建左侧导航栏
        self.create_sidebar()
        main_layout.addWidget(self.sidebar_frame)
        
        # 创建右侧内容区
        self.create_content_area()
        main_layout.addWidget(self.content_area)
        
        # 设置布局比例
        main_layout.setStretch(0, 1)  # 侧边栏占比
        main_layout.setStretch(1, 4)  # 内容区占比
        
        # 初始化显示账号管理页面
        self.show_page(0)
        
    def create_sidebar(self):
        """创建左侧导航栏"""
        self.sidebar_frame = QFrame()
        self.sidebar_frame.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                color: white;
            }
            QPushButton {
                text-align: left;
                padding: 10px;
                border: none;
                color: white;
                background-color: transparent;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
        """)
        
        sidebar_layout = QVBoxLayout(self.sidebar_frame)
        sidebar_layout.setSpacing(0)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Logo区域
        logo_label = QLabel("消息转发器")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("padding: 20px; font-size: 18px; font-weight: bold;")
        sidebar_layout.addWidget(logo_label)
        
        # 导航按钮
        self.nav_buttons = []
        nav_items = [
            ("账号管理", "icons/accounts.png"),
            ("群组管理", "icons/groups.png"),
            ("规则配置", "icons/rules.png"),
            ("数据统计", "icons/stats.png"),
        ]
        
        for i, (text, icon) in enumerate(nav_items):
            btn = QPushButton(text)
            if icon:
                btn.setIcon(QIcon(icon))
            btn.setFixedHeight(50)
            btn.clicked.connect(lambda x, index=i: self.show_page(index))
            self.nav_buttons.append(btn)
            sidebar_layout.addWidget(btn)
            
        # 添加底部弹簧
        sidebar_layout.addStretch()
        
    def create_content_area(self):
        """创建右侧内容区"""
        self.content_area = QFrame()
        self.content_area.setStyleSheet("""
            QFrame {
                background-color: white;
            }
        """)
        
        content_layout = QVBoxLayout(self.content_area)
        
        # 创建堆叠窗口部件用于切换页面
        self.stack = QStackedWidget()
        
        # 添加各个页面
        self.stack.addWidget(AccountsWidget())
        self.stack.addWidget(GroupsWidget())
        self.stack.addWidget(RulesWidget())
        self.stack.addWidget(StatisticsWidget())
        
        content_layout.addWidget(self.stack)
        
    def show_page(self, index):
        """切换显示页面"""
        # 更新按钮状态
        for i, btn in enumerate(self.nav_buttons):
            if i == index:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2980b9;
                        color: white;
                        text-align: left;
                        padding: 10px;
                        border: none;
                    }
                """)
            else:
                btn.setStyleSheet("")
        
        # 切换页面
        self.stack.setCurrentIndex(index)
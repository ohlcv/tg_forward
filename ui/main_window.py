# ui/main_window.py

from qtpy.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame, QApplication, QMessageBox
)
from qtpy.QtCore import Qt
from qt_material import apply_stylesheet

from .accounts import AccountsWidget
from .groups import GroupsWidget
from .rules import RulesWidget
from .statistics import StatisticsWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Telegram 消息转发")
        self.setMinimumSize(1200, 800)
        
        # 设置应用主题
        self.setup_theme()
        
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

    def setup_theme(self):
        """设置应用程序主题"""
        try:
            extra = {
                'danger': '#dc3545',
                'warning': '#ffc107',
                'success': '#17a2b8',
                'font_family': 'Roboto',
                'density_scale': '0'
            }
            apply_stylesheet(QApplication.instance(), theme='light_cyan.xml', extra=extra)
            # print("✅ qt-material 主题加载成功")
        except Exception as e:
            pass
            # print(f"❌ qt-material 主题加载失败: {str(e)}")
        
    def create_sidebar(self):
        """创建左侧导航栏"""
        self.sidebar_frame = QFrame()
        
        sidebar_layout = QVBoxLayout(self.sidebar_frame)
        sidebar_layout.setSpacing(8)
        sidebar_layout.setContentsMargins(12, 20, 12, 20)
        
        # Logo区域
        logo_label = QLabel("消息转发器")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            padding: 16px;
        """)
        sidebar_layout.addWidget(logo_label)
        
        # 导航按钮
        self.nav_buttons = []
        nav_items = [
            ("账号管理", "账号设置与管理"),
            ("群组管理", "管理转发群组"),
            ("规则配置", "设置转发规则"),
            ("数据统计", "查看转发数据"),
        ]
        
        for i, (text, tooltip) in enumerate(nav_items):
            btn = QPushButton(text)
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            btn.setFixedHeight(40)
            btn.clicked.connect(lambda x, index=i: self.show_page(index))
            self.nav_buttons.append(btn)
            sidebar_layout.addWidget(btn)
            
        # 添加底部弹簧
        sidebar_layout.addStretch()
        
    def create_content_area(self):
        """创建右侧内容区"""
        self.content_area = QFrame()
        
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
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
            btn.setChecked(i == index)
            
        # 切换页面
        self.stack.setCurrentIndex(index)
        
    def closeEvent(self, event):
        """弹出确认对话框询问用户是否关闭程序"""
        reply = QMessageBox.question(
            self,
            "退出确认",
            "你确定要退出程序吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

# ui/widgets/date_picker.py

from PyQt6.QtWidgets import (
    QWidget, QLineEdit, QPushButton, QCalendarWidget,
    QVBoxLayout, QHBoxLayout
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon
import os

class DatePicker(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建日期显示框
        self.date_edit = QLineEdit()
        self.date_edit.setReadOnly(True)
        self.date_edit.setMinimumWidth(120)  # 设置最小宽度
        self.date_edit.setStyleSheet("""
            QLineEdit {
                padding: 5px 10px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: white;
            }
        """)
        
        # 创建日期选择按钮
        self.calendar_btn = QPushButton()
        self.calendar_btn.setFixedSize(30, 30)
        self.calendar_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.calendar_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #ccc;
                border-radius: 4px;
                margin-left: 5px;
                background: white;
                padding: 5px;
            }
            QPushButton:hover {
                background: #f0f0f0;
            }
        """)
        
        # 设置日历图标
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'calendar.png')
        if os.path.exists(icon_path):
            self.calendar_btn.setIcon(QIcon(icon_path))
        else:
            self.calendar_btn.setText("📅")  # 使用 Emoji 作为备选
        
        # 创建日历控件
        self.calendar = QCalendarWidget(self)
        self.calendar.setWindowFlags(Qt.WindowType.Popup)
        self.calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QCalendarWidget QToolButton {
                color: black;
                padding: 5px;
                border: none;
            }
            QCalendarWidget QMenu {
                width: 150px;
                left: 20px;
                color: black;
            }
            QCalendarWidget QSpinBox {
                width: 60px;
                color: black;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: black;
                selection-background-color: #3498db;
                selection-color: white;
            }
            QCalendarWidget QAbstractItemView:disabled {
                color: #808080;
            }
        """)
        
        # 连接信号
        self.calendar_btn.clicked.connect(self.show_calendar)
        self.calendar.clicked.connect(self.date_selected)
        
        # 添加到布局
        layout.addWidget(self.date_edit)
        layout.addWidget(self.calendar_btn)
        
        # 设置默认日期
        self.set_date(QDate.currentDate())
        
    def show_calendar(self):
        """显示日历控件"""
        pos = self.calendar_btn.mapToGlobal(self.calendar_btn.rect().bottomRight())
        self.calendar.move(pos.x() - self.calendar.width() + 30, pos.y() + 2)
        self.calendar.show()
        
    def date_selected(self, date):
        """日期被选择"""
        self.set_date(date)
        self.calendar.hide()
        
    def set_date(self, date):
        """设置日期"""
        self.date_edit.setText(date.toString("yyyy-MM-dd"))
        
    def get_date(self):
        """获取选择的日期"""
        return QDate.fromString(self.date_edit.text(), "yyyy-MM-dd")
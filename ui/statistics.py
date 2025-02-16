# ui/statistics.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QFrame, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QDateEdit
)
from PyQt6.QtCore import Qt, QTimer, QDate
from PyQt6.QtGui import QColor
import logging
from datetime import datetime, timedelta
from config.settings import settings

logger = logging.getLogger(__name__)

class StatCard(QFrame):
    """统计卡片组件"""
    def __init__(self, title: str, value: str, color: str = "#3498db"):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 8px;
                padding: 10px;
                color: white;
            }}
            QLabel {{
                color: white;
            }}
        """)
        
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; opacity: 0.9;")
        layout.addWidget(title_label)
        
        # 数值
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(self.value_label)
        
    def update_value(self, value: str):
        """更新数值"""
        self.value_label.setText(value)

class StatisticsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.start_auto_refresh()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 顶部统计卡片
        cards_layout = QHBoxLayout()
        
        self.total_messages = StatCard("总转发消息", "0", "#3498db")
        cards_layout.addWidget(self.total_messages)
        
        self.today_messages = StatCard("今日转发", "0", "#2ecc71")
        cards_layout.addWidget(self.today_messages)
        
        self.success_rate = StatCard("成功率", "0%", "#e74c3c")
        cards_layout.addWidget(self.success_rate)
        
        self.active_rules = StatCard("活动规则", "0", "#9b59b6")
        cards_layout.addWidget(self.active_rules)
        
        layout.addLayout(cards_layout)
        
        # 标签页
        tab_widget = QTabWidget()
        
        # 转发记录标签页
        tab_widget.addTab(ForwardLogsTab(), "转发记录")
        
        # 规则统计标签页
        tab_widget.addTab(RuleStatsTab(), "规则统计")
        
        # 错误日志标签页
        tab_widget.addTab(ErrorLogsTab(), "错误日志")
        
        layout.addWidget(tab_widget)
        
        # 底部工具栏
        toolbar = QHBoxLayout()
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh_stats)
        toolbar.addWidget(refresh_btn)
        
        export_btn = QPushButton("导出数据")
        export_btn.clicked.connect(self.export_data)
        toolbar.addWidget(export_btn)
        
        toolbar.addStretch()
        
        self.status_label = QLabel("最后更新: 从未")
        toolbar.addWidget(self.status_label)
        
        layout.addLayout(toolbar)
        
    def start_auto_refresh(self):
        """启动自动刷新"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_stats)
        self.timer.start(30000)  # 30秒刷新一次
        
    def refresh_stats(self):
        """刷新统计数据"""
        try:
            # 更新总转发消息数
            total = settings.settings.value("stats/total_messages", 0)
            self.total_messages.update_value(str(total))
            
            # 更新今日转发数
            today = settings.settings.value(f"stats/daily/{QDate.currentDate().toString('yyyy-MM-dd')}", 0)
            self.today_messages.update_value(str(today))
            
            # 更新成功率
            total_success = settings.settings.value("stats/total_success", 0)
            if total > 0:
                success_rate = (total_success / total) * 100
                self.success_rate.update_value(f"{success_rate:.1f}%")
            
            # 更新活动规则数
            rules = settings.get_forward_rules()
            active_rules = sum(1 for r in rules if not r.get('disabled', False))
            self.active_rules.update_value(str(active_rules))
            
            # 更新最后更新时间
            self.status_label.setText(f"最后更新: {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"刷新统计数据失败: {str(e)}")
            
    def export_data(self):
        """导出统计数据"""
        # TODO: 实现数据导出功能
        pass

class ForwardLogsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_logs()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 筛选工具栏
        filter_layout = QHBoxLayout()
        
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-7))
        filter_layout.addWidget(QLabel("开始日期:"))
        filter_layout.addWidget(self.date_from)
        
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        filter_layout.addWidget(QLabel("结束日期:"))
        filter_layout.addWidget(self.date_to)
        
        self.rule_combo = QComboBox()
        self.rule_combo.addItem("所有规则")
        rules = settings.get_forward_rules()
        for rule in rules:
            self.rule_combo.addItem(rule['name'])
        filter_layout.addWidget(QLabel("规则:"))
        filter_layout.addWidget(self.rule_combo)
        
        filter_btn = QPushButton("筛选")
        filter_btn.clicked.connect(self.load_logs)
        filter_layout.addWidget(filter_btn)
        
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # 日志表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "时间", "规则", "源群组", "目标", "状态", "消息内容"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)
        
    def load_logs(self):
        """加载转发日志"""
        try:
            # TODO: 实现日志加载逻辑
            pass
        except Exception as e:
            logger.error(f"加载转发日志失败: {str(e)}")

class RuleStatsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_stats()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 规则统计表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "规则名称", "总转发数", "今日转发", "成功率", "平均延迟", "状态"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
    def load_stats(self):
        """加载规则统计"""
        try:
            rules = settings.get_forward_rules()
            self.table.setRowCount(len(rules))
            
            for i, rule in enumerate(rules):
                self.table.setItem(i, 0, QTableWidgetItem(rule['name']))
                
                # 获取规则统计数据
                stats = settings.settings.value(f"stats/rules/{rule['name']}", {})
                
                self.table.setItem(i, 1, QTableWidgetItem(str(stats.get('total', 0))))
                self.table.setItem(i, 2, QTableWidgetItem(str(stats.get('today', 0))))
                
                success_rate = stats.get('success_rate', 0)
                rate_item = QTableWidgetItem(f"{success_rate:.1f}%")
                if success_rate >= 90:
                    rate_item.setBackground(QColor("#2ecc71"))
                elif success_rate >= 70:
                    rate_item.setBackground(QColor("#f1c40f"))
                else:
                    rate_item.setBackground(QColor("#e74c3c"))
                self.table.setItem(i, 3, rate_item)
                
                self.table.setItem(i, 4, QTableWidgetItem(f"{stats.get('avg_delay', 0):.1f}秒"))
                
                status = "启用" if not rule.get('disabled') else "禁用"
                self.table.setItem(i, 5, QTableWidgetItem(status))
                
        except Exception as e:
            logger.error(f"加载规则统计失败: {str(e)}")

class ErrorLogsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_errors()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 错误日志表格
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "时间", "规则", "错误类型", "错误信息"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)
        
    def load_errors(self):
        """加载错误日志"""
        try:
            # TODO: 实现错误日志加载逻辑
            pass
        except Exception as e:
            logger.error(f"加载错误日志失败: {str(e)}")
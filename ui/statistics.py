# ui/statistics.py

from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QFrame, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QMessageBox
)
from qtpy.QtCore import Qt, QTimer, QDate
from qtpy.QtGui import QColor
import logging
from datetime import datetime, timedelta
from config.settings import settings
from ui.widgets.date_picker import DatePicker

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
            # 获取总转发消息数
            total_logs = settings.db.get_forward_logs()
            self.total_messages.update_value(str(len(total_logs)))
            
            # 计算今日转发数
            today = datetime.now().strftime('%Y-%m-%d')
            today_logs = settings.db.get_forward_logs(
                start_date=today,
                end_date=today
            )
            self.today_messages.update_value(str(len(today_logs)))
            
            # 计算成功率
            success_logs = [log for log in total_logs if log.status == 'success']
            if total_logs:
                success_rate = (len(success_logs) / len(total_logs)) * 100
                self.success_rate.update_value(f"{success_rate:.1f}%")
            
            # 获取活动规则数
            active_rules = settings.db.get_rules(enabled_only=True)
            self.active_rules.update_value(str(len(active_rules)))
            
            # 更新最后更新时间
            self.status_label.setText(f"最后更新: {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"刷新统计数据失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"刷新统计数据失败: {str(e)}")
            
    def export_data(self):
        """导出统计数据"""
        # TODO: 实现数据导出功能
        QMessageBox.information(self, "提示", "导出功能待实现")

class ForwardLogsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_logs()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 筛选工具栏
        filter_layout = QHBoxLayout()
        
        # 使用新的日期选择器
        date_range = QHBoxLayout()
        date_range.setSpacing(10)
        
        self.date_from = DatePicker()
        self.date_from.set_date(QDate.currentDate().addDays(-7))
        date_label = QLabel("日期范围:")
        date_label.setStyleSheet("margin-right: 5px;")
        date_range.addWidget(date_label)
        date_range.addWidget(self.date_from)
        
        date_range.addWidget(QLabel("至"))
        
        self.date_to = DatePicker()
        self.date_to.set_date(QDate.currentDate())
        date_range.addWidget(self.date_to)
        
        filter_layout.addLayout(date_range)
        
        # 规则选择下拉框
        rule_layout = QHBoxLayout()
        rule_layout.setSpacing(5)
        rule_label = QLabel("规则:")
        rule_label.setStyleSheet("margin-left: 15px;")
        rule_layout.addWidget(rule_label)
        
        self.rule_combo = QComboBox()
        # self.rule_combo.setStyleSheet("""
        #     QComboBox {
        #         padding: 5px 10px;
        #         border: 1px solid #ccc;
        #         border-radius: 4px;
        #         background: white;
        #         min-width: 150px;
        #     }
        #     QComboBox::drop-down {
        #         border: none;
        #     }
        #     QComboBox::down-arrow {
        #         image: url(assets/dropdown.png);
        #         width: 12px;
        #         height: 12px;
        #     }
        # """)
        self.rule_combo.addItem("所有规则")
        rules = settings.get_forward_rules()
        for rule in rules:
            self.rule_combo.addItem(rule['name'])
        rule_layout.addWidget(self.rule_combo)
        
        filter_layout.addLayout(rule_layout)
        
        # 筛选按钮
        filter_btn = QPushButton("筛选")
        # filter_btn.setStyleSheet("""
        #     QPushButton {
        #         padding: 5px 15px;
        #         background-color: #3498db;
        #         color: white;
        #         border: none;
        #         border-radius: 4px;
        #         margin-left: 15px;
        #     }
        #     QPushButton:hover {
        #         background-color: #2980b9;
        #     }
        # """)
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
        # self.table.setStyleSheet("""
        #     QTableWidget {
        #         border: 1px solid #ccc;
        #         border-radius: 4px;
        #         background: white;
        #     }
        #     QTableWidget::item {
        #         padding: 5px;
        #     }
        #     QHeaderView::section {
        #         background-color: #f8f9fa;
        #         padding: 5px;
        #         border: none;
        #         border-bottom: 1px solid #dee2e6;
        #     }
        # """)
        layout.addWidget(self.table)

    def load_logs(self):
        """加载转发日志"""
        try:
            # 获取筛选条件
            start_date = self.date_from.get_date().toString("yyyy-MM-dd")
            end_date = self.date_to.get_date().toString("yyyy-MM-dd")
            rule_name = self.rule_combo.currentText()
            
            # 从数据库获取日志
            logs = []
            if rule_name == "所有规则":
                logs = settings.get_forward_logs(
                    start_date=start_date,
                    end_date=end_date
                )
            else:
                rule = settings.db.get_rule_by_name(rule_name)
                if rule:
                    logs = settings.get_forward_logs(
                        rule_id=rule.id,
                        start_date=start_date,
                        end_date=end_date
                    )
            
            # 更新表格
            self.table.setRowCount(len(logs))
            for i, log in enumerate(logs):
                # 时间
                time_item = QTableWidgetItem(log.created_at.strftime("%Y-%m-%d %H:%M:%S"))
                self.table.setItem(i, 0, time_item)
                
                # 获取规则信息
                rule = settings.db.get_rule_by_id(log.rule_id)
                if rule:
                    # 规则名
                    rule_item = QTableWidgetItem(rule.name)
                    self.table.setItem(i, 1, rule_item)
                    
                    # 获取源群组信息
                    source_group = settings.db.get_group_by_id(rule.source_group_id)
                    if source_group:
                        source_item = QTableWidgetItem(source_group.title)
                        self.table.setItem(i, 2, source_item)
                    
                    # 获取目标信息
                    target_group = settings.db.get_group_by_id(rule.target_id)
                    if target_group:
                        target_item = QTableWidgetItem(
                            f"{rule.target_type}: {target_group.title}"
                        )
                        self.table.setItem(i, 3, target_item)
                
                # 状态
                status_item = QTableWidgetItem(log.status)
                status_color = QColor("#28a745") if log.status == "success" else QColor("#dc3545")
                status_item.setForeground(status_color)
                self.table.setItem(i, 4, status_item)
                
                # 消息内容
                message_item = QTableWidgetItem(log.message_text[:100] + "..." if len(log.message_text) > 100 else log.message_text)
                if log.error_message:
                    message_item.setToolTip(f"错误信息: {log.error_message}")
                self.table.setItem(i, 5, message_item)
            
            # 调整列宽
            self.table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载转发日志失败: {str(e)}")

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
                # 获取规则的所有日志
                db_rule = settings.db.get_rule_by_name(rule['name'])
                if db_rule:
                    logs = settings.db.get_forward_logs(rule_id=db_rule.id)
                    
                    # 获取今日日志
                    today = datetime.now().strftime('%Y-%m-%d')
                    today_logs = settings.db.get_forward_logs(
                        rule_id=db_rule.id,
                        start_date=today,
                        end_date=today
                    )
                    
                    # 计算统计数据
                    total = len(logs)
                    today_count = len(today_logs)
                    success_count = len([log for log in logs if log.status == 'success'])
                    success_rate = (success_count / total * 100) if total > 0 else 0
                    
                    self.table.setItem(i, 0, QTableWidgetItem(rule['name']))
                    self.table.setItem(i, 1, QTableWidgetItem(str(total)))
                    self.table.setItem(i, 2, QTableWidgetItem(str(today_count)))
                    
                    rate_item = QTableWidgetItem(f"{success_rate:.1f}%")
                    if success_rate >= 90:
                        rate_item.setBackground(QColor("#2ecc71"))
                    elif success_rate >= 70:
                        rate_item.setBackground(QColor("#f1c40f"))
                    else:
                        rate_item.setBackground(QColor("#e74c3c"))
                    self.table.setItem(i, 3, rate_item)
                    
                    # TODO: 计算平均延迟
                    self.table.setItem(i, 4, QTableWidgetItem("N/A"))
                    
                    status = "启用" if not rule.get('disabled') else "禁用"
                    self.table.setItem(i, 5, QTableWidgetItem(status))
                    
        except Exception as e:
            logger.error(f"加载规则统计失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载规则统计失败: {str(e)}")

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
            # 获取所有失败的转发记录
            error_logs = settings.db.get_forward_logs()
            error_logs = [log for log in error_logs if log.status == 'failed']
            
            self.table.setRowCount(len(error_logs))
            for i, log in enumerate(error_logs):
                # 时间
                time_item = QTableWidgetItem(log.created_at.strftime("%Y-%m-%d %H:%M:%S"))
                self.table.setItem(i, 0, time_item)
                
                # 获取规则信息
                rule = settings.db.get_rule_by_id(log.rule_id)
                if rule:
                    rule_item = QTableWidgetItem(rule.name)
                    self.table.setItem(i, 1, rule_item)
                
                # 错误类型和信息
                error_msg = log.error_message or "未知错误"
                error_type = "转发失败"  # 可以根据错误信息进一步分类
                
                self.table.setItem(i, 2, QTableWidgetItem(error_type))
                self.table.setItem(i, 3, QTableWidgetItem(error_msg))
            
        except Exception as e:
            logger.error(f"加载错误日志失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载错误日志失败: {str(e)}")
# ui/system_tray.py

from qtpy.QtWidgets import QSystemTrayIcon, QMenu, QMessageBox
from qtpy.QtGui import QIcon
from qtpy.QtCore import Qt, QTimer
from core.forward import ForwardEngine
import asyncio
import logging

logger = logging.getLogger(__name__)

class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, main_window):
        super().__init__(parent=main_window)
        self.main_window = main_window
        self.forward_engine = ForwardEngine()
        self.running = False
        
        # 设置图标
        self.setIcon(QIcon("icons/app.png"))
        self.setToolTip("Telegram 消息转发")
        
        # 创建托盘菜单
        self.menu = QMenu()
        self.create_menu()
        self.setContextMenu(self.menu)
        
        # 设置托盘图标双击事件
        self.activated.connect(self.on_tray_activated)
        
        # 状态更新定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(10000)  # 每10秒更新一次状态
        
    def create_menu(self):
        """创建托盘菜单"""
        # 显示/隐藏主窗口
        self.show_action = self.menu.addAction("显示主窗口")
        self.show_action.triggered.connect(self.toggle_window)
        
        self.menu.addSeparator()
        
        # 转发控制
        self.start_action = self.menu.addAction("开始转发")
        self.start_action.triggered.connect(self.start_forward)
        
        self.stop_action = self.menu.addAction("停止转发")
        self.stop_action.triggered.connect(self.stop_forward)
        self.stop_action.setEnabled(False)
        
        self.menu.addSeparator()
        
        # 统计子菜单
        stats_menu = self.menu.addMenu("统计信息")
        
        self.total_action = stats_menu.addAction("总转发: 0")
        self.total_action.setEnabled(False)
        
        self.today_action = stats_menu.addAction("今日转发: 0")
        self.today_action.setEnabled(False)
        
        self.success_action = stats_menu.addAction("成功率: 0%")
        self.success_action.setEnabled(False)
        
        self.menu.addSeparator()
        
        # 退出
        quit_action = self.menu.addAction("退出")
        quit_action.triggered.connect(self.quit_application)
        
    def toggle_window(self):
        """切换主窗口显示状态"""
        if self.main_window.isVisible():
            self.main_window.hide()
            self.show_action.setText("显示主窗口")
        else:
            self.main_window.show()
            self.main_window.activateWindow()
            self.show_action.setText("隐藏主窗口")
            
    def start_forward(self):
        """开始转发"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 启动转发引擎
            loop.run_until_complete(self.forward_engine.start())
            
            self.running = True
            self.start_action.setEnabled(False)
            self.stop_action.setEnabled(True)
            
            self.showMessage(
                "转发服务",
                "转发服务已启动",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            
            logger.info("转发服务已启动")
            
        except Exception as e:
            self.showMessage(
                "错误",
                f"启动转发服务失败: {str(e)}",
                QSystemTrayIcon.MessageIcon.Critical,
                2000
            )
            logger.error(f"启动转发服务失败: {e}")
            
    def stop_forward(self):
        """停止转发"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 停止转发引擎
            loop.run_until_complete(self.forward_engine.stop())
            
            self.running = False
            self.start_action.setEnabled(True)
            self.stop_action.setEnabled(False)
            
            self.showMessage(
                "转发服务",
                "转发服务已停止",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            
            logger.info("转发服务已停止")
            
        except Exception as e:
            self.showMessage(
                "错误",
                f"停止转发服务失败: {str(e)}",
                QSystemTrayIcon.MessageIcon.Critical,
                2000
            )
            logger.error(f"停止转发服务失败: {e}")
            
    def update_status(self):
        """更新状态信息"""
        if self.running:
            # 从settings中读取统计数据
            from config.settings import settings
            
            total = settings.settings.value("stats/total_messages", 0)
            total_success = settings.settings.value("stats/total_success", 0)
            success_rate = (total_success / total * 100) if total > 0 else 0
            
            # 更新菜单项
            self.total_action.setText(f"总转发: {total}")
            self.today_action.setText(f"今日转发: {total_success}")
            self.success_action.setText(f"成功率: {success_rate:.1f}%")
            
            # 更新工具提示
            self.setToolTip(f"转发服务运行中\n总转发: {total}\n今日转发: {total_success}")
            
    def on_tray_activated(self, reason):
        """托盘图标被激活时的处理"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.toggle_window()
            
    def quit_application(self):
        """退出应用程序"""
        if self.running:
            reply = QMessageBox.question(
                None,
                "确认退出",
                "转发服务正在运行，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
                
            # 停止转发服务
            self.stop_forward()
            
        # 退出应用
        self.main_window.close()
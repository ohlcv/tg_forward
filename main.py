import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication
from ui.main_window import MainWindow

def setup_application():
    """设置应用程序基本信息"""
    QCoreApplication.setOrganizationName("TGForward")
    QCoreApplication.setApplicationName("Telegram Forward")
    QCoreApplication.setApplicationVersion("1.0.0")

def main():
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    setup_application()
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
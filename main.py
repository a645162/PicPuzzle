# -*- coding: utf-8 -*-
"""
拼图工具主程序
"""
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    """主函数"""
    from main_window import MainWindow

    # 创建应用程序
    app = QApplication(sys.argv)

    # 设置应用程序属性
    app.setApplicationName("拼图工具")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("LiGroup")

    # # 设置高DPI支持
    # app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    # app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # 创建主窗口
    window = MainWindow()
    window.show()

    # 运行应用程序
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

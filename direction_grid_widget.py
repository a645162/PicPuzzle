# -*- coding: utf-8 -*-
"""
九宫格方向控制组件
"""
from PySide6.QtWidgets import QWidget, QGridLayout, QPushButton, QSizePolicy
from PySide6.QtCore import Qt


class DirectionGridWidget(QWidget):
    """九宫格方向控制组件，提供上下左右和中心5个按钮位置"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

        # 按钮引用
        self.top_button = None
        self.bottom_button = None
        self.left_button = None
        self.right_button = None
        self.center_button = None

    def setup_ui(self):
        """设置界面"""
        # 创建3x3网格布局
        layout = QGridLayout(self)
        layout.setSpacing(2)  # 紧凑间距
        layout.setContentsMargins(1, 1, 1, 1)  # 最小边距

        # 设置行列的最小尺寸和拉伸因子
        for i in range(3):
            layout.setRowMinimumHeight(i, 30)  # 减少最小行高
            layout.setColumnMinimumWidth(i, 40)  # 减少最小列宽
            layout.setRowStretch(i, 0)  # 不拉伸，保持最小尺寸
            layout.setColumnStretch(i, 0)  # 不拉伸，保持最小尺寸

        # 在所有位置创建占位组件，有效位置后面会被按钮替换
        for row in range(3):
            for col in range(3):
                placeholder = QWidget()
                placeholder.setMinimumSize(40, 30)
                placeholder.setMaximumSize(40, 30)  # 限制最大尺寸
                if self._is_valid_position(row, col):
                    # 有效位置设置背景色以便调试
                    placeholder.setStyleSheet(
                        "background-color: #f0f0f0; border: 1px solid #ccc;"
                    )
                layout.addWidget(placeholder, row, col)

        # 设置组件的尺寸策略
        from PySide6.QtWidgets import QSizePolicy

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def _is_valid_position(self, row, col):
        """检查是否是有效位置（上下左右中）"""
        # 上 (0,1), 左 (1,0), 中 (1,1), 右 (1,2), 下 (2,1)
        valid_positions = [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]
        return (row, col) in valid_positions

    def set_top_button(self, button: QPushButton):
        """设置上方按钮"""
        self._set_button_at_position(button, 0, 1)
        self.top_button = button

    def set_bottom_button(self, button: QPushButton):
        """设置下方按钮"""
        self._set_button_at_position(button, 2, 1)
        self.bottom_button = button

    def set_left_button(self, button: QPushButton):
        """设置左侧按钮"""
        self._set_button_at_position(button, 1, 0)
        self.left_button = button

    def set_right_button(self, button: QPushButton):
        """设置右侧按钮"""
        self._set_button_at_position(button, 1, 2)
        self.right_button = button

    def set_center_button(self, button: QPushButton):
        """设置中心按钮"""
        self._set_button_at_position(button, 1, 1)
        self.center_button = button

    def _set_button_at_position(self, button: QPushButton, row: int, col: int):
        """在指定位置设置按钮"""
        if not self._is_valid_position(row, col):
            raise ValueError(f"位置 ({row}, {col}) 不是有效位置")

        layout = self.layout()

        # 移除该位置的旧组件
        old_item = layout.itemAtPosition(row, col)
        if old_item:
            old_widget = old_item.widget()
            if old_widget:
                layout.removeWidget(old_widget)
                old_widget.setParent(None)

        # 设置按钮样式和大小
        button.setMinimumSize(40, 30)  # 设置最小尺寸
        button.setMaximumSize(40, 30)  # 限制最大尺寸，保持紧凑
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 固定尺寸策略

        # 添加按钮到布局
        layout.addWidget(button, row, col, Qt.AlignCenter)

    def get_buttons(self):
        """获取所有按钮的字典"""
        return {
            "top": self.top_button,
            "bottom": self.bottom_button,
            "left": self.left_button,
            "right": self.right_button,
            "center": self.center_button,
        }

    def set_all_buttons_enabled(self, enabled: bool):
        """启用或禁用所有按钮"""
        for button in self.get_buttons().values():
            if button:
                button.setEnabled(enabled)

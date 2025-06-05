# -*- coding: utf-8 -*-
"""
预览窗口
"""
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter
import config
from models import PuzzleModel, ImageOrientation
from puzzle_exporter import PuzzleExporter


class PreviewWindow(QDialog):
    """预览窗口"""

    def __init__(self, model: PuzzleModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.exporter = PuzzleExporter(model)
        self.setWindowTitle("拼图预览")
        self.setModal(False)

        # 设置窗口标志，支持最大化、最小化和调整大小
        self.setWindowFlags(
            Qt.Window  # 独立窗口
            | Qt.WindowMinMaxButtonsHint  # 最大化/最小化按钮
            | Qt.WindowCloseButtonHint  # 关闭按钮
            | Qt.WindowTitleHint  # 标题栏
        )

        # 设置初始大小和最小大小
        self.resize(800, 600)
        self.setMinimumSize(800, 600)

        self.setup_ui()
        self.update_preview()

    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)

        # 信息标签
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet(
            "font-size: 12px; padding: 5px; background-color: #f0f0f0; border: 1px solid #ccc;"
        )
        layout.addWidget(self.info_label)

        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(Qt.AlignCenter)
        scroll_area.setStyleSheet("border: 1px solid #ccc;")
        layout.addWidget(scroll_area)

        # 预览标签
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(200, 200)
        self.preview_label.setStyleSheet("background-color: white; margin: 10px;")
        scroll_area.setWidget(self.preview_label)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        refresh_button = QPushButton("刷新预览")
        refresh_button.setFixedHeight(35)
        refresh_button.clicked.connect(self.update_preview)
        button_layout.addWidget(refresh_button)

        # 添加弹簧，使按钮右对齐
        button_layout.addStretch()

        close_button = QPushButton("关闭")
        close_button.setFixedHeight(35)
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

        # 设置布局边距
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

    def update_preview(self):
        """更新预览"""
        try:
            preview_pixmap = self._create_preview_image()
            if preview_pixmap and not preview_pixmap.isNull():
                self.preview_label.setPixmap(preview_pixmap)

                # 更新信息
                size = preview_pixmap.size()
                valid_area = self.exporter.get_valid_area()
                if valid_area:
                    min_row, max_row, min_col, max_col = valid_area
                    area_info = (
                        f"有效区域: {max_row - min_row + 1}x{max_col - min_col + 1}"
                    )
                else:
                    area_info = "无图片"

                self.info_label.setText(
                    f"预览尺寸: {size.width()}x{size.height()} | {area_info}"
                )
            else:
                self.preview_label.setText("没有图片可预览")
                self.info_label.setText("请先在网格中放置图片")
        except Exception as e:
            self.preview_label.setText(f"预览失败: {e}")
            self.info_label.setText("预览生成失败")

    def _create_preview_image(self):
        """创建预览图片"""
        # 使用固定的预览尺寸
        cell_width = config.PREVIEW_CELL_WIDTH
        cell_height = config.PREVIEW_CELL_HEIGHT

        # 使用导出器生成预览图片，启用网格线显示
        return self.exporter.create_puzzle_image(
            cell_width, cell_height, bg_color=Qt.lightGray, draw_grid=True
        )

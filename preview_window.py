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


class PreviewWindow(QDialog):
    """预览窗口"""

    def __init__(self, model: PuzzleModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.setWindowTitle("拼图预览")
        self.setModal(False)
        self.resize(800, 600)
        self.setup_ui()
        self.update_preview()

    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)

        # 信息标签
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)

        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(Qt.AlignCenter)
        layout.addWidget(scroll_area)

        # 预览标签
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(200, 200)
        self.preview_label.setStyleSheet("border: 1px solid gray;")
        scroll_area.setWidget(self.preview_label)

        # 按钮
        button_layout = QHBoxLayout()

        refresh_button = QPushButton("刷新预览")
        refresh_button.clicked.connect(self.update_preview)
        button_layout.addWidget(refresh_button)

        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def update_preview(self):
        """更新预览"""
        try:
            preview_pixmap = self._create_preview_image()
            if preview_pixmap and not preview_pixmap.isNull():
                self.preview_label.setPixmap(preview_pixmap)

                # 更新信息
                size = preview_pixmap.size()
                valid_area = self._get_valid_area()
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

    def _get_valid_area(self):
        """计算有效区域（包含图片的区域）"""
        min_row, max_row = None, None
        min_col, max_col = None, None

        for row in range(self.model.rows):
            for col in range(self.model.cols):
                cell = self.model.get_cell(row, col)
                if cell and cell.is_occupied and cell.is_main_cell:
                    # 更新边界
                    if min_row is None or row < min_row:
                        min_row = row
                    if max_row is None or row > max_row:
                        max_row = row
                    if min_col is None or col < min_col:
                        min_col = col
                    if max_col is None or col > max_col:
                        max_col = col

                    # 对于竖屏图片，需要考虑它占用的额外行
                    if (
                        cell.image
                        and cell.image.orientation == ImageOrientation.VERTICAL
                    ):
                        bottom_row = row + config.VERTICAL_IMAGE_SPAN - 1
                        if max_row is None or bottom_row > max_row:
                            max_row = bottom_row

        # 如果没有找到图片，返回None
        if min_row is None:
            return None

        return min_row, max_row, min_col, max_col

    def _create_preview_image(self):
        """创建预览图片"""
        # 使用固定的预览尺寸
        cell_width = config.PREVIEW_CELL_WIDTH
        cell_height = config.PREVIEW_CELL_HEIGHT

        return self._create_puzzle_image(cell_width, cell_height)

    def _create_puzzle_image(self, cell_width: int, cell_height: int):
        """创建拼图图片（统一的图片生成函数）"""
        # 计算有效区域
        valid_area = self._get_valid_area()
        if valid_area is None:
            return None

        min_row, max_row, min_col, max_col = valid_area

        # 计算有效区域的尺寸
        valid_rows = max_row - min_row + 1
        valid_cols = max_col - min_col + 1

        # 计算间隔尺寸
        spacing = config.calculate_spacing(cell_height)

        # 计算有效区域的输出尺寸，考虑格子间的间隔
        # 宽度：格子数 * 格子宽度 + (格子数-1) * 间隔
        total_width = (
            cell_width * valid_cols + spacing * (valid_cols - 1)
            if valid_cols > 1
            else cell_width * valid_cols
        )
        # 高度：格子数 * 格子高度 + (格子数-1) * 间隔
        total_height = (
            cell_height * valid_rows + spacing * (valid_rows - 1)
            if valid_rows > 1
            else cell_height * valid_rows
        )

        # 创建输出图片
        output_pixmap = QPixmap(total_width, total_height)
        output_pixmap.fill(Qt.white)

        painter = QPainter(output_pixmap)
        try:
            # 只遍历有效区域
            for row in range(min_row, max_row + 1):
                for col in range(min_col, max_col + 1):
                    cell = self.model.get_cell(row, col)

                    if cell and cell.is_occupied and cell.image and cell.is_main_cell:
                        # 计算相对于有效区域的位置
                        relative_row = row - min_row
                        relative_col = col - min_col

                        # 计算目标位置，考虑间隔
                        # x位置：列数 * (格子宽度 + 间隔)
                        x = relative_col * (cell_width + spacing)
                        # y位置：行数 * (格子高度 + 间隔)
                        y = relative_row * (cell_height + spacing)

                        # 计算目标尺寸
                        if cell.image.orientation == ImageOrientation.VERTICAL:
                            # 竖屏图片：宽度 = 1个格子宽度，高度 = 3个格子高度 + 2个间隔
                            target_width = cell_width
                            target_height = cell_height * 3 + spacing * 2
                        else:
                            # 横屏图片：标准1个格子
                            target_width = cell_width
                            target_height = cell_height

                        # 加载并缩放图片
                        source_pixmap = QPixmap(str(cell.image.path))
                        if not source_pixmap.isNull():
                            # 缩放图片到目标尺寸，保持宽高比
                            scaled_pixmap = source_pixmap.scaled(
                                target_width,
                                target_height,
                                Qt.KeepAspectRatio,
                                Qt.SmoothTransformation,
                            )

                            # 居中绘制
                            draw_x = x + (target_width - scaled_pixmap.width()) // 2
                            draw_y = y + (target_height - scaled_pixmap.height()) // 2

                            painter.drawPixmap(draw_x, draw_y, scaled_pixmap)

        finally:
            painter.end()

        return output_pixmap

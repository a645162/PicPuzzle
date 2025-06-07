# -*- coding: utf-8 -*-
"""
网格预览组件
"""
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRect, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QMouseEvent, QFont
from models import PuzzleModel, ImageOrientation

# ========== 常量配置 ==========

# 网格预览组件配置
GRID_MIN_WIDTH = 400
GRID_MIN_HEIGHT = 300
GRID_BACKGROUND_COLOR = "white"
GRID_BORDER_COLOR = "#ccc"

# 颜色配置
# 横屏图片颜色
HORIZONTAL_IMAGE_COLOR = QColor(60, 179, 113, 150)  # 海绿色
HORIZONTAL_IMAGE_TEXT_COLOR = QColor(255, 255, 255)

# 竖屏图片颜色
VERTICAL_IMAGE_MAIN_COLOR = QColor(70, 130, 180, 150)  # 钢蓝色（主格子）
VERTICAL_IMAGE_SUB_COLOR = QColor(135, 206, 235, 100)  # 天空蓝色（占位格子）
VERTICAL_IMAGE_TEXT_COLOR = QColor(255, 255, 255)

# 空闲格子颜色
EMPTY_CELL_COLOR = QColor(255, 255, 255)
OCCUPIED_FALLBACK_COLOR = QColor(200, 200, 200, 100)

# 网格线颜色
GRID_LINE_COLOR = QColor(200, 200, 200)
GRID_LINE_WIDTH = 1
GRID_OUTLINE_COLOR = QColor(150, 150, 150)

# 选中区域颜色
SELECTED_AREA_BORDER_COLOR = QColor(255, 0, 0)
SELECTED_AREA_FILL_COLOR = QColor(255, 0, 0, 50)
SELECTED_AREA_BORDER_WIDTH = 3

# 行号列号标注配置
ROW_COL_LABEL_COLOR = QColor(100, 100, 100)
ROW_COL_LABEL_BACKGROUND = QColor(240, 240, 240)
ROW_COL_LABEL_WIDTH = 25  # 行号/列号标注区域宽度
ROW_COL_LABEL_HEIGHT = 20  # 行号/列号标注区域高度
ROW_COL_FONT_SIZE = 9

# 文本配置
HORIZONTAL_IMAGE_MARKER = "H"
VERTICAL_IMAGE_MARKER = "V"

# ==============================


class GridPreviewWidget(QWidget):
    """网格预览部件，用于显示整个网格和选中区域，带有行号列号标注"""

    area_selected = Signal(int, int)  # 发送选中的区域信号 (row, col)

    def __init__(self, model: PuzzleModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.selected_rect = QRect()  # 当前选中的区域
        self.setStyleSheet(
            f"background-color: {GRID_BACKGROUND_COLOR}; border: 1px solid {GRID_BORDER_COLOR};"
        )
        self.setMinimumSize(
            GRID_MIN_WIDTH + ROW_COL_LABEL_WIDTH, 
            GRID_MIN_HEIGHT + ROW_COL_LABEL_HEIGHT
        )  # 设置最小尺寸，考虑行号列号区域

    def _get_grid_rect(self):
        """获取实际网格绘制区域（排除行号列号标注区域）"""
        return QRect(
            ROW_COL_LABEL_WIDTH,
            ROW_COL_LABEL_HEIGHT,
            self.width() - ROW_COL_LABEL_WIDTH,
            self.height() - ROW_COL_LABEL_HEIGHT
        )

    def paintEvent(self, event):
        """绘制网格和选中区域"""
        super().paintEvent(event)
        painter = QPainter(self)
        
        # 设置字体
        font = QFont()
        font.setPointSize(ROW_COL_FONT_SIZE)
        painter.setFont(font)

        # 获取实际网格区域
        grid_rect = self._get_grid_rect()
        
        # 计算每个单元格的大小
        cell_width = grid_rect.width() / self.model.cols
        cell_height = grid_rect.height() / self.model.rows

        # 绘制行号列号标注背景
        painter.setBrush(ROW_COL_LABEL_BACKGROUND)
        painter.setPen(QPen(GRID_OUTLINE_COLOR, GRID_LINE_WIDTH))
        
        # 左上角空白区域
        painter.drawRect(0, 0, ROW_COL_LABEL_WIDTH, ROW_COL_LABEL_HEIGHT)
        
        # 列号标注背景
        painter.drawRect(ROW_COL_LABEL_WIDTH, 0, grid_rect.width(), ROW_COL_LABEL_HEIGHT)
        
        # 行号标注背景
        painter.drawRect(0, ROW_COL_LABEL_HEIGHT, ROW_COL_LABEL_WIDTH, grid_rect.height())

        # 绘制列号
        painter.setPen(QPen(ROW_COL_LABEL_COLOR, 1))
        for col in range(self.model.cols):
            x = ROW_COL_LABEL_WIDTH + col * cell_width + cell_width / 2 - 5
            y = ROW_COL_LABEL_HEIGHT / 2 + 3
            painter.drawText(int(x), int(y), str(col))

        # 绘制行号
        for row in range(self.model.rows):
            x = ROW_COL_LABEL_WIDTH / 2 - 5
            y = ROW_COL_LABEL_HEIGHT + row * cell_height + cell_height / 2 + 3
            painter.drawText(int(x), int(y), str(row))

        # 绘制网格背景（区分已占用和空闲的格子，以及横屏和竖屏图片）
        for row in range(self.model.rows):
            for col in range(self.model.cols):
                cell = self.model.get_cell(row, col)
                x = grid_rect.x() + col * cell_width
                y = grid_rect.y() + row * cell_height

                if cell and cell.is_occupied and cell.image:
                    # 根据图片类型选择不同颜色
                    if cell.image.orientation == ImageOrientation.VERTICAL:
                        # 竖屏图片用蓝色系
                        if cell.is_main_cell:
                            painter.setBrush(VERTICAL_IMAGE_MAIN_COLOR)
                            # 在主格子上绘制"V"标记
                            painter.setPen(QPen(GRID_LINE_COLOR, GRID_LINE_WIDTH))
                            painter.drawRect(x, y, cell_width, cell_height)
                            painter.setPen(QPen(VERTICAL_IMAGE_TEXT_COLOR, 2))
                            painter.drawText(
                                int(x + cell_width // 2 - 5),
                                int(y + cell_height // 2 + 5),
                                VERTICAL_IMAGE_MARKER,
                            )
                        else:
                            painter.setBrush(VERTICAL_IMAGE_SUB_COLOR)
                            painter.setPen(QPen(GRID_LINE_COLOR, GRID_LINE_WIDTH))
                            painter.drawRect(x, y, cell_width, cell_height)
                    else:
                        # 横屏图片用绿色系
                        painter.setBrush(HORIZONTAL_IMAGE_COLOR)
                        painter.setPen(QPen(GRID_LINE_COLOR, GRID_LINE_WIDTH))
                        painter.drawRect(x, y, cell_width, cell_height)
                        # 在横屏图片格子上绘制"H"标记
                        painter.setPen(QPen(HORIZONTAL_IMAGE_TEXT_COLOR, 2))
                        painter.drawText(
                            int(x + cell_width // 2 - 5),
                            int(y + cell_height // 2 + 5),
                            HORIZONTAL_IMAGE_MARKER,
                        )
                elif cell and cell.is_occupied:
                    # 占用但没有图片信息的格子（应该不会出现，但为了安全）
                    painter.setBrush(OCCUPIED_FALLBACK_COLOR)
                    painter.setPen(QPen(GRID_LINE_COLOR, GRID_LINE_WIDTH))
                    painter.drawRect(x, y, cell_width, cell_height)
                else:
                    # 空闲格子用白色填充
                    painter.setBrush(EMPTY_CELL_COLOR)
                    painter.setPen(QPen(GRID_LINE_COLOR, GRID_LINE_WIDTH))
                    painter.drawRect(x, y, cell_width, cell_height)

        # 绘制网格线
        painter.setBrush(QColor(0, 0, 0, 0))  # 透明填充
        painter.setPen(QPen(GRID_OUTLINE_COLOR, GRID_LINE_WIDTH))
        
        # 绘制水平网格线
        for row in range(self.model.rows + 1):
            y = grid_rect.y() + row * cell_height
            painter.drawLine(grid_rect.x(), y, grid_rect.right(), y)

        # 绘制垂直网格线
        for col in range(self.model.cols + 1):
            x = grid_rect.x() + col * cell_width
            painter.drawLine(x, grid_rect.y(), x, grid_rect.bottom())

        # 绘制选中区域（如果存在）
        if not self.selected_rect.isNull():
            painter.setPen(QPen(SELECTED_AREA_BORDER_COLOR, SELECTED_AREA_BORDER_WIDTH))
            painter.setBrush(SELECTED_AREA_FILL_COLOR)
            # QRect的x()对应col，y()对应row
            x = grid_rect.x() + self.selected_rect.x() * cell_width
            y = grid_rect.y() + self.selected_rect.y() * cell_height
            width = self.selected_rect.width() * cell_width
            height = self.selected_rect.height() * cell_height
            painter.drawRect(x, y, width, height)

    def set_selected_area(self, rect: QRect):
        """设置选中区域并更新界面"""
        self.selected_rect = rect
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        """鼠标点击事件，选择单个格子"""
        if event.button() == Qt.LeftButton:
            # 获取实际网格区域
            grid_rect = self._get_grid_rect()
            
            # 检查点击是否在网格区域内
            if not grid_rect.contains(event.position().toPoint()):
                super().mousePressEvent(event)
                return

            # 计算点击的格子位置（相对于网格区域）
            click_x = event.position().x() - grid_rect.x()
            click_y = event.position().y() - grid_rect.y()
            
            cell_width = grid_rect.width() / self.model.cols
            cell_height = grid_rect.height() / self.model.rows

            col = int(click_x / cell_width)
            row = int(click_y / cell_height)

            # 确保坐标在有效范围内
            if 0 <= row < self.model.rows and 0 <= col < self.model.cols:
                # 设置为1x1的选择区域，使用(left, top, width, height)格式
                # 这里left=col, top=row
                new_rect = QRect(col, row, 1, 1)
                self.set_selected_area(new_rect)
                self.area_selected.emit(row, col)

        super().mousePressEvent(event)

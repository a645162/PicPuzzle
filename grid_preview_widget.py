# -*- coding: utf-8 -*-
"""
网格预览组件
"""
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRect, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QMouseEvent, QFont

from models import PuzzleModel, ImageOrientation

from config import AREA_SELECT_MAIN_POSITION

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

# 拖拽选择区域颜色
DRAG_SELECTION_BORDER_COLOR = QColor(0, 150, 255)
DRAG_SELECTION_FILL_COLOR = QColor(0, 150, 255, 30)
DRAG_SELECTION_BORDER_WIDTH = 2

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
    """网格预览部件，用于显示整个网格和选中区域，带有行号列号标注和拖拽选择功能"""

    area_selected = Signal(int, int)  # 发送选中的区域信号 (row, col)
    area_drag_selected = Signal(QRect)  # 发送拖拽选择的区域信号

    def __init__(self, model: PuzzleModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.selected_rect = QRect()  # 当前选中的区域

        # 拖拽选择相关状态
        self.is_dragging = False  # 是否正在拖拽选择
        self.drag_start_row = -1  # 拖拽起始行
        self.drag_start_col = -1  # 拖拽起始列
        self.drag_current_row = -1  # 拖拽当前行
        self.drag_current_col = -1  # 拖拽当前列

        self.setStyleSheet(
            f"background-color: {GRID_BACKGROUND_COLOR}; border: 1px solid {GRID_BORDER_COLOR};"
        )
        self.setMinimumSize(
            GRID_MIN_WIDTH + ROW_COL_LABEL_WIDTH, GRID_MIN_HEIGHT + ROW_COL_LABEL_HEIGHT
        )  # 设置最小尺寸，考虑行号列号区域

        # 启用鼠标跟踪，以便在拖拽时能接收到鼠标移动事件
        self.setMouseTracking(True)

    def _get_grid_rect(self):
        """获取实际网格绘制区域（排除行号列号标注区域）"""
        return QRect(
            ROW_COL_LABEL_WIDTH,
            ROW_COL_LABEL_HEIGHT,
            self.width() - ROW_COL_LABEL_WIDTH,
            self.height() - ROW_COL_LABEL_HEIGHT,
        )

    def _get_cell_from_position(self, x, y):
        """根据屏幕坐标获取对应的格子行列，返回(row, col)，如果超出范围返回(-1, -1)"""
        grid_rect = self._get_grid_rect()

        # 检查是否在网格区域内
        if not grid_rect.contains(int(x), int(y)):
            return -1, -1

        # 计算相对于网格区域的坐标
        relative_x = x - grid_rect.x()
        relative_y = y - grid_rect.y()

        cell_width = grid_rect.width() / self.model.cols
        cell_height = grid_rect.height() / self.model.rows

        col = int(relative_x / cell_width)
        row = int(relative_y / cell_height)

        # 确保坐标在有效范围内
        if 0 <= row < self.model.rows and 0 <= col < self.model.cols:
            return row, col
        else:
            return -1, -1

    def _get_drag_selection_rect(self):
        """获取当前拖拽选择的矩形区域（网格坐标）"""
        if not self.is_dragging:
            return QRect()

        # 计算矩形的左上角和右下角
        min_row = min(self.drag_start_row, self.drag_current_row)
        max_row = max(self.drag_start_row, self.drag_current_row)
        min_col = min(self.drag_start_col, self.drag_current_col)
        max_col = max(self.drag_start_col, self.drag_current_col)

        # 返回QRect(left, top, width, height) = QRect(col, row, width, height)
        return QRect(min_col, min_row, max_col - min_col + 1, max_row - min_row + 1)

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
        painter.drawRect(
            ROW_COL_LABEL_WIDTH, 0, grid_rect.width(), ROW_COL_LABEL_HEIGHT
        )

        # 行号标注背景
        painter.drawRect(
            0, ROW_COL_LABEL_HEIGHT, ROW_COL_LABEL_WIDTH, grid_rect.height()
        )

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

        # 绘制拖拽选择区域（如果正在拖拽）
        if self.is_dragging:
            drag_rect = self._get_drag_selection_rect()
            if not drag_rect.isNull():
                painter.setPen(
                    QPen(DRAG_SELECTION_BORDER_COLOR, DRAG_SELECTION_BORDER_WIDTH)
                )
                painter.setBrush(DRAG_SELECTION_FILL_COLOR)
                x = grid_rect.x() + drag_rect.x() * cell_width
                y = grid_rect.y() + drag_rect.y() * cell_height
                width = drag_rect.width() * cell_width
                height = drag_rect.height() * cell_height
                painter.drawRect(x, y, width, height)

        # 绘制确定的选中区域（如果存在且不在拖拽中）
        if not self.selected_rect.isNull() and not self.is_dragging:
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
        """鼠标按下事件，开始拖拽选择"""
        if event.button() == Qt.LeftButton:
            row, col = self._get_cell_from_position(
                event.position().x(), event.position().y()
            )

            if row >= 0 and col >= 0:  # 确保在有效的网格范围内
                # 开始拖拽选择
                self.is_dragging = True
                self.drag_start_row = row
                self.drag_start_col = col
                self.drag_current_row = row
                self.drag_current_col = col
                self.update()  # 立即更新显示

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件，更新拖拽选择区域"""
        if self.is_dragging:
            row, col = self._get_cell_from_position(
                event.position().x(), event.position().y()
            )

            if row >= 0 and col >= 0:  # 在有效范围内
                if row != self.drag_current_row or col != self.drag_current_col:
                    self.drag_current_row = row
                    self.drag_current_col = col
                    self.update()  # 更新显示

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件，完成拖拽选择"""
        if event.button() == Qt.LeftButton and self.is_dragging:
            # 完成拖拽选择
            drag_rect = self._get_drag_selection_rect()

            if not drag_rect.isNull():
                # 应用选择的主格子逻辑（如果启用）
                if AREA_SELECT_MAIN_POSITION:
                    # 对于单个格子的选择，获取主格子位置
                    if drag_rect.width() == 1 and drag_rect.height() == 1:
                        main_row, main_col = self.model.get_main_cell_position(
                            drag_rect.y(), drag_rect.x()
                        )
                        final_rect = QRect(main_col, main_row, 1, 1)
                    else:
                        final_rect = drag_rect
                else:
                    final_rect = drag_rect

                # 设置选中区域
                self.set_selected_area(final_rect)

                # 根据是否为拖拽选择发送不同的信号
                if final_rect.width() > 1 or final_rect.height() > 1:
                    # 拖拽选择多个格子，发送区域信号
                    self.area_drag_selected.emit(final_rect)
                else:
                    # 单个格子选择，发送单点信号
                    self.area_selected.emit(final_rect.y(), final_rect.x())

            # 重置拖拽状态
            self.is_dragging = False
            self.drag_start_row = -1
            self.drag_start_col = -1
            self.drag_current_row = -1
            self.drag_current_col = -1
            self.update()  # 最终更新显示

        super().mouseReleaseEvent(event)

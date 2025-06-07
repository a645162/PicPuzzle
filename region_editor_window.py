# -*- coding: utf-8 -*-
"""
区域编辑窗口
"""
from PySide6.QtWidgets import (
    QWidget,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QSpinBox,
    QMessageBox,
)
from PySide6.QtCore import Qt, QRect, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QMouseEvent

import config
from models import PuzzleModel, ImageOrientation

# ========== 常量配置 ==========

# 窗口配置
WINDOW_TITLE = "区域编辑"
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 600
WINDOW_DEFAULT_WIDTH = 800
WINDOW_DEFAULT_HEIGHT = 600

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

# 按钮配置
BUTTON_HEIGHT = 35
MOVEMENT_BUTTON_WIDTH = 80
PRESET_BUTTON_MIN_WIDTH = 60

# 布局配置
LAYOUT_MARGIN = 10
LAYOUT_SPACING = 10
BUTTON_LAYOUT_SPACING = 5

# 文本配置
HORIZONTAL_IMAGE_MARKER = "H"
VERTICAL_IMAGE_MARKER = "V"

# 状态消息
STATUS_NO_SELECTION = "请选择一个区域"
STATUS_NO_VERTICAL_IMAGES = "选中区域内没有竖屏图片"
EXPANSION_COMPLETE_TITLE = "扩展完成"
CLEAR_CONFIRM_TITLE = "确认清空"
CLEAR_SUCCESS_TITLE = "成功"
CLEAR_SUCCESS_MESSAGE = "区域已清空"

# ==============================


class GridPreviewWidget(QWidget):
    """网格预览部件，用于显示整个网格和选中区域"""

    area_selected = Signal(int, int)  # 发送选中的区域信号 (row, col)

    def __init__(self, model: PuzzleModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.selected_rect = QRect()  # 当前选中的区域
        self.setStyleSheet(
            f"background-color: {GRID_BACKGROUND_COLOR}; border: 1px solid {GRID_BORDER_COLOR};"
        )
        self.setMinimumSize(GRID_MIN_WIDTH, GRID_MIN_HEIGHT)  # 设置最小尺寸

    def paintEvent(self, event):
        """绘制网格和选中区域"""
        super().paintEvent(event)
        painter = QPainter(self)

        # 计算每个单元格的大小
        cell_width = self.width() / self.model.cols
        cell_height = self.height() / self.model.rows

        # 绘制网格背景（区分已占用和空闲的格子，以及横屏和竖屏图片）
        for row in range(self.model.rows):
            for col in range(self.model.cols):
                cell = self.model.get_cell(row, col)
                x = col * cell_width
                y = row * cell_height

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
                                x + cell_width // 2 - 5,
                                y + cell_height // 2 + 5,
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
                            x + cell_width // 2 - 5,
                            y + cell_height // 2 + 5,
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
        for row in range(self.model.rows + 1):
            y = row * cell_height
            painter.drawLine(0, y, self.width(), y)

        for col in range(self.model.cols + 1):
            x = col * cell_width
            painter.drawLine(x, 0, x, self.height())

        # 绘制选中区域（如果存在）
        if not self.selected_rect.isNull():
            painter.setPen(QPen(SELECTED_AREA_BORDER_COLOR, SELECTED_AREA_BORDER_WIDTH))
            painter.setBrush(SELECTED_AREA_FILL_COLOR)
            # QRect的x()对应col，y()对应row
            x = self.selected_rect.x() * cell_width
            y = self.selected_rect.y() * cell_height
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
            # 计算点击的格子位置
            cell_width = self.width() / self.model.cols
            cell_height = self.height() / self.model.rows

            col = int(event.position().x() / cell_width)
            row = int(event.position().y() / cell_height)

            # 确保坐标在有效范围内
            if 0 <= row < self.model.rows and 0 <= col < self.model.cols:
                # 设置为1x1的选择区域，使用(left, top, width, height)格式
                # 这里left=col, top=row
                new_rect = QRect(col, row, 1, 1)
                self.set_selected_area(new_rect)
                self.area_selected.emit(row, col)

        super().mousePressEvent(event)


class RegionEditorWindow(QDialog):
    """区域编辑窗口"""

    def __init__(self, model: PuzzleModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.setWindowTitle(WINDOW_TITLE)
        self.setModal(False)

        # 设置窗口标志，支持最大化、最小化和调整大小
        self.setWindowFlags(
            Qt.Window  # 独立窗口
            | Qt.WindowMinMaxButtonsHint  # 最大化/最小化按钮
            | Qt.WindowCloseButtonHint  # 关闭按钮
            | Qt.WindowTitleHint  # 标题栏
        )

        # 设置初始大小和最小大小
        self.resize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        self.setup_ui()

        # 设置默认选中区域（1x1，位置在(0,0)）
        self.start_row_spinbox.setValue(0)
        self.start_col_spinbox.setValue(0)
        self.rows_spinbox.setValue(1)
        self.cols_spinbox.setValue(1)
        self._update_selected_area()

        self.update_preview()

    def showEvent(self, event):
        """窗口显示时刷新预览"""
        super().showEvent(event)
        self.update_preview()

    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)

        # 控制面板
        control_layout = QHBoxLayout()

        # 移动方向按钮
        move_layout = QVBoxLayout()

        move_up_button = QPushButton("↑ 上移")
        move_up_button.clicked.connect(self._move_up)
        move_layout.addWidget(move_up_button)

        move_row_layout = QHBoxLayout()
        move_left_button = QPushButton("← 左移")
        move_left_button.clicked.connect(self._move_left)
        move_right_button = QPushButton("→ 右移")
        move_right_button.clicked.connect(self._move_right)
        move_row_layout.addWidget(move_left_button)
        move_row_layout.addWidget(move_right_button)
        move_layout.addLayout(move_row_layout)

        move_down_button = QPushButton("↓ 下移")
        move_down_button.clicked.connect(self._move_down)
        move_layout.addWidget(move_down_button)

        control_layout.addLayout(move_layout)

        # 区域设置
        area_layout = QVBoxLayout()
        area_layout.addWidget(QLabel("选择区域:"))

        row_col_layout = QHBoxLayout()

        # 起始行
        start_row_layout = QVBoxLayout()
        start_row_layout.addWidget(QLabel("起始行"))
        self.start_row_spinbox = QSpinBox()
        self.start_row_spinbox.setRange(0, self.model.rows - 1)
        self.start_row_spinbox.valueChanged.connect(self._update_selected_area)
        start_row_layout.addWidget(self.start_row_spinbox)

        # 起始列
        start_col_layout = QVBoxLayout()
        start_col_layout.addWidget(QLabel("起始列"))
        self.start_col_spinbox = QSpinBox()
        self.start_col_spinbox.setRange(0, self.model.cols - 1)
        self.start_col_spinbox.valueChanged.connect(self._update_selected_area)
        start_col_layout.addWidget(self.start_col_spinbox)

        # 行数
        rows_layout = QVBoxLayout()
        rows_layout.addWidget(QLabel("行数"))
        self.rows_spinbox = QSpinBox()
        self.rows_spinbox.setRange(1, self.model.rows)
        self.rows_spinbox.valueChanged.connect(self._update_selected_area)
        rows_layout.addWidget(self.rows_spinbox)

        # 列数
        cols_layout = QVBoxLayout()
        cols_layout.addWidget(QLabel("列数"))
        self.cols_spinbox = QSpinBox()
        self.cols_spinbox.setRange(1, self.model.cols)
        self.cols_spinbox.valueChanged.connect(self._update_selected_area)
        cols_layout.addWidget(self.cols_spinbox)

        row_col_layout.addLayout(start_row_layout)
        row_col_layout.addLayout(start_col_layout)
        row_col_layout.addLayout(rows_layout)
        row_col_layout.addLayout(cols_layout)
        area_layout.addLayout(row_col_layout)

        control_layout.addLayout(area_layout)

        # 添加弹簧使按钮右对齐
        control_layout.addStretch()

        layout.addLayout(control_layout)

        # 预览区域
        preview_layout = QHBoxLayout()

        # 网格预览
        self.grid_preview = GridPreviewWidget(self.model)
        self.grid_preview.area_selected.connect(self._on_area_selected)
        preview_layout.addWidget(self.grid_preview, 1)

        # 按钮
        button_layout = QHBoxLayout()

        # 预设区域按钮
        preset_layout = QVBoxLayout()
        preset_layout.addWidget(QLabel("快速选择:"))

        preset_button_layout = QHBoxLayout()

        full_grid_button = QPushButton("全部网格")
        full_grid_button.clicked.connect(self._select_full_grid)
        preset_button_layout.addWidget(full_grid_button)

        single_row_button = QPushButton("单行")
        single_row_button.clicked.connect(self._select_single_row)
        preset_button_layout.addWidget(single_row_button)

        single_col_button = QPushButton("单列")
        single_col_button.clicked.connect(self._select_single_col)
        preset_button_layout.addWidget(single_col_button)

        preset_layout.addLayout(preset_button_layout)
        button_layout.addLayout(preset_layout)

        button_layout.addStretch()

        auto_expand_button = QPushButton("智能扩展")
        auto_expand_button.setFixedHeight(35)
        auto_expand_button.clicked.connect(self._auto_expand_for_vertical_images)
        button_layout.addWidget(auto_expand_button)

        debug_button = QPushButton("调试信息")
        debug_button.setFixedHeight(35)
        debug_button.clicked.connect(self.debug_region_info)
        button_layout.addWidget(debug_button)

        refresh_button = QPushButton("刷新预览")
        refresh_button.setFixedHeight(35)
        refresh_button.clicked.connect(self.update_preview)
        button_layout.addWidget(refresh_button)

        clear_button = QPushButton("清空区域")
        clear_button.setFixedHeight(35)
        clear_button.clicked.connect(self._clear_region)
        button_layout.addWidget(clear_button)

        close_button = QPushButton("关闭")
        close_button.setFixedHeight(35)
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        layout.addLayout(preview_layout)
        layout.addLayout(button_layout)

        # 添加状态栏
        self.status_label = QLabel(STATUS_NO_SELECTION)
        self.status_label.setStyleSheet(
            "QLabel { padding: 5px; border-top: 1px solid #ccc; }"
        )
        layout.addWidget(self.status_label)

        # 设置布局边距
        layout.setContentsMargins(
            LAYOUT_MARGIN, LAYOUT_MARGIN, LAYOUT_MARGIN, LAYOUT_MARGIN
        )
        layout.setSpacing(LAYOUT_SPACING)

    def update_preview(self):
        """更新预览"""
        self.grid_preview.update()
        self._update_status()

    def _update_status(self):
        """更新状态信息"""
        current_rect = self.grid_preview.selected_rect
        if current_rect.isNull():
            self.status_label.setText("请选择一个区域")
            return

        # 计算区域内的图片数量
        occupied_count = 0
        total_cells = current_rect.width() * current_rect.height()

        # QRect: left()=col, top()=row, right()=col+width, bottom()=row+height
        start_row = current_rect.top()
        start_col = current_rect.left()
        end_row = current_rect.bottom()
        end_col = current_rect.right()

        # 获取图片统计信息
        vertical_images = self.get_vertical_images_in_region(current_rect)
        horizontal_images = self.get_horizontal_images_in_region(current_rect)

        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                cell = self.model.get_cell(row, col)
                if cell and cell.is_occupied:
                    occupied_count += 1

        status_text = (
            f"选中区域: ({start_row}, {start_col}) - "
            f"({end_row-1}, {end_col-1}) | "
            f"大小: {current_rect.width()}x{current_rect.height()} | "
            f"已占用: {occupied_count}/{total_cells} 格子 | "
            f"横屏: {len(horizontal_images)} 竖屏: {len(vertical_images)}"
        )
        self.status_label.setText(status_text)

    def _update_selected_area(self):
        """更新选中区域"""
        start_row = self.start_row_spinbox.value()
        start_col = self.start_col_spinbox.value()
        rows = self.rows_spinbox.value()
        cols = self.cols_spinbox.value()

        # 确保区域不超过网格范围
        end_row = min(start_row + rows, self.model.rows)
        end_col = min(start_col + cols, self.model.cols)

        # QRect(left, top, width, height) -> QRect(col, row, width, height)
        selected_rect = QRect(
            start_col, start_row, end_col - start_col, end_row - start_row
        )
        self.grid_preview.set_selected_area(selected_rect)
        self._auto_expand_for_vertical_images_silent()  # 自动检查竖屏图片
        self._update_status()

    def _move_up(self):
        """向上移动区域"""
        current_rect = self.grid_preview.selected_rect
        if current_rect.isNull():
            return

        new_top = max(current_rect.top() - 1, 0)
        new_rect = QRect(
            current_rect.left(), new_top, current_rect.width(), current_rect.height()
        )

        # 检查新位置是否有效
        if new_rect.bottom() <= self.model.rows:
            self._update_spinboxes_from_rect(new_rect)
            self.grid_preview.set_selected_area(new_rect)
            self._auto_expand_for_vertical_images_silent()  # 自动检查竖屏图片
            self._update_status()

    def _move_down(self):
        """向下移动区域"""
        current_rect = self.grid_preview.selected_rect
        if current_rect.isNull():
            return

        new_top = current_rect.top() + 1
        new_rect = QRect(
            current_rect.left(), new_top, current_rect.width(), current_rect.height()
        )

        # 检查新位置是否有效，如果超出边界则调整大小
        if new_rect.bottom() > self.model.rows:
            # 超出下边界，调整高度
            new_height = max(1, self.model.rows - new_top)
            new_rect = QRect(
                current_rect.left(), new_top, current_rect.width(), new_height
            )

        self._update_spinboxes_from_rect(new_rect)
        self.grid_preview.set_selected_area(new_rect)
        self._auto_expand_for_vertical_images_silent()  # 自动检查竖屏图片
        self._update_status()

    def _move_left(self):
        """向左移动区域"""
        current_rect = self.grid_preview.selected_rect
        if current_rect.isNull():
            return

        new_left = max(current_rect.left() - 1, 0)
        new_rect = QRect(
            new_left, current_rect.top(), current_rect.width(), current_rect.height()
        )

        # 检查新位置是否有效
        if new_rect.right() <= self.model.cols:
            self._update_spinboxes_from_rect(new_rect)
            self.grid_preview.set_selected_area(new_rect)
            self._auto_expand_for_vertical_images_silent()  # 自动检查竖屏图片
            self._update_status()

    def _move_right(self):
        """向右移动区域"""
        current_rect = self.grid_preview.selected_rect
        if current_rect.isNull():
            return

        new_left = current_rect.left() + 1
        new_rect = QRect(
            new_left, current_rect.top(), current_rect.width(), current_rect.height()
        )

        # 检查新位置是否有效，如果超出边界则调整大小
        if new_rect.right() > self.model.cols:
            # 超出右边界，调整宽度
            new_width = max(1, self.model.cols - new_left)
            new_rect = QRect(
                new_left, current_rect.top(), new_width, current_rect.height()
            )

        self._update_spinboxes_from_rect(new_rect)
        self.grid_preview.set_selected_area(new_rect)
        self._auto_expand_for_vertical_images_silent()  # 自动检查竖屏图片
        self._update_status()

    def _update_spinboxes_from_rect(self, rect: QRect):
        """根据矩形更新数值框"""
        self.start_row_spinbox.setValue(rect.top())
        self.start_col_spinbox.setValue(rect.left())
        self.rows_spinbox.setValue(rect.height())
        self.cols_spinbox.setValue(rect.width())

    def _on_area_selected(self, row: int, col: int):
        """处理网格点击选择"""
        # 设置选中的区域为点击的单个格子
        new_rect = QRect(col, row, 1, 1)
        self._update_spinboxes_from_rect(new_rect)
        self.grid_preview.set_selected_area(new_rect)
        self._auto_expand_for_vertical_images_silent()  # 自动检查竖屏图片
        self._update_status()

    def _select_full_grid(self):
        """选择整个网格"""
        new_rect = QRect(0, 0, self.model.cols, self.model.rows)
        self._update_spinboxes_from_rect(new_rect)
        self.grid_preview.set_selected_area(new_rect)
        self._auto_expand_for_vertical_images_silent()  # 自动检查竖屏图片
        self._update_status()

    def _select_single_row(self):
        """选择单行（当前选中区域的起始行）"""
        current_rect = self.grid_preview.selected_rect
        start_row = current_rect.top() if not current_rect.isNull() else 0
        new_rect = QRect(0, start_row, self.model.cols, 1)
        self._update_spinboxes_from_rect(new_rect)
        self.grid_preview.set_selected_area(new_rect)
        self._auto_expand_for_vertical_images_silent()  # 自动检查竖屏图片
        self._update_status()

    def _select_single_col(self):
        """选择单列（当前选中区域的起始列）"""
        current_rect = self.grid_preview.selected_rect
        start_col = current_rect.left() if not current_rect.isNull() else 0
        new_rect = QRect(start_col, 0, 1, self.model.rows)
        self._update_spinboxes_from_rect(new_rect)
        self.grid_preview.set_selected_area(new_rect)
        self._auto_expand_for_vertical_images_silent()  # 自动检查竖屏图片
        self._update_status()

    def get_vertical_images_in_region(self, rect: QRect):
        """获取指定区域内的所有竖屏图片信息"""
        vertical_images = []
        if rect.isNull():
            return vertical_images

        start_row = rect.top()
        start_col = rect.left()
        end_row = rect.bottom()
        end_col = rect.right()

        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                cell = self.model.get_cell(row, col)
                if (
                    cell
                    and cell.is_occupied
                    and cell.image
                    and cell.image.orientation == ImageOrientation.VERTICAL
                    and cell.is_main_cell
                ):
                    vertical_images.append(
                        {
                            "row": row,
                            "col": col,
                            "image": cell.image,
                            "start_row": row,
                            "end_row": row + config.VERTICAL_IMAGE_SPAN,
                            "occupied_cells": [
                                (row + i, col)
                                for i in range(config.VERTICAL_IMAGE_SPAN)
                            ],
                        }
                    )
        return vertical_images

    def get_horizontal_images_in_region(self, rect: QRect):
        """获取指定区域内的所有横屏图片信息"""
        horizontal_images = []
        if rect.isNull():
            return horizontal_images

        start_row = rect.top()
        start_col = rect.left()
        end_row = rect.bottom()
        end_col = rect.right()

        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                cell = self.model.get_cell(row, col)
                if (
                    cell
                    and cell.is_occupied
                    and cell.image
                    and cell.image.orientation == ImageOrientation.HORIZONTAL
                    and cell.is_main_cell
                ):
                    horizontal_images.append(
                        {
                            "row": row,
                            "col": col,
                            "image": cell.image,
                            "occupied_cells": [(row, col)],
                        }
                    )
        return horizontal_images

    def debug_region_info(self):
        """调试输出当前选中区域的详细信息"""
        current_rect = self.grid_preview.selected_rect
        if current_rect.isNull():
            print("没有选中区域")
            return

        print("\n=== 区域信息调试 ===")
        print(
            f"选中区域: ({current_rect.left()}, {current_rect.top()}) 大小: {current_rect.width()}x{current_rect.height()}"
        )

        vertical_images = self.get_vertical_images_in_region(current_rect)
        horizontal_images = self.get_horizontal_images_in_region(current_rect)

        print(f"竖屏图片数量: {len(vertical_images)}")
        for i, vimg in enumerate(vertical_images):
            print(
                f"  竖屏图片 {i+1}: 位置({vimg['row']}, {vimg['col']}) - {vimg['image'].path.name}"
            )
            print(f"    占用行: {vimg['start_row']}-{vimg['end_row']}")

        print(f"横屏图片数量: {len(horizontal_images)}")
        for i, himg in enumerate(horizontal_images):
            print(
                f"  横屏图片 {i+1}: 位置({himg['row']}, {himg['col']}) - {himg['image'].path.name}"
            )

        print("===================\n")

    def _auto_expand_for_vertical_images_silent(self):
        """静默自动扩展选中区域以包含完整的竖屏图片（不显示消息框）"""
        current_rect = self.grid_preview.selected_rect
        if current_rect.isNull():
            return False

        # 获取选中区域内的所有竖屏图片
        vertical_images = self.get_vertical_images_in_region(current_rect)

        if not vertical_images:
            return False

        # 计算需要扩展的边界
        new_top = current_rect.top()
        new_bottom = current_rect.bottom()
        new_left = current_rect.left()
        new_right = current_rect.right()

        expanded = False
        for vimg in vertical_images:
            img_top = vimg["start_row"]
            img_bottom = vimg["end_row"]

            # 检查是否需要扩展
            if img_top < new_top or img_bottom > new_bottom:
                expanded = True
                new_top = min(new_top, img_top)
                new_bottom = max(new_bottom, img_bottom)

        if not expanded:
            return False

        # 确保不超出网格范围
        new_top = max(0, new_top)
        new_bottom = min(self.model.rows, new_bottom)

        # 创建新的矩形
        new_rect = QRect(new_left, new_top, new_right - new_left, new_bottom - new_top)

        # 更新显示
        self._update_spinboxes_from_rect(new_rect)
        self.grid_preview.set_selected_area(new_rect)

        return True

    def _auto_expand_for_vertical_images(self):
        """自动扩展选中区域以包含完整的竖屏图片"""
        current_rect = self.grid_preview.selected_rect
        if current_rect.isNull():
            QMessageBox.information(self, "提示", "请先选择一个区域")
            return

        # 获取选中区域内的所有竖屏图片
        vertical_images = self.get_vertical_images_in_region(current_rect)

        if not vertical_images:
            QMessageBox.information(self, "提示", "选中区域内没有竖屏图片")
            return

        # 计算需要扩展的边界
        new_top = current_rect.top()
        new_bottom = current_rect.bottom()
        new_left = current_rect.left()
        new_right = current_rect.right()

        for vimg in vertical_images:
            img_top = vimg["start_row"]
            img_bottom = vimg["end_row"]

            # 扩展区域以包含完整的竖屏图片
            new_top = min(new_top, img_top)
            new_bottom = max(new_bottom, img_bottom)

        # 确保不超出网格范围
        new_top = max(0, new_top)
        new_bottom = min(self.model.rows, new_bottom)

        # 创建新的矩形
        new_rect = QRect(new_left, new_top, new_right - new_left, new_bottom - new_top)

        # 更新显示
        self._update_spinboxes_from_rect(new_rect)
        self.grid_preview.set_selected_area(new_rect)
        self._update_status()

        QMessageBox.information(
            self,
            "扩展完成",
            f"已扩展区域以包含 {len(vertical_images)} 个完整的竖屏图片",
        )

    def _clear_region(self):
        """清空指定区域"""
        current_rect = self.grid_preview.selected_rect
        if current_rect.isNull():
            return

        # 显示确认对话框
        reply = QMessageBox.question(
            self,
            "确认清空",
            f"确定要清空区域 ({current_rect.top()},{current_rect.left()}) - ({current_rect.bottom()-1},{current_rect.right()-1}) 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # 清除该区域内的所有图片
            start_row = current_rect.top()
            start_col = current_rect.left()
            end_row = current_rect.bottom()
            end_col = current_rect.right()

            for row in range(start_row, end_row):
                for col in range(start_col, end_col):
                    self.model.remove_image(row, col)

            # 更新显示
            self.update_preview()
            if self.parent():
                # 更新主窗口显示
                self.parent().grid_widget.refresh_display()
                self.parent().image_list_widget.update_lists()
                self.parent().set_modified(True)  # 标记主窗口为已修改
            QMessageBox.information(self, "成功", "区域已清空")

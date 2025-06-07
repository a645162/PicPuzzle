# -*- coding: utf-8 -*-
"""
区域编辑窗口
"""
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QSpinBox,
    QMessageBox,
)
from PySide6.QtCore import Qt, QRect

import config
from models import PuzzleModel, ImageOrientation
from grid_preview_widget import GridPreviewWidget

# ========== 常量配置 ==========

# 窗口配置
WINDOW_TITLE = "区域编辑"
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 600
WINDOW_DEFAULT_WIDTH = 800
WINDOW_DEFAULT_HEIGHT = 600

# 按钮配置
BUTTON_HEIGHT = 35
MOVEMENT_BUTTON_WIDTH = 80
PRESET_BUTTON_MIN_WIDTH = 60

# 布局配置
LAYOUT_MARGIN = 10
LAYOUT_SPACING = 10
BUTTON_LAYOUT_SPACING = 5

# ==============================


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
        self.status_label = QLabel("请选择一个区域")
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
        end_row = current_rect.top() + current_rect.height()
        end_col = current_rect.left() + current_rect.width()

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
            self._auto_expand_for_vertical_images(silent=True)  # 移动操作需要自动检查竖屏图片
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
        self._auto_expand_for_vertical_images(silent=True)  # 移动操作需要自动检查竖屏图片
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
            self._auto_expand_for_vertical_images(silent=True)  # 移动操作需要自动检查竖屏图片
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
        self._auto_expand_for_vertical_images(silent=True)  # 移动操作需要自动检查竖屏图片
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
        self._update_status()

    def _select_full_grid(self):
        """选择整个网格"""
        new_rect = QRect(0, 0, self.model.cols, self.model.rows)
        self._update_spinboxes_from_rect(new_rect)
        self.grid_preview.set_selected_area(new_rect)
        self._auto_expand_for_vertical_images(silent=True)  # 快速选择需要自动检查竖屏图片
        self._update_status()

    def _select_single_row(self):
        """选择单行（当前选中区域的起始行）"""
        current_rect = self.grid_preview.selected_rect
        start_row = current_rect.top() if not current_rect.isNull() else 0
        new_rect = QRect(0, start_row, self.model.cols, 1)
        self._update_spinboxes_from_rect(new_rect)
        self.grid_preview.set_selected_area(new_rect)
        self._auto_expand_for_vertical_images(silent=True)  # 快速选择需要自动检查竖屏图片
        self._update_status()

    def _select_single_col(self):
        """选择单列（当前选中区域的起始列）"""
        current_rect = self.grid_preview.selected_rect
        start_col = current_rect.left() if not current_rect.isNull() else 0
        new_rect = QRect(start_col, 0, 1, self.model.rows)
        self._update_spinboxes_from_rect(new_rect)
        self.grid_preview.set_selected_area(new_rect)
        self._auto_expand_for_vertical_images(silent=True)  # 快速选择需要自动检查竖屏图片
        self._update_status()

    def get_vertical_images_in_region(self, rect: QRect):
        """获取指定区域内的所有竖屏图片信息"""
        vertical_images = []
        if rect.isNull():
            return vertical_images

        start_row = rect.top()
        start_col = rect.left()
        end_row = rect.top() + rect.height()
        end_col = rect.left() + rect.width()

        # 用于记录已经处理过的竖屏图片，避免重复
        processed_images = set()

        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                cell = self.model.get_cell(row, col)
                if (
                    cell
                    and cell.is_occupied
                    and cell.image
                    and cell.image.orientation == ImageOrientation.VERTICAL
                ):
                    # 获取主格子位置
                    main_row, main_col = self.model.get_main_cell_position(row, col)

                    # 用图片路径和主格子位置作为唯一标识
                    image_key = (cell.image.path, main_row, main_col)

                    if image_key not in processed_images:
                        processed_images.add(image_key)
                        vertical_images.append(
                            {
                                "row": main_row,
                                "col": main_col,
                                "image": cell.image,
                                "start_row": main_row,
                                "end_row": main_row + config.VERTICAL_IMAGE_SPAN,
                                "occupied_cells": [
                                    (main_row + i, main_col)
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
        end_row = rect.top() + rect.height()
        end_col = rect.left() + rect.width()

        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                cell = self.model.get_cell(row, col)
                if (
                    cell
                    and cell.is_occupied
                    and cell.image
                    and cell.image.orientation == ImageOrientation.HORIZONTAL
                    and cell.is_main_cell  # 横屏图片只有一个格子，都是主格子
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

    def _auto_expand_for_vertical_images(self, silent=False):
        """自动扩展选中区域以包含完整的竖屏图片

        Args:
            silent (bool): 是否静默模式，静默模式不显示消息框但仍输出调试信息
        """
        current_rect = self.grid_preview.selected_rect
        if current_rect.isNull():
            if not silent:
                QMessageBox.information(self, "提示", "请先选择一个区域")
            return False

        print(f"\n=== 智能扩展调试信息 ({'静默模式' if silent else '交互模式'}) ===")
        print(
            f"当前选中区域: 列{current_rect.left()}-{current_rect.left()+current_rect.width()-1} "
            f"行{current_rect.top()}-{current_rect.top()+current_rect.height()-1} "
            f"大小: {current_rect.width()}x{current_rect.height()}"
        )

        # 检查区域内所有格子的状态
        print("区域内所有格子的状态:")
        start_row = current_rect.top()
        start_col = current_rect.left()
        end_row = current_rect.top() + current_rect.height()
        end_col = current_rect.left() + current_rect.width()

        print(f"检查范围: 行 {start_row}-{end_row-1}, 列 {start_col}-{end_col-1}")

        # 统计各种格子类型的数量
        empty_cells = 0
        occupied_cells = 0
        vertical_cells = 0
        horizontal_cells = 0
        main_cells = 0
        sub_cells = 0

        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                cell = self.model.get_cell(row, col)
                if cell:
                    if cell.is_occupied:
                        occupied_cells += 1
                        if cell.is_main_cell:
                            main_cells += 1
                        else:
                            sub_cells += 1

                        if cell.image:
                            if cell.image.orientation == ImageOrientation.VERTICAL:
                                vertical_cells += 1
                            else:
                                horizontal_cells += 1

                            print(
                                f"  格子({row}, {col}): 已占用, {cell.image.orientation.value}, "
                                f"{'主格子' if cell.is_main_cell else '子格子'} - {cell.image.path.name}"
                            )
                            if not cell.is_main_cell:
                                print(f"    主格子位置: {cell.main_position}")
                        else:
                            print(f"  格子({row}, {col}): 已占用但无图片信息")
                    else:
                        empty_cells += 1
                        print(f"  格子({row}, {col}): 空闲")

        print(f"格子统计: 总计{end_row-start_row}x{end_col-start_col}={occupied_cells+empty_cells}个格子")
        print(f"  空闲: {empty_cells}, 已占用: {occupied_cells} (主格子: {main_cells}, 子格子: {sub_cells})")
        print(f"  竖屏格子: {vertical_cells}, 横屏格子: {horizontal_cells}")

        # 获取选中区域内的所有竖屏图片
        vertical_images = self.get_vertical_images_in_region(current_rect)
        horizontal_images = self.get_horizontal_images_in_region(current_rect)

        print(f"唯一图片统计:")
        print(f"  竖屏图片数量: {len(vertical_images)}")
        for i, vimg in enumerate(vertical_images):
            print(
                f"    竖屏图片 {i+1}: 主格子({vimg['row']}, {vimg['col']}) - {vimg['image'].path.name}"
            )
            print(f"      占用行范围: {vimg['start_row']}-{vimg['end_row']-1} (需要{vimg['end_row']-vimg['start_row']}行)")
            print(f"      占用格子: {vimg['occupied_cells']}")

        print(f"  横屏图片数量: {len(horizontal_images)}")
        for i, himg in enumerate(horizontal_images):
            print(
                f"    横屏图片 {i+1}: 位置({himg['row']}, {himg['col']}) - {himg['image'].path.name}"
            )

        if not vertical_images:
            print("没有找到竖屏图片，无需扩展")
            if not silent:
                QMessageBox.information(self, "提示", "选中区域内没有竖屏图片")
            print("===================\n")
            return False

        # 计算需要扩展的边界
        new_top = current_rect.top()
        new_bottom = current_rect.bottom()
        new_left = current_rect.left()
        new_right = current_rect.right()

        print(f"原始边界: top={new_top}, bottom={new_bottom}, left={new_left}, right={new_right}")

        expansion_needed = False
        expansion_details = []

        for i, vimg in enumerate(vertical_images):
            img_top = vimg["start_row"]
            img_bottom = vimg["end_row"]

            print(f"分析竖屏图片 {i+1} ({vimg['image'].path.name}):")
            print(f"  图片需要占用行: {img_top}-{img_bottom-1}")
            print(f"  当前选中区域行: {new_top}-{new_bottom-1}")

            # 检查是否需要扩展
            need_expand_top = img_top < new_top
            need_expand_bottom = img_bottom > new_bottom

            if need_expand_top or need_expand_bottom:
                expansion_needed = True
                old_top, old_bottom = new_top, new_bottom

                if need_expand_top:
                    new_top = min(new_top, img_top)
                    expansion_details.append(f"向上扩展到行{img_top}")
                    print(f"  需要向上扩展: 从行{old_top}扩展到行{img_top}")

                if need_expand_bottom:
                    new_bottom = max(new_bottom, img_bottom)
                    expansion_details.append(f"向下扩展到行{img_bottom-1}")
                    print(f"  需要向下扩展: 从行{old_bottom-1}扩展到行{img_bottom-1}")

                print(f"  扩展后行范围: {new_top}-{new_bottom-1}")
            else:
                print(f"  该竖屏图片已完整包含在选中区域内")

        if not expansion_needed:
            print("所有竖屏图片都已完整包含在选中区域内，无需扩展")
            if not silent:
                QMessageBox.information(self, "提示", "选中区域已包含所有完整的竖屏图片")
            print("===================\n")
            return False

        # 确保不超出网格范围
        original_new_top, original_new_bottom = new_top, new_bottom
        new_top = max(0, new_top)
        new_bottom = min(self.model.rows, new_bottom)

        if original_new_top != new_top or original_new_bottom != new_bottom:
            print(f"边界调整: 原始({original_new_top}-{original_new_bottom-1}) -> 最终({new_top}-{new_bottom-1})")

        print(f"最终边界: top={new_top}, bottom={new_bottom}, left={new_left}, right={new_right}")

        # 创建新的矩形
        new_rect = QRect(new_left, new_top, new_right - new_left, new_bottom - new_top)

        print(f"扩展结果:")
        print(f"  原始区域大小: {current_rect.width()}x{current_rect.height()}")
        print(f"  扩展后区域大小: {new_rect.width()}x{new_rect.height()}")
        print(f"  扩展详情: {'; '.join(expansion_details)}")

        # 计算扩展后新增的格子数
        original_cells = current_rect.width() * current_rect.height()
        new_cells = new_rect.width() * new_rect.height()
        added_cells = new_cells - original_cells
        print(f"  新增格子数: {added_cells} (原{original_cells} -> 新{new_cells})")

        # 更新显示
        self._update_spinboxes_from_rect(new_rect)
        self.grid_preview.set_selected_area(new_rect)
        self._update_status()

        print("===================\n")

        if not silent:
            QMessageBox.information(
                self,
                "扩展完成",
                f"已扩展区域以包含 {len(vertical_images)} 个完整的竖屏图片\n"
                f"区域大小: {current_rect.width()}x{current_rect.height()} -> {new_rect.width()}x{new_rect.height()}\n"
                f"新增格子: {added_cells} 个",
            )

        return True

    def _clear_region(self):
        """清空指定区域"""
        current_rect = self.grid_preview.selected_rect
        if current_rect.isNull():
            return

        # 在清空之前先自动扩展选择区域以包含完整的竖屏图片
        self._auto_expand_for_vertical_images(silent=True)

        # 重新获取扩展后的区域
        current_rect = self.grid_preview.selected_rect

        # 显示确认对话框
        reply = QMessageBox.question(
            self,
            "确认清空",
            f"确定要清空区域 ({current_rect.top()},{current_rect.left()}) - ({current_rect.top() + current_rect.height() - 1},{current_rect.left() + current_rect.width() - 1}) 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # 清除该区域内的所有图片
            start_row = current_rect.top()
            start_col = current_rect.left()
            end_row = current_rect.top() + current_rect.height()
            end_col = current_rect.left() + current_rect.width()

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

# -*- coding: utf-8 -*-
"""
预览窗口
"""
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QCheckBox,
    QSpinBox,
    QMessageBox,
)
from PySide6.QtCore import Qt

import config
from models import PuzzleModel
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

        # 控制选项
        control_layout = QHBoxLayout()

        self.show_grid_checkbox = QCheckBox("显示网格")
        self.show_grid_checkbox.setChecked(True)  # 默认显示网格
        self.show_grid_checkbox.stateChanged.connect(self.update_preview)
        control_layout.addWidget(self.show_grid_checkbox)

        self.auto_scale_checkbox = QCheckBox("自动缩放")
        self.auto_scale_checkbox.setChecked(True)  # 默认启用自动缩放
        self.auto_scale_checkbox.stateChanged.connect(self.update_preview)
        control_layout.addWidget(self.auto_scale_checkbox)

        # 添加间隔设置
        control_layout.addWidget(QLabel("间隔:"))
        self.spacing_spinbox = QSpinBox()
        self.spacing_spinbox.setRange(-1, 1000)
        self.spacing_spinbox.setValue(-1)  # 默认自动计算
        self.spacing_spinbox.setSpecialValueText("自动计算")
        self.spacing_spinbox.setSuffix(" px")
        self.spacing_spinbox.valueChanged.connect(self.update_preview)
        control_layout.addWidget(self.spacing_spinbox)

        control_layout.addStretch()  # 添加弹簧使控件左对齐
        layout.addLayout(control_layout)

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
        self.preview_label.setScaledContents(False)  # 手动控制缩放
        scroll_area.setWidget(self.preview_label)

        # 保存滚动区域引用用于自动缩放
        self.scroll_area = scroll_area

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        refresh_button = QPushButton("刷新预览")
        refresh_button.setFixedHeight(35)
        refresh_button.clicked.connect(self.update_preview)
        button_layout.addWidget(refresh_button)

        # 添加弹簧，使按钮右对齐
        button_layout.addStretch()

        # 始终显示导出按钮
        export_button = QPushButton("导出")
        export_button.setFixedHeight(35)
        export_button.clicked.connect(self._export_puzzle)
        button_layout.addWidget(export_button)

        close_button = QPushButton("关闭")
        close_button.setFixedHeight(35)
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

        # 设置布局边距
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

    def _export_puzzle(self):
        """执行导出操作"""
        # 显示导出对话框
        dialog = ExportDialog(self.model, self)

        if dialog.exec() == QDialog.Accepted:
            cell_width, cell_height, custom_spacing = dialog.get_export_settings()

            # 选择保存位置
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存拼图",
                str(Path.home() / "puzzle.png"),
                "PNG图片 (*.png);;JPEG图片 (*.jpg);;所有文件 (*.*)",
            )

            if save_path:
                try:
                    exporter = PuzzleExporter(self.model)
                    exporter.export_to_file(
                        save_path, cell_width, cell_height, custom_spacing
                    )
                    QMessageBox.information(
                        self, "导出成功", f"拼图已保存到: {save_path}"
                    )
                except Exception as e:
                    QMessageBox.warning(self, "导出失败", f"导出时出错: {e}")

    def update_preview(self):
        """更新预览"""
        try:
            preview_pixmap = self._create_preview_image()
            if preview_pixmap and not preview_pixmap.isNull():
                # 根据复选框状态决定是否自动缩放
                if self.auto_scale_checkbox.isChecked():
                    scaled_pixmap = self._scale_pixmap_to_fit(preview_pixmap)
                else:
                    scaled_pixmap = preview_pixmap

                self.preview_label.setPixmap(scaled_pixmap)

                # 更新信息
                size = preview_pixmap.size()
                scaled_size = scaled_pixmap.size()
                valid_area = self.exporter.get_valid_area()
                if valid_area:
                    min_row, max_row, min_col, max_col = valid_area
                    area_info = (
                        f"有效区域: {max_row - min_row + 1}x{max_col - min_col + 1}"
                    )
                else:
                    area_info = "无图片"

                # 添加网格状态和间隔信息
                grid_status = (
                    "显示网格" if self.show_grid_checkbox.isChecked() else "隐藏网格"
                )
                spacing_value = self.spacing_spinbox.value()
                spacing_info = (
                    "自动间隔" if spacing_value == -1 else f"{spacing_value}px间隔"
                )

                # 显示原始尺寸和缩放后尺寸
                if self.auto_scale_checkbox.isChecked() and scaled_size != size:
                    scale_ratio = (
                        scaled_size.width() / size.width() if size.width() > 0 else 1
                    )
                    info_parts = [
                        f"原始: {size.width()}x{size.height()}",
                        f"显示: {scaled_size.width()}x{scaled_size.height()}",
                        f"缩放: {scale_ratio:.2f}",
                        area_info,
                        grid_status,
                        spacing_info,
                    ]
                else:
                    info_parts = [
                        f"尺寸: {size.width()}x{size.height()}",
                        area_info,
                        grid_status,
                        spacing_info,
                    ]

                self.info_label.setText(" | ".join(info_parts))
            else:
                self.preview_label.setText("没有图片可预览")
                self.info_label.setText("请先在网格中放置图片")
        except Exception as e:
            self.preview_label.setText(f"预览失败: {e}")
            self.info_label.setText("预览生成失败")

    def resizeEvent(self, event):
        """窗口大小变化时重新缩放预览图片"""
        super().resizeEvent(event)
        # 延迟更新预览，避免在调整大小过程中频繁重绘
        if hasattr(self, "preview_label"):
            self.update_preview()

    def _scale_pixmap_to_fit(self, pixmap):
        """将图片按比例缩放以适应滚动区域"""
        if not pixmap or pixmap.isNull():
            return pixmap

        # 获取滚动区域的可用尺寸（减去边距和滚动条空间）
        available_size = self.scroll_area.size()
        margin = 40  # 留出一些边距
        max_width = available_size.width() - margin
        max_height = available_size.height() - margin

        # 确保最小尺寸
        max_width = max(200, max_width)
        max_height = max(200, max_height)

        # 获取原始图片尺寸
        original_size = pixmap.size()

        # 如果图片小于可用空间，则不放大，保持原始尺寸
        if original_size.width() <= max_width and original_size.height() <= max_height:
            return pixmap

        # 计算缩放比例，保持宽高比
        width_ratio = max_width / original_size.width()
        height_ratio = max_height / original_size.height()
        scale_ratio = min(width_ratio, height_ratio)

        # 计算新的尺寸
        new_width = int(original_size.width() * scale_ratio)
        new_height = int(original_size.height() * scale_ratio)

        # 缩放图片
        return pixmap.scaled(
            new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

    def _create_preview_image(self):
        """创建预览图片"""
        # 使用固定的预览尺寸
        cell_width = config.PREVIEW_CELL_WIDTH
        cell_height = config.PREVIEW_CELL_HEIGHT

        # 根据复选框状态决定是否显示网格和背景色
        show_grid = self.show_grid_checkbox.isChecked()
        bg_color = Qt.lightGray if show_grid else Qt.white

        # 获取自定义间隔设置
        custom_spacing = (
            self.spacing_spinbox.value() if self.spacing_spinbox.value() != -1 else None
        )

        # 使用导出器生成预览图片
        return self.exporter.create_puzzle_image(
            cell_width,
            cell_height,
            bg_color=bg_color,
            draw_grid=show_grid,
            custom_spacing=custom_spacing,
        )


class ExportDialog(QDialog):
    """导出对话框"""

    def __init__(self, model: PuzzleModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.setWindowTitle("导出拼图")
        self.setModal(True)
        self.setup_ui()

    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)

        # 输出尺寸设置
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("单个格子输出尺寸:"))

        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(100, 10000)
        self.width_spinbox.setValue(config.GRID_OUTPUT_WIDTH)
        size_layout.addWidget(self.width_spinbox)

        size_layout.addWidget(QLabel("x"))

        self.height_spinbox = QSpinBox()
        self.height_spinbox.setRange(100, 10000)
        self.height_spinbox.setValue(config.GRID_OUTPUT_HEIGHT)
        size_layout.addWidget(self.height_spinbox)

        layout.addLayout(size_layout)

        # 间隔设置
        spacing_layout = QHBoxLayout()
        spacing_layout.addWidget(QLabel("图片间隔:"))

        self.spacing_spinbox = QSpinBox()
        self.spacing_spinbox.setRange(-1, 1000)
        self.spacing_spinbox.setValue(-1)  # 默认自动计算
        self.spacing_spinbox.setSpecialValueText("自动计算")
        self.spacing_spinbox.setSuffix(" px")
        spacing_layout.addWidget(self.spacing_spinbox)
        spacing_layout.addStretch()

        layout.addLayout(spacing_layout)

        # 预览信息
        self.info_label = QLabel()
        self._update_info()
        layout.addWidget(self.info_label)

        # 按钮
        button_layout = QHBoxLayout()

        export_button = QPushButton("导出")
        export_button.clicked.connect(self.accept)
        button_layout.addWidget(export_button)

        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        # 连接信号更新预览
        self.width_spinbox.valueChanged.connect(self._update_info)
        self.height_spinbox.valueChanged.connect(self._update_info)
        self.spacing_spinbox.valueChanged.connect(self._update_info)

    def _update_info(self):
        """更新信息显示"""
        total_width = self.width_spinbox.value() * self.model.cols
        total_height = self.height_spinbox.value() * self.model.rows
        spacing_text = (
            "自动间隔"
            if self.spacing_spinbox.value() == -1
            else f"{self.spacing_spinbox.value()}px间隔"
        )
        self.info_label.setText(
            f"总输出尺寸: {total_width} x {total_height} | {spacing_text}"
        )

    def get_export_settings(self):
        """获取导出设置"""
        custom_spacing = (
            self.spacing_spinbox.value() if self.spacing_spinbox.value() != -1 else None
        )
        return self.width_spinbox.value(), self.height_spinbox.value(), custom_spacing

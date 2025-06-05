# -*- coding: utf-8 -*-
"""
图片列表组件
"""
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QPushButton,
    QFileDialog,
    QGroupBox,
    QMessageBox,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QIcon

from models import PuzzleModel, ImageInfo, ImageOrientation
import config


class ImageListItem(QListWidgetItem):
    """图片列表项"""

    def __init__(self, image_info: ImageInfo, parent=None):
        super().__init__(parent)
        self.image_info = image_info
        self.update_display()

    def update_display(self):
        """更新显示"""
        # 设置图标
        try:
            pixmap = QPixmap(str(self.image_info.path))
            if not pixmap.isNull():
                # 创建缩略图
                thumbnail_size = 64
                scaled_pixmap = pixmap.scaled(
                    thumbnail_size,
                    thumbnail_size,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                self.setIcon(QIcon(scaled_pixmap))
        except Exception as e:
            print(f"无法创建缩略图 {self.image_info.path}: {e}")

        # 设置文本
        orientation_text = (
            "横屏"
            if self.image_info.orientation == ImageOrientation.HORIZONTAL
            else "竖屏"
        )
        text = f"{self.image_info.path.name}\n({orientation_text}, {self.image_info.width}x{self.image_info.height})"
        self.setText(text)

        # 设置提示
        self.setToolTip(str(self.image_info.path))


class ImageListWidget(QWidget):
    """图片列表组件"""

    image_selected = Signal(ImageInfo)  # 图片选择信号

    def __init__(self, model: PuzzleModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.selected_image = None
        self.setup_ui()
        self.update_lists()

    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)

        # 控制按钮
        button_layout = QHBoxLayout()

        load_button = QPushButton("加载图片目录")
        load_button.clicked.connect(self._load_directory)
        button_layout.addWidget(load_button)

        refresh_button = QPushButton("刷新列表")
        refresh_button.clicked.connect(self.update_lists)
        button_layout.addWidget(refresh_button)

        button_layout.addStretch()

        layout.addLayout(button_layout)

        # 创建滚动区域包含图片列表
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 图片列表容器
        lists_container = QWidget()
        lists_layout = QVBoxLayout(lists_container)

        # 未使用图片列表
        unused_group = QGroupBox("未使用图片")
        unused_layout = QVBoxLayout(unused_group)

        self.unused_list = QListWidget()
        self.unused_list.setMinimumHeight(200)  # 设置最小高度而非最大高度
        self.unused_list.itemClicked.connect(self._on_unused_item_clicked)
        self.unused_list.itemDoubleClicked.connect(self._on_unused_item_double_clicked)
        unused_layout.addWidget(self.unused_list)

        unused_info_layout = QHBoxLayout()
        self.unused_count_label = QLabel("数量: 0")
        unused_info_layout.addWidget(self.unused_count_label)
        unused_info_layout.addStretch()

        remove_unused_button = QPushButton("移除选中")
        remove_unused_button.clicked.connect(self._remove_unused_image)
        unused_info_layout.addWidget(remove_unused_button)

        unused_layout.addLayout(unused_info_layout)
        lists_layout.addWidget(unused_group)

        # 已使用图片列表
        used_group = QGroupBox("已使用图片")
        used_layout = QVBoxLayout(used_group)

        self.used_list = QListWidget()
        self.used_list.setMinimumHeight(200)  # 设置最小高度而非最大高度
        self.used_list.itemClicked.connect(self._on_used_item_clicked)
        self.used_list.itemDoubleClicked.connect(self._on_used_item_double_clicked)
        used_layout.addWidget(self.used_list)

        used_info_layout = QHBoxLayout()
        self.used_count_label = QLabel("数量: 0")
        used_info_layout.addWidget(self.used_count_label)
        used_info_layout.addStretch()

        return_button = QPushButton("返回未使用")
        return_button.clicked.connect(self._return_to_unused)
        used_info_layout.addWidget(return_button)

        used_layout.addLayout(used_info_layout)
        lists_layout.addWidget(used_group)

        # 当前选择信息
        selection_group = QGroupBox("当前选择")
        selection_layout = QVBoxLayout(selection_group)

        self.selection_label = QLabel("未选择图片")
        self.selection_label.setWordWrap(True)
        selection_layout.addWidget(self.selection_label)

        selection_button_layout = QHBoxLayout()

        self.preview_button = QPushButton("预览")
        self.preview_button.setEnabled(False)
        self.preview_button.clicked.connect(self._preview_image)
        selection_button_layout.addWidget(self.preview_button)

        self.clear_selection_button = QPushButton("清除选择")
        self.clear_selection_button.setEnabled(False)
        self.clear_selection_button.clicked.connect(self._clear_selection)
        selection_button_layout.addWidget(self.clear_selection_button)

        selection_layout.addLayout(selection_button_layout)
        lists_layout.addWidget(selection_group)

        # 将容器放入滚动区域
        scroll_area.setWidget(lists_container)
        layout.addWidget(scroll_area)

    def _load_directory(self):
        """加载图片目录"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择图片目录", str(Path.home())
        )

        if directory:
            try:
                count = self.model.load_images_from_directory(Path(directory))
                self.update_lists()
                QMessageBox.information(self, "加载完成", f"成功加载 {count} 张图片")
            except Exception as e:
                QMessageBox.warning(self, "加载失败", f"加载图片时出错: {e}")

    def _on_unused_item_clicked(self, item: QListWidgetItem):
        """未使用列表项点击"""
        if isinstance(item, ImageListItem):
            self._select_image(item.image_info)

    def _on_unused_item_double_clicked(self, item: QListWidgetItem):
        """未使用列表项双击"""
        if isinstance(item, ImageListItem):
            self._select_image(item.image_info)
            self.image_selected.emit(item.image_info)

    def _on_used_item_clicked(self, item: QListWidgetItem):
        """已使用列表项点击"""
        if isinstance(item, ImageListItem):
            self._select_image(item.image_info)

    def _on_used_item_double_clicked(self, item: QListWidgetItem):
        """已使用列表项双击"""
        # 双击已使用的图片可以从网格中移除
        if isinstance(item, ImageListItem):
            self._remove_from_grid(item.image_info)

    def _select_image(self, image_info: ImageInfo):
        """选择图片"""
        self.selected_image = image_info
        self._update_selection_display()

    def _clear_selection(self):
        """清除选择"""
        self.selected_image = None
        self._update_selection_display()

        # 清除列表选择
        self.unused_list.clearSelection()
        self.used_list.clearSelection()

    def _update_selection_display(self):
        """更新选择显示"""
        if self.selected_image:
            orientation_text = (
                "横屏"
                if self.selected_image.orientation == ImageOrientation.HORIZONTAL
                else "竖屏"
            )
            span_text = (
                "1个格子"
                if self.selected_image.orientation == ImageOrientation.HORIZONTAL
                else f"{config.VERTICAL_IMAGE_SPAN}个格子"
            )

            text = f"已选择: {self.selected_image.path.name}\n"
            text += f"方向: {orientation_text}\n"
            text += f"尺寸: {self.selected_image.width}x{self.selected_image.height}\n"
            text += f"占用: {span_text}"

            self.selection_label.setText(text)
            self.preview_button.setEnabled(True)
            self.clear_selection_button.setEnabled(True)
        else:
            self.selection_label.setText("未选择图片")
            self.preview_button.setEnabled(False)
            self.clear_selection_button.setEnabled(False)

    def _preview_image(self):
        """预览图片"""
        if self.selected_image:
            from PySide6.QtWidgets import QDialog, QLabel
            from PySide6.QtCore import Qt

            dialog = QDialog(self)
            dialog.setWindowTitle(f"预览 - {self.selected_image.path.name}")
            dialog.setModal(True)

            layout = QVBoxLayout(dialog)

            label = QLabel()
            pixmap = QPixmap(str(self.selected_image.path))
            if not pixmap.isNull():
                # 缩放到合适大小
                max_size = 800
                scaled_pixmap = pixmap.scaled(
                    max_size, max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                label.setPixmap(scaled_pixmap)

            layout.addWidget(label)

            dialog.exec()

    def _remove_unused_image(self):
        """移除未使用的图片"""
        current_item = self.unused_list.currentItem()
        if isinstance(current_item, ImageListItem):
            self.model.unused_images.remove(current_item.image_info)
            if self.selected_image == current_item.image_info:
                self._clear_selection()
            self.update_lists()

    def _return_to_unused(self):
        """将选中的已使用图片返回到未使用列表"""
        current_item = self.used_list.currentItem()
        if isinstance(current_item, ImageListItem):
            self._remove_from_grid(current_item.image_info)

    def _remove_from_grid(self, image_info: ImageInfo):
        """从网格中移除图片"""
        # 在网格中查找并移除该图片
        for row in range(self.model.rows):
            for col in range(self.model.cols):
                cell = self.model.get_cell(row, col)
                if cell and cell.image == image_info and cell.is_main_cell:
                    self.model.remove_image(row, col)
                    self.update_lists()
                    return

    def update_lists(self):
        """更新列表"""
        # 清空列表
        self.unused_list.clear()
        self.used_list.clear()

        # 添加未使用图片
        for image_info in self.model.unused_images:
            item = ImageListItem(image_info)
            self.unused_list.addItem(item)

        # 添加已使用图片
        for image_info in self.model.used_images:
            item = ImageListItem(image_info)
            self.used_list.addItem(item)

        # 更新计数
        self.unused_count_label.setText(f"数量: {len(self.model.unused_images)}")
        self.used_count_label.setText(f"数量: {len(self.model.used_images)}")

    def get_selected_image(self) -> Optional[ImageInfo]:
        """获取当前选择的图片"""
        return self.selected_image

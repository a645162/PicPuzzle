# -*- coding: utf-8 -*-
"""
网格组件
"""
from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen
from typing import Optional
import config
from models import PuzzleModel, ImageInfo, ImageOrientation


class GridCellWidget(QLabel):
    """网格单元格组件"""

    clicked = Signal(int, int)  # 点击信号，传递行列坐标

    def __init__(self, row: int, col: int, parent=None):
        super().__init__(parent)
        self.row = row
        self.col = col
        self.setFixedSize(config.GRID_PREVIEW_WIDTH, config.GRID_PREVIEW_HEIGHT)
        self.setStyleSheet(
            """
            QLabel {
                border: 2px solid #cccccc;
                background-color: #f0f0f0;
            }
            QLabel:hover {
                border: 2px solid #0078d4;
                background-color: #e3f2fd;
            }
        """
        )
        self.setAlignment(Qt.AlignCenter)
        self.setText(f"({row}, {col})")
        self.setScaledContents(True)

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.row, self.col)
        super().mousePressEvent(event)

    def set_image(self, image_info: Optional[ImageInfo], is_main_cell: bool = True):
        """设置图片"""
        if image_info is None:
            self.clear_image()
            return

        try:
            pixmap = QPixmap(str(image_info.path))
            if not pixmap.isNull():
                if image_info.orientation == ImageOrientation.VERTICAL:
                    if is_main_cell:
                        # 竖屏图片的主单元格，显示完整图片
                        # 计算竖屏图片应有的高度
                        vertical_height = config.VERTICAL_PREVIEW_HEIGHT
                        scaled_pixmap = pixmap.scaled(
                            config.GRID_PREVIEW_WIDTH,
                            vertical_height,
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation,
                        )
                        self.setPixmap(scaled_pixmap)
                        self.setStyleSheet(
                            """
                            QLabel {
                                border: 2px solid #4caf50;
                                background-color: #e8f5e8;
                            }
                        """
                        )
                    else:
                        # 竖屏图片的占位单元格
                        self.setPixmap(self._create_placeholder_pixmap())
                        self.setStyleSheet(
                            """
                            QLabel {
                                border: 2px solid #ff6b6b;
                                background-color: #ffe0e0;
                            }
                        """
                        )
                else:
                    # 横屏图片，使用标准尺寸
                    scaled_pixmap = pixmap.scaled(
                        self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    self.setPixmap(scaled_pixmap)
                    self.setStyleSheet(
                        """
                        QLabel {
                            border: 2px solid #4caf50;
                            background-color: #e8f5e8;
                        }
                    """
                    )
        except Exception as e:
            print(f"无法加载图片 {image_info.path}: {e}")
            self.clear_image()

    def clear_image(self):
        """清除图片"""
        self.clear()
        self.setText(f"({self.row}, {self.col})")
        self.setStyleSheet(
            """
            QLabel {
                border: 2px solid #cccccc;
                background-color: #f0f0f0;
            }
            QLabel:hover {
                border: 2px solid #0078d4;
                background-color: #e3f2fd;
            }
        """
        )

    def _create_placeholder_pixmap(self) -> QPixmap:
        """创建占位符图片"""
        pixmap = QPixmap(self.size())
        pixmap.fill(QColor(255, 224, 224))

        painter = QPainter(pixmap)
        painter.setPen(QPen(QColor(255, 107, 107), 2))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "竖屏占位")
        painter.end()

        return pixmap


class GridWidget(QWidget):
    """网格组件"""

    cell_clicked = Signal(int, int)  # 单元格点击信号

    def __init__(self, model: PuzzleModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.cells = []
        self.grid_layout = None
        self.setup_ui()
        self.update_grid()

    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)

        # 控制面板
        control_panel = QHBoxLayout()

        # 网格大小控制
        from PySide6.QtWidgets import QSpinBox, QLabel as QStaticLabel

        control_panel.addWidget(QStaticLabel("行数:"))
        self.rows_spinbox = QSpinBox()
        self.rows_spinbox.setRange(1, 20)
        self.rows_spinbox.setValue(self.model.rows)
        self.rows_spinbox.valueChanged.connect(self._on_grid_size_changed)
        control_panel.addWidget(self.rows_spinbox)

        control_panel.addWidget(QStaticLabel("列数:"))
        self.cols_spinbox = QSpinBox()
        self.cols_spinbox.setRange(1, 20)
        self.cols_spinbox.setValue(self.model.cols)
        self.cols_spinbox.valueChanged.connect(self._on_grid_size_changed)
        control_panel.addWidget(self.cols_spinbox)

        control_panel.addStretch()

        # 清空网格按钮
        clear_button = QPushButton("清空网格")
        clear_button.clicked.connect(self._clear_grid)
        control_panel.addWidget(clear_button)
        layout.addLayout(control_panel)

        # 创建滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 网格容器
        self.grid_container = QWidget()
        self.scroll_area.setWidget(self.grid_container)

        layout.addWidget(self.scroll_area)

    def _on_grid_size_changed(self):
        """网格大小改变"""
        rows = self.rows_spinbox.value()
        cols = self.cols_spinbox.value()
        self.model.resize_grid(rows, cols)
        self.update_grid()

    def _clear_grid(self):
        """清空网格"""
        for row in range(self.model.rows):
            for col in range(self.model.cols):
                self.model.remove_image(row, col)
        self.update_grid()

    def update_grid(self):
        """更新网格显示"""
        # 清除旧的网格
        if self.grid_layout:
            while self.grid_layout.count():
                child = self.grid_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            self.grid_container.layout().deleteLater()
        # 创建新的网格布局
        self.grid_layout = QGridLayout(self.grid_container)

        # 设置网格间隔
        # 根据竖屏和横屏视频的尺寸关系计算间隔
        self.grid_layout.setSpacing(config.GRID_SPACING)

        self.cells = []

        # 创建网格单元格
        for row in range(self.model.rows):
            cell_row = []
            for col in range(self.model.cols):
                cell_widget = GridCellWidget(row, col)
                cell_widget.clicked.connect(self._on_cell_clicked)
                self.grid_layout.addWidget(cell_widget, row, col)
                cell_row.append(cell_widget)
            self.cells.append(cell_row)

        # 更新显示
        self.refresh_display()

    def _on_cell_clicked(self, row: int, col: int):
        """单元格点击处理"""
        self.cell_clicked.emit(row, col)

    def refresh_display(self):
        """刷新显示"""
        for row in range(self.model.rows):
            for col in range(self.model.cols):
                cell = self.model.get_cell(row, col)
                if cell and len(self.cells) > row and len(self.cells[row]) > col:
                    cell_widget = self.cells[row][col]
                    cell_widget.set_image(cell.image, cell.is_main_cell)

    def place_image_at(self, row: int, col: int, image: ImageInfo) -> bool:
        """在指定位置放置图片"""
        success = self.model.place_image(row, col, image)
        if success:
            self.refresh_display()
        return success

    def remove_image_at(self, row: int, col: int) -> Optional[ImageInfo]:
        """移除指定位置的图片"""
        image = self.model.remove_image(row, col)
        if image:
            self.refresh_display()
        return image

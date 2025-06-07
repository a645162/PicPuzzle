# -*- coding: utf-8 -*-
"""
主窗口
"""
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QSplitter,
    QMessageBox,
    QFileDialog,
    QLabel,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction
from pathlib import Path
from datetime import datetime

import config

from models import PuzzleModel, ImageInfo, ImageOrientation
from grid_widget import GridWidget
from image_list_widget import ImageListWidget
from state_manager import StateManager
from preview_window import PreviewWindow
from region_editor_window import RegionEditorWindow


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()

        self.model = PuzzleModel(config.DEFAULT_GRID_ROWS, config.DEFAULT_GRID_COLS)
        self.state_manager = StateManager()
        self.is_modified = False  # 添加修改状态标记
        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()
        self.connect_signals()

        # 设置窗口
        self.setWindowTitle("拼图工具")
        self.setMinimumSize(1200, 800)
        self.resize(1600, 1000)
        self.update_window_title()  # 初始化窗口标题

    def setup_ui(self):
        """设置界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # 左侧：图片列表
        self.image_list_widget = ImageListWidget(self.model)
        self.image_list_widget.setMaximumWidth(400)
        splitter.addWidget(self.image_list_widget)

        # 右侧：网格
        self.grid_widget = GridWidget(self.model)
        splitter.addWidget(self.grid_widget)

        # 设置分割器比例
        splitter.setSizes([400, 1200])

    def setup_menu(self):
        """设置菜单"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")

        load_action = QAction("加载图片目录(&L)", self)
        load_action.setShortcut("Ctrl+L")
        load_action.triggered.connect(self._load_directory)
        file_menu.addAction(load_action)

        file_menu.addSeparator()

        # 状态保存/加载
        save_state_action = QAction("保存状态(&S)", self)
        save_state_action.setShortcut("Ctrl+S")
        save_state_action.triggered.connect(self._save_state)
        file_menu.addAction(save_state_action)

        load_state_action = QAction("加载状态(&O)", self)
        load_state_action.setShortcut("Ctrl+O")
        load_state_action.triggered.connect(self._load_state)
        file_menu.addAction(load_state_action)

        file_menu.addSeparator()

        # 预览与导出功能
        export_action = QAction("预览与导出拼图(&E)", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._show_preview)  # 直接连接到_show_preview
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")

        clear_grid_action = QAction("清空网格(&C)", self)
        clear_grid_action.setShortcut("Ctrl+R")
        clear_grid_action.triggered.connect(self._clear_grid)
        edit_menu.addAction(clear_grid_action)

        clear_images_action = QAction("清空图片列表(&I)", self)
        clear_images_action.triggered.connect(self._clear_images)
        edit_menu.addAction(clear_images_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")

        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        # 新增区域编辑菜单项
        # 区域编辑菜单
        region_menu = menubar.addMenu("区域(&R)")

        edit_region_action = QAction("区域编辑(&R)", self)
        edit_region_action.setShortcut("Ctrl+R")
        edit_region_action.triggered.connect(self._show_region_editor)
        region_menu.addAction(edit_region_action)

    def setup_status_bar(self):
        """设置状态栏"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("就绪")

        # 状态标签
        self.grid_status_label = QLabel()
        self.image_status_label = QLabel()

        self.status_bar.addPermanentWidget(self.grid_status_label)
        self.status_bar.addPermanentWidget(self.image_status_label)

        self.update_status()

    def connect_signals(self):
        """连接信号"""
        # 网格点击信号
        self.grid_widget.cell_clicked.connect(self._on_cell_clicked)

        # 图片选择信号
        self.image_list_widget.image_selected.connect(self._on_image_selected)

        # 定时更新状态
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)  # 每秒更新一次

    def set_modified(self, modified: bool = True):
        """设置修改状态"""
        if self.is_modified != modified:
            self.is_modified = modified
            self.update_window_title()

    def update_window_title(self):
        """更新窗口标题"""
        title = "拼图工具"
        if self.is_modified:
            title += " *"
        self.setWindowTitle(title)

    def closeEvent(self, event):
        """重写关闭事件"""
        if self.is_modified:
            tip_str = str(
                "当前有未保存的修改，确定要退出吗？\n\n"
                '点击"是"直接退出\n点击"否"取消退出\n'
                '点击"Save"保存后退出'
            )

            reply = QMessageBox.question(
                self,
                "确认退出",
                tip_str,
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Save,
                QMessageBox.Save,
            )

            if reply == QMessageBox.Save:
                # 保存状态
                self._save_state()
                # 如果保存成功（修改状态被清除），则退出
                if not self.is_modified:
                    event.accept()
                else:
                    event.ignore()
            elif reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def _on_cell_clicked(self, row: int, col: int):
        """处理网格点击"""
        cell = self.model.get_cell(row, col)

        if cell and cell.is_occupied:
            # 如果格子已被占用，询问是否移除图片
            reply = QMessageBox.question(
                self,
                "确认移除",
                f"确定要移除位置 ({row+1}, {col+1}) 的图片吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                image = self.grid_widget.remove_image_at(row, col)
                if image:
                    self.image_list_widget.update_lists()
                    self.status_bar.showMessage(f"已移除图片: {image.path.name}")
                    self.set_modified(True)  # 标记为已修改
        else:
            # 如果格子空闲，尝试放置选中的图片
            selected_image = self.image_list_widget.get_selected_image()
            if selected_image:
                # 检查是否会替换现有图片（对于竖屏图片）
                will_replace = False
                replaced_images = []

                if selected_image.orientation == ImageOrientation.VERTICAL:
                    # 检查竖屏图片占用的所有格子
                    for r in range(
                        row, min(row + config.VERTICAL_IMAGE_SPAN, self.model.rows)
                    ):
                        check_cell = self.model.get_cell(r, col)
                        if check_cell and check_cell.is_occupied and check_cell.image:
                            will_replace = True
                            if check_cell.image not in replaced_images:
                                replaced_images.append(check_cell.image)

                # 如果会替换现有图片，询问确认
                if will_replace:
                    image_names = [img.path.name for img in replaced_images]
                    reply = QMessageBox.question(
                        self,
                        "确认替换",
                        f"放置此图片将替换以下图片：\n{', '.join(image_names)}\n\n确定要继续吗？",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No,
                    )

                    if reply != QMessageBox.Yes:
                        return

                if self.grid_widget.place_image_at(row, col, selected_image):
                    self.image_list_widget.update_lists()
                    self.status_bar.showMessage(
                        f"已放置图片: {selected_image.path.name}"
                    )
                    self.set_modified(True)  # 标记为已修改
                else:
                    # 检查失败原因
                    if selected_image.orientation == ImageOrientation.VERTICAL:
                        if row + config.VERTICAL_IMAGE_SPAN > self.model.rows:
                            QMessageBox.warning(
                                self,
                                "放置失败",
                                f"竖屏图片需要{config.VERTICAL_IMAGE_SPAN}个格子的高度，当前位置不够",
                            )
                        else:
                            QMessageBox.warning(
                                self, "放置失败", "目标位置的某些格子已被占用"
                            )
                    else:
                        QMessageBox.warning(self, "放置失败", "目标位置已被占用")
            else:
                self.status_bar.showMessage("请先选择一张图片")

    def _on_image_selected(self, image: ImageInfo):
        """处理图片选择"""
        orientation_text = (
            "横屏" if image.orientation == ImageOrientation.HORIZONTAL else "竖屏"
        )
        self.status_bar.showMessage(
            f"已选择 {orientation_text} 图片: {image.path.name}"
        )

    def _load_directory(self):
        """加载图片目录"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择图片目录", str(Path.home())
        )

        if directory:
            try:
                count = self.model.load_images_from_directory(Path(directory))
                self.image_list_widget.update_lists()
                self.status_bar.showMessage(f"成功加载 {count} 张图片")

                if count > 0:
                    self.set_modified(True)  # 标记为已修改

                if count == 0:
                    QMessageBox.information(
                        self,
                        "加载完成",
                        f"目录中没有找到符合16:9比例的图片\n支持格式: {', '.join(config.SUPPORTED_IMAGE_FORMATS)}",
                    )
                else:
                    QMessageBox.information(
                        self, "加载完成", f"成功加载 {count} 张图片"
                    )
            except Exception as e:
                QMessageBox.warning(self, "加载失败", f"加载图片时出错: {e}")

    def _clear_grid(self):
        """清空网格"""
        reply = QMessageBox.question(
            self,
            "确认清空",
            "确定要清空整个网格吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            for row in range(self.model.rows):
                for col in range(self.model.cols):
                    self.model.remove_image(row, col)

            self.grid_widget.refresh_display()
            self.image_list_widget.update_lists()
            self.status_bar.showMessage("网格已清空")
            self.set_modified(True)  # 标记为已修改

    def _clear_images(self):
        """清空图片列表"""
        reply = QMessageBox.question(
            self,
            "确认清空",
            "确定要清空所有图片吗？这将同时清空网格。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # 先清空网格
            for row in range(self.model.rows):
                for col in range(self.model.cols):
                    self.model.remove_image(row, col)

            # 清空图片列表
            self.model.unused_images.clear()
            self.model.used_images.clear()

            self.grid_widget.refresh_display()
            self.image_list_widget.update_lists()
            self.image_list_widget._clear_selection()
            self.status_bar.showMessage("所有图片已清空")
            self.set_modified(True)  # 标记为已修改

    def _show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于拼图工具",
            "拼图工具 v1.0\n\n"
            "作者：孔昊旻\n\n"
            "功能特性:\n"
            "• 支持横屏和竖屏图片（16:9比例）\n"
            "• 可调整网格大小\n"
            "• 竖屏图片自动占用3个格子\n"
            "• 支持图片预览和导出\n"
            "• 直观的拖拽式操作\n\n"
            "使用方法:\n"
            "1. 加载图片目录\n"
            "2. 选择图片\n"
            "3. 点击网格格子放置图片\n"
            "4. 导出最终拼图",
        )

    def _save_state(self):
        """保存当前状态"""
        try:
            # Current Py Dir
            current_py_dir = Path(__file__).parent

            default_dir = current_py_dir / "data"
            default_dir.mkdir(parents=True, exist_ok=True)

            # 选择保存位置
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存状态",
                str(
                    default_dir
                    / f"puzzle_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                ),
                "JSON文件 (*.json);;所有文件 (*.*)",
            )

            if save_path:
                filename = self.state_manager.save_state(self.model, save_path)
                QMessageBox.information(self, "保存成功", f"状态已保存到: {filename}")
                self.status_bar.showMessage("状态保存成功")
                self.set_modified(False)  # 清除修改状态
        except Exception as e:
            QMessageBox.warning(self, "保存失败", f"保存状态时出错: {e}")

    def _load_state(self):
        """加载状态"""
        try:
            current_py_dir = Path(__file__).parent

            default_dir = current_py_dir / "data"

            if not default_dir.exists():
                # 选择状态文件
                load_path, _ = QFileDialog.getOpenFileName(
                    self,
                    "加载状态",
                    str(Path.home()),
                    "JSON文件 (*.json);;所有文件 (*.*)",
                )
            else:
                # 默认目录存在，直接使用
                load_path, _ = QFileDialog.getOpenFileName(
                    self,
                    "加载状态",
                    str(default_dir),
                    "JSON文件 (*.json);;所有文件 (*.*)",
                )

            if load_path:
                # 确认加载
                warning_text = "加载状态将清空当前的网格和图片列表，确定要继续吗？"
                if self.is_modified:
                    warning_text = "当前有未保存的修改！\n" + warning_text

                reply = QMessageBox.question(
                    self,
                    "确认加载",
                    warning_text,
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )

                if reply == QMessageBox.Yes:
                    state_data = self.state_manager.load_state(load_path)
                    if state_data:
                        success = self.state_manager.apply_state_to_model(
                            self.model, state_data
                        )
                        if success:
                            # 刷新界面
                            self.grid_widget.refresh_display()
                            self.image_list_widget.update_lists()
                            self.image_list_widget._clear_selection()

                            QMessageBox.information(
                                self, "加载成功", f"状态已从 {load_path} 加载"
                            )
                            self.status_bar.showMessage("状态加载成功")
                            self.set_modified(False)  # 清除修改状态
                        else:
                            QMessageBox.warning(
                                self, "加载失败", "应用状态到模型时失败"
                            )
                    else:
                        QMessageBox.warning(self, "加载失败", "读取状态文件失败")
        except Exception as e:
            QMessageBox.warning(self, "加载失败", f"加载状态时出错: {e}")

    def update_status(self):
        """更新状态栏"""
        # 网格状态
        occupied_cells = 0
        total_cells = self.model.rows * self.model.cols

        for row in range(self.model.rows):
            for col in range(self.model.cols):
                cell = self.model.get_cell(row, col)
                if cell and cell.is_occupied:
                    occupied_cells += 1

        self.grid_status_label.setText(
            f"网格: {self.model.rows}x{self.model.cols} ({occupied_cells}/{total_cells})"
        )

        # 图片状态
        unused_count = len(self.model.unused_images)
        used_count = len(self.model.used_images)
        total_images = unused_count + used_count

        self.image_status_label.setText(
            f"图片: {total_images}张 (已用:{used_count}, 未用:{unused_count})"
        )

    def _show_preview(self):
        """显示预览窗口"""
        # 检查是否有图片
        has_images = False
        for row in range(self.model.rows):
            for col in range(self.model.cols):
                cell = self.model.get_cell(row, col)
                if cell and cell.is_occupied and cell.is_main_cell:
                    has_images = True
                    break
            if has_images:
                break

        if not has_images:
            QMessageBox.information(self, "预览失败", "网格中没有任何图片")
            return

        # 创建并显示预览窗口
        preview_window = PreviewWindow(self.model, self)
        preview_window.show()
        preview_window.raise_()  # 将窗口提到前台
        preview_window.activateWindow()  # 激活窗口

    def _show_region_editor(self):
        """显示区域编辑窗口"""
        if not hasattr(self, "region_editor") or not self.region_editor:
            self.region_editor = RegionEditorWindow(self.model, self)
        self.region_editor.show()
        self.region_editor.raise_()  # 将窗口提到前台
        self.region_editor.activateWindow()  # 激活窗口

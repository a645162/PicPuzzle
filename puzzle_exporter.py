# -*- coding: utf-8 -*-
"""
拼图导出器
"""
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtCore import Qt

import config
from models import PuzzleModel, ImageOrientation


class PuzzleExporter:
    """拼图导出器"""

    def __init__(self, model: PuzzleModel):
        self.model = model

    def get_valid_area(self):
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

    def calculate_spacing(self, cell_height: int):
        """
        计算精确的间隔值

        基于16:9比例的实际计算：
        - 横屏视频：宽W，高H = W × 9/16
        - 竖屏视频：宽W，高V = W × 16/9

        由于宽度相同，我们有：
        - 横屏高度：H = W × 9/16
        - 竖屏高度：V = W × 16/9

        竖屏高度与横屏高度的比例：
        V/H = (W × 16/9) / (W × 9/16) = (16/9) / (9/16) = (16/9) × (16/9) = 256/81

        因此：V = H × 256/81

        竖屏占用3个格子高度加2个间隔：
        V = 3H + 2×spacing

        代入得：H × 256/81 = 3H + 2×spacing

        解得：spacing = (H × 256/81 - 3H) / 2
                     = H × (256/81 - 3) / 2
                     = H × (256 - 243) / (81 × 2)
                     = H × 13 / 162

        但这个计算有问题，让我重新理解：

        实际上，如果我们固定宽度相同，那么：
        - cell_height 就是横屏的高度
        - 竖屏的实际高度应该是 cell_height × 16/9 ÷ 9/16 = cell_height × (16/9) × (16/9) = cell_height × 256/81

        但这样竖屏会非常高。让我重新理解需求：

        实际上应该是：
        - 横屏：宽度W，高度 cell_height
        - 竖屏：宽度W（相同），高度按比例应该是 W × 16/9
        - 但由于 cell_height = W × 9/16，所以 W = cell_height × 16/9
        - 因此竖屏高度 = (cell_height × 16/9) × 16/9 = cell_height × 256/81

        这太高了。让我重新理解：应该是竖屏和横屏都保持16:9比例，但宽度相同。

        如果宽度相同为W：
        - 横屏：宽W，高 W×9/16
        - 竖屏：宽W，高 W×16/9

        竖屏高度/横屏高度 = (W×16/9) / (W×9/16) = 256/81 ≈ 3.16

        由于占用3个格子+2个间隔：
        W×16/9 = 3×(W×9/16) + 2×spacing
        W×16/9 = 3W×9/16 + 2×spacing
        W×16/9 = W×27/16 + 2×spacing
        2×spacing = W×16/9 - W×27/16
        2×spacing = W×(16×16 - 27×9)/(9×16)
        2×spacing = W×(256 - 243)/144
        2×spacing = W×13/144
        spacing = W×13/288

        由于 cell_height = W×9/16，所以 W = cell_height×16/9
        spacing = (cell_height×16/9)×13/288 = cell_height×13×16/(288×9) = cell_height×208/2592 = cell_height×13/162

        验证这个结果：这确实是正确的数学计算。
        但为了更清晰，我们直接用比例关系：
        """
        # 基于16:9比例的实际计算
        # 横屏高度：cell_height
        # 竖屏高度：cell_height × (16/9) / (9/16) = cell_height × 256/81
        vertical_height = cell_height * 256 // 81

        # 竖屏占用3个格子高度 + 2个间隔 = 竖屏实际高度
        # 3 × cell_height + 2 × spacing = vertical_height
        # spacing = (vertical_height - 3 × cell_height) / 2
        spacing = (vertical_height - 3 * cell_height) // 2

        return max(spacing, 1)  # 确保间隔至少为1像素

    def create_puzzle_image(
        self,
        cell_width: int,
        cell_height: int,
        bg_color=Qt.white,
        draw_grid=False,
        custom_spacing=None,
        show_indices=False,
    ):
        """
        创建拼图图片

        参数:
            cell_width: 单元格宽度
            cell_height: 单元格高度
            bg_color: 背景颜色，默认为白色
            draw_grid: 是否绘制网格线，突出显示间隔
            custom_spacing: 自定义间隔，如果为None则自动计算
        """
        # 计算有效区域
        valid_area = self.get_valid_area()
        if valid_area is None:
            raise ValueError("没有找到任何图片")

        min_row, max_row, min_col, max_col = valid_area

        # 计算有效区域的尺寸
        valid_rows = max_row - min_row + 1
        valid_cols = max_col - min_col + 1

        # 计算间隔尺寸
        if custom_spacing is not None:
            spacing = custom_spacing
        else:
            spacing = self.calculate_spacing(cell_height)

        # 确保间隔至少为0像素
        spacing = max(spacing, 0)

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
        )  # 创建输出图片
        output_pixmap = QPixmap(total_width, total_height)
        # 使用指定的背景颜色
        output_pixmap.fill(bg_color)

        painter = QPainter(output_pixmap)
        try:
            # 绘制网格线，显示间隔
            if draw_grid:
                painter.setPen(Qt.darkGray)
                # 绘制垂直线
                for col in range(valid_cols + 1):
                    x = col * (cell_width + spacing) - spacing // 2
                    painter.drawLine(x, 0, x, total_height)
                # 绘制水平线
                for row in range(valid_rows + 1):
                    y = row * (cell_height + spacing) - spacing // 2
                    painter.drawLine(0, y, total_width, y)

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
                            target_height = (
                                cell_height * config.VERTICAL_IMAGE_SPAN
                                + spacing * (config.VERTICAL_IMAGE_SPAN - 1)
                            )
                        else:
                            # 横屏图片：标准1个格子
                            target_width = cell_width
                            target_height = (
                                cell_height  # 绘制单元格背景（如果需要显示间隔）
                            )
                        if draw_grid:
                            painter.fillRect(
                                x, y, target_width, target_height, Qt.white
                            )

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

            # 绘制行号和列号
            if show_indices:
                painter.setPen(Qt.red)
                painter.setFont(painter.font())
                font = painter.font()
                font.setPointSize(max(8, min(cell_width, cell_height) // 10))
                font.setBold(True)
                painter.setFont(font)

                # 绘制列号（在顶部）
                for col in range(min_col, max_col + 1):
                    relative_col = col - min_col
                    x = relative_col * (cell_width + spacing) + cell_width // 2
                    painter.drawText(x - 10, 15, f"{col}")

                # 绘制行号（在左侧）
                for row in range(min_row, max_row + 1):
                    relative_row = row - min_row
                    y = relative_row * (cell_height + spacing) + cell_height // 2
                    painter.drawText(5, y + 5, f"{row}")

        finally:
            painter.end()

        return output_pixmap

    def export_to_file(
        self, save_path: str, cell_width: int, cell_height: int, custom_spacing=None
    ):
        """导出拼图到文件"""
        # 导出时不显示网格线，使用纯白色背景
        output_pixmap = self.create_puzzle_image(
            cell_width,
            cell_height,
            bg_color=Qt.white,
            draw_grid=False,
            custom_spacing=custom_spacing,
        )
        output_pixmap.save(save_path)

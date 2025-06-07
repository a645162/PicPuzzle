# -*- coding: utf-8 -*-
"""
数据模型
"""
from enum import Enum
from typing import Optional, List
from dataclasses import dataclass
from pathlib import Path


class ImageOrientation(Enum):
    """图片方向枚举"""

    HORIZONTAL = "horizontal"  # 横屏
    VERTICAL = "vertical"  # 竖屏


@dataclass
class ImageInfo:
    """图片信息数据类"""

    path: Path
    orientation: ImageOrientation
    width: int
    height: int

    def __str__(self):
        return f"{self.path.name} ({self.orientation.value})"


@dataclass
class GridCell:
    """网格单元格数据类"""

    row: int
    col: int
    image: Optional[ImageInfo] = None
    is_occupied: bool = False
    is_main_cell: bool = True  # 是否是主单元格（对于竖屏图片，只有左上角是主单元格）
    main_position: Optional[tuple] = (
        None  # 如果是竖屏图片的占位格子，存储主格子的坐标 (row, col)
    )

    def __post_init__(self):
        self.id = f"{self.row}_{self.col}"


class PuzzleModel:
    """拼图模型类"""

    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        self.grid: List[List[GridCell]] = []
        self.used_images: List[ImageInfo] = []
        self.unused_images: List[ImageInfo] = []
        self.image_directory: Optional[Path] = None  # 图片目录路径
        self._initialize_grid()

    def _initialize_grid(self):
        """初始化网格"""
        self.grid = []
        for row in range(self.rows):
            grid_row = []
            for col in range(self.cols):
                grid_row.append(GridCell(row, col))
            self.grid.append(grid_row)

    def resize_grid(self, rows: int, cols: int):
        """调整网格大小"""
        # 保存当前图片
        current_images = []
        for row in self.grid:
            for cell in row:
                if cell.image and cell.is_main_cell:
                    current_images.append(cell.image)

        # 重置网格
        self.rows = rows
        self.cols = cols
        self._initialize_grid()

        # 将图片移回未使用列表
        self.unused_images.extend(current_images)
        self.used_images.clear()

    def can_place_image(self, row: int, col: int, image: ImageInfo) -> bool:
        """检查是否可以放置图片"""
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            return False

        if image.orientation == ImageOrientation.HORIZONTAL:
            # 横屏图片只占一个格子
            return not self.grid[row][col].is_occupied
        else:
            # 竖屏图片占3个格子（垂直方向）
            if row + 2 >= self.rows:  # 检查是否有足够的行
                return False

            for i in range(3):
                if self.grid[row + i][col].is_occupied:
                    return False
            return True

    def place_image(self, row: int, col: int, image: ImageInfo) -> bool:
        """放置图片"""
        if not self.can_place_image(row, col, image):
            return False

        if image.orientation == ImageOrientation.HORIZONTAL:
            # 横屏图片
            self.grid[row][col].image = image
            self.grid[row][col].is_occupied = True
            self.grid[row][col].is_main_cell = True
            self.grid[row][col].main_position = None  # 横屏图片无需main_position
        else:
            # 竖屏图片占3个格子
            for i in range(3):
                self.grid[row + i][col].image = image
                self.grid[row + i][col].is_occupied = True
                self.grid[row + i][col].is_main_cell = i == 0  # 只有第一个是主单元格
                # 为非主格子设置main_position指向主格子
                if i == 0:
                    self.grid[row + i][col].main_position = None  # 主格子自身
                else:
                    self.grid[row + i][col].main_position = (row, col)  # 指向主格子

        # 移动到已使用列表
        if image in self.unused_images:
            self.unused_images.remove(image)
        if image not in self.used_images:
            self.used_images.append(image)

        return True

    def remove_image(self, row: int, col: int) -> Optional[ImageInfo]:
        """移除图片"""
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            return None

        cell = self.grid[row][col]
        if not cell.is_occupied or not cell.image:
            return None

        image = cell.image

        # 找到这个图片占据的所有格子并清空
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c].image == image:
                    self.grid[r][c].image = None
                    self.grid[r][c].is_occupied = False
                    self.grid[r][c].is_main_cell = True
                    self.grid[r][c].main_position = None  # 移动到未使用列表
        if image in self.used_images:
            self.used_images.remove(image)
        if image not in self.unused_images:
            self.unused_images.append(image)

        return image

    def get_cell(self, row: int, col: int) -> Optional[GridCell]:
        """获取单元格"""
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            return None
        return self.grid[row][col]

    def get_main_cell_position(self, row: int, col: int) -> tuple[int, int]:
        """
        获取指定位置对应的主格子位置
        如果是竖屏图片的非主格子，则返回其main_position
        如果是主格子或横屏图片，则返回自身位置
        """
        cell = self.get_cell(row, col)
        if cell and cell.is_occupied and cell.main_position is not None:
            # 这是竖屏图片的非主格子，返回主格子位置
            return cell.main_position
        else:
            # 这是主格子或空格子，返回自身位置
            return (row, col)

    def load_images_from_directory(self, directory: Path) -> int:
        """从目录加载图片"""
        from PIL import Image
        import config

        loaded_count = 0

        if not directory.exists() or not directory.is_dir():
            return loaded_count  # 保存图片目录路径
        self.image_directory = directory

        for file_path in directory.iterdir():
            if file_path.suffix.lower() in config.SUPPORTED_IMAGE_FORMATS:
                try:
                    with Image.open(file_path) as img:
                        width, height = img.size  # 判断图片方向（简单的宽高比较）
                        if width > height:
                            orientation = ImageOrientation.HORIZONTAL
                        elif height > width:
                            orientation = ImageOrientation.VERTICAL
                        else:
                            continue  # 跳过正方形图片

                        image_info = ImageInfo(
                            path=file_path,
                            orientation=orientation,
                            width=width,
                            height=height,
                        )

                        if image_info not in self.unused_images:
                            self.unused_images.append(image_info)
                            loaded_count += 1

                except Exception as e:
                    print(f"无法加载图片 {file_path}: {e}")

        return loaded_count

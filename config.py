# -*- coding: utf-8 -*-
"""
配置文件
"""

# 网格配置
# 预览配置
PREVIEW_CELL_WIDTH = 160
PREVIEW_CELL_HEIGHT = PREVIEW_CELL_WIDTH * 9 // 16  # 90

# 输出配置
GRID_OUTPUT_WIDTH = 1920
GRID_OUTPUT_HEIGHT = 1080

# 竖屏图片占据的格子数（纵向）
VERTICAL_IMAGE_SPAN = 3


# 计算间隔 - 预览和输出都使用动态计算
def calculate_spacing(cell_height: int) -> int:
    """计算格子间距，确保3个横屏图片的高度等于1个竖屏图片的高度"""
    vertical_height = cell_height * VERTICAL_IMAGE_SPAN
    horizontal_height = cell_height
    # 3个横屏 + 2个间隔 = 1个竖屏
    # spacing = (vertical_height - 3 * horizontal_height) / 2
    return max(0, (vertical_height - 3 * horizontal_height) // 2)


# 状态文件配置
DATA_DIR = "data"
STATE_FILE_EXTENSION = ".json"

# 默认网格行列数
DEFAULT_GRID_ROWS = 13
DEFAULT_GRID_COLS = 10

# 支持的图片格式
SUPPORTED_IMAGE_FORMATS = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"]

# 图片比例（16:9）
IMAGE_ASPECT_RATIO = 16 / 9  # 横屏比例 ≈ 1.778
VERTICAL_ASPECT_RATIO = 9 / 16  # 竖屏比例 ≈ 0.5625

# -*- coding: utf-8 -*-
"""
状态管理模块
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import config
from models import PuzzleModel, ImageInfo, ImageOrientation


class StateManager:
    """状态管理器"""

    def __init__(self):
        # 确保数据目录存在
        self.data_dir = Path(config.DATA_DIR)
        self.data_dir.mkdir(exist_ok=True)

    def save_state(
        self, model: PuzzleModel, custom_filename: Optional[str] = None
    ) -> str:
        """保存当前状态到JSON文件"""
        # 生成文件名
        if custom_filename:
            filename = custom_filename
            if not filename.endswith(config.STATE_FILE_EXTENSION):
                filename += config.STATE_FILE_EXTENSION
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}{config.STATE_FILE_EXTENSION}"

        file_path = self.data_dir / filename

        # 构建状态数据
        state_data = {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "image_directory": (
                str(model.image_directory) if model.image_directory else None
            ),
            "grid_config": {
                "rows": model.rows,
                "cols": model.cols,
                "preview_width": config.GRID_PREVIEW_WIDTH,
                "preview_height": config.GRID_PREVIEW_HEIGHT,
                "output_width": config.GRID_OUTPUT_WIDTH,
                "output_height": config.GRID_OUTPUT_HEIGHT,
                "spacing": config.GRID_SPACING,
                "output_spacing": config.OUTPUT_SPACING,
            },
            "images": {
                "unused": [
                    self._serialize_image(img, model.image_directory)
                    for img in model.unused_images
                ],
                "used": [
                    self._serialize_image(img, model.image_directory)
                    for img in model.used_images
                ],
            },
            "grid_layout": [],
        }

        # 保存网格布局
        for row in range(model.rows):
            grid_row = []
            for col in range(model.cols):
                cell = model.get_cell(row, col)
                if cell and cell.image and cell.is_main_cell:
                    cell_data = {
                        "row": row,
                        "col": col,
                        "image": self._serialize_image(
                            cell.image, model.image_directory
                        ),
                        "is_main_cell": True,
                    }
                    grid_row.append(cell_data)
                else:
                    grid_row.append(None)
            state_data["grid_layout"].append(grid_row)

        # 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=2, ensure_ascii=False)

        return str(file_path)

    def load_state(self, file_path: str) -> Optional[Dict[str, Any]]:
        """从JSON文件加载状态"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                state_data = json.load(f)
            return state_data
        except Exception as e:
            print(f"加载状态文件失败: {e}")
            return None

    def apply_state_to_model(
        self, model: PuzzleModel, state_data: Dict[str, Any]
    ) -> bool:
        """将状态应用到模型"""
        try:
            # 重置模型
            grid_config = state_data.get("grid_config", {})
            rows = grid_config.get("rows", config.DEFAULT_GRID_ROWS)
            cols = grid_config.get("cols", config.DEFAULT_GRID_COLS)

            model.resize_grid(rows, cols)

            # 获取图片目录
            image_directory_str = state_data.get("image_directory")
            image_directory = Path(image_directory_str) if image_directory_str else None

            # 设置模型的图片目录
            if image_directory:
                model.image_directory = image_directory

            # 加载图片列表
            images_data = state_data.get("images", {})

            # 清空现有图片
            model.unused_images.clear()
            model.used_images.clear()

            # 加载未使用图片
            for img_data in images_data.get("unused", []):
                image_info = self._deserialize_image(img_data, image_directory)
                if image_info and image_info.path.exists():
                    model.unused_images.append(image_info)

            # 加载已使用图片
            for img_data in images_data.get("used", []):
                image_info = self._deserialize_image(img_data, image_directory)
                if image_info and image_info.path.exists():
                    model.used_images.append(image_info)

            # 恢复网格布局
            grid_layout = state_data.get("grid_layout", [])
            for row_idx, grid_row in enumerate(grid_layout):
                if row_idx >= model.rows:
                    break
                for col_idx, cell_data in enumerate(grid_row):
                    if col_idx >= model.cols or not cell_data:
                        continue

                    image_data = cell_data.get("image")
                    if image_data:
                        image_info = self._deserialize_image(
                            image_data, image_directory
                        )
                        if image_info and image_info.path.exists():
                            # 确保图片在已使用列表中
                            if image_info not in model.used_images:
                                model.used_images.append(image_info)
                            if image_info in model.unused_images:
                                model.unused_images.remove(image_info)

                            # 放置图片
                            model.place_image(row_idx, col_idx, image_info)

            return True

        except Exception as e:
            print(f"应用状态到模型失败: {e}")
            return False

    def _serialize_image(
        self, image_info: ImageInfo, image_directory: Optional[Path] = None
    ) -> Dict[str, Any]:
        """序列化图片信息"""
        # 如果提供了图片目录，则保存相对路径，否则保存绝对路径（向后兼容）
        if image_directory:
            try:
                # 计算相对于图片目录的相对路径
                relative_path = image_info.path.relative_to(image_directory)
                path_str = str(relative_path)
            except ValueError:
                # 如果无法计算相对路径，则使用绝对路径
                path_str = str(image_info.path)
        else:
            path_str = str(image_info.path)

        return {
            "path": path_str,
            "orientation": image_info.orientation.value,
            "width": image_info.width,
            "height": image_info.height,
        }

    def _deserialize_image(
        self, image_data: Dict[str, Any], image_directory: Optional[Path] = None
    ) -> Optional[ImageInfo]:
        """反序列化图片信息"""
        try:
            path_str = image_data["path"]
            path = Path(path_str)

            # 如果路径不是绝对路径且提供了图片目录，则构建绝对路径
            if not path.is_absolute() and image_directory:
                path = image_directory / path

            orientation = ImageOrientation(image_data["orientation"])
            width = image_data["width"]
            height = image_data["height"]

            return ImageInfo(
                path=path, orientation=orientation, width=width, height=height
            )
        except Exception as e:
            print(f"反序列化图片信息失败: {e}")
            return None

    def list_state_files(self) -> List[str]:
        """列出所有状态文件"""
        if not self.data_dir.exists():
            return []

        state_files = []
        for file_path in self.data_dir.iterdir():
            if file_path.suffix == config.STATE_FILE_EXTENSION:
                state_files.append(str(file_path))

        # 按修改时间排序（最新的在前）
        state_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return state_files

    def get_state_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """获取状态文件基本信息"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                state_data = json.load(f)

            grid_config = state_data.get("grid_config", {})
            images_data = state_data.get("images", {})

            return {
                "filename": Path(file_path).name,
                "timestamp": state_data.get("timestamp", ""),
                "grid_size": f"{grid_config.get('rows', 0)}x{grid_config.get('cols', 0)}",
                "unused_count": len(images_data.get("unused", [])),
                "used_count": len(images_data.get("used", [])),
                "total_images": len(images_data.get("unused", []))
                + len(images_data.get("used", [])),
            }
        except Exception as e:
            print(f"获取状态文件信息失败: {e}")
            return None

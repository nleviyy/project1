import json
from pathlib import Path
from typing import List, Optional, Any, Union

from src.models.MenuItem import MenuItem
from src.models.HashTable import HashNode, HashTable
from src.core.paths import MENU_PATH
from src.core.JSONStorage import load_data, save_data

__all__ = ["HashNode", "HashTable", "MenuCatalog"]


class MenuCatalog:
    def __init__(self):
        self._items: HashTable = HashTable()

    def load_from_dict(self, data: Any):
        self._items.clear()
        if not data:
            return

        if isinstance(data, list):
            items_list = data
        elif isinstance(data, dict):
            items_list = data.values()
        else:
            return

        for info in items_list:
            if not isinstance(info, dict):
                continue
            try:
                item = MenuItem.from_dict(info)
                self._items.put(item.id, item)
            except Exception as e:
                key = info.get("id", info.get("item_id", ""))
                print(f"[Cảnh báo] Bỏ qua món ID {key} do dữ liệu không hợp lệ: {e}")

    def load_from_file(self, file_path: Optional[Union[str, Path]] = None) -> bool:
        """Đọc thực đơn trực tiếp từ file JSON."""
        target = Path(file_path) if file_path else MENU_PATH
        if not target.exists():
            return False
        try:
            data = load_data(target, default_data=[])
            self.load_from_dict(data)
            return True
        except Exception as e:
            print(f"[Lỗi MenuCatalog] Không thể tải dữ liệu từ '{target}': {e}")
            return False

    def save_to_file(self, file_path: Optional[Union[str, Path]] = None) -> bool:
        """Lưu toàn bộ danh mục món ăn hiện tại ra file JSON."""
        target = Path(file_path) if file_path else MENU_PATH
        try:
            save_data(target, self.to_dict())
            return True
        except Exception as e:
            print(f"[Lỗi MenuCatalog] Không thể lưu file '{target}': {e}")
            return False

    def to_dict(self) -> list:
        return [item.to_dict() for item in self._items.values()]

    def to_list(self) -> list:
        return self.to_dict()

    def add_item(self, item: MenuItem) -> bool:
        if not isinstance(item, MenuItem):
            raise TypeError("Đối tượng thêm vào phải thuộc lớp MenuItem.")
        
        if item.id in self._items:
            return False
        
        self._items.put(item.id, item)
        return True

    def update_item(self, item_id: str, **kwargs) -> bool:
        item = self.get_item(item_id)
        if not item:
            return False

        kwargs.pop("id", None)
        kwargs.pop("item_id", None)

        key_mapping = {
            "unit_price": "price",
            "status": "is_available",
            "item_type": "category"
        }

        current_data = item.to_dict() if hasattr(item, "to_dict") else item.model_dump()

        for k, v in kwargs.items():
            actual_key = key_mapping.get(k, k)
            if actual_key in current_data:
                current_data[actual_key] = v

        try:
            validated_item = MenuItem(**current_data)
            self._items.put(item_id, validated_item)
            return True
        except Exception as e:
            print(f"[Lỗi cập nhật] Dữ liệu cập nhật món ID '{item_id}' không hợp lệ: {e}")
            return False

    def remove_item(self, item_id: str) -> bool:
        return self._items.remove(item_id)

    def get_item(self, item_id: str) -> Optional[MenuItem]:
        return self._items.get(item_id)

    def get_all_items(self) -> List[MenuItem]:
        return list(self._items.values())

    def search_items(self, keyword: str) -> List[MenuItem]:
        """Tìm món theo tên hoặc mã món qua vòng lặp tuyến tính (tự viết)."""
        if not keyword or not isinstance(keyword, str):
            return []
        kw = keyword.lower().strip()
        if not kw:
            return []
        results = []
        for item in self._items.values():
            if kw in item.name.lower() or kw in item.id.lower():
                results.append(item)
        return results

    def autocomplete_items(
        self,
        keyword: str,
        max_results: int = 5,
    ) -> List[MenuItem]:
        """
        Gợi ý món ăn có tên hoặc mã món bắt đầu bằng keyword.
        Sử dụng str.startswith trên bản đã casefold.
        Lưu ý: Giữ nguyên hành vi bỏ qua món khớp hoàn toàn (is_exact) theo code hiện tại.
        """
        if not isinstance(keyword, str) or max_results < 1:
            return []

        query = keyword.strip()
        if not query:
            return []

        query_fold = query.casefold()

        suggestions: List[MenuItem] = []
        for item in self._items.values():
            name_fold = item.name.casefold()
            id_fold = item.id.casefold()

            matches_name = name_fold.startswith(query_fold)
            matches_id = id_fold.startswith(query_fold)
            is_exact_match = (name_fold == query_fold or id_fold == query_fold)

            if (matches_name or matches_id) and not is_exact_match:
                suggestions.append(item)
                if len(suggestions) >= max_results:
                    break
        return suggestions

    def filter_by_type(self, item_type: str) -> List[MenuItem]:
        """Lọc món theo danh mục (so sánh không phân biệt hoa thường)."""
        if not item_type or not isinstance(item_type, str):
            return []
        target_type = item_type.casefold().strip()
        if not target_type:
            return []
        return [
            item for item in self._items.values()
            if item.category.casefold().strip() == target_type
        ]

    def filter_by_category(self, category: str) -> List[MenuItem]:
        """Bí danh cho filter_by_type để đồng nhất với trường 'category'."""
        return self.filter_by_type(category)

    def get_categories(self) -> List[str]:
        """
        Lấy danh sách các phân loại món ăn hiện có (so sánh không phân biệt hoa thường).
        Dùng HashTable tự cài làm bảng tra cứu đã thấy, không dùng set built-in.
        """
        seen_categories = HashTable()
        categories: List[str] = []
        for item in self._items.values():
            cat = item.category.strip()
            cat_fold = cat.casefold()
            if cat_fold not in seen_categories:
                seen_categories.put(cat_fold, True)
                categories.append(cat)
        return categories

    def filter_by_availability(self, is_available: bool = True) -> List[MenuItem]:
        """Lọc danh sách món ăn theo trạng thái phục vụ (còn món / hết món)."""
        return [item for item in self._items.values() if item.is_available == is_available]

import sys
from typing import Dict, List, Optional, Any

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from .MenuItem import MenuItem

class MenuCatalog:
    def __init__(self):
        self._items: Dict[str, MenuItem] = {}

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
            key = info.get("id", info.get("item_id", info.get("Item_id", "")))
            try:
                item_data = {
                    "id": str(key),
                    "name": info.get("name", info.get("Name", "")),
                    "category": info.get("category", info.get("item_type", info.get("Item_type", "Chưa phân loại"))),
                    "price": info.get("price", info.get("unit_price", info.get("Unit_price", 1))),
                    "unit": info.get("unit", info.get("Unit", "phần")),
                    "is_available": info.get("is_available", info.get("status", info.get("Status_of_menuItem", True))),
                    "description": info.get("description", info.get("Description", "")),
                    "prep_time": int(info.get("prep_time", info.get("Prep_time", 0))),
                    "image": info.get("image", ""),
                    "color": info.get("color", "#68452f"),
                }
                item = MenuItem(**item_data)
                self._items[item.id] = item
            except Exception as e:
                print(f"[Cảnh báo] Bỏ qua món ID {key} do dữ liệu không hợp lệ: {e}")

    def to_dict(self) -> list:
        return [item.to_dict() for item in self._items.values()]

    def to_list(self) -> list:
        return self.to_dict()

    def add_item(self, item: MenuItem) -> bool:
        if not isinstance(item, MenuItem):
            raise TypeError("Đối tượng thêm vào phải thuộc lớp MenuItem.")
        
        if item.id in self._items:
            return False
        
        self._items[item.id] = item
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
            self._items[item_id] = validated_item
            return True
        except Exception as e:
            print(f"[Lỗi cập nhật] Dữ liệu cập nhật món ID '{item_id}' không hợp lệ: {e}")
            return False

    def remove_item(self, item_id: str) -> bool:
        return self._items.pop(item_id, None) is not None

    def get_item(self, item_id: str) -> Optional[MenuItem]:
        return self._items.get(item_id)

    def get_all_items(self) -> List[MenuItem]:
        return list(self._items.values())

    def search_items(self, keyword: str) -> List[MenuItem]:
        if not keyword or not isinstance(keyword, str):
            return []
        kw = keyword.lower().strip()
        if not kw:
            return []
        return [
            item for item in self._items.values()
            if kw in item.name.lower() or kw in item.id.lower()
        ]

    def filter_by_type(self, item_type: str) -> List[MenuItem]:
        if not item_type or not isinstance(item_type, str):
            return []
        target_type = item_type.lower().strip()
        if not target_type:
            return []
        return [
            item for item in self._items.values()
            if item.category.lower() == target_type
        ]

    def filter_by_category(self, category: str) -> List[MenuItem]:
        """Bí danh cho filter_by_type để đồng nhất với trường 'category'."""
        return self.filter_by_type(category)

    def get_categories(self) -> List[str]:
        """Lấy danh sách các phân loại món ăn hiện có."""
        return list(dict.fromkeys(item.category for item in self._items.values()))

    def filter_by_availability(self, is_available: bool = True) -> List[MenuItem]:
        """Lọc danh sách món ăn theo trạng thái phục vụ (còn món / hết món)."""
        return [item for item in self._items.values() if item.is_available == is_available]

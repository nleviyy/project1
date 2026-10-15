import os
import sys
from typing import Dict, List, Optional, Any

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

from MenuItem import MenuItem


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
                    "price": float(info.get("price", info.get("unit_price", info.get("Unit_price", 1)))),
                    "unit": info.get("unit", info.get("Unit", "phần")),
                    "is_available": info.get("is_available", info.get("status", info.get("Status_of_menuItem", True))),
                    "description": info.get("description", info.get("Description", "")),
                    "prep_time": int(info.get("prep_time", info.get("Prep_time", 0)))
                }
                item = MenuItem(**item_data)
                self._items[item.id] = item
            except Exception as e:
                print(f"[Cảnh báo] Bỏ qua món ID {key} do dữ liệu không hợp lệ: {e}")

    def to_dict(self) -> list:
        return [
            item.model_dump() if hasattr(item, "model_dump") else item.dict()
            for item in self._items.values()
        ]

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

        key_mapping = {
            "unit_price": "price",
            "status": "is_available",
            "item_type": "category"
        }

        for k, v in kwargs.items():
            actual_key = key_mapping.get(k, k)
            if hasattr(item, actual_key):
                setattr(item, actual_key, v)

        return True

    def remove_item(self, item_id: str) -> bool:
        return self._items.pop(item_id, None) is not None

    def get_item(self, item_id: str) -> Optional[MenuItem]:
        return self._items.get(item_id)

    def get_all_items(self) -> List[MenuItem]:
        return list(self._items.values())

    def search_items(self, keyword: str) -> List[MenuItem]:
        kw = keyword.lower().strip()
        return [
            item for item in self._items.values()
            if kw in item.name.lower() or kw in item.id.lower()
        ]

    def filter_by_type(self, item_type: str) -> List[MenuItem]:
        target_type = item_type.lower().strip()
        return [
            item for item in self._items.values()
            if item.category.lower() == target_type
        ]


if __name__ == "__main__":
    catalog = MenuCatalog()
    sample = MenuItem(id="TEST01", name="Trà đào", category="Đồ uống", price=30000, unit="ly")
    catalog.add_item(sample)
    found = catalog.get_item("TEST01")
    print(f"[MenuCatalog Test] Đã thêm và lấy món: {found.name} ({found.id}) - Tổng số món: {len(catalog.get_all_items())}")
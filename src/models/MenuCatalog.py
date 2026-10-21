import json
<<<<<<< Updated upstream
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
=======
import sys
import unicodedata
from pathlib import Path
from typing import Optional, Union

from src.structures.linked_list import DoublyLinkedList
from src.structures.hash_table import HashNode, HashTable
>>>>>>> Stashed changes

from src.models.MenuItem import MenuItem
from src.models.JSONStorage import JSONStorage

__all__ = ["HashNode", "HashTable", "MenuCatalog"]



def _normalize_text(text: str) -> str:
    """Normalize Vietnamese accents and casefold for resilient matching."""
    text = text.replace("đ", "d").replace("Đ", "d")
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    ).casefold()


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
            except (TypeError, ValueError) as e:
                print(f"[Cảnh báo] Bỏ qua món ID {key} do dữ liệu không hợp lệ: {e}")

    def load_from_file(self, file_path: Optional[Union[str, Path]] = None) -> bool:
        target = Path(file_path) if file_path else (Path(__file__).resolve().parents[2] / "data" / "menu.json")
        if not target.exists():
            return False
        data = JSONStorage.load_data(str(target), default_data=[], strict=True)
        if not isinstance(data, (list, dict)):
            raise ValueError(f"Dữ liệu thực đơn trong '{target}' phải là danh sách hoặc object.")
        self.load_from_dict(data)
        return True

    def save_to_file(self, file_path: Optional[Union[str, Path]] = None) -> bool:
        target = Path(file_path) if file_path else (Path(__file__).resolve().parents[2] / "data" / "menu.json")
        return JSONStorage.save_data(str(target), self.to_dict())

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

<<<<<<< Updated upstream
    def update_item(self, item_id: str, **kwargs) -> bool:
=======
    def load_from_file(self, file_path=None) -> bool:
        """Đọc thực đơn trực tiếp từ file JSON."""
        target = Path(file_path) if file_path else (Path(__file__).resolve().parents[2] / "data" / "menu.json")
        if not target.exists():
            return False
        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.load_from_dict(data)
            return True
        except Exception as e:
            print(f"[Lỗi MenuCatalog] Không thể tải dữ liệu từ '{target}': {e}")
            return False

    def save_to_file(self, file_path=None) -> bool:
        """Lưu toàn bộ danh mục món ăn hiện tại ra file JSON."""
        target = Path(file_path) if file_path else (Path(__file__).resolve().parents[2] / "data" / "menu.json")
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                json.dump(JSONStorage.to_json_data(self.to_dict()), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[Lỗi MenuCatalog] Không thể lưu file '{target}': {e}")
            return False

    def update_item(
        self,
        item_id,
        name=None,
        category=None,
        price=None,
        unit=None,
        is_available=None,
        description=None,
        prep_time=None,
        image=None,
        color=None,
        **kwargs,
    ):
        if price is None and "unit_price" in kwargs:
            price = kwargs["unit_price"]
        if is_available is None and "status" in kwargs:
            is_available = kwargs["status"]
        if category is None and "item_type" in kwargs:
            category = kwargs["item_type"]

>>>>>>> Stashed changes
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
        except (TypeError, ValueError) as e:
            print(f"[Lỗi cập nhật] Dữ liệu cập nhật món ID '{item_id}' không hợp lệ: {e}")
            return False

<<<<<<< Updated upstream
    def remove_item(self, item_id: str) -> bool:
        return self._items.pop(item_id, None) is not None
=======

    def remove_item(self, item_id):
        item = self._items.get(item_id)
        if item is None:
            return False
        self._items.remove(item_id)
        self._list.remove(item)
        return True
>>>>>>> Stashed changes

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

    @staticmethod
    def _matches_prefix(value: str, keyword: str) -> bool:
        value = value.casefold()
        keyword = keyword.casefold()
        if len(keyword) > len(value):
            return False

        index = 0
        while index < len(keyword):
            if value[index] != keyword[index]:
                return False
            index += 1
        return True

    def autocomplete_items(
        self,
        keyword: str,
        max_results: int = 5,
    ) -> List[MenuItem]:
        """Return menu items matching prefix of full name, ID, or individual words."""
        if not isinstance(keyword, str) or max_results < 1:
            return []

        query = keyword.strip()
        if not query:
            return []

        query_fold = query.casefold()
        norm_query = _normalize_text(query)

        tier1: List[MenuItem] = []
        tier2: List[MenuItem] = []
        tier3: List[MenuItem] = []
        seen_ids = set()

        for item in self._items.values():
            name_fold = item.name.casefold()
            id_fold = item.id.casefold()
            is_exact = (name_fold == query_fold or id_fold == query_fold)
            if is_exact:
                continue

            # Tier 1: Direct prefix on whole name or whole ID
            if self._matches_prefix(item.name, query) or self._matches_prefix(item.id, query):
                tier1.append(item)
                seen_ids.add(item.id)
                continue

            # Tier 2: Word-level prefix in name
            words = name_fold.split()
            if any(self._matches_prefix(w, query_fold) for w in words):
                tier2.append(item)
                seen_ids.add(item.id)
                continue

            # Tier 3: Unaccented prefix (whole name or any word)
            norm_name = _normalize_text(item.name)
            if norm_name.startswith(norm_query) or any(w.startswith(norm_query) for w in norm_name.split()):
                tier3.append(item)
                seen_ids.add(item.id)

        combined = tier1 + tier2 + tier3
        return combined[:max_results]

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
        return self.filter_by_type(category)

    def get_categories(self) -> List[str]:
        seen = set()
        categories = []
        for item in self._items.values():
            if item.category not in seen:
                seen.add(item.category)
                categories.append(item.category)
        return categories

<<<<<<< Updated upstream
    def filter_by_availability(self, is_available: bool = True) -> List[MenuItem]:
        return [item for item in self._items.values() if item.is_available == is_available]

        return [item for item in self._items.values() if item.is_available == is_available]
=======
    def filter_by_availability(self, is_available=True):
        result = DoublyLinkedList()
        node = self._list.head
        while node is not None:
            if node.data.is_available == is_available:
                result.add_last(node.data)
            node = node.next
        return result

    @staticmethod
    def _matches_prefix(value: str, keyword: str) -> bool:
        value = value.casefold()
        keyword = keyword.casefold()
        if len(keyword) > len(value):
            return False

        index = 0
        while index < len(keyword):
            if value[index] != keyword[index]:
                return False
            index += 1
        return True

    def autocomplete_items(
        self,
        keyword: str,
        max_results: int = 5,
    ) -> list:
        """Trả về danh sách món có tên hoặc mã bắt đầu bằng keyword."""
        if not isinstance(keyword, str) or max_results < 1:
            return []

        query = keyword.strip()
        if not query:
            return []

        suggestions = []
        node = self._list.head
        while node is not None:
            item = node.data
            matches_name = self._matches_prefix(item.name, query)
            matches_id = self._matches_prefix(item.id, query)
            is_exact_match = (
                item.name.casefold() == query.casefold()
                or item.id.casefold() == query.casefold()
            )
            if (matches_name or matches_id) and not is_exact_match:
                suggestions.append(item)
                if len(suggestions) >= max_results:
                    break
            node = node.next
        return suggestions

>>>>>>> Stashed changes

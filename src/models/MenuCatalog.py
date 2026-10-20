import json
from pathlib import Path
import sys
from typing import Dict, List, Optional, Any, Union

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from .MenuItem import MenuItem

__all__ = ["HashNode", "HashTable", "MenuCatalog"]

class HashNode:

    def __init__(self, key: Any, value: Any):
        self.key = key
        self.value = value
        self.next: Optional["HashNode"] = None

class HashTable:
    def __init__(self, capacity: int = 32):
        if capacity < 1:
            capacity = 32
        self.capacity: int = capacity
        self.size: int = 0
        self.buckets: List[Optional[HashNode]] = [None] * self.capacity
        self._keys_order: List[Any] = []

    def _hash(self, key: Any) -> int:
        key_str = str(key)
        hash_val = 0
        for char in key_str:
            hash_val = (hash_val * 31 + ord(char)) % self.capacity
        return hash_val

    def _resize(self) -> None:
        old_buckets = self.buckets
        self.capacity *= 2
        self.buckets = [None] * self.capacity
        self.size = 0
        order_backup = list(self._keys_order)
        self._keys_order.clear()

        for head in old_buckets:
            current = head
            while current is not None:
                self.put(current.key, current.value)
                current = current.next
        self._keys_order = [k for k in order_backup if self.contains(k)]

    def put(self, key: Any, value: Any) -> None:
        index = self._hash(key)
        current = self.buckets[index]

        while current is not None:
            if current.key == key:
                current.value = value
                return
            current = current.next

        new_node = HashNode(key, value)
        new_node.next = self.buckets[index]
        self.buckets[index] = new_node
        self.size += 1
        self._keys_order.append(key)

        if self.size / self.capacity >= 0.75:
            self._resize()

    def get(self, key: Any, default: Any = None) -> Any:
        index = self._hash(key)
        current = self.buckets[index]
        while current is not None:
            if current.key == key:
                return current.value
            current = current.next
        return default

    def remove(self, key: Any) -> bool:
        index = self._hash(key)
        current = self.buckets[index]
        prev = None

        while current is not None:
            if current.key == key:
                if prev is None:
                    self.buckets[index] = current.next
                else:
                    prev.next = current.next
                self.size -= 1
                if key in self._keys_order:
                    self._keys_order.remove(key)
                return True
            prev = current
            current = current.next

        return False

    def pop(self, key: Any, default: Any = None) -> Any:
        index = self._hash(key)
        current = self.buckets[index]
        prev = None

        while current is not None:
            if current.key == key:
                val = current.value
                if prev is None:
                    self.buckets[index] = current.next
                else:
                    prev.next = current.next
                self.size -= 1
                if key in self._keys_order:
                    self._keys_order.remove(key)
                return val
            prev = current
            current = current.next

        return default

    def contains(self, key: Any) -> bool:
        index = self._hash(key)
        current = self.buckets[index]
        while current is not None:
            if current.key == key:
                return True
            current = current.next
        return False

    def clear(self) -> None:
        self.buckets = [None] * self.capacity
        self.size = 0
        self._keys_order.clear()

    def values(self) -> List[Any]:
        return [self.get(k) for k in self._keys_order]

    def keys(self) -> List[Any]:
        return list(self._keys_order)

    def items(self) -> List[tuple]:
        return [(k, self.get(k)) for k in self._keys_order]

    def __len__(self) -> int:
        return self.size

    def __getitem__(self, key: Any) -> Any:
        val = self.get(key)
        if val is None and not self.contains(key):
            raise KeyError(key)
        return val

    def __setitem__(self, key: Any, value: Any) -> None:
        self.put(key, value)

    def __delitem__(self, key: Any) -> None:
        if not self.remove(key):
            raise KeyError(key)

    def __contains__(self, key: Any) -> bool:
        return self.contains(key)

    def __iter__(self):
        return iter(self.keys())

__all__ = ["HashNode", "HashTable", "MenuCatalog"]

class HashNode:

    def __init__(self, key: Any, value: Any):
        self.key = key
        self.value = value
        self.next: Optional["HashNode"] = None

class HashTable:

    def __init__(self, capacity: int = 32):
        if capacity < 1:
            capacity = 32
        self.capacity: int = capacity
        self.size: int = 0
        self.buckets: List[Optional[HashNode]] = [None] * self.capacity

    def _hash(self, key: Any) -> int:
        key_str = str(key)
        hash_val = 0
        for char in key_str:
            hash_val = (hash_val * 31 + ord(char)) % self.capacity
        return hash_val

    def _resize(self) -> None:
        old_buckets = self.buckets
        self.capacity *= 2
        self.buckets = [None] * self.capacity
        self.size = 0

        for head in old_buckets:
            current = head
            while current is not None:
                self.put(current.key, current.value)
                current = current.next

    def put(self, key: Any, value: Any) -> None:
        index = self._hash(key)
        current = self.buckets[index]

        while current is not None:
            if current.key == key:
                current.value = value
                return
            current = current.next

        new_node = HashNode(key, value)
        new_node.next = self.buckets[index]
        self.buckets[index] = new_node
        self.size += 1

        if self.size / self.capacity >= 0.75:
            self._resize()

    def get(self, key: Any, default: Any = None) -> Any:
        index = self._hash(key)
        current = self.buckets[index]
        while current is not None:
            if current.key == key:
                return current.value
            current = current.next
        return default

    def remove(self, key: Any) -> bool:
        index = self._hash(key)
        current = self.buckets[index]
        prev = None

        while current is not None:
            if current.key == key:
                if prev is None:
                    self.buckets[index] = current.next
                else:
                    prev.next = current.next
                self.size -= 1
                return True
            prev = current
            current = current.next

        return False

    def pop(self, key: Any, default: Any = None) -> Any:
        index = self._hash(key)
        current = self.buckets[index]
        prev = None

        while current is not None:
            if current.key == key:
                val = current.value
                if prev is None:
                    self.buckets[index] = current.next
                else:
                    prev.next = current.next
                self.size -= 1
                return val
            prev = current
            current = current.next

        return default

    def contains(self, key: Any) -> bool:
        index = self._hash(key)
        current = self.buckets[index]
        while current is not None:
            if current.key == key:
                return True
            current = current.next
        return False

    def clear(self) -> None:
        self.buckets = [None] * self.capacity
        self.size = 0

    def values(self) -> List[Any]:
        res: List[Any] = []
        for head in self.buckets:
            current = head
            while current is not None:
                res.append(current.value)
                current = current.next
        return res

    def keys(self) -> List[Any]:
        res: List[Any] = []
        for head in self.buckets:
            current = head
            while current is not None:
                res.append(current.key)
                current = current.next
        return res

    def items(self) -> List[tuple]:
        res: List[tuple] = []
        for head in self.buckets:
            current = head
            while current is not None:
                res.append((current.key, current.value))
                current = current.next
        return res

    def __len__(self) -> int:
        return self.size

    def __getitem__(self, key: Any) -> Any:
        val = self.get(key)
        if val is None and not self.contains(key):
            raise KeyError(key)
        return val

    def __setitem__(self, key: Any, value: Any) -> None:
        self.put(key, value)

    def __delitem__(self, key: Any) -> None:
        if not self.remove(key):
            raise KeyError(key)

    def __contains__(self, key: Any) -> bool:
        return self.contains(key)

    def __iter__(self):
        return iter(self.keys())

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
            except Exception as e:
                print(f"[Cảnh báo] Bỏ qua món ID {key} do dữ liệu không hợp lệ: {e}")

    def load_from_file(self, file_path: Optional[Union[str, Path]] = None) -> bool:
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

    def save_to_file(self, file_path: Optional[Union[str, Path]] = None) -> bool:
        target = Path(file_path) if file_path else (Path(__file__).resolve().parents[2] / "data" / "menu.json")
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
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
        if not isinstance(keyword, str) or max_results < 1:
            return []

        query = keyword.strip()
        if not query:
            return []

        suggestions: List[MenuItem] = []
        for item in self._items.values():
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
        return suggestions

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

    def filter_by_availability(self, is_available: bool = True) -> List[MenuItem]:
        return [item for item in self._items.values() if item.is_available == is_available]

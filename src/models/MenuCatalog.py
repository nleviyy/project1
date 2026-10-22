import json
import sys
import unicodedata
from pathlib import Path
from typing import Optional, Union

from src.structures.linked_list import DoublyLinkedList
from src.structures.hash_table import HashNode, HashTable
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
        self._items = HashTable()          # id -> MenuItem (tra cứu nhanh)
        self._list = DoublyLinkedList()    # các MenuItem theo thứ tự thêm vào (để hiển thị)

    # ---------- Nạp dữ liệu ----------

    def load_from_dict(self, data):
        self._items = HashTable()
        self._list = DoublyLinkedList()

        if data is None:
            return
        if isinstance(data, HashTable):
            info_list = data.values()
        elif isinstance(data, DoublyLinkedList):
            info_list = data
        elif isinstance(data, (list, tuple)):
            info_list = data
        else:
            return

        for info in info_list:
            if not isinstance(info, (HashTable, dict)):
                continue
            try:
                item = MenuItem.from_dict(info)
                self.remove_item(item.id)      # trùng id thì món sau thay món trước
                self.add_item(item)
            except (ValueError, TypeError) as e:
                print("[Cảnh báo] Bỏ qua món ID " + str(info.get("id")) + " do dữ liệu không hợp lệ: " + str(e))

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

    def to_dict(self):
        """Trả về DoublyLinkedList các HashTable."""
        result = DoublyLinkedList()
        node = self._list.head
        while node is not None:
            result.add_last(node.data.to_dict())
            node = node.next
        return result

    def to_list(self):
        return self.to_dict()

    # ---------- Thêm / sửa / xóa ----------

    def add_item(self, item):
        if not isinstance(item, MenuItem):
            raise TypeError("Đối tượng thêm vào phải thuộc lớp MenuItem.")
        if self._items.contains(item.id):
            return False
        self._items.put(item.id, item)
        self._list.add_last(item)
        return True

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

        item = self.get_item(item_id)
        if item is None:
            return False
        try:
            item.update(
                name=name,
                category=category,
                price=price,
                unit=unit,
                is_available=is_available,
                description=description,
                prep_time=prep_time,
                image=image,
                color=color,
            )
            return True
        except ValueError as e:
            print("[Lỗi cập nhật] Dữ liệu cập nhật món ID '" + str(item_id) + "' không hợp lệ: " + str(e))
            return False

    def remove_item(self, item_id):
        item = self._items.get(item_id)
        if item is None:
            return False
        self._items.remove(item_id)
        self._list.remove(item)
        return True

    # ---------- Truy vấn items ----------

    def get_item(self, item_id):
        return self._items.get(item_id)

    def get_all_items(self):
        result = DoublyLinkedList()
        node = self._list.head
        while node is not None:
            result.add_last(node.data)
            node = node.next
        return result

    def search_items(self, keyword):
        result = DoublyLinkedList()
        if not keyword or not isinstance(keyword, str):
            return result
        kw = keyword.lower().strip()
        if not kw:
            return result
        node = self._list.head
        while node is not None:
            item = node.data
            if kw in item.name.lower() or kw in item.id.lower():
                result.add_last(item)
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

    def filter_by_type(self, item_type):
        result = DoublyLinkedList()
        if not item_type or not isinstance(item_type, str):
            return result
        target_type = item_type.lower().strip()
        if not target_type:
            return result
        node = self._list.head
        while node is not None:
            if node.data.category.lower() == target_type:
                result.add_last(node.data)
            node = node.next
        return result

    def filter_by_category(self, category):
        """Tên khác của filter_by_type."""
        return self.filter_by_type(category)

    def get_categories(self):
        result = DoublyLinkedList()
        seen = HashTable()
        node = self._list.head
        while node is not None:
            category = node.data.category
            if not seen.contains(category):
                seen.put(category, True)
                result.add_last(category)
            node = node.next
        return result

    def filter_by_availability(self, is_available=True):
        result = DoublyLinkedList()
        node = self._list.head
        while node is not None:
            if node.data.is_available == is_available:
                result.add_last(node.data)
            node = node.next
        return result

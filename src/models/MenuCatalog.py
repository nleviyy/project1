import sys

from src.structures.linked_list import DoublyLinkedList
from src.structures.hash_table import HashTable

from src.models.MenuItem import MenuItem
from src.models.HashTable import HashNode, HashTable
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
    ):
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

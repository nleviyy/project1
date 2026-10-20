from __future__ import annotations
from typing import Any
from src.models.MenuItem import MenuItem


class _StackNode:
    def __init__(self, data, next_node=None):
        self.data = data
        self.next = next_node


class Stack:
    """Ngăn xếp tự cài đặt bằng danh sách liên kết (LIFO)."""

    def __init__(self):
        self._top = None
        self._size = 0

    def push(self, data):
        self._top = _StackNode(data, self._top)
        self._size += 1

    def pop(self):
        if self._top is None:
            raise IndexError("Ngăn xếp rỗng")
        data = self._top.data
        self._top = self._top.next
        self._size -= 1
        return data

    def clear(self):
        self._top = None
        self._size = 0

    def __len__(self):
        return self._size

    def __eq__(self, other):
        if isinstance(other, list):
            if len(self) != len(other):
                return False
            curr = self._top
            items = []
            while curr:
                items.append(curr.data)
                curr = curr.next
            return items[::-1] == other
        if isinstance(other, Stack):
            if len(self) != len(other):
                return False
            c1, c2 = self._top, other._top
            while c1 and c2:
                if c1.data != c2.data:
                    return False
                c1, c2 = c1.next, c2.next
            return True
        return False


class CartItem:
    def __init__(
        self,
        menu_item_id,
        item_name,
        unit_price,
        quantity,
        note="",
        prep_time=0,
    ):
        self.menu_item_id = menu_item_id
        self.item_name = item_name
        self.unit_price = unit_price
        self.quantity = quantity
        self.note = note
        self.prep_time = prep_time

    def calculate_subtotal(self):
        return self.unit_price * self.quantity

    def to_dict(self):
        data = {
            "menu_item_id": self.menu_item_id,
            "item_name": self.item_name,
            "unit_price": self.unit_price,
            "quantity": self.quantity,
            "subtotal": self.calculate_subtotal(),
            "note": self.note,
        }
        if self.prep_time:
            data["prep_time"] = self.prep_time
        return data

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["menu_item_id"],
            data["item_name"],
            data["unit_price"],
            data["quantity"],
            data.get("note", ""),
            data.get("prep_time", 0),
        )


class Cart:
    def __init__(self):
        self._items = []
        self.undo_stack = Stack()
        self.redo_stack = Stack()

    def _snapshot(self):
        return [item.to_dict() for item in self._items]

    def _restore(self, snapshot):
        self._items = [CartItem.from_dict(data) for data in snapshot]

    def _save_for_undo(self):
        self.undo_stack.push(self._snapshot())
        self.redo_stack.clear()

    def undo(self):
        if len(self.undo_stack) == 0:
            return False
        self.redo_stack.push(self._snapshot())
        self._restore(self.undo_stack.pop())
        return True

    def redo(self):
        if len(self.redo_stack) == 0:
            return False
        self.undo_stack.push(self._snapshot())
        self._restore(self.redo_stack.pop())
        return True

    def can_undo(self):
        return len(self.undo_stack) > 0

    def can_redo(self):
        return len(self.redo_stack) > 0

    def count_lines(self):
        return len(self._items)

    def _find(self, menu_item_id):
        for item in self._items:
            if item.menu_item_id == menu_item_id:
                return item
        return None

    def _get_val(self, obj, key, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    def add_item(self, menu_item, quantity: int = 1, note: str = ""):
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Số lượng phải là số nguyên lớn hơn 0")

        item_id = self._get_val(menu_item, "id") or self._get_val(menu_item, "menu_item_id")
        item_name = self._get_val(menu_item, "name") or self._get_val(menu_item, "item_name")
        unit_price = self._get_val(menu_item, "price", self._get_val(menu_item, "unit_price", 0))
        is_available = self._get_val(menu_item, "is_available", True)
        prep_time = self._get_val(menu_item, "prep_time", 0) or 0

        if not is_available:
            raise ValueError("Món '" + str(item_name) + "' đã hết")
        if unit_price < 0:
            raise ValueError("Đơn giá không được âm")

        self._save_for_undo()
        existing = self._find(item_id)
        if existing is None:
            self._items.append(
                CartItem(item_id, item_name, unit_price, quantity, note, prep_time)
            )
        else:
            existing.quantity += quantity
            if note != "":
                existing.note = note

    def remove_item(self, menu_item_id):
        item = self._find(menu_item_id)
        if item is None:
            raise ValueError("Món " + str(menu_item_id) + " không có trong giỏ")
        self._save_for_undo()
        self._items.remove(item)

    def update_quantity(self, menu_item_id, quantity):
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Số lượng phải lớn hơn 0 (muốn bỏ món thì dùng remove_item)")
        item = self._find(menu_item_id)
        if item is None:
            raise ValueError("Món " + str(menu_item_id) + " không có trong giỏ")
        self._save_for_undo()
        item.quantity = quantity

    def set_note(self, menu_item_id, note):
        item = self._find(menu_item_id)
        if item is None:
            raise ValueError("Món " + str(menu_item_id) + " không có trong giỏ")
        self._save_for_undo()
        item.note = note

    def update_item(self, menu_item_id, quantity=None, note=None):
        if quantity is not None and (not isinstance(quantity, int) or quantity <= 0):
            raise ValueError("Số lượng phải là số nguyên lớn hơn 0.")
        item = self._find(menu_item_id)
        if item is None:
            raise ValueError("Món " + str(menu_item_id) + " không có trong giỏ")
        self._save_for_undo()
        if quantity is not None:
            item.quantity = quantity
        if note is not None:
            item.note = note

    def clear(self):
        self._items = []
        self.undo_stack.clear()
        self.redo_stack.clear()

    def get_order_items(self):
        return self._snapshot()

    def is_empty(self):
        return len(self._items) == 0

    def calculate_total(self):
        total = 0
        for item in self._items:
            total += item.calculate_subtotal()
        return total

from __future__ import annotations
from collections.abc import Mapping


class CartItem:
    def __init__(
        self, menu_item_id, item_name, unit_price, quantity, note="", prep_time=None
    ):
        self.menu_item_id = menu_item_id
        self.item_name = item_name
        self.unit_price = unit_price
        self.quantity = quantity
        self.note = note
        self.prep_time = prep_time

    @property
    def item_id(self):
        return self.menu_item_id

    @property
    def name(self):
        return self.item_name

    @property
    def price(self):
        return self.unit_price

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
        if self.prep_time is not None:
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
            data.get("prep_time"),
        )


class Cart:
    def __init__(self):
        self._items = []         
        self.undo_stack = []
        self.redo_stack = []

    def _snapshot(self):
        return [item.to_dict() for item in self._items]

    def _restore(self, snapshot):
        self._items = [CartItem.from_dict(data) for data in snapshot]

    def _save_for_undo(self):
        self.undo_stack.append(self._snapshot())
        self.redo_stack.clear()           

    def undo(self):
        if len(self.undo_stack) == 0:
            return False
        self.redo_stack.append(self._snapshot())   
        self._restore(self.undo_stack.pop())       
        return True

    def redo(self):
        if len(self.redo_stack) == 0:
            return False
        self.undo_stack.append(self._snapshot())   
        self._restore(self.redo_stack.pop())       
        return True

    def can_undo(self):
        return len(self.undo_stack) > 0

    def can_redo(self):
        return len(self.redo_stack) > 0

    def _find(self, menu_item_id):
        for item in self._items:
            if item.menu_item_id == menu_item_id:
                return item
        return None

    @property
    def items(self):
        return self._items

    def total_amount(self):
        return self.calculate_total()

    def add_item(self, menu_item, quantity=1, note="", *extra_args):
        if extra_args:
            item_id = menu_item
            item_name = quantity
            unit_price = note
            quantity = extra_args[0]
            note = extra_args[1] if len(extra_args) > 1 else ""
            prep_time = None
            is_available = True
        else:
            if not isinstance(quantity, int) or quantity <= 0:
                raise ValueError("Số lượng phải là số nguyên lớn hơn 0")

            if isinstance(menu_item, Mapping):
                item_id = menu_item["id"]
                item_name = menu_item["name"]
                unit_price = menu_item["price"]
                is_available = menu_item.get("is_available", True)
                prep_time = menu_item.get("prep_time")
            else:
                item_id = menu_item.id
                item_name = menu_item.name
                unit_price = menu_item.price
                is_available = menu_item.is_available
                prep_time = menu_item.prep_time

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

    def update_item(self, menu_item_id, quantity, note=""):
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Số lượng phải lớn hơn 0 (muốn bỏ món thì dùng remove_item)")
        item = self._find(menu_item_id)
        if item is None:
            raise ValueError("Món " + str(menu_item_id) + " không có trong giỏ")
        self._save_for_undo()
        item.quantity = quantity
        item.note = note

    def set_note(self, menu_item_id, note):
        item = self._find(menu_item_id)
        if item is None:
            raise ValueError("Món " + str(menu_item_id) + " không có trong giỏ")
        self._save_for_undo()
        item.note = note

    def clear(self):
        self._items = []
        self.undo_stack.clear()
        self.redo_stack.clear()

    def get_order_items(self):
        return self._snapshot()

    def count_lines(self):
        return len(self._items)

    def is_empty(self):
        return len(self._items) == 0

    def calculate_total(self):
        total = 0
        for item in self._items:
            total += item.calculate_subtotal()
        return total

    def to_text(self):
        if len(self._items) == 0:
            return "(giỏ hàng trống)"
        lines = []
        for item in self._items:
            money = "{:,}".format(item.calculate_subtotal()).replace(",", ".")
            lines.append("{} x{} = {}".format(item.item_name, item.quantity, money))
        return "; ".join(lines)
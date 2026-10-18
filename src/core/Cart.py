from __future__ import annotations

from typing import Any


class CartItem:
    def __init__(
        self,
        menu_item_id: str,
        item_name: str,
        unit_price: int,
        quantity: int,
        note: str = "",
        prep_time: int = 0,
    ) -> None:
        self.menu_item_id = menu_item_id
        self.item_name = item_name
        self.unit_price = unit_price
        self.quantity = quantity
        self.note = note
        self.prep_time = prep_time

    def calculate_subtotal(self) -> int:
        return self.unit_price * self.quantity

    def to_dict(self) -> dict[str, Any]:
        item = {
            "menu_item_id": self.menu_item_id,
            "item_name": self.item_name,
            "unit_price": self.unit_price,
            "quantity": self.quantity,
            "subtotal": self.calculate_subtotal(),
            "note": self.note,
        }
        if self.prep_time:
            item["prep_time"] = self.prep_time
        return item

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CartItem:
        return cls(
            data["menu_item_id"],
            data["item_name"],
            data["unit_price"],
            data["quantity"],
            data.get("note", ""),
            data.get("prep_time", 0),
        )


class Cart:
    def __init__(self) -> None:
        self._items: list[CartItem] = []
        self.undo_stack: list[list[dict[str, Any]]] = []
        self.redo_stack: list[list[dict[str, Any]]] = []

    def _snapshot(self) -> list[dict[str, Any]]:
        return [item.to_dict() for item in self._items]

    def _restore(self, snapshot: list[dict[str, Any]]) -> None:
        self._items = [CartItem.from_dict(data) for data in snapshot]

    def _save_for_undo(self) -> None:
        self.undo_stack.append(self._snapshot())
        self.redo_stack.clear()

    def undo(self) -> bool:
        if not self.undo_stack:
            return False
        self.redo_stack.append(self._snapshot())
        self._restore(self.undo_stack.pop())
        return True

    def redo(self) -> bool:
        if not self.redo_stack:
            return False
        self.undo_stack.append(self._snapshot())
        self._restore(self.redo_stack.pop())
        return True

    def can_undo(self) -> bool:
        return bool(self.undo_stack)

    def can_redo(self) -> bool:
        return bool(self.redo_stack)

    def _find(self, menu_item_id: str) -> CartItem | None:
        return next(
            (item for item in self._items if item.menu_item_id == menu_item_id),
            None,
        )

    @staticmethod
    def _menu_values(menu_item: Any) -> dict[str, Any]:
        if hasattr(menu_item, "to_dict"):
            return menu_item.to_dict()
        if isinstance(menu_item, dict):
            return menu_item
        raise TypeError("menu_item must be a MenuItem or a dictionary")

    def add_item(self, menu_item: Any, quantity: int = 1, note: str = "") -> None:
        item_data = self._menu_values(menu_item)
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Số lượng phải là số nguyên lớn hơn 0")
        if not item_data.get("is_available", True):
            raise ValueError(f"Món '{item_data['name']}' đã hết")

        price = item_data["price"]
        if isinstance(price, bool) or not isinstance(price, int) or price < 0:
            raise ValueError("Đơn giá phải là số nguyên VNĐ không âm")

        existing = self._find(item_data["id"])
        self._save_for_undo()
        if existing is None:
            self._items.append(
                CartItem(
                    item_data["id"],
                    item_data["name"],
                    price,
                    quantity,
                    note,
                    item_data.get("prep_time", 0),
                )
            )
        else:
            existing.quantity += quantity
            if note:
                existing.note = note

    def remove_item(self, menu_item_id: str) -> None:
        item = self._find(menu_item_id)
        if item is None:
            raise ValueError(f"Món {menu_item_id} không có trong giỏ")
        self._save_for_undo()
        self._items.remove(item)

    def update_quantity(self, menu_item_id: str, quantity: int) -> None:
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Số lượng phải lớn hơn 0 (muốn bỏ món thì dùng remove_item)")
        item = self._find(menu_item_id)
        if item is None:
            raise ValueError(f"Món {menu_item_id} không có trong giỏ")
        if item.quantity == quantity:
            return
        self._save_for_undo()
        item.quantity = quantity

    def set_note(self, menu_item_id: str, note: str) -> None:
        item = self._find(menu_item_id)
        if item is None:
            raise ValueError(f"Món {menu_item_id} không có trong giỏ")
        if item.note == note:
            return
        self._save_for_undo()
        item.note = note

    def update_item(self, menu_item_id: str, quantity: int, note: str) -> None:
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Số lượng phải lớn hơn 0 (muốn bỏ món thì dùng remove_item)")
        item = self._find(menu_item_id)
        if item is None:
            raise ValueError(f"Món {menu_item_id} không có trong giỏ")
        if item.quantity == quantity and item.note == note:
            return
        self._save_for_undo()
        item.quantity = quantity
        item.note = note

    def clear(self) -> None:
        self._items.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()

    def get_order_items(self) -> list[dict[str, Any]]:
        return self._snapshot()

    def count_lines(self) -> int:
        return len(self._items)

    def is_empty(self) -> bool:
        return not self._items

    def calculate_total(self) -> int:
        return sum(item.calculate_subtotal() for item in self._items)

    def to_text(self) -> str:
        if self.is_empty():
            return "(giỏ hàng trống)"
        lines = []
        for item in self._items:
            money = f"{item.calculate_subtotal():,}".replace(",", ".")
            lines.append(f"{item.item_name} x{item.quantity} = {money}")
        return "; ".join(lines)

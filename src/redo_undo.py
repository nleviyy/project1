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

    def add_item(self, menu_item, quantity=1, note=""):

        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Số lượng phải là số nguyên lớn hơn 0")
        if not menu_item.get("is_available", True):
            raise ValueError("Món '" + str(menu_item["name"]) + "' đã hết")
        price = menu_item["price"]
        if isinstance(price, bool) or not isinstance(price, int) or price < 0:
            raise ValueError("Đơn giá phải là số nguyên VNĐ không âm")

        self._save_for_undo()
        existing = self._find(menu_item["id"])
        if existing is None:
            self._items.append(CartItem(menu_item["id"], menu_item["name"],
                                        price, quantity, note,
                                        menu_item.get("prep_time", 0)))
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
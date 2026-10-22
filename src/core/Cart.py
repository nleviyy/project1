from src.structures.linked_list import DoublyLinkedList
from src.structures.stack import Stack
from src.structures.hash_table import HashTable


class CartItem:
    def __init__(
        self,
        menu_item_id,
        item_name,
        unit_price,
        quantity,
        note="",
        prep_time=None,
    ):
        self.menu_item_id = menu_item_id
        self.item_name = item_name
        self.unit_price = unit_price
        self.quantity = quantity
        self.note = note
        self.prep_time = prep_time

    def calculate_subtotal(self):
        return self.unit_price * self.quantity

    def copy(self):
        """Tạo bản sao của món (dùng để lưu trạng thái cho undo/redo)."""
        return CartItem(
            self.menu_item_id,
            self.item_name,
            self.unit_price,
            self.quantity,
            self.note,
            self.prep_time,
        )

    def to_dict(self):
        """Đóng gói thông tin món vào một HashTable."""
        data = HashTable()
        data.put("menu_item_id", self.menu_item_id)
        data.put("item_name", self.item_name)
        data.put("unit_price", self.unit_price)
        data.put("quantity", self.quantity)
        data.put("subtotal", self.calculate_subtotal())
        data.put("note", self.note)
        if self.prep_time is not None:
            data.put("prep_time", self.prep_time)
        return data

    @classmethod
    def from_dict(cls, data):
        return cls(
            menu_item_id=data.get("menu_item_id"),
            item_name=data.get("item_name"),
            unit_price=data.get("unit_price"),
            quantity=data.get("quantity"),
            note=data.get("note", ""),
            prep_time=data.get("prep_time"),
        )


class Cart:
    def __init__(self):
        self._items = DoublyLinkedList()   # danh sách các CartItem trong giỏ
        self.undo_stack = Stack()          # mỗi phần tử là 1 DoublyLinkedList (bản sao giỏ hàng)
        self.redo_stack = Stack()

    # ---------- Undo / Redo ----------

    def _snapshot(self):
        """Chụp lại giỏ hàng hiện tại: sao chép từng món vào một danh sách mới."""
        snap = DoublyLinkedList()
        node = self._items.head
        while node is not None:
            snap.add_last(node.data.copy())
            node = node.next
        return snap

    def _save_for_undo(self):
        """Gọi trước mỗi lần thay đổi giỏ hàng."""
        self.undo_stack.push(self._snapshot())
        self.redo_stack.clear()

    def undo(self):
        if self.undo_stack.is_empty():
            return False
        self.redo_stack.push(self._snapshot())
        self._items = self.undo_stack.pop()
        return True

    def redo(self):
        if self.redo_stack.is_empty():
            return False
        self.undo_stack.push(self._snapshot())
        self._items = self.redo_stack.pop()
        return True

    def can_undo(self):
        return not self.undo_stack.is_empty()

    def can_redo(self):
        return not self.redo_stack.is_empty()

    # ---------- Tìm món ----------

    def count_lines(self):
        return len(self._items)

    def _find(self, menu_item_id):
        """Trả về CartItem có id tương ứng, không có thì trả về None."""
        node = self._items.head
        while node is not None:
            if node.data.menu_item_id == menu_item_id:
                return node.data
            node = node.next
        return None

    # ---------- Thao tác giỏ hàng ----------

    @staticmethod
    def _validate_quantity(quantity):
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Số lượng phải là số nguyên lớn hơn 0")

    def add_item(self, menu_item, quantity=1, note="", *extra_args):
        if extra_args:
            item_id = menu_item
            item_name = quantity
            unit_price = note
            quantity = extra_args[0]
            note = extra_args[1] if len(extra_args) > 1 else ""
            prep_time = 0
            is_available = True
            self._validate_quantity(quantity)
        else:
            self._validate_quantity(quantity)
            if isinstance(menu_item, dict):
                item_id = menu_item.get("id")
                item_name = menu_item.get("name")
                unit_price = menu_item.get("price")
                is_available = menu_item.get("is_available", True)
                prep_time = menu_item.get("prep_time")
            else:
                item_id = menu_item.id
                item_name = menu_item.name
                unit_price = menu_item.price
                is_available = getattr(menu_item, "is_available", True)
                prep_time = getattr(menu_item, "prep_time", None)

        if not is_available:
            raise ValueError("Món '" + str(item_name) + "' đã hết")
        if unit_price < 0:
            raise ValueError("Đơn giá không được âm")

        self._save_for_undo()
        existing = self._find(item_id)
        if existing is None:
            self._items.add_last(
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
        self._validate_quantity(quantity)
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
        if quantity is not None:
            self._validate_quantity(quantity)
        item = self._find(menu_item_id)
        if item is None:
            raise ValueError("Món " + str(menu_item_id) + " không có trong giỏ")
        self._save_for_undo()
        if quantity is not None:
            item.quantity = quantity
        if note is not None:
            item.note = note

    def clear(self):
        self._items.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()

    # ---------- Truy vấn ----------

    def get_order_items(self):
        """Trả về DoublyLinkedList, mỗi phần tử là 1 HashTable mô tả món."""
        result = DoublyLinkedList()
        node = self._items.head
        while node is not None:
            result.add_last(node.data.to_dict())
            node = node.next
        return result

    def count_lines(self):
        return self._items.size

    def is_empty(self):
        return self._items.is_empty()

    def calculate_total(self):
        total = 0
        node = self._items.head
        while node is not None:
            total += node.data.calculate_subtotal()
            node = node.next
        return total

    def to_text(self):
        if self._items.is_empty():
            return "(giỏ hàng trống)"
        text = ""
        node = self._items.head
        while node is not None:
            item = node.data
            money = "{:,}".format(item.calculate_subtotal()).replace(",", ".")
            if text != "":
                text += "; "
            text += "{} x{} = {}".format(item.item_name, item.quantity, money)
            node = node.next
        return text

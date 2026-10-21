from datetime import datetime

from src.structures.linked_list import DoublyLinkedList
from src.structures.hash_table import HashTable
from .OrderItem import OrderItem
from .Payment import Payment


def _now():
    return datetime.now().isoformat()


class OrderStatus:
    PENDING = "PENDING"
    PREPARING = "PREPARING"
    SERVED = "SERVED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

    @staticmethod
    def get_label(status):
        label = ORDER_STATUS_LABELS.get(status)
        if label is None:
            return str(status)
        return label


ORDER_STATUS_LABELS = HashTable()
ORDER_STATUS_LABELS.put("PENDING", "Chờ xác nhận")
ORDER_STATUS_LABELS.put("PREPARING", "Đang chế biến")
ORDER_STATUS_LABELS.put("SERVED", "Đã lên món")
ORDER_STATUS_LABELS.put("COMPLETED", "Hoàn thành")
ORDER_STATUS_LABELS.put("CANCELLED", "Đã hủy")

ORDER_STATUS_TRANSITIONS = HashTable()

_after_pending = DoublyLinkedList()
_after_pending.add_last("PREPARING")
_after_pending.add_last("CANCELLED")
ORDER_STATUS_TRANSITIONS.put("PENDING", _after_pending)

_after_preparing = DoublyLinkedList()
_after_preparing.add_last("SERVED")
ORDER_STATUS_TRANSITIONS.put("PREPARING", _after_preparing)

ORDER_STATUS_TRANSITIONS.put("SERVED", DoublyLinkedList())
ORDER_STATUS_TRANSITIONS.put("COMPLETED", DoublyLinkedList())
ORDER_STATUS_TRANSITIONS.put("CANCELLED", DoublyLinkedList())


def is_valid_transition(current_status, new_status):
    """True nếu được phép chuyển từ current_status sang new_status."""
    allowed = ORDER_STATUS_TRANSITIONS.get(current_status)
    if allowed is None:
        return False
    node = allowed.head
    while node is not None:
        if node.data == new_status:
            return True
        node = node.next
    return False


class Order:
    def __init__(
        self,
        id,
        table_id,
        items=None,
        notes="",
        status="PENDING",
        discount_amount=0,
        created_at=None,
        updated_at=None,
        preparing_started_at=None,
    ):
        if not isinstance(id, str) or id.strip() == "":
            raise ValueError("Mã đơn hàng không được để trống.")
        if not ORDER_STATUS_LABELS.contains(status):
            raise ValueError("Trạng thái đơn không hợp lệ: " + str(status))
        if isinstance(discount_amount, bool) or not isinstance(discount_amount, int) or discount_amount < 0:
            raise ValueError("Tiền giảm giá phải là số nguyên không âm.")
        if items is not None and not isinstance(items, DoublyLinkedList):
            normalized_items = DoublyLinkedList()
            try:
                for item in items:
                    normalized_items.add_last(item)
            except TypeError as error:
                raise TypeError("items phải là danh sách các OrderItem.") from error
            items = normalized_items

        self.id = id
        self.table_id = table_id
        self.status = status
        self.items = items if items is not None else DoublyLinkedList()
        self.notes = notes if notes is not None else ""
        self.discount_amount = discount_amount
        self.created_at = created_at if created_at is not None else _now()
        self.updated_at = updated_at if updated_at is not None else _now()
        self.preparing_started_at = preparing_started_at

    # ---------- Thông tin chung ----------

    @property
    def order_id(self):
        """Tên khác của id, để KitchenManager dùng thống nhất."""
        return self.id

    @property
    def total_amount(self):
        total = 0
        node = self.items.head
        while node is not None:
            total += node.data.subtotal
            node = node.next
        return total

    @property
    def final_amount(self):
        final = self.total_amount - self.discount_amount
        if final < 0:
            return 0
        return final

    def calculate_prep_time(self):
        """Tổng thời gian chế biến = tổng (số lượng * thời gian chế biến) của các món."""
        total = 0
        node = self.items.head
        while node is not None:
            item = node.data
            prep_time = item.prep_time if item.prep_time is not None else 0
            total += item.quantity * prep_time
            node = node.next
        return total

    @property
    def is_pending(self):
        return self.status == "PENDING"

    @property
    def is_preparing(self):
        return self.status == "PREPARING"

    @property
    def is_served(self):
        return self.status == "SERVED"

    @property
    def is_completed(self):
        return self.status == "COMPLETED"

    @property
    def is_cancelled(self):
        return self.status == "CANCELLED"

    @property
    def is_active(self):
        return self.status in ("PENDING", "PREPARING", "SERVED")

    @property
    def can_modify(self):
        return self.can_modify_items()

    def can_modify_items(self):
        """Chỉ cho phép thêm/sửa món khi đơn chưa vào bếp chế biến (PENDING)."""
        return self.status == "PENDING"

    # ---------- Thao tác món trong đơn ----------

    def _find_item(self, menu_item_id):
        node = self.items.head
        while node is not None:
            if node.data.menu_item_id == menu_item_id:
                return node.data
            node = node.next
        return None

    def add_item(self, item):
        """Thêm 1 OrderItem vào đơn. Nếu đã có món trùng id và note thì cộng dồn số lượng."""
        if not self.can_modify_items():
            raise ValueError("Không thể sửa món khi đơn đang ở trạng thái '" + str(self.status) + "'.")
        if not isinstance(item, OrderItem):
            raise TypeError("Món thêm vào phải là OrderItem.")

        existing = self._find_item(item.menu_item_id)
        if existing is not None and existing.note == item.note and existing.unit_price == item.unit_price:
            existing.update_quantity(existing.quantity + item.quantity)
        else:
            self.items.add_last(item)
        self._touch()
        return True

    def update_item_quantity(self, menu_item_id, quantity):
        if not self.can_modify_items():
            raise ValueError("Không thể sửa món khi đơn đang ở trạng thái '" + str(self.status) + "'.")
        item = self._find_item(menu_item_id)
        if item is None:
            return False
        item.update_quantity(quantity)
        self._touch()
        return True

    def update_item_note(self, menu_item_id, note):
        if not self.can_modify_items():
            raise ValueError("Không thể sửa món khi đơn đang ở trạng thái '" + str(self.status) + "'.")
        item = self._find_item(menu_item_id)
        if item is None:
            return False
        item.update_note(note)
        self._touch()
        return True

    def remove_item(self, menu_item_id):
        if not self.can_modify_items():
            raise ValueError("Không thể sửa món khi đơn đang ở trạng thái '" + str(self.status) + "'.")
        node = self.items.head
        while node is not None:
            if node.data.menu_item_id == menu_item_id:
                self.items.remove(node.data)
                self._touch()
                return True
            node = node.next
        return False

    def _touch(self):
        self.updated_at = _now()

    def set_discount(self, amount):
        if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
            raise ValueError("Tiền giảm giá phải là số nguyên không âm.")
        self.discount_amount = amount
        self._touch()

    # ---------- Trạng thái ----------

    def set_status(self, new_status):
        return self.change_status(new_status)

    def can_transition_to(self, new_status):
        return is_valid_transition(self.status, new_status)

    def change_status(self, new_status):
        if self.status == new_status:
            return True

        if new_status == "COMPLETED":
            if self.status == "SERVED":
                raise ValueError("Đơn hàng chỉ được hoàn tất sau khi thanh toán thành công.")
            return False

        if not is_valid_transition(self.status, new_status):
            return False

        self.status = new_status
        self._touch()
        if new_status == "PREPARING":
            self.preparing_started_at = self.updated_at
        elif new_status in ("PENDING", "SERVED", "COMPLETED", "CANCELLED"):
            self.preparing_started_at = None
        return True

    def mark_preparing(self):
        return self.change_status("PREPARING")

    def mark_served(self):
        return self.change_status("SERVED")

    def mark_completed(self, payment):
        if payment.order_id != self.id or not payment.is_successful:
            raise ValueError("Chỉ thanh toán SUCCESS của đúng đơn mới được hoàn tất đơn hàng.")
        if self.status != "SERVED":
            raise ValueError("Không thể hoàn tất đơn khi đang ở trạng thái '" + str(self.status) + "'.")
        self.status = "COMPLETED"
        self._touch()
        self.preparing_started_at = None
        return True

    def cancel(self):
        if self.status != "PENDING":
            return False
        return self.change_status("CANCELLED")

    # ---------- Chuyển đổi dữ liệu ----------

    def to_dict(self):
        items_data = DoublyLinkedList()
        node = self.items.head
        while node is not None:
            items_data.add_last(node.data.to_dict())
            node = node.next

        data = HashTable()
        data.put("id", self.id)
        data.put("table_id", self.table_id)
        data.put("status", self.status)
        data.put("created_at", self.created_at)
        data.put("updated_at", self.updated_at)
        data.put("preparing_started_at", self.preparing_started_at)
        data.put("items", items_data)
        data.put("notes", self.notes)
        data.put("discount_amount", self.discount_amount)
        data.put("total_amount", self.total_amount)
        data.put("final_amount", self.final_amount)
        return data

    @classmethod
    def from_dict(cls, data):
        items = DoublyLinkedList()
        items_data = data.get("items")
        if items_data is not None:
            for item_data in items_data:
                if isinstance(item_data, OrderItem):
                    items.add_last(item_data)
                else:
                    items.add_last(OrderItem.from_dict(item_data))

        status = data.get("status")
        if status is None:
            status = "PENDING"
        discount_amount = data.get("discount_amount")
        if discount_amount is None:
            discount_amount = 0

        return cls(
            id=data.get("id"),
            table_id=data.get("table_id"),
            items=items,
            notes=data.get("notes"),
            status=status,
            discount_amount=discount_amount,
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            preparing_started_at=data.get("preparing_started_at"),
        )

    @classmethod
    def from_cart(cls, order_id, table_id, cart_items, notes=""):
        order_items = DoublyLinkedList()
        node = cart_items.head
        while node is not None:
            order_items.add_last(OrderItem.from_dict(node.data))
            node = node.next

        return cls(
            id=order_id,
            table_id=table_id,
            items=order_items,
            notes=notes,
            status="PENDING",
        )
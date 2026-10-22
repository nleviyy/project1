from datetime import datetime

from src.structures.linked_list import DoublyLinkedList
from .Order import OrderStatus, is_valid_transition


def now_time():
    return datetime.now().isoformat(timespec="seconds")


class KitchenOrder:
    def __init__(
        self,
        order_id,
        table_id=1,
        items=None,
        notes="",
        prep_time=0,
        status=None,
        created_at=None,
        updated_at=None,
    ):
        self.order_id = order_id
        self.table_id = table_id
        self.items = items if items is not None else DoublyLinkedList()   # các OrderItem
        self.notes = notes
        self._prep_time = prep_time
        self.status = self._normalize_status(status) if status is not None else OrderStatus.PENDING
        self.created_at = created_at or now_time()
        self.updated_at = updated_at or self.created_at

    @staticmethod
    def _normalize_status(status):
        if status is None:
            return OrderStatus.PENDING
        if isinstance(status, OrderStatus):
            return status
        value = getattr(status, "value", status)
        value = str(value).upper()
        if value in {member.value for member in OrderStatus}:
            return OrderStatus(value)
        return value

    @property
    def id(self):
        return self.order_id

    def set_status(self, new_status):
        """Đổi trạng thái. Trả về True nếu đổi được, False nếu không hợp lệ (giống Order)."""
        if not is_valid_transition(self.status, new_status):
            return False
        self.status = new_status
        self.updated_at = now_time()
        return True

    def change_status(self, new_status):
        """Giống set_status nhưng báo lỗi nếu không đổi được."""
        if not self.set_status(new_status):
            raise ValueError(
                "Không thể chuyển từ '"
                + OrderStatus.get_label(current_status)
                + "' sang '"
                + OrderStatus.get_label(target_status)
                + "'"
            )
        return True

    def calculate_prep_time(self):
        if self.items.is_empty():
            return self._prep_time

        total_prep_time = 0
        node = self.items.head
        while node is not None:
            item = node.data
            quantity = item.quantity
            prep_time = item.prep_time if item.prep_time is not None else 0

            if quantity <= 0:
                raise ValueError("Số lượng món phải lớn hơn 0.")
            if prep_time < 0:
                raise ValueError("Thời gian chế biến không được âm.")
            total_prep_time += quantity * prep_time
            node = node.next

        return total_prep_time
from datetime import datetime
from uuid import uuid4

from .Order import ORDER_STATUS_TRANSITIONS, OrderStatus


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
        status=OrderStatus.PENDING,
        created_at=None,
    ):
        self.order_id = order_id
        self.table_id = table_id
        self.items = items if items is not None else []
        self.notes = notes
        self._prep_time = prep_time
        self.status = status
        self.created_at = created_at or now_time()
        self.updated_at = self.created_at

    @property
    def id(self):
        return self.order_id

    def change_status(self, new_status):
        self.set_status(new_status)
        return True

    def set_status(self, new_status):
        allowed = ORDER_STATUS_TRANSITIONS.get(self.status, [])
        if new_status not in allowed:
            raise ValueError(
                "Không thể chuyển từ '"
                + OrderStatus.get_label(self.status)
                + "' sang '"
                + OrderStatus.get_label(new_status)
                + "'"
            )
        self.status = new_status
        self.updated_at = now_time()

    def calculate_prep_time(self):
        if not self.items:
            return self._prep_time

        items = self.items.values() if isinstance(self.items, dict) else self.items
        total_prep_time = 0
        for item in items:
            if isinstance(item, dict):
                quantity = item.get("sl", item.get("quantity", 1))
                prep_time = item.get("prep_time", 0)
            else:
                quantity = getattr(item, "quantity", 1)
                prep_time = getattr(item, "prep_time", 0)

            quantity = int(quantity)
            prep_time = int(prep_time or 0)
            if quantity <= 0:
                raise ValueError("Số lượng món phải lớn hơn 0.")
            if prep_time < 0:
                raise ValueError("Thời gian chế biến không được âm.")
            total_prep_time += quantity * prep_time

        return total_prep_time

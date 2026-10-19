from collections import deque
from datetime import datetime
from uuid import uuid4

def now_time():
    return datetime.now().isoformat(timespec="seconds")


class OrderStatus:
    PENDING = "PENDING"
    PREPARING = "PREPARING"
    SERVED = "SERVED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

    LABELS = {
        PENDING: "Chờ xác nhận",
        PREPARING: "Đang chế biến",
        SERVED: "Đã lên món",
        COMPLETED: "Hoàn thành",
        CANCELLED: "Đã hủy",
    }

    VALID_NEXT = {
        PENDING: [PREPARING, CANCELLED],
        PREPARING: [SERVED, CANCELLED],
        SERVED: [COMPLETED],
        COMPLETED: [],
        CANCELLED: [],
    }

    @staticmethod
    def get_label(status):
        return OrderStatus.LABELS.get(status, str(status))


class Order:
    def __init__(self, order_id, table_id=1, items=None, notes="", prep_time=0):
        self.order_id = order_id
        self.table_id = table_id
        self.items = items if items is not None else []
        self.notes = notes
        self._prep_time = prep_time         
        self.status = OrderStatus.PENDING
        self.created_at = now_time()
        self.updated_at = self.created_at

    def set_status(self, new_status):
        allowed = OrderStatus.VALID_NEXT.get(self.status, [])
        if new_status not in allowed:
            raise ValueError("Không thể chuyển từ '" + OrderStatus.get_label(self.status)
                             + "' sang '" + OrderStatus.get_label(new_status) + "'")
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
            prep_time = int(prep_time)
            if quantity <= 0:
                raise ValueError("Số lượng món phải lớn hơn 0.")
            if prep_time < 0:
                raise ValueError("Thời gian chế biến không được âm.")
            total_prep_time += quantity * prep_time

        return total_prep_time

class KitchenManager:
    def __init__(self):
        self._queue = deque()        
        self._current_order = None     

    # ---------- 8.1: thêm đơn, lấy đơn ----------
    def add_order(self, order):
        order_id = self._get_order_id(order)
        if self._is_in_kitchen(order_id):
            raise ValueError("Đơn " + str(order_id) + " đã có trong bếp rồi")
        if order.status != OrderStatus.PENDING:
            raise ValueError("Chỉ nhận đơn ở trạng thái '"
                             + OrderStatus.get_label(OrderStatus.PENDING) + "'")
        self._queue.append(order)      # append = thêm vào cuối hàng

    def restore_orders(self, orders):
        """Rebuild the in-memory queue from persisted PENDING/PREPARING orders."""
        self._queue.clear()
        self._current_order = None
        active_orders = sorted(orders, key=lambda order: order.created_at)
        for order in active_orders:
            if order.status == OrderStatus.PENDING:
                self.add_order(order)
            elif order.status == OrderStatus.PREPARING:
                if self._current_order is not None:
                    raise ValueError("Chỉ có thể có một đơn PREPARING trong bếp.")
                self._current_order = order

    def receive_order(self, table_id, items, notes=""):
        """Create and queue an order from cart items; return its estimated wait in minutes."""
        order = Order(
            order_id=f"ORD-{uuid4().hex[:12].upper()}",
            table_id=table_id,
            items=items,
            notes=notes,
        )
        order.calculate_prep_time()
        self.add_order(order)
        return self.estimate_wait_time(order)

    def start_next_order(self):
        if self._current_order is not None:
            raise ValueError("Đơn " + str(self._get_order_id(self._current_order))
                             + " đang làm chưa hoàn tất")
        if len(self._queue) == 0:
            return None
        order = self._queue.popleft() 
        self._set_order_status(order, OrderStatus.PREPARING)
        self._current_order = order
        return order

    def finish_current_order(self):
        """Đơn đã lên món (SERVED) thì rời khỏi bếp."""
        if self._current_order is None:
            raise ValueError("Bếp chưa làm đơn nào")
        order = self._current_order
        if order.status != OrderStatus.SERVED:
            raise ValueError("Đơn " + str(self._get_order_id(order)) + " chưa lên món (đang '"
                             + OrderStatus.get_label(order.status) + "')")
        self._current_order = None
        return order

    # ---------- 8.2: cập nhật trạng thái bếp ----------
    def get_status(self, order_id):
        order = self._find_order(order_id)
        return order.status if order is not None else None

    def get_status_label(self, order_id):
        return OrderStatus.get_label(self.get_status(order_id))

    def change_status(self, order_id, new_status):
        if self._current_order is None or self._get_order_id(self._current_order) != order_id:
            raise ValueError("Chỉ đổi được trạng thái của đơn bếp đang làm")
        self._set_order_status(self._current_order, new_status)

    def advance_status(self):
        if self._current_order is None:
            raise ValueError("Bếp chưa làm đơn nào")
        order = self._current_order
        if order.status == OrderStatus.SERVED:
            raise ValueError("Đơn đã lên món, hãy gọi finish_current_order()")
        next_list = OrderStatus.VALID_NEXT[order.status]
        if len(next_list) == 0:
            raise ValueError("Đơn đã ở trạng thái cuối cùng")
        self._set_order_status(order, next_list[0])
        return order.status

    def cancel_order(self, order_id):
       
        current = self._current_order
        if current is not None and self._get_order_id(current) == order_id:
            self._set_order_status(current, OrderStatus.CANCELLED)
            self._current_order = None
            return
        for order in self._queue:
            if self._get_order_id(order) == order_id:
                self._set_order_status(order, OrderStatus.CANCELLED)
                self._queue.remove(order)
                return
        raise ValueError("Không tìm thấy đơn " + str(order_id) + " trong bếp")

    # ---------- Xem thông tin hàng đợi ----------
    def peek_next_order(self):
        if len(self._queue) == 0:
            return None
        return self._queue[0]

    def get_current_order(self):
        return self._current_order

    def get_waiting_orders(self):
        return list(self._queue)

    def count_waiting(self):
        return len(self._queue)

    def is_empty(self):
        return len(self._queue) == 0 and self._current_order is None

    # ---------- 7.3: thời gian chờ dự kiến ----------
    def estimate_wait_time(self, order):
        current = self._current_order
        order_id = self._get_order_id(order)
        if current is not None and self._get_order_id(current) == order_id:
            return self._calculate_prep_time(order)

        total = 0
        if current is not None:
            total += self._calculate_prep_time(current)
        for waiting in self._queue:
            if self._get_order_id(waiting) == order_id:
                break
            total += self._calculate_prep_time(waiting)
        return total + self._calculate_prep_time(order)

    def _find_order(self, order_id):
        if self._current_order is not None and self._get_order_id(self._current_order) == order_id:
            return self._current_order
        for order in self._queue:
            if self._get_order_id(order) == order_id:
                return order
        return None

    def _is_in_kitchen(self, order_id):
        return self._find_order(order_id) is not None

    @staticmethod
    def _get_order_id(order):
        return getattr(order, "order_id", getattr(order, "id", None))

    @staticmethod
    def _calculate_prep_time(order):
        if hasattr(order, "calculate_prep_time"):
            return order.calculate_prep_time()
        total = 0
        for item in order.items:
            quantity = getattr(item, "quantity", 1)
            prep_time = getattr(item, "prep_time", 0)
            total += int(quantity) * int(prep_time)
        return total

    @staticmethod
    def _set_order_status(order, status):
        if hasattr(order, "set_status"):
            order.set_status(status)
            return
        if hasattr(order, "change_status"):
            if not order.change_status(status):
                raise ValueError(
                    f"Không thể chuyển đơn {KitchenManager._get_order_id(order)} "
                    f"sang trạng thái {status}."
                )
            return
        raise TypeError("Đơn hàng không hỗ trợ cập nhật trạng thái.")
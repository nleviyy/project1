from typing import Optional, List, Any
from datetime import datetime
from src.models.Order import Order, OrderStatus, ORDER_STATUS_TRANSITIONS
from src.models.OrderItem import OrderItem
from src.core.sorting import merge_sort
from src.core.deque import Deque


class KitchenManager:
    def __init__(self):
        self._queue = Deque()
        self._current_order = None
        self._next_id = 1

    def _get_order_id(self, order):
        if order is None:
            return None
        return getattr(order, "order_id", getattr(order, "id", None))

    def _set_status(self, order, new_status):
        if hasattr(order, "set_status"):
            order.set_status(new_status)
        else:
            order.change_status(new_status)

    def _find_order(self, order_id):
        if self._get_order_id(self._current_order) == order_id:
            return self._current_order
        for order in self._queue.to_list():
            if self._get_order_id(order) == order_id:
                return order
        return None

    def _is_in_kitchen(self, order_id):
        return self._find_order(order_id) is not None

    def add_order(self, order: Order):
        oid = self._get_order_id(order)
        if self._is_in_kitchen(oid):
            raise ValueError("Đơn " + str(oid) + " đã có trong bếp rồi")
        if order.status != OrderStatus.PENDING:
            raise ValueError(
                "Chỉ nhận đơn ở trạng thái '"
                + OrderStatus.get_label(OrderStatus.PENDING)
                + "'"
            )
        self._queue.add_last(order)

    def start_next_order(self):
        if self._current_order is not None:
            oid = self._get_order_id(self._current_order)
            raise ValueError("Đơn " + str(oid) + " đang làm chưa hoàn tất")
        if self._queue.is_empty():
            return None
        order = self._queue.remove_first()
        self._set_status(order, OrderStatus.PREPARING)
        self._current_order = order
        return order

    def finish_current_order(self):
        if self._current_order is None:
            raise ValueError("Bếp chưa làm đơn nào")
        order = self._current_order
        if order.status != OrderStatus.SERVED:
            oid = self._get_order_id(order)
            raise ValueError(
                "Đơn " + str(oid) + " chưa lên món (đang '"
                + OrderStatus.get_label(order.status) + "')"
            )
        self._current_order = None
        return order

    def restore_orders(self, orders: List[Order]):
        """
        Dựng lại hàng đợi và đơn đang chế biến từ danh sách đơn đã lưu.
        Sử dụng merge_sort tự cài (ổn định, O(n log n)).
        - Đơn có priority_at được đưa lên trước, sắp giảm dần theo priority_at.
        - Phần còn lại giữ FIFO theo created_at tăng dần.
        """
        self._queue = Deque()
        self._current_order = None
        active = [o for o in orders if o.status in (OrderStatus.PENDING, OrderStatus.PREPARING)]
        # Sắp xếp tăng dần theo created_at bằng merge_sort tự cài
        active = merge_sort(active, key=lambda o: str(o.created_at))

        preparing = [o for o in active if o.status == OrderStatus.PREPARING]
        if preparing:
            self._current_order = preparing[0]

        waiting = [o for o in active if o is not self._current_order]
        for order in waiting:
            if order.status == OrderStatus.PREPARING:
                # Đơn bị gián đoạn được đưa về PENDING khi khôi phục bếp
                order.status = "PENDING"

        prioritized = [o for o in waiting if getattr(o, "priority_at", None)]
        normal = [o for o in waiting if not getattr(o, "priority_at", None)]

        # Sắp xếp prioritized giảm dần theo priority_at bằng merge_sort
        prioritized = merge_sort(prioritized, key=lambda o: str(o.priority_at), reverse=True)
        # Sắp xếp normal tăng dần theo created_at bằng merge_sort
        normal = merge_sort(normal, key=lambda o: str(o.created_at))

        for order in prioritized + normal:
            self._queue.add_last(order)

    def prioritize_order(self, order_id):
        """Đưa đơn đang chờ lên đầu hàng đợi (ngay sau đơn đang chế biến)."""
        if self._get_order_id(self._current_order) == order_id:
            raise ValueError("Đơn " + str(order_id) + " đang chế biến, không thể ưu tiên")
        order = self._queue.pop_where(lambda o: self._get_order_id(o) == order_id)
        if order is None:
            raise ValueError("Không tìm thấy đơn " + str(order_id) + " trong hàng đợi")
        self._queue.add_first(order)
        return order

    def move_waiting(self, order_id, step):
        """Đổi chỗ đơn đang chờ với đơn liền kề trong hàng đợi (step = -1 lên, +1 xuống)."""
        orders = self._queue.to_list()
        index = None
        for i, o in enumerate(orders):
            if self._get_order_id(o) == order_id:
                index = i
                break

        if index is None:
            raise ValueError("Không tìm thấy đơn " + str(order_id) + " trong hàng đợi")
        target = index + step
        if not 0 <= target < len(orders):
            raise ValueError("Đơn đã ở vị trí " + ("đầu" if step < 0 else "cuối") + " hàng đợi")
        orders[index], orders[target] = orders[target], orders[index]
        self._queue = Deque()
        for order in orders:
            self._queue.add_last(order)
        return orders

    def get_status(self, order_id):
        order = self._find_order(order_id)
        if order is None:
            return None
        return order.status

    def get_status_label(self, order_id):
        return OrderStatus.get_label(self.get_status(order_id))

    def change_status(self, order_id, new_status):
        if self._current_order is None or self._get_order_id(self._current_order) != order_id:
            raise ValueError("Chỉ đổi được trạng thái của đơn bếp đang làm")
        self._set_status(self._current_order, new_status)

    def advance_status(self):
        if self._current_order is None:
            raise ValueError("Bếp chưa làm đơn nào")
        order = self._current_order
        if order.status == OrderStatus.SERVED:
            raise ValueError("Đơn đã lên món, hãy gọi finish_current_order()")
        next_statuses = ORDER_STATUS_TRANSITIONS.get(order.status, [])
        if not next_statuses:
            raise ValueError("Đơn đã ở trạng thái cuối cùng")
        self._set_status(order, next_statuses[0])
        return order.status

    def cancel_order(self, order_id):
        if self._get_order_id(self._current_order) == order_id:
            raise ValueError(f"Đơn {order_id} đang chế biến, không thể hủy")
        
        order = self._queue.pop_where(lambda o: self._get_order_id(o) == order_id)
        if order is not None:
            self._set_status(order, OrderStatus.CANCELLED)
            return
        raise ValueError("Không tìm thấy đơn " + str(order_id) + " trong bếp")

    def peek_next_order(self):
        return self._queue.peek_first()

    def get_current_order(self):
        return self._current_order

    def get_waiting_orders(self):
        return self._queue.to_list()

    def count_waiting(self):
        return self._queue.size

    def is_empty(self):
        return self._queue.is_empty() and self._current_order is None

    def _get_current_remaining_time(self) -> int:
        """Tính thời gian còn lại của đơn đang nấu (tổng thời gian trừ thời gian đã trôi qua)."""
        if self._current_order is None:
            return 0
        total_prep = self._current_order.calculate_prep_time()
        elapsed = 0
        updated_at = getattr(self._current_order, "updated_at", None)
        if updated_at:
            try:
                start_dt = datetime.fromisoformat(updated_at)
                elapsed = max(0, int((datetime.now() - start_dt).total_seconds() / 60))
            except Exception:
                elapsed = 0
        return max(0, total_prep - elapsed)

    def estimate_wait_time(self, order):
        oid = self._get_order_id(order)
        if self._get_order_id(self._current_order) == oid:
            return self._get_current_remaining_time()

        total = 0
        if self._current_order is not None:
            total += self._get_current_remaining_time()
        for waiting in self._queue.to_list():
            if self._get_order_id(waiting) == oid:
                break
            total += waiting.calculate_prep_time()
        return total + order.calculate_prep_time()

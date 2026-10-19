from collections import deque
from uuid import uuid4

from src.models.KitchenOrder import KitchenOrder
from src.models.Order import ORDER_STATUS_TRANSITIONS, OrderStatus


class KitchenManager:
    def __init__(self):
        self._queue = deque()
        self._current_order = None

    def _get_order_id(self, order):
        if order is None:
            return None
        return getattr(order, "order_id", getattr(order, "id", None))

    def add_order(self, order):
        oid = self._get_order_id(order)
        if self._is_in_kitchen(oid):
            raise ValueError("Đơn " + str(oid) + " đã có trong bếp rồi")
        if order.status != OrderStatus.PENDING:
            raise ValueError(
                "Chỉ nhận đơn ở trạng thái '"
                + OrderStatus.get_label(OrderStatus.PENDING)
                + "'"
            )
        self._queue.append(order)

    def receive_order(self, table_id, items, notes=""):
        order = KitchenOrder(
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
            oid = self._get_order_id(self._current_order)
            raise ValueError(
                "Đơn " + str(oid) + " đang làm chưa hoàn tất"
            )
        if not self._queue:
            return None
        order = self._queue.popleft()
        if hasattr(order, "set_status"):
            order.set_status(OrderStatus.PREPARING)
        else:
            order.change_status(OrderStatus.PREPARING)
        self._current_order = order
        return order

    def restore_current_order_to_queue(self, order_id):
        """Khôi phục đơn về đầu Queue nếu lưu trạng thái PREPARING thất bại."""
        order = self._current_order
        if (
            order is None
            or self._get_order_id(order) != order_id
            or order.status != OrderStatus.PREPARING
        ):
            return False

        order.status = OrderStatus.PENDING
        if hasattr(order, "_touch"):
            order._touch()
        self._current_order = None
        self._queue.appendleft(order)
        return True

    def finish_current_order(self):
        if self._current_order is None:
            raise ValueError("Bếp chưa làm đơn nào")
        order = self._current_order
        if order.status != OrderStatus.SERVED:
            oid = self._get_order_id(order)
            raise ValueError(
                "Đơn "
                + str(oid)
                + " chưa lên món (đang '"
                + OrderStatus.get_label(order.status)
                + "')"
            )
        self._current_order = None
        return order

    def get_status(self, order_id):
        order = self._find_order(order_id)
        return order.status if order is not None else None

    def get_status_label(self, order_id):
        return OrderStatus.get_label(self.get_status(order_id))

    def change_status(self, order_id, new_status):
        if self._current_order is None or self._get_order_id(self._current_order) != order_id:
            raise ValueError("Chỉ đổi được trạng thái của đơn bếp đang làm")
        if hasattr(self._current_order, "set_status"):
            self._current_order.set_status(new_status)
        else:
            self._current_order.change_status(new_status)

    def advance_status(self):
        if self._current_order is None:
            raise ValueError("Bếp chưa làm đơn nào")
        order = self._current_order
        if order.status == OrderStatus.SERVED:
            raise ValueError("Đơn đã lên món, hãy gọi finish_current_order()")
        next_statuses = ORDER_STATUS_TRANSITIONS[order.status]
        if not next_statuses:
            raise ValueError("Đơn đã ở trạng thái cuối cùng")
        if hasattr(order, "set_status"):
            order.set_status(next_statuses[0])
        else:
            order.change_status(next_statuses[0])
        return order.status

    def cancel_order(self, order_id):
        current = self._current_order
        if current is not None and self._get_order_id(current) == order_id:
            if current.status != OrderStatus.PENDING:
                raise ValueError("Chỉ có thể hủy đơn ở trạng thái PENDING.")
            if hasattr(current, "set_status"):
                current.set_status(OrderStatus.CANCELLED)
            else:
                current.change_status(OrderStatus.CANCELLED)
            self._current_order = None
            return
        for order in self._queue:
            if self._get_order_id(order) == order_id:
                if order.status != OrderStatus.PENDING:
                    raise ValueError("Chỉ có thể hủy đơn ở trạng thái PENDING.")
                if hasattr(order, "set_status"):
                    order.set_status(OrderStatus.CANCELLED)
                else:
                    order.change_status(OrderStatus.CANCELLED)
                self._queue.remove(order)
                return
        raise ValueError("Không tìm thấy đơn " + str(order_id) + " trong bếp")

    def peek_next_order(self):
        return self._queue[0] if self._queue else None

    def get_current_order(self):
        return self._current_order

    def get_waiting_orders(self):
        return list(self._queue)

    def count_waiting(self):
        return len(self._queue)

    def is_empty(self):
        return not self._queue and self._current_order is None

    def estimate_wait_time(self, order):
        oid = self._get_order_id(order)
        current = self._current_order
        if current is not None and self._get_order_id(current) == oid:
            return order.calculate_prep_time()

        total = 0
        if current is not None:
            total += current.calculate_prep_time()
        for waiting in self._queue:
            if self._get_order_id(waiting) == oid:
                break
            total += waiting.calculate_prep_time()
        return total + order.calculate_prep_time()

    def _find_order(self, order_id):
        if self._current_order is not None and self._get_order_id(self._current_order) == order_id:
            return self._current_order
        for order in self._queue:
            if self._get_order_id(order) == order_id:
                return order
        return None

    def _is_in_kitchen(self, order_id):
        return self._find_order(order_id) is not None

from collections import deque
from datetime import datetime
from math import ceil

from src.models.Order import ORDER_STATUS_TRANSITIONS, Order, OrderStatus
from src.models.OrderItem import OrderItem


class KitchenManager:
    def __init__(self):
        self._queue: deque[Order] = deque()
        self._current_order = None
        self._next_id = 1

    def _get_order_id(self, order):
        if order is None:
            return None
        return getattr(order, "order_id", getattr(order, "id", None))

    def _set_status(self, order, new_status):
        if not order.set_status(new_status):
            raise ValueError(
                "Không thể chuyển trạng thái đơn "
                + str(self._get_order_id(order))
                + " sang '"
                + OrderStatus.get_label(new_status)
                + "'"
            )

    def _find_order(self, order_id):
        if self._get_order_id(self._current_order) == order_id:
            return self._current_order
        for order in self._queue:
            if self._get_order_id(order) == order_id:
                return order
        return None

    def _is_in_kitchen(self, order_id):
        return self._find_order(order_id) is not None

    def add_order(self, order):
        if not isinstance(order, Order):
            raise TypeError("KitchenManager chỉ nhận đối tượng Order.")
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
        order_items = []
        source_items = items.items() if isinstance(items, dict) else enumerate(items or [])
        for item_key, item_data in source_items:
            if isinstance(item_data, OrderItem):
                order_items.append(item_data)
                continue
            if not isinstance(item_data, dict):
                raise TypeError("Mỗi món trong đơn bếp phải là OrderItem hoặc dict.")
            menu_item_id = item_data.get(
                "menu_item_id",
                item_data.get("id", item_key),
            )
            order_items.append(
                OrderItem(
                    menu_item_id=str(menu_item_id),
                    item_name=str(
                        item_data.get(
                            "item_name",
                            item_data.get("name", menu_item_id),
                        )
                    ),
                    unit_price=item_data.get(
                        "unit_price",
                        item_data.get("price", 0),
                    ),
                    quantity=item_data.get("quantity", item_data.get("sl", 1)),
                    subtotal=item_data.get("subtotal"),
                    note=item_data.get("note", ""),
                    prep_time=item_data.get("prep_time", 0),
                )
            )
        order_id = "ORD-" + str(self._next_id).zfill(4)
        while self._is_in_kitchen(order_id):
            self._next_id += 1
            order_id = "ORD-" + str(self._next_id).zfill(4)
        order = Order(
            id=order_id,
            table_id=table_id,
            items=order_items,
            notes=notes,
        )
        self.add_order(order)
        self._next_id += 1
        return self.estimate_wait_time(order)


    def start_next_order(self):
        if self._current_order is not None:
            oid = self._get_order_id(self._current_order)
            raise ValueError("Đơn " + str(oid) + " đang làm chưa hoàn tất")
        if not self._queue:
            return None
        order = self._queue.popleft()
        self._set_status(order, OrderStatus.PREPARING)
        self._current_order = order
        return order

    def restore_current_order_to_queue(self, order_id):
        order = self._current_order
        if (
            order is None
            or self._get_order_id(order) != order_id
            or order.status != OrderStatus.PREPARING
        ):
            return False

        order.status = OrderStatus.PENDING
        order.preparing_started_at = None
        order._touch()
        self._current_order = None
        self._queue.appendleft(order)
        return True

    def restore_order_to_queue(self, order, position):
        if not isinstance(order, Order) or order.status != OrderStatus.PENDING:
            return False
        if self._is_in_kitchen(self._get_order_id(order)):
            return False
        self._queue.insert(min(max(position, 0), len(self._queue)), order)
        return True

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
        next_statuses = ORDER_STATUS_TRANSITIONS[order.status]
        if not next_statuses:
            raise ValueError("Đơn đã ở trạng thái cuối cùng")
        self._set_status(order, next_statuses[0])
        return order.status


    def cancel_order(self, order_id):
        if self._get_order_id(self._current_order) == order_id:
            raise ValueError("Không thể hủy đơn bếp đang được chế biến.")
        for order in self._queue:
            if self._get_order_id(order) == order_id:
                if order.status != OrderStatus.PENDING:
                    raise ValueError("Chỉ có thể hủy đơn ở trạng thái PENDING.")
                self._set_status(order, OrderStatus.CANCELLED)
                self._queue.remove(order)
                return
        raise ValueError("Không tìm thấy đơn " + str(order_id) + " trong bếp")


    def peek_next_order(self):
        return self._queue[0] if self._queue else None

    def get_current_order(self):
        return self._current_order

    def get_waiting_orders(self):
        return list(self._queue)

    def synchronize_orders(self, orders):
        active_orders = [
            order
            for order in orders
            if order.status in (OrderStatus.PENDING, OrderStatus.PREPARING)
        ]
        active_orders.sort(key=lambda order: str(order.created_at or ""))
        preparing_orders = [
            order for order in active_orders if order.status == OrderStatus.PREPARING
        ]
        if len(preparing_orders) > 1:
            raise ValueError("Chỉ được có một đơn PREPARING trong bếp.")

        for order in orders:
            order_id = self._get_order_id(order)
            if isinstance(order_id, str) and order_id.startswith("ORD-"):
                sequence = order_id.rsplit("-", 1)[-1]
                if sequence.isdigit():
                    self._next_id = max(self._next_id, int(sequence) + 1)

        self._queue = deque()
        self._current_order = preparing_orders[0] if preparing_orders else None
        for order in active_orders:
            if order.status == OrderStatus.PENDING:
                self.add_order(order)

    def restore_orders(self, orders):
        self.synchronize_orders(orders or [])

    def count_waiting(self):
        return len(self._queue)

    def is_empty(self):
        return not self._queue and self._current_order is None

    def estimate_wait_time(self, order):
        oid = self._get_order_id(order)
        if self._get_order_id(self._current_order) == oid:
            return self._remaining_prep_time(self._current_order)

        total = 0
        if self._current_order is not None:
            total += self._remaining_prep_time(self._current_order)
        for waiting in self._queue:
            if self._get_order_id(waiting) == oid:
                break
            total += waiting.calculate_prep_time()
        return total + order.calculate_prep_time()

    @staticmethod
    def _remaining_prep_time(order):
        prep_seconds = order.calculate_prep_time() * 60
        started_at = getattr(order, "preparing_started_at", None)
        if not started_at:
            return ceil(prep_seconds / 60)

        try:
            started = datetime.fromisoformat(started_at)
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"Thời điểm bắt đầu chế biến của đơn '{order.id}' không hợp lệ."
            ) from error

        now = datetime.now(started.tzinfo) if started.tzinfo else datetime.now()
        elapsed = max(0, (now - started).total_seconds())
        return ceil(max(0, prep_seconds - elapsed) / 60)

from src.models.Order import ORDER_STATUS_TRANSITIONS, Order, OrderStatus
from src.models.OrderItem import OrderItem
from src.structures.linked_list import DoublyLinkedList


class KitchenManager:
    def __init__(self):
        self._queue = DoublyLinkedList()   # hàng đợi các đơn đang chờ (vào trước ra trước)
        self._current_order = None         # đơn bếp đang làm
        self._next_id = 1                  # dùng để sinh mã đơn

    # ---------- Tiện ích ----------

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
        """Tìm đơn theo mã, trong đơn đang làm và trong hàng đợi."""
        if self._get_order_id(self._current_order) == order_id:
            return self._current_order
        node = self._queue.head
        while node is not None:
            if self._get_order_id(node.data) == order_id:
                return node.data
            node = node.next
        return None

    def _is_in_kitchen(self, order_id):
        return self._find_order(order_id) is not None

    # ---------- Nhận đơn ----------

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
        self._queue.add_last(order)

    def receive_order(self, table_id, items, notes=""):
        """
        items: DoublyLinkedList, mỗi phần tử là OrderItem
               hoặc HashTable (kết quả của Cart.get_order_items()).
        """
        order_id = "ORD-" + str(self._next_id).zfill(4)
        self._next_id += 1

        order_items = DoublyLinkedList()
        if isinstance(items, dict):
            for menu_item_id, details in items.items():
                if isinstance(details, dict):
                    order_items.add_last(
                        OrderItem(
                            menu_item_id=menu_item_id,
                            item_name=details.get("item_name", details.get("name", str(menu_item_id))),
                            unit_price=details.get("unit_price", 0),
                            quantity=details.get("quantity", details.get("sl", 1)),
                            note=details.get("note", ""),
                            prep_time=details.get("prep_time", 0),
                        )
                    )
        else:
            for data in items:
                if isinstance(data, OrderItem):
                    order_items.add_last(data)
                else:
                    order_items.add_last(OrderItem.from_dict(data))

        order = Order(
            id=order_id,
            table_id=table_id,
            items=order_items,
            notes=notes,
        )
        self.add_order(order)
        self._next_id += 1
        return self.estimate_wait_time(order)

    # ---------- Chế biến ----------

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

    def restore_current_order_to_queue(self, order_id):
        if (
            self._current_order is None
            or self._get_order_id(self._current_order) != order_id
        ):
            return False
        order = self._current_order
        order.status = OrderStatus.PENDING
        order.preparing_started_at = None
        order._touch()
        self._queue.add_first(order)
        self._current_order = None
        return True

    def restore_order_to_queue(self, order, position):
        if not isinstance(order, Order) or order.status != OrderStatus.PENDING:
            return False
        if self._is_in_kitchen(self._get_order_id(order)):
            return False
        pos = min(max(position, 0), self._queue.size)
        self._queue.insert(pos, order)
        return True

    # ---------- Trạng thái ----------

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
        next_statuses = ORDER_STATUS_TRANSITIONS.get(order.status)
        if next_statuses is None or next_statuses.is_empty():
            raise ValueError("Đơn đã ở trạng thái cuối cùng")
        self._set_status(order, next_statuses.peek_first())
        return order.status

    # ---------- Hủy đơn ----------

    def cancel_order(self, order_id):
        if self._get_order_id(self._current_order) == order_id:
            raise ValueError("Không thể hủy đơn bếp đang được chế biến")

        node = self._queue.head
        while node is not None:
            order = node.data
            if self._get_order_id(order) == order_id:
                self._set_status(order, OrderStatus.CANCELLED)
                self._queue.remove(order)
                return
            node = node.next
        raise ValueError("Không tìm thấy đơn " + str(order_id) + " trong bếp")

    # ---------- Truy vấn ----------

    def peek_next_order(self):
        return self._queue.peek_first()

    def get_current_order(self):
        return self._current_order

    def get_waiting_orders(self):
        """Trả về một DoublyLinkedList mới chứa các đơn đang chờ."""
        result = DoublyLinkedList()
        node = self._queue.head
        while node is not None:
            result.add_last(node.data)
            node = node.next
        return result

    def synchronize_orders(self, orders):
        """
        Đồng bộ lại hàng đợi và đơn đang làm theo danh sách orders (list hoặc DoublyLinkedList).
        """
        orders_list = []
        if isinstance(orders, DoublyLinkedList):
            node = orders.head
            while node is not None:
                orders_list.append(node.data)
                node = node.next
        elif orders is not None:
            orders_list = list(orders)

        active_orders = [
            order
            for order in orders_list
            if order.status in (OrderStatus.PENDING, OrderStatus.PREPARING)
        ]
        active_orders.sort(key=lambda order: str(order.created_at or ""))
        preparing_orders = [
            order for order in active_orders if order.status == OrderStatus.PREPARING
        ]
        if len(preparing_orders) > 1:
            raise ValueError("Chỉ được có một đơn PREPARING trong bếp.")

        for order in orders_list:
            order_id = self._get_order_id(order)
            if isinstance(order_id, str) and order_id.startswith("ORD-"):
                sequence = order_id.rsplit("-", 1)[-1]
                if sequence.isdigit():
                    self._next_id = max(self._next_id, int(sequence) + 1)

        self._queue = DoublyLinkedList()
        self._current_order = preparing_orders[0] if preparing_orders else None
        for order in active_orders:
            if order.status == OrderStatus.PENDING:
                self.add_order(order)

    def restore_orders(self, orders):
        self.synchronize_orders(orders or [])

    def count_waiting(self):
        return len(self._queue)

    def is_empty(self):
        return self._queue.is_empty() and self._current_order is None

    def estimate_wait_time(self, order):
        """Thời gian chờ = đơn đang làm + các đơn xếp trước + chính đơn này."""
        oid = self._get_order_id(order)
        if self._get_order_id(self._current_order) == oid:
            return order.calculate_prep_time()

        total = 0
        if self._current_order is not None:
            total += self._current_order.calculate_prep_time()
        node = self._queue.head
        while node is not None:
            if self._get_order_id(node.data) == oid:
                break
            total += node.data.calculate_prep_time()
            node = node.next
        return total + order.calculate_prep_time()

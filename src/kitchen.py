import os
import sys
from collections import deque
from datetime import datetime

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

# Thống nhất theo chỉ đạo của Mentor: Sử dụng duy nhất Order và OrderStatus từ src.models.Order
try:
    from src.models.Order import Order, OrderStatus
except ImportError:
    try:
        from models.Order import Order, OrderStatus
    except ImportError:
        from .models.Order import Order, OrderStatus


def now_time():
    return datetime.now().isoformat(timespec="seconds")

class KitchenManager:
    def __init__(self):
        self._queue = deque()        
        self._current_order = None     

    # ---------- 8.1: thêm đơn, lấy đơn ----------
    def add_order(self, order):
        if self._is_in_kitchen(order.order_id):
            raise ValueError("Đơn " + str(order.order_id) + " đã có trong bếp rồi")
        if order.status != OrderStatus.PENDING:
            raise ValueError("Chỉ nhận đơn ở trạng thái '"
                             + OrderStatus.get_label(OrderStatus.PENDING) + "'")
        self._queue.append(order)      # append = thêm vào cuối hàng

    def start_next_order(self):
        if self._current_order is not None:
            raise ValueError("Đơn " + str(self._current_order.order_id)
                             + " đang làm chưa hoàn tất")
        if len(self._queue) == 0:
            return None
        order = self._queue.popleft() 
        order.set_status(OrderStatus.PREPARING)
        self._current_order = order
        return order

    def finish_current_order(self):
        """Đơn đã lên món (SERVED) thì rời khỏi bếp."""
        if self._current_order is None:
            raise ValueError("Bếp chưa làm đơn nào")
        order = self._current_order
        if order.status != OrderStatus.SERVED:
            raise ValueError("Đơn " + str(order.order_id) + " chưa lên món (đang '"
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
        if self._current_order is None or self._current_order.order_id != order_id:
            raise ValueError("Chỉ đổi được trạng thái của đơn bếp đang làm")
        self._current_order.set_status(new_status)  

    def advance_status(self):
        if self._current_order is None:
            raise ValueError("Bếp chưa làm đơn nào")
        order = self._current_order
        if order.status == OrderStatus.SERVED:
            raise ValueError("Đơn đã lên món, hãy gọi finish_current_order()")
        next_list = OrderStatus.VALID_NEXT[order.status]
        if len(next_list) == 0:
            raise ValueError("Đơn đã ở trạng thái cuối cùng")
        order.set_status(next_list[0])
        return order.status

    def cancel_order(self, order_id):
       
        current = self._current_order
        if current is not None and current.order_id == order_id:
            current.set_status(OrderStatus.CANCELLED)  
            self._current_order = None
            return
        for order in self._queue:
            if order.order_id == order_id:
                order.set_status(OrderStatus.CANCELLED)
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
        if current is not None and current.order_id == order.order_id:
            return order.calculate_prep_time()

        total = 0
        if current is not None:
            total += current.calculate_prep_time()
        for waiting in self._queue:
            if waiting.order_id == order.order_id:
                break
            total += waiting.calculate_prep_time()
        return total + order.calculate_prep_time()

    def _find_order(self, order_id):
        if self._current_order is not None and self._current_order.order_id == order_id:
            return self._current_order
        for order in self._queue:
            if order.order_id == order_id:
                return order
        return None

    def _is_in_kitchen(self, order_id):
        return self._find_order(order_id) is not None
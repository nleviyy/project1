from src.models.KitchenOrder import KitchenOrder
from src.models.Order import ORDER_STATUS_TRANSITIONS, OrderStatus


class Node:
    def __init__(self, data):
        self.data = data
        self.prev = None
        self.next = None


class DoublyLinkedList:
    def __init__(self):
        self.head = None   
        self.tail = None   
        self.size = 0     

    def is_empty(self):
        return self.size == 0

    def add_last(self, data):
        new_node = Node(data)
        if self.tail is None:          
            self.head = new_node
            self.tail = new_node
        else:
            new_node.prev = self.tail
            self.tail.next = new_node
            self.tail = new_node
        self.size += 1

    def remove_first(self):
        if self.head is None:
            return None
        data = self.head.data
        self.head = self.head.next
        if self.head is None:          
            self.tail = None
        else:
            self.head.prev = None
        self.size -= 1
        return data

    def peek_first(self):
        if self.head is None:
            return None
        return self.head.data

    def remove(self, data):
        node = self.head
        while node is not None:
            if node.data == data:
                break
            node = node.next

        if node is None:               
            return False

        if node.prev is None:          
            self.head = node.next
        else:
            node.prev.next = node.next

        if node.next is None:         
            self.tail = node.prev
        else:
            node.next.prev = node.prev

        self.size -= 1
        return True

    def to_list(self):
        result = []
        node = self.head
        while node is not None:
            result.append(node.data)
            node = node.next
        return result


class KitchenManager:
    def __init__(self):
        self._queue = DoublyLinkedList()   
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
        self._queue.add_last(order)

    def receive_order(self, table_id, items, notes=""):
        order_id = "ORD-" + str(self._next_id).zfill(4)   
        self._next_id += 1
        order = KitchenOrder(
            order_id=order_id,
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
            self._set_status(self._current_order, OrderStatus.CANCELLED)
            self._current_order = None
            return
        
        for order in self._queue.to_list():
            if self._get_order_id(order) == order_id:
                self._set_status(order, OrderStatus.CANCELLED)
                self._queue.remove(order)
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

    def estimate_wait_time(self, order):
        oid = self._get_order_id(order)
        if self._get_order_id(self._current_order) == oid:
            return order.calculate_prep_time()

        total = 0
        if self._current_order is not None:
            total += self._current_order.calculate_prep_time()
        for waiting in self._queue.to_list():
            if self._get_order_id(waiting) == oid:
                break
            total += waiting.calculate_prep_time()
        return total + order.calculate_prep_time()
from datetime import datetime

from src.structures.linked_list import DoublyLinkedList
from src.structures.hash_table import HashTable


class PaymentMethod:
    CASH = "CASH"
    BANK_TRANSFER = "BANK_TRANSFER"
    CARD = "CARD"


class PaymentStatus:
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"
    REFUNDED = "REFUNDED"


def _non_negative_int(value, name, default=0):
    if value is None:
        return default
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError(name + " phải là số nguyên.")
    if number < 0:
        raise ValueError(name + " không được âm.")
    return number


class Payment:
    def __init__(
        self,
        id=None,
        order_id=None,
        table_id=None,
        cashier_name=None,
        amount=0,
        discount_rate=0.0,
        amount_paid=0,
        method=None,
        status=None,
        transaction_code=None,
        note="",
        cash_received=None,
        change_due=0,
        payment_time=None,
        payment_id=None,
    ):
        if id is None:
            id = payment_id
        if id is None or order_id is None or table_id is None or cashier_name is None:
            raise ValueError("Thiếu thông tin bắt buộc: id, order_id, table_id, cashier_name.")

        if method is None:
            method = PaymentMethod.CASH
        if method != PaymentMethod.CASH and method != PaymentMethod.BANK_TRANSFER and method != PaymentMethod.CARD:
            raise ValueError("Phương thức thanh toán không hợp lệ: " + str(method))

        if status is None:
            status = PaymentStatus.SUCCESS
        if (
            status != PaymentStatus.SUCCESS
            and status != PaymentStatus.FAILED
            and status != PaymentStatus.PENDING
            and status != PaymentStatus.REFUNDED
        ):
            raise ValueError("Trạng thái giao dịch không hợp lệ: " + str(status))

        if discount_rate is None:
            discount_rate = 0.0
        if discount_rate < 0 or discount_rate > 1:
            raise ValueError("Tỷ lệ giảm giá phải nằm trong khoảng 0 đến 1.")

        self.id = id
        self.order_id = order_id
        self.table_id = table_id
        self.cashier_name = cashier_name
        self.payment_time = payment_time if payment_time is not None else datetime.now().isoformat()
        self.amount = _non_negative_int(amount, "Tổng tiền")
        self.discount_rate = discount_rate
        self.amount_paid = _non_negative_int(amount_paid, "Số tiền khách trả")
        self.method = method
        self.status = status
        self.transaction_code = transaction_code
        self.note = note if note is not None else ""
        self.cash_received = _non_negative_int(cash_received, "Tiền khách đưa", None)
        self.change_due = _non_negative_int(change_due, "Tiền thối")

        # Giao dịch thành công mà chưa ghi số tiền trả thì tự tính theo giảm giá
        if self.status == PaymentStatus.SUCCESS and self.amount_paid == 0:
            self.amount_paid = int(self.amount * (1 - self.discount_rate))

    @property
    def payment_id(self):
        return self.id

    @property
    def is_successful(self):
        return self.status == PaymentStatus.SUCCESS

    def calculate_change(self, cash_given):
        """Tính tiền thối lại cho khách khi thanh toán tiền mặt."""
        final_due = int(self.amount * (1 - self.discount_rate))
        if cash_given < final_due:
            raise ValueError(
                "Số tiền khách đưa ({:,} VNĐ) không đủ thanh toán ({:,} VNĐ).".format(
                    cash_given, final_due
                )
            )
        return cash_given - final_due

    def to_dict(self):
        data = HashTable()
        data.put("id", self.id)
        data.put("order_id", self.order_id)
        data.put("table_id", self.table_id)
        data.put("payment_time", self.payment_time)
        data.put("amount", self.amount)
        data.put("discount_rate", self.discount_rate)
        data.put("amount_paid", self.amount_paid)
        data.put("method", self.method)
        data.put("status", self.status)
        data.put("cashier_name", self.cashier_name)
        data.put("transaction_code", self.transaction_code)
        data.put("note", self.note)
        data.put("cash_received", self.cash_received)
        data.put("change_due", self.change_due)
        return data

    @classmethod
    def from_dict(cls, data):
        payment_id = data.get("id")
        if payment_id is None:
            payment_id = data.get("payment_id")
        return cls(
            id=payment_id,
            order_id=data.get("order_id"),
            table_id=data.get("table_id"),
            cashier_name=data.get("cashier_name"),
            amount=data.get("amount"),
            discount_rate=data.get("discount_rate"),
            amount_paid=data.get("amount_paid"),
            method=data.get("method"),
            status=data.get("status"),
            transaction_code=data.get("transaction_code"),
            note=data.get("note"),
            cash_received=data.get("cash_received"),
            change_due=data.get("change_due"),
            payment_time=data.get("payment_time"),
        )

    @classmethod
    def model_validate(cls, data):
        if not isinstance(data, (dict, HashTable)):
            raise TypeError("Dữ liệu thanh toán phải là dict hoặc HashTable.")
        return cls.from_dict(data)

    def model_dump(self):
        return self.to_dict()

    @classmethod
    def calculate_revenue(cls, payments):
        total_revenue = 0
        processed_payment_ids = HashTable()
        paid_orders = HashTable()
        paid_order_ids = DoublyLinkedList()

        payment_list = []
        if isinstance(payments, DoublyLinkedList):
            node = payments.head
            while node is not None:
                payment_list.append(node.data)
                node = node.next
        elif payments is not None:
            payment_list = list(payments)

        for payment in payment_list:
            if not payment.is_successful:
                continue
            if processed_payment_ids.contains(payment.id):
                continue
            if paid_orders.contains(payment.order_id):
                continue

            total_revenue += payment.amount_paid
            processed_payment_ids.put(payment.id, True)
            paid_orders.put(payment.order_id, True)
            paid_order_ids.add_last(payment.order_id)

        result = HashTable()
        result.put("total_revenue", total_revenue)
        result.put("paid_orders_count", paid_orders.size)
        result.put("paid_order_ids", paid_order_ids)
        return result
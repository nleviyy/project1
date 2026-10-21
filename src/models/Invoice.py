from datetime import datetime

from src.structures.linked_list import DoublyLinkedList
from src.structures.hash_table import HashTable
from .OrderItem import OrderItem
from .Payment import PaymentMethod


def _non_negative_int(value, name, default=None):
    if value is None:
        return default
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError(name + " phải là số nguyên.")
    if number < 0:
        raise ValueError(name + " không được âm.")
    return number


class Invoice:
    def __init__(
        self,
        id,
        order_id,
        table_id,
        total_amount,
        payment_method,
        cashier_name,
        payment_id=None,
        issued_at=None,
        items=None,
        subtotal=None,
        discount_amount=0,
        final_amount=None,
    ):
        if not isinstance(id, str) or id.strip() == "":
            raise ValueError("Mã hóa đơn không được để trống.")
        if not isinstance(order_id, str) or order_id.strip() == "":
            raise ValueError("Mã đơn hàng không được để trống.")
        if table_id is None:
            raise ValueError("Mã bàn không được để trống.")
        if cashier_name is None:
            raise ValueError("Tên thu ngân không được để trống.")
        if (
            payment_method != PaymentMethod.CASH
            and payment_method != PaymentMethod.BANK_TRANSFER
            and payment_method != PaymentMethod.CARD
        ):
            raise ValueError("Phương thức thanh toán không hợp lệ: " + str(payment_method))
        self.id = id
        self.payment_id = payment_id
        self.order_id = order_id
        self.table_id = table_id
        self.issued_at = issued_at if issued_at is not None else datetime.now().isoformat(timespec="seconds")
        self.payment_method = payment_method
        self.cashier_name = cashier_name

        # Chi tiết món: DoublyLinkedList các HashTable
        self.items = DoublyLinkedList()
        if items is not None:
            item_values = items if isinstance(items, (DoublyLinkedList, list, tuple)) else None
            if item_values is None:
                raise TypeError("items phải là danh sách các OrderItem hoặc dữ liệu món.")
            for item in item_values:
                if isinstance(item, OrderItem):
                    self.items.add_last(item.to_dict())
                else:
                    self.items.add_last(item)

        self.total_amount = _non_negative_int(total_amount, "Tổng tiền thanh toán")
        if self.total_amount is None:
            raise ValueError("Tổng tiền thanh toán không được để trống.")
        self.discount_amount = _non_negative_int(discount_amount, "Tiền giảm giá", 0)

        self.subtotal = _non_negative_int(subtotal, "Tổng tiền trước giảm giá", self.total_amount)
        self.final_amount = _non_negative_int(final_amount, "Số tiền thực thu", self.total_amount)

    def generate_text_receipt(self):
        text = "=" * 40 + "\n"
        text += "          HÓA ĐƠN THANH TOÁN\n"
        text += " Mã hóa đơn: " + str(self.id) + "\n"
        text += " Đơn hàng: " + str(self.order_id) + " | Bàn: " + str(self.table_id) + "\n"
        text += " Thời gian : " + str(self.issued_at) + "\n"
        text += "-" * 40 + "\n"
        text += "{:<20}{:>4}{:>16}".format("Tên món", "SL", "Thành tiền") + "\n"
        text += "-" * 40 + "\n"

        node = self.items.head
        while node is not None:
            item = node.data       # HashTable mô tả món

            name = item.get("item_name")
            if name is None:
                name = item.get("name")
            if name is None:
                name = "Món"

            quantity = item.get("quantity")
            if quantity is None:
                quantity = 1

            amount = item.get("subtotal")
            if amount is None:
                unit_price = item.get("unit_price")
                if unit_price is None:
                    unit_price = 0
                amount = unit_price * quantity

            text += "{:<20}{:>4}{:>14,d}đ".format(str(name)[:19], quantity, amount) + "\n"
            node = node.next

        text += "-" * 40 + "\n"
        text += "Tổng tiền món : {:>18,d} VNĐ".format(self.subtotal) + "\n"
        text += "Giảm giá      : -{:>17,d} VNĐ".format(self.discount_amount) + "\n"
        text += "THỰC THU      : {:>18,d} VNĐ".format(self.final_amount) + "\n"
        text += "Hình thức TT  : " + str(self.payment_method) + "\n"
        text += "=" * 40 + "\n"
        text += "    Cảm ơn quý khách và hẹn gặp lại!\n"
        text += "=" * 40
        return text

    def to_dict(self):
        data = HashTable()
        data.put("id", self.id)
        data.put("payment_id", self.payment_id)
        data.put("order_id", self.order_id)
        data.put("table_id", self.table_id)
        data.put("issued_at", self.issued_at)
        data.put("items", self.items)
        data.put("subtotal", self.subtotal)
        data.put("discount_amount", self.discount_amount)
        data.put("total_amount", self.total_amount)
        data.put("final_amount", self.final_amount)
        data.put("payment_method", self.payment_method)
        data.put("cashier_name", self.cashier_name)
        return data

    def model_dump(self):
        return self.to_dict()

    @classmethod
    def from_dict(cls, data):
        discount_amount = data.get("discount_amount")
        if discount_amount is None:
            discount_amount = 0
        return cls(
            id=data.get("id"),
            order_id=data.get("order_id"),
            table_id=data.get("table_id"),
            total_amount=data.get("total_amount"),
            payment_method=data.get("payment_method"),
            cashier_name=data.get("cashier_name"),
            payment_id=data.get("payment_id"),
            issued_at=data.get("issued_at"),
            items=data.get("items"),
            subtotal=data.get("subtotal"),
            discount_amount=discount_amount,
            final_amount=data.get("final_amount"),
        )
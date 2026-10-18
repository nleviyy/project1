"""
Model Payment: Quản lý thông tin và kết quả giao dịch thanh toán.
Đảm bảo toàn bộ số tiền là số nguyên int (VNĐ), chống thanh toán trùng lặp.
"""
from datetime import datetime
from typing import Any, Dict, Optional


class PaymentMethod:
    CASH = "CASH"                    # Tiền mặt
    BANK_TRANSFER = "BANK_TRANSFER"  # Chuyển khoản (VietQR / Internet Banking)
    MOMO = "MOMO"                    # Ví MoMo
    CARD = "CARD"                    # Thẻ ngân hàng / POS

    ALL = {CASH, BANK_TRANSFER, MOMO, CARD}


class PaymentStatus:
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

    ALL = {PENDING, SUCCESS, FAILED}


class Payment:
    """
    Đại diện cho một giao dịch thanh toán trong hệ thống.
    """

    def __init__(
        self,
        id: str,
        order_id: str,
        table_id: int,
        amount_paid: int,
        method: str = PaymentMethod.CASH,
        status: str = PaymentStatus.SUCCESS,
        payment_time: Optional[str] = None,
        cashier_name: str = "Vy",
        transaction_code: Optional[str] = None,
        note: str = "",
    ):
        self.id: str = str(id).strip()
        self.order_id: str = str(order_id).strip()
        self.table_id: int = int(table_id)
        self.amount_paid: int = int(amount_paid)
        self.method: str = method.upper().strip()
        self.status: str = status.upper().strip()
        self.payment_time: str = payment_time or datetime.now().isoformat(timespec="seconds")
        self.cashier_name: str = str(cashier_name).strip()
        self.transaction_code: Optional[str] = str(transaction_code).strip() if transaction_code else None
        self.note: str = (note or "").strip()

        if self.amount_paid < 0:
            raise ValueError("Số tiền thanh toán không được âm.")

    @property
    def is_successful(self) -> bool:
        return self.status == PaymentStatus.SUCCESS

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "table_id": self.table_id,
            "payment_time": self.payment_time,
            "amount_paid": int(self.amount_paid),
            "method": self.method,
            "status": self.status,
            "cashier_name": self.cashier_name,
            "transaction_code": self.transaction_code,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Payment":
        return cls(
            id=str(data.get("id", "")),
            order_id=str(data.get("order_id", "")),
            table_id=int(data.get("table_id", 0)),
            amount_paid=int(data.get("amount_paid", 0)),
            method=str(data.get("method", PaymentMethod.CASH)),
            status=str(data.get("status", PaymentStatus.SUCCESS)),
            payment_time=data.get("payment_time"),
            cashier_name=str(data.get("cashier_name", "Vy")),
            transaction_code=data.get("transaction_code"),
            note=str(data.get("note", "")),
        )

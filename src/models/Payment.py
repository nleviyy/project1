from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.models.HashTable import HashTable


class PaymentMethod(str, Enum):
    CASH = "CASH"
    BANK_TRANSFER = "BANK_TRANSFER"
    CARD = "CARD"


class PaymentStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"
    REFUNDED = "REFUNDED"


class Payment(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="payment_id", description="Mã giao dịch thanh toán")
    order_id: str = Field(..., description="Mã đơn hàng liên kết")
    table_id: Union[int, str] = Field(..., description="Mã bàn thanh toán")
    payment_time: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Thời gian thanh toán")
    amount: int = Field(default=0, ge=0, description="Tổng tiền gốc của hóa đơn (VNĐ)")
    discount_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Tỷ lệ giảm giá (VD: 0.1 tương ứng 10%)")
    amount_paid: int = Field(default=0, ge=0, description="Số tiền thực tế khách trả (VNĐ)")
    method: PaymentMethod = Field(
        default=PaymentMethod.CASH, description="Phương thức thanh toán"
    )
    status: Optional[PaymentStatus] = Field(
        default=None, description="Trạng thái giao dịch"
    )
    cashier_name: str = Field(..., description="Tên nhân viên thu ngân")
    transaction_code: Optional[str] = Field(default=None, description="Mã giao dịch ngân hàng/điện tử nếu có")
    note: Optional[str] = Field(default="", description="Ghi chú thanh toán")
    cash_received: Optional[int] = Field(default=None, ge=0, description="Tiền mặt khách đưa (VNĐ)")
    change_due: int = Field(default=0, ge=0, description="Tiền thối lại (VNĐ)")

    @model_validator(mode="before")
    @classmethod
    def set_default_status(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "status" not in data or data["status"] is None:
                # Nếu amount_paid > 0 và không truyền status rõ ràng (tương thích test cũ), SUCCESS; ngược lại PENDING
                if data.get("amount_paid", 0) > 0 and not data.get("is_pending_test"):
                    data["status"] = PaymentStatus.SUCCESS
                else:
                    data["status"] = PaymentStatus.PENDING
        return data

    @model_validator(mode='after')
    def calculate_final_amount(self):
        """Tự động tính toán số tiền cần trả sau giảm giá nếu amount_paid chưa được gán."""
        if self.status is None:
            self.status = PaymentStatus.PENDING

        final_due = int(self.amount * (1 - self.discount_rate))
        if self.status == PaymentStatus.SUCCESS and self.amount_paid == 0:
            self.amount_paid = final_due
        return self

    @property
    def is_successful(self) -> bool:
        """Kiểm tra xem giao dịch có thành công hay không."""
        return self.status == PaymentStatus.SUCCESS

    def calculate_change(self, cash_given: int) -> int:
        """Tính tiền thối lại cho khách khi thanh toán tiền mặt (UI hỗ trợ)."""
        final_due = int(self.amount * (1 - self.discount_rate))
        if cash_given < final_due:
            raise ValueError(f"Số tiền khách đưa ({cash_given:,} VNĐ) không đủ thanh toán ({final_due:,} VNĐ).")
        return cash_given - final_due

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Payment":
        return cls.model_validate(data)

    @classmethod
    def calculate_revenue(cls, payments: List["Payment"]) -> Dict[str, Any]:
        """
        Thuật toán tính doanh thu an toàn bằng HashTable (không dùng set built-in):
        - Chỉ cộng tiền các giao dịch thành công (SUCCESS).
        - Tránh cộng trùng lặp mã giao dịch (payment_id) và tránh cộng dồn nhiều lần cho cùng một đơn hàng (order_id).
        - Trả về tổng doanh thu, số lượng đơn đã thanh toán và danh sách mã đơn.
        """
        total_revenue = 0
        paid_order_ids_table = HashTable()
        processed_payment_ids_table = HashTable()
        paid_order_ids_list = []

        for payment in payments:
            if not payment.is_successful:
                continue

            if payment.id in processed_payment_ids_table:
                continue

            if payment.order_id in paid_order_ids_table:
                continue

            total_revenue += payment.amount_paid
            processed_payment_ids_table.put(payment.id, True)
            paid_order_ids_table.put(payment.order_id, True)
            paid_order_ids_list.append(payment.order_id)

        return {
            "total_revenue": total_revenue,
            "paid_orders_count": len(paid_order_ids_list),
            "paid_order_ids": paid_order_ids_list,
        }

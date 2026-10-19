from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, model_validator

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
    status: PaymentStatus = Field(
        default=PaymentStatus.SUCCESS, description="Trạng thái giao dịch"
    )
    cashier_name: str = Field(..., description="Tên nhân viên thu ngân")
    transaction_code: Optional[str] = Field(default=None, description="Mã giao dịch ngân hàng/điện tử nếu có")
    note: Optional[str] = Field(default="", description="Ghi chú thanh toán")
    cash_received: Optional[int] = Field(default=None, ge=0, description="Tiền mặt khách đưa (VNĐ)")
    change_due: int = Field(default=0, ge=0, description="Tiền thối lại (VNĐ)")

    @model_validator(mode='after')
    def calculate_final_amount(self):
        """Tự động tính toán số tiền cần trả sau giảm giá nếu amount_paid chưa được gán."""
        final_due = int(self.amount * (1 - self.discount_rate))
        if self.status == "SUCCESS" and self.amount_paid == 0:
            self.amount_paid = final_due
        return self

    @property
    def is_successful(self) -> bool:
        """Kiểm tra xem giao dịch có thành công hay không."""
        return self.status == "SUCCESS"

    def calculate_change(self, cash_given: int) -> int:
        """Tính tiền thối lại cho khách khi thanh toán tiền mặt."""
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
        Thuật toán tính doanh thu an toàn:
        - Chỉ cộng tiền các giao dịch thành công (SUCCESS).
        - Tránh cộng trùng lặp mã giao dịch (payment_id) và tránh cộng dồn nhiều lần cho cùng một đơn hàng (order_id).
        - Trả về tổng doanh thu, số lượng đơn đã thanh toán và danh sách mã đơn.
        """
        total_revenue = 0
        paid_order_ids = set()
        processed_payment_ids = set()

        for payment in payments:
            if not payment.is_successful:
                continue

            if payment.id in processed_payment_ids:
                continue

            if payment.order_id in paid_order_ids:
                continue

            total_revenue += payment.amount_paid
            processed_payment_ids.add(payment.id)
            paid_order_ids.add(payment.order_id)

        return {
            "total_revenue": total_revenue,
            "paid_orders_count": len(paid_order_ids),
            "paid_order_ids": list(paid_order_ids)
        }
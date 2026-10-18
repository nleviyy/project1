from typing import Optional, Literal, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, model_validator

PaymentMethod = Literal["CASH", "BANK_TRANSFER", "CREDIT_CARD", "E_WALLET"]
PaymentStatus = Literal["SUCCESS", "FAILED", "PENDING", "REFUNDED"]

class Payment(BaseModel):
    id: str = Field(..., alias="payment_id")
    order_id: str
    table_id: str 
    payment_time: str = Field(default_factory=lambda: datetime.now().isoformat())
    amount: int = Field(..., ge=0, description="Tổng tiền gốc của hóa đơn (VNĐ)")
    discount_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Tỷ lệ giảm giá (VD: 0.1 tương ứng 10%)")
    amount_paid: int = Field(..., ge=0, description="Số tiền thực tế khách trả (VNĐ)")
    method: PaymentMethod
    status: PaymentStatus = Field(default="SUCCESS")
    cashier_name: str
    transaction_code: Optional[str] = None
    note: Optional[str] = ""

    @model_validator(mode='after')
    def calculate_final_amount(self):
        """Tự động tính toán số tiền cần trả sau giảm giá nếu chưa gán"""
        # Có thể dùng để kiểm tra tính hợp lệ số tiền khách đưa
        return self

    @property
    def is_successful(self) -> bool:
        return self.status == "SUCCESS"

    def calculate_change(self, cash_given: int) -> int:
        """Tính tiền thối lại cho khách khi thanh toán tiền mặt"""
        final_due = int(self.amount * (1 - self.discount_rate))
        if cash_given < final_due:
            raise ValueError("Số tiền khách đưa không đủ thanh toán.")
        return cash_given - final_due

    @classmethod
    def calculate_revenue(cls, payments: List["Payment"]) -> Dict[str, Any]:
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
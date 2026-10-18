from typing import Optional, Literal, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

PaymentMethod = Literal["CASH", "BANK_TRANSFER", "CREDIT_CARD", "E_WALLET"]
PaymentStatus = Literal["SUCCESS", "FAILED", "PENDING", "REFUNDED"]


class Payment(BaseModel):
    id: str
    order_id: str
    table_id: int
    payment_time: str = Field(default_factory=lambda: datetime.now().isoformat())
    amount_paid: float = Field(..., ge=0.0)
    method: PaymentMethod
    status: PaymentStatus = Field(default="SUCCESS")
    cashier_name: str
    transaction_code: Optional[str] = None
    note: Optional[str] = ""

    @property
    def is_successful(self) -> bool:
        return self.status == "SUCCESS"

    @classmethod
    def calculate_revenue(cls, payments: List["Payment"]) -> Dict[str, Any]:
        total_revenue = 0.0
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
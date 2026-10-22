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
    payment_time: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Thời gian thanh toán (ISO string)"
    )
    amount: int = Field(default=0, ge=0, description="Tổng tiền gốc của hóa đơn (VNĐ)")
    discount_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Tỷ lệ giảm giá (VD: 0.1 tương ứng 10%)")
    amount_paid: int = Field(default=0, ge=0, description="Số tiền thực tế khách trả (VNĐ)")
    method: PaymentMethod = Field(
        default=PaymentMethod.CASH, description="Phương thức thanh toán"
    )
    status: PaymentStatus = Field(
        default=PaymentStatus.PENDING, description="Trạng thái giao dịch"
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
                data["status"] = PaymentStatus.PENDING
        return data

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
        - Chống cộng trùng lặp đơn hàng (Idempotency).
        """
        seen_orders = HashTable()
        total_revenue = 0

        for p in payments:
            if p.is_successful:
                if not seen_orders.contains(p.order_id):
                    total_revenue += p.amount_paid
                    seen_orders.put(p.order_id, True)

        return {
            "total_revenue": total_revenue,
            "successful_orders_count": seen_orders.size,
        }

from datetime import datetime
from typing import Any, Union

from pydantic import BaseModel, Field, model_validator

from .Payment import PaymentMethod


class Invoice(BaseModel):
    id: str = Field(..., description="Mã hóa đơn")
    payment_id: str | None = Field(default=None, description="Mã giao dịch thanh toán")
    order_id: str = Field(..., description="Mã đơn hàng")
    table_id: Union[int, str] = Field(..., description="Mã bàn hoặc hình thức mang đi")
    issued_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds"),
        description="Thời điểm lập hóa đơn",
    )
    items: list[dict[str, Any]] = Field(default_factory=list, description="Chi tiết món")
    subtotal: int | None = Field(default=None, ge=0, description="Tổng tiền trước giảm giá (VNĐ)")
    discount_amount: int = Field(default=0, ge=0, description="Tiền giảm giá (VNĐ)")
    total_amount: int = Field(..., ge=0, description="Tổng tiền thanh toán (VNĐ)")
    final_amount: int | None = Field(default=None, ge=0, description="Số tiền thực thu (VNĐ)")
    payment_method: PaymentMethod
    cashier_name: str

    @model_validator(mode="after")
    def populate_totals(self):
        if self.subtotal is None:
            self.subtotal = self.total_amount
        if self.final_amount is None:
            self.final_amount = self.total_amount
        return self

    def generate_text_receipt(self) -> str:
        lines = [
            "=" * 40,
            "          HÓA ĐƠN THANH TOÁN",
            f" Mã hóa đơn: {self.id}",
            f" Đơn hàng: {self.order_id} | Bàn: {self.table_id}",
            f" Thời gian : {self.issued_at}",
            "-" * 40,
            f"{'Tên món':<20}{'SL':>4}{'Thành tiền':>16}",
            "-" * 40,
        ]
        for item in self.items:
            name = item.get("item_name", item.get("name", "Món"))[:19]
            quantity = item.get("quantity", 1)
            amount = item.get("subtotal", item.get("unit_price", 0) * quantity)
            lines.append(f"{name:<20}{quantity:>4}{amount:>14,d}đ")
        lines.extend(
            [
                "-" * 40,
                f"Tổng tiền món : {self.subtotal:>18,d} VNĐ",
                f"Giảm giá      : -{self.discount_amount:>17,d} VNĐ",
                f"THỰC THU      : {self.final_amount:>18,d} VNĐ",
                f"Hình thức TT  : {self.payment_method.value}",
                "=" * 40,
                "    Cảm ơn quý khách và hẹn gặp lại!",
                "=" * 40,
            ]
        )
        return "\n".join(lines)

from datetime import datetime
from typing import Any, Union
from pydantic import BaseModel, Field, model_validator

from .Payment import PaymentMethod


class InvoiceItem(BaseModel):
    name: str = Field(..., description="Tên món")
    quantity: int = Field(default=1, ge=1, description="Số lượng món")
    unit_price: int = Field(default=0, ge=0, description="Đơn giá (VNĐ)")
    subtotal: int = Field(default=0, ge=0, description="Thành tiền (VNĐ)")

    @model_validator(mode="before")
    @classmethod
    def parse_item(cls, data: Any) -> Any:
        if isinstance(data, dict):
            name = data.get("item_name") or data.get("name") or "Món"
            quantity = int(data.get("quantity") or data.get("sl") or 1)
            unit_price = int(data.get("unit_price") or data.get("price") or 0)
            subtotal = int(data.get("subtotal") or (unit_price * quantity))
            return {
                "name": name,
                "quantity": quantity,
                "unit_price": unit_price,
                "subtotal": subtotal,
            }
        return data


class Invoice(BaseModel):
    id: str = Field(..., description="Mã hóa đơn")
    payment_id: str | None = Field(default=None, description="Mã giao dịch thanh toán")
    order_id: str = Field(..., description="Mã đơn hàng")
    table_id: Union[int, str] = Field(..., description="Mã bàn hoặc hình thức mang đi")
    issued_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds"),
        description="Thời điểm lập hóa đơn",
    )
    items: list[InvoiceItem] = Field(default_factory=list, description="Chi tiết món")
    subtotal: int | None = Field(default=None, ge=0, description="Tổng tiền trước giảm giá (VNĐ)")
    discount_amount: int = Field(default=0, ge=0, description="Tiền giảm giá (VNĐ)")
    total_amount: int = Field(..., ge=0, description="Tổng tiền thanh toán (VNĐ)")
    final_amount: int | None = Field(default=None, ge=0, description="Số tiền thực thu (VNĐ)")
    payment_method: PaymentMethod
    cashier_name: str

    @model_validator(mode="before")
    @classmethod
    def convert_items(cls, data: Any) -> Any:
        if isinstance(data, dict) and "items" in data and isinstance(data["items"], list):
            converted = []
            for item in data["items"]:
                if isinstance(item, InvoiceItem):
                    converted.append(item)
                elif isinstance(item, dict):
                    converted.append(InvoiceItem.model_validate(item))
                else:
                    converted.append(item)
            data["items"] = converted
        return data

    @model_validator(mode="after")
    def populate_totals(self):
        if self.subtotal is None:
            self.subtotal = self.total_amount
        if self.final_amount is None:
            self.final_amount = self.total_amount
        return self

    def generate_text_receipt(self) -> str:
        subtotal_val = int(self.subtotal or 0)
        discount_val = int(self.discount_amount or 0)
        final_val = int(self.final_amount or 0)

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
            name = item.name[:19]
            quantity = int(item.quantity)
            amount = int(item.subtotal)
            lines.append(f"{name:<20}{quantity:>4}{amount:>14,d}đ")
        lines.extend(
            [
                "-" * 40,
                f"Tổng tiền món : {subtotal_val:>18,d} VNĐ",
                f"Giảm giá      : -{discount_val:>17,d} VNĐ",
                f"THỰC THU      : {final_val:>18,d} VNĐ",
                f"Hình thức TT  : {self.payment_method.value}",
                "=" * 40,
                "    Cảm ơn quý khách và hẹn gặp lại!",
                "=" * 40,
            ]
        )
        return "\n".join(lines)

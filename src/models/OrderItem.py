from typing import Optional
from pydantic import BaseModel, Field, model_validator


class OrderItem(BaseModel):
    menu_item_id: str = Field(..., description="Mã món ăn từ menu (VD: M02)")
    item_name: str = Field(..., description="Tên món ăn")
    unit_price: int = Field(..., description="Đơn giá (VNĐ)", ge=0)
    quantity: int = Field(..., description="Số lượng món", gt=0)
    subtotal: Optional[int] = Field(default=None, description="Thành tiền món này (VNĐ)", ge=0)
    note: Optional[str] = Field(default="", description="Ghi chú món ăn")
<<<<<<< HEAD
    prep_time: int = Field(
        default=0,
        description="Thời gian chế biến một món (phút)",
        ge=0,
        exclude_if=lambda value: value == 0,
    )
=======
    prep_time: Optional[int] = Field(default=None, description="Thời gian chế biến (phút)", ge=0)
>>>>>>> ea871dd676a571a2fd5bbd6558f66b372f5927f2

    @model_validator(mode='after')
    def auto_calculate_subtotal(self):
        """Nếu JSON không truyền subtotal hoặc bằng 0 thì tự tính: đơn giá * số lượng."""
        if self.subtotal is None or self.subtotal == 0:
            self.subtotal = self.unit_price * self.quantity
        return self

    def update_quantity(self, quantity: int) -> None:
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Số lượng phải là số nguyên lớn hơn 0.")
        self.quantity = quantity
        self.subtotal = self.unit_price * quantity

    def update_note(self, note: str) -> None:
        self.note = note

    def to_dict(self) -> dict:
        data = self.model_dump(mode="json")
        if data.get("prep_time") is None:
            data.pop("prep_time", None)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "OrderItem":
        return cls.model_validate(data)
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class OrderItem(BaseModel):
    menu_item_id: str = Field(..., description="Mã món ăn từ menu (VD: M02)")
    item_name: str = Field(..., description="Tên món ăn")
    unit_price: int = Field(..., description="Đơn giá (VNĐ)", ge=0)
    quantity: int = Field(..., description="Số lượng món", gt=0)
    subtotal: Optional[int] = Field(default=None, description="Thành tiền món này (VNĐ)", ge=0)
    note: Optional[str] = Field(default="", description="Ghi chú món ăn")
    prep_time: int = Field(
        default=0,
        description="Thời gian chế biến một món (phút)",
        ge=0,
        exclude_if=lambda value: value == 0,
    )

    def __init__(
        self,
        menu_item_id: Optional[str] = None,
        item_name: Optional[str] = None,
        unit_price: Optional[int] = None,
        quantity: Optional[int] = None,
        note: Optional[str] = "",
        prep_time: Optional[int] = None,
        **kwargs,
    ):
        if menu_item_id is not None and "menu_item_id" not in kwargs:
            kwargs["menu_item_id"] = menu_item_id
        if item_name is not None and "item_name" not in kwargs:
            kwargs["item_name"] = item_name
        if unit_price is not None and "unit_price" not in kwargs:
            kwargs["unit_price"] = unit_price
        if quantity is not None and "quantity" not in kwargs:
            kwargs["quantity"] = quantity
        if note and "note" not in kwargs:
            kwargs["note"] = note
        if prep_time is not None and "prep_time" not in kwargs:
            kwargs["prep_time"] = prep_time
        super().__init__(**kwargs)

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
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "OrderItem":
        return cls.model_validate(data)
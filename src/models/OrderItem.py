from typing import Optional
from pydantic import BaseModel, Field, model_validator


class OrderItem(BaseModel):
    menu_item_id: str = Field(default="M01", description="Mã món ăn từ menu (VD: M02)")
    item_name: str = Field(default="Món", description="Tên món ăn")
    unit_price: int = Field(default=0, description="Đơn giá (VNĐ)", ge=0)
    quantity: int = Field(default=1, description="Số lượng món", gt=0)
    subtotal: Optional[int] = Field(default=None, description="Thành tiền món này (VNĐ)", ge=0)
    note: Optional[str] = Field(default="", description="Ghi chú món ăn")
    prep_time: int = Field(
        default=0,
        description="Thời gian chế biến một món (phút)",
        ge=0,
        exclude_if=lambda value: value == 0,
    )

    @model_validator(mode="before")
    @classmethod
    def populate_defaults(cls, data):
        if isinstance(data, dict):
            if "menu_item_id" not in data:
                data["menu_item_id"] = data.get("item_id", "M01")
            if "item_name" not in data:
                data["item_name"] = data.get("name", "Món")
            if "unit_price" not in data:
                data["unit_price"] = data.get("price", 0)
            if "quantity" not in data:
                data["quantity"] = data.get("sl", 1)
        return data

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
        if self.prep_time == 0 and "prep_time" in data:
            del data["prep_time"]
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "OrderItem":
        return cls.model_validate(data)



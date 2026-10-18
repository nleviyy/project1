from typing import Optional
from pydantic import BaseModel, Field, model_validator


class OrderItem(BaseModel):
    menu_item_id: str = Field(..., description="Mã món ăn từ menu (VD: M02)")
    item_name: str = Field(..., description="Tên món ăn")
    unit_price: float = Field(..., description="Đơn giá", ge=0.0)
    quantity: int = Field(..., description="Số lượng món", gt=0)
    subtotal: Optional[float] = Field(default=None, description="Thành tiền món này", ge=0.0)
    note: Optional[str] = Field(default="", description="Ghi chú món ăn")

    @model_validator(mode='after')
    def auto_calculate_subtotal(self):
        """Nếu JSON không truyền subtotal hoặc bằng 0 thì tự tính: đơn giá * số lượng."""
        if self.subtotal is None or self.subtotal == 0:
            self.subtotal = self.unit_price * self.quantity
        return self
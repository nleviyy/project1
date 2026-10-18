from typing import Optional
from pydantic import BaseModel, Field

class OrderItem(BaseModel):
    item_id: str = Field(..., description="Mã món ăn gốc từ menu", min_length=2)
    name: str = Field(..., description="Tên món ăn")
    quantity: int = Field(..., description="Số lượng món", gt=0)
    # Lưu lại đơn giá tại thời điểm đặt để đổi giá menu không làm sai hóa đơn cũ
    price: int = Field(..., description="Đơn giá lúc đặt (VNĐ)", ge=0)
    note: Optional[str] = Field(default="", description="Ghi chú thêm (VD: ít đá, không cay)")

    @property
    def amount(self) -> int:
        """Tính tổng tiền của món ăn (số lượng * đơn giá)"""
        return self.quantity * self.price
from typing import List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field, model_validator
from OrderItem import OrderItem

StatusType = Literal["PENDING", "PREPARING", "SERVED", "COMPLETED", "CANCELLED"]


class Order(BaseModel):
    id: str = Field(..., description="Mã định danh đơn hàng (VD: ORD-20261014-001)")
    table_id: int = Field(..., description="Số bàn đặt món")
    status: StatusType = Field(default="PENDING", description="Trạng thái đơn hàng")
    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(), 
        description="Thời gian tạo đơn"
    )
    updated_at: Optional[str] = Field(
        default_factory=lambda: datetime.now().isoformat(), 
        description="Thời gian cập nhật gần nhất"
    )
    items: List[OrderItem] = Field(default_factory=list, description="Danh sách món")

    @property
    def total_amount(self) -> float:
        """Tổng tiền toàn bộ đơn hàng tính từ các items."""
        return sum(item.subtotal for item in self.items)

    def can_modify_items(self) -> bool:
        """Chỉ cho phép thêm/sửa món khi đơn chưa chế biến/phục vụ."""
        return self.status == "PENDING"

    def add_item(self, item: OrderItem) -> bool:
        """Thêm món vào đơn hàng và cập nhật lại updated_at."""
        if not self.can_modify_items():
            raise ValueError("Lỗi: Chỉ có thể thêm món khi đơn hàng ở trạng thái PENDING.")
        self.items.append(item)
        self.updated_at = datetime.now().isoformat()
        return True

    def change_status(self, new_status: StatusType) -> bool:
        """Cập nhật trạng thái đơn hàng theo nghiệp vụ."""
        if self.status == new_status:
            return True

        if new_status == "CANCELLED" and self.status in ["SERVED", "COMPLETED"]:
            raise ValueError("Lỗi: Không thể hủy đơn hàng đã phục vụ (SERVED) hoặc hoàn tất (COMPLETED).")

        if self.status in ["COMPLETED", "CANCELLED"]:
            raise ValueError(f"Lỗi: Không thể thay đổi trạng thái của đơn hàng đã {self.status}.")

        self.status = new_status
        self.updated_at = datetime.now().isoformat()
        return True
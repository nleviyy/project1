from typing import List, Optional, Literal, Union, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from OrderItem import OrderItem

StatusType = Literal["PENDING", "PREPARING", "SERVED", "COMPLETED", "CANCELLED"]


class Order(BaseModel):
    id: str = Field(..., description="Mã đơn hàng (VD: ORD-20261014-001)")
    # Hỗ trợ cả số nguyên (1, 2) hoặc chuỗi ("Bàn số 1", "Mang về")
    table_id: Union[int, str] = Field(..., description="Bàn đặt món")
    status: StatusType = Field(default="PENDING", description="Trạng thái hiện tại")
    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(), 
        description="Thời gian tạo đơn"
    )
    updated_at: Optional[str] = Field(
        default_factory=lambda: datetime.now().isoformat(), 
        description="Thời gian cập nhật gần nhất"
    )
    items: List[OrderItem] = Field(default_factory=list, description="Danh sách món đã đặt")
    notes: Optional[str] = Field(default="", description="Ghi chú toàn đơn")

    # Bản đồ quy tắc chuyển trạng thái hợp lệ
    VALID_TRANSITIONS: dict = {
        "PENDING": ["PREPARING", "CANCELLED"],
        "PREPARING": ["SERVED", "CANCELLED"],
        "SERVED": ["COMPLETED"],
        "COMPLETED": [],
        "CANCELLED": []
    }

    @property
    def total_amount(self) -> float:
        """Tổng tiền toàn bộ đơn hàng tính từ các items."""
        return sum(item.subtotal for item in self.items)

    def can_modify_items(self) -> bool:
        """Chỉ cho phép thêm/sửa món khi đơn chưa vào bếp chế biến."""
        return self.status == "PENDING"

    def add_item(self, item: OrderItem) -> bool:
        """Thêm món vào đơn hàng (chỉ khi PENDING)."""
        if not self.can_modify_items():
            raise ValueError(f"Không thể sửa món khi đơn đang ở trạng thái '{self.status}'.")
        self.items.append(item)
        self.updated_at = datetime.now().isoformat()
        return True

    def change_status(self, new_status: StatusType) -> bool:
        """Kiểm tra và cập nhật trạng thái theo đúng luồng nghiệp vụ."""
        if self.status == new_status:
            return True

        allowed_next_statuses = self.VALID_TRANSITIONS.get(self.status, [])
        if new_status not in allowed_next_statuses:
            raise ValueError(
                f"Lỗi chuyển trạng thái: Không thể chuyển từ '{self.status}' sang '{new_status}'."
            )

        self.status = new_status
        self.updated_at = datetime.now().isoformat()
        return True

    # ---------- Các hàm chuyển đổi nhanh theo từng công đoạn ----------

    def mark_preparing(self) -> bool:
        """Bếp tiếp nhận và bắt đầu nấu (PENDING -> PREPARING)."""
        return self.change_status("PREPARING")

    def mark_served(self) -> bool:
        """Bếp nấu xong, nhân viên bưng lên bàn (PREPARING -> SERVED)."""
        return self.change_status("SERVED")

    def mark_completed(self) -> bool:
        """Khách đã thanh toán hóa đơn (SERVED -> COMPLETED)."""
        return self.change_status("COMPLETED")

    def cancel(self) -> bool:
        """Hủy đơn hàng (Chỉ được hủy khi PENDING hoặc PREPARING)."""
        return self.change_status("CANCELLED")

    # ---------- Hàm Factory tạo đơn trực tiếp từ Giỏ hàng ----------

    @classmethod
    def from_cart(cls, order_id: str, table_id: Union[int, str], cart_items: Dict[str, Any], notes: str = "") -> "Order":
        """Chuyển đổi dữ liệu từ Giỏ hàng Streamlit sang đối tượng Order."""
        order_items = []
        for item_id, item_info in cart_items.items():
            order_items.append(
                OrderItem(
                    menu_item_id=item_id,
                    item_name=item_info.get("ten", ""),
                    unit_price=float(item_info.get("gia", 0)),
                    quantity=int(item_info.get("sl", 1)),
                    subtotal=float(item_info.get("gia", 0) * item_info.get("sl", 1)),
                    note=item_info.get("ghi_chu", "")
                )
            )

        return cls(
            id=order_id,
            table_id=table_id,
            items=order_items,
            notes=notes,
            status="PENDING"
        )
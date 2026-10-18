from typing import ClassVar, List, Optional, Literal, Union, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from .OrderItem import OrderItem
from .Payment import Payment

StatusType = Literal["PENDING", "PREPARING", "SERVED", "COMPLETED", "CANCELLED"]


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    PREPARING = "PREPARING"
    SERVED = "SERVED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Order(BaseModel):
    id: str = Field(..., description="Mã đơn hàng (VD: ORD-20261014-001)")
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
    discount_amount: int = Field(default=0, ge=0, description="Tiền giảm giá (VNĐ)")

    VALID_TRANSITIONS: ClassVar[dict[str, list[str]]] = {
        "PENDING": ["PREPARING", "CANCELLED"],
        "PREPARING": ["SERVED", "CANCELLED"],
        "SERVED": [],
        "COMPLETED": [],
        "CANCELLED": []
    }

    @property
    def total_amount(self) -> int:
        """Tổng tiền toàn bộ đơn hàng tính từ các items."""
        return sum(item.subtotal for item in self.items)

    @property
    def final_amount(self) -> int:
        return max(0, self.total_amount - self.discount_amount)

    @property
    def is_pending(self) -> bool:
        return self.status == "PENDING"

    @property
    def is_preparing(self) -> bool:
        return self.status == "PREPARING"

    @property
    def is_served(self) -> bool:
        return self.status == "SERVED"

    @property
    def is_completed(self) -> bool:
        return self.status == "COMPLETED"

    @property
    def is_active(self) -> bool:
        return self.status in ("PENDING", "PREPARING", "SERVED")

    @property
    def can_modify(self) -> bool:
        return self.can_modify_items()

    def can_modify_items(self) -> bool:
        """Chỉ cho phép thêm/sửa món khi đơn chưa vào bếp chế biến."""
        return self.status == "PENDING"

    def add_item(self, item: OrderItem) -> bool:
        """Thêm món vào đơn hàng (chỉ khi PENDING)."""
        if not self.can_modify_items():
            raise ValueError(f"Không thể sửa món khi đơn đang ở trạng thái '{self.status}'.")
        for current in self.items:
            if (
                current.menu_item_id == item.menu_item_id
                and current.note == item.note
                and current.unit_price == item.unit_price
            ):
                current.update_quantity(current.quantity + item.quantity)
                self.updated_at = datetime.now().isoformat()
                return True
        self.items.append(item)
        self.updated_at = datetime.now().isoformat()
        return True

    def change_status(self, new_status: StatusType) -> bool:
        """Kiểm tra và cập nhật trạng thái theo đúng luồng nghiệp vụ."""
        new_status = new_status.value if isinstance(new_status, OrderStatus) else new_status
        if self.status == new_status:
            return True

        if new_status == "COMPLETED":
            if self.status == "SERVED":
                raise ValueError("Đơn hàng chỉ được hoàn tất sau khi thanh toán thành công.")
            return False

        allowed_next_statuses = self.VALID_TRANSITIONS.get(self.status, [])
        if new_status not in allowed_next_statuses:
            return False

        self.status = new_status
        self.updated_at = datetime.now().isoformat()
        return True

    def can_transition_to(self, new_status: StatusType) -> bool:
        new_status = new_status.value if isinstance(new_status, OrderStatus) else new_status
        return new_status in self.VALID_TRANSITIONS.get(self.status, [])

    def _touch(self) -> None:
        self.updated_at = datetime.now().isoformat()

    def set_discount(self, amount: int) -> None:
        if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
            raise ValueError("Tiền giảm giá phải là số nguyên không âm.")
        self.discount_amount = amount
        self.updated_at = datetime.now().isoformat()

    def update_item_quantity(self, menu_item_id: str, quantity: int) -> bool:
        if not self.can_modify_items():
            raise ValueError(f"Không thể sửa món khi đơn đang ở trạng thái '{self.status}'.")
        for item in self.items:
            if item.menu_item_id == menu_item_id:
                item.update_quantity(quantity)
                self.updated_at = datetime.now().isoformat()
                return True
        return False

    def remove_item(self, menu_item_id: str) -> bool:
        if not self.can_modify_items():
            raise ValueError(f"Không thể sửa món khi đơn đang ở trạng thái '{self.status}'.")
        for index, item in enumerate(self.items):
            if item.menu_item_id == menu_item_id:
                del self.items[index]
                self.updated_at = datetime.now().isoformat()
                return True
        return False

    def to_dict(self) -> dict:
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict) -> "Order":
        return cls.model_validate(data)

    # ---------- Các hàm chuyển đổi nhanh theo từng công đoạn ----------

    def mark_preparing(self) -> bool:
        """Bếp tiếp nhận và bắt đầu nấu (PENDING -> PREPARING)."""
        return self.change_status("PREPARING")

    def mark_served(self) -> bool:
        """Bếp nấu xong, nhân viên bưng lên bàn (PREPARING -> SERVED)."""
        return self.change_status("SERVED")

    def mark_completed(self, payment: Payment) -> bool:
        """Hoàn tất đơn sau khi thanh toán SUCCESS cho đúng đơn hàng."""
        if payment.order_id != self.id or not payment.is_successful:
            raise ValueError("Chỉ thanh toán SUCCESS của đúng đơn mới được hoàn tất đơn hàng.")
        if self.status != "SERVED":
            raise ValueError(
                f"Không thể hoàn tất đơn khi đang ở trạng thái '{self.status}'."
            )
        self.status = "COMPLETED"
        self.updated_at = datetime.now().isoformat()
        return True

    def cancel(self) -> bool:
        """Hủy đơn hàng (Chỉ được hủy khi PENDING hoặc PREPARING)."""
        return self.change_status("CANCELLED")

    @classmethod
    def from_cart(cls, order_id: str, table_id: Union[int, str], cart_items: Dict[str, Any], notes: str = "") -> "Order":
        """Chuyển đổi dữ liệu từ Giỏ hàng Streamlit sang đối tượng Order."""
        order_items = []
        for item_id, item_info in cart_items.items():
            order_items.append(
                OrderItem(
                    menu_item_id=item_id,
                    item_name=item_info.get("ten", ""),
                    unit_price=int(item_info.get("gia", 0)),
                    quantity=int(item_info.get("sl", 1)),
                    subtotal=int(item_info.get("gia", 0) * item_info.get("sl", 1)),
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
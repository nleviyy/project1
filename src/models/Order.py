from typing import List, Optional, Literal, Union, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from .OrderItem import OrderItem
from .Payment import Payment
from src.models.HashTable import HashTable

StatusType = Literal["PENDING", "PREPARING", "SERVED", "COMPLETED", "CANCELLED"]


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    PREPARING = "PREPARING"
    SERVED = "SERVED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

    @staticmethod
    def get_label(status):
        return get_order_status_label(status)


# Bảng chuyển trạng thái sử dụng HashTable tự cài đặt (không dùng dict built-in)
# Quy tắc: PREPARING không thể hủy sang CANCELLED (Phase 1.4)
ORDER_STATUS_TRANSITIONS: HashTable = HashTable()
ORDER_STATUS_TRANSITIONS.put("PENDING", ["PREPARING", "CANCELLED"])
ORDER_STATUS_TRANSITIONS.put("PREPARING", ["SERVED"])
ORDER_STATUS_TRANSITIONS.put("SERVED", [])
ORDER_STATUS_TRANSITIONS.put("COMPLETED", [])
ORDER_STATUS_TRANSITIONS.put("CANCELLED", [])

ORDER_STATUS_LABELS: HashTable = HashTable()
ORDER_STATUS_LABELS.put("PENDING", "Chờ xác nhận")
ORDER_STATUS_LABELS.put("PREPARING", "Đang chế biến")
ORDER_STATUS_LABELS.put("SERVED", "Đã lên món")
ORDER_STATUS_LABELS.put("COMPLETED", "Hoàn thành")
ORDER_STATUS_LABELS.put("CANCELLED", "Đã hủy")


def get_order_status_label(status: Union[str, OrderStatus]) -> str:
    val = status.value if isinstance(status, OrderStatus) else str(status)
    lbl = ORDER_STATUS_LABELS.get(val)
    return lbl if lbl is not None else val


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
    kitchen_note: str = Field(default="", description="Ghi chú của bếp")
    priority_at: Optional[str] = Field(default=None, description="Thời điểm bếp ưu tiên đơn (ISO)")
    prep_time: int = Field(default=0, ge=0, description="Thời gian chế biến độc lập (phút)")

    def __init__(self, *args, **data):
        if args:
            if "id" not in data and "order_id" not in data:
                data["id"] = args[0]
            if len(args) > 1 and "table_id" not in data:
                data["table_id"] = args[1]
            elif len(args) == 1 and "table_id" not in data:
                # Tương thích gọi cũ trong unit test: Order("A")
                data["table_id"] = 1
            if len(args) > 2 and "items" not in data:
                data["items"] = args[2]
            if len(args) > 3 and "notes" not in data:
                data["notes"] = args[3]
        if "order_id" in data and "id" not in data:
            data["id"] = data.pop("order_id")
        super().__init__(**data)

    @property
    def order_id(self) -> str:
        """Alias cho id để tương thích thống nhất với KitchenManager."""
        return self.id

    @property
    def total_amount(self) -> int:
        """Tổng tiền toàn bộ đơn hàng tính từ các items."""
        return sum(item.subtotal for item in self.items)

    @property
    def final_amount(self) -> int:
        return max(0, self.total_amount - self.discount_amount)

    def set_status(self, new_status: Union[StatusType, OrderStatus]) -> bool:
        """Cập nhật trạng thái thống nhất giữa các tầng, ném ValueError khi vi phạm luồng."""
        if not self.change_status(new_status):
            target_str = new_status.value if isinstance(new_status, OrderStatus) else str(new_status)
            raise ValueError(
                f"Không thể chuyển đơn '{self.id}' từ trạng thái '{self.status}' sang '{target_str}'."
            )
        return True

    def calculate_prep_time(self) -> int:
        """Tính tổng thời gian chế biến dự kiến cho toàn bộ đơn hàng."""
        if not self.items:
            return self.prep_time
        total = 0
        for item in self.items:
            qty = int(getattr(item, "quantity", 1))
            pt = int(getattr(item, "prep_time", 0) or 0)
            total += qty * pt
        return total if total > 0 else self.prep_time

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
        """Chỉ cho phép thêm/sửa món khi đơn chưa vào bếp chế biến (PENDING)."""
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

    def change_status(self, new_status: Union[StatusType, OrderStatus]) -> bool:
        """Kiểm tra và cập nhật trạng thái theo đúng luồng nghiệp vụ."""
        target = new_status.value if isinstance(new_status, OrderStatus) else str(new_status)
        if self.status == target:
            return True

        if target == "COMPLETED":
            if self.status == "SERVED":
                raise ValueError("Đơn hàng chỉ được hoàn tất sau khi thanh toán thành công.")
            return False

        allowed = ORDER_STATUS_TRANSITIONS.get(self.status, [])
        if target not in allowed:
            return False

        self.status = target
        self.updated_at = datetime.now().isoformat()
        return True

    def can_transition_to(self, new_status: StatusType) -> bool:
        target = new_status.value if isinstance(new_status, OrderStatus) else str(new_status)
        allowed = ORDER_STATUS_TRANSITIONS.get(self.status, [])
        return target in allowed

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
        data = self.model_dump(mode="json")
        data["total_amount"] = self.total_amount
        data["final_amount"] = self.final_amount
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Order":
        return cls.model_validate(data)

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
        """Hủy đơn hàng (Chỉ được hủy khi PENDING)."""
        return self.change_status("CANCELLED")

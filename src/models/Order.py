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

    @staticmethod
    def get_label(status):
        value = status.value if isinstance(status, OrderStatus) else status
        return ORDER_STATUS_LABELS.get(value, str(value))


ORDER_STATUS_TRANSITIONS: dict[str, list[str]] = {
    "PENDING": ["PREPARING", "CANCELLED"],
    "PREPARING": ["SERVED"],
    "SERVED": [],
    "COMPLETED": [],
    "CANCELLED": [],
}
ORDER_STATUS_LABELS: dict[str, str] = {
    "PENDING": "Chờ xác nhận",
    "PREPARING": "Đang chế biến",
    "SERVED": "Đã lên món",
    "COMPLETED": "Hoàn thành",
    "CANCELLED": "Đã hủy",
}


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
    preparing_started_at: Optional[str] = Field(
        default=None,
        description="Thời điểm bắt đầu chế biến để tính ETA còn lại",
    )
    items: List[OrderItem] = Field(default_factory=list, description="Danh sách món đã đặt")
    notes: Optional[str] = Field(default="", description="Ghi chú toàn đơn")
    discount_amount: int = Field(default=0, ge=0, description="Tiền giảm giá (VNĐ)")
    kitchen_note: str = Field(default="", description="Ghi chú của bếp")
    priority_at: Optional[str] = Field(default=None, description="Thời điểm bếp ưu tiên đơn (ISO)")

<<<<<<< Updated upstream
    VALID_TRANSITIONS: ClassVar[dict[str, list[str]]] = ORDER_STATUS_TRANSITIONS
=======

class Order:
    def __init__(
        self,
        id,
        table_id,
        items=None,
        notes="",
        status="PENDING",
        discount_amount=0,
        created_at=None,
        updated_at=None,
        preparing_started_at=None,
    ):
        if not isinstance(id, str) or id.strip() == "":
            raise ValueError("Mã đơn hàng không được để trống.")
        if not ORDER_STATUS_LABELS.contains(status):
            raise ValueError("Trạng thái đơn không hợp lệ: " + str(status))
        if isinstance(discount_amount, bool) or not isinstance(discount_amount, int) or discount_amount < 0:
            raise ValueError("Tiền giảm giá phải là số nguyên không âm.")
        if items is not None and not isinstance(items, DoublyLinkedList):
            normalized_items = DoublyLinkedList()
            try:
                for item in items:
                    normalized_items.add_last(item)
            except TypeError as error:
                raise TypeError("items phải là danh sách các OrderItem.") from error
            items = normalized_items

        self.id = id
        self.table_id = table_id
        self.status = status
        self.items = items if items is not None else DoublyLinkedList()
        self.notes = notes if notes is not None else ""
        self.discount_amount = discount_amount
        self.created_at = created_at if created_at is not None else _now()
        self.updated_at = updated_at if updated_at is not None else _now()
        self.preparing_started_at = preparing_started_at


    # ---------- Thông tin chung ----------
>>>>>>> Stashed changes

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
        """Cập nhật trạng thái thống nhất giữa các tầng."""
        if not self.change_status(new_status):
            raise ValueError(
                f"Không thể chuyển đơn {self.id} sang trạng thái {new_status}."
            )
        return True

    def calculate_prep_time(self) -> int:
        """Tính tổng thời gian chế biến dự kiến cho toàn bộ đơn hàng."""
        if not self.items:
            return 0
        total = 0
        for item in self.items:
            if isinstance(item, dict):
                qty = int(item.get("sl", item.get("quantity", 1)))
                pt = int(item.get("prep_time", 0) or 0)
            else:
                qty = int(getattr(item, "quantity", 1))
                pt = int(getattr(item, "prep_time", 0) or 0)
            total += qty * pt
        return total

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

        allowed_next_statuses = ORDER_STATUS_TRANSITIONS.get(self.status, [])
        if new_status not in allowed_next_statuses:
            return False

        self.status = new_status
<<<<<<< Updated upstream
        now = datetime.now().isoformat()
        self.updated_at = now
        if new_status == "PREPARING":
            self.preparing_started_at = now
        elif new_status == "PENDING":
            self.preparing_started_at = None
        elif new_status == "SERVED":
=======
        self._touch()
        if new_status == "PREPARING":
            self.preparing_started_at = self.updated_at
        elif new_status in ("PENDING", "SERVED", "COMPLETED", "CANCELLED"):
>>>>>>> Stashed changes
            self.preparing_started_at = None
        return True

    def can_transition_to(self, new_status: StatusType) -> bool:
        new_status = new_status.value if isinstance(new_status, OrderStatus) else new_status
        return new_status in ORDER_STATUS_TRANSITIONS.get(self.status, [])

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

    def update_item_note(self, menu_item_id: str, note: str) -> bool:
        if not self.can_modify_items():
            raise ValueError(f"Không thể sửa món khi đơn đang ở trạng thái '{self.status}'.")
        for item in self.items:
            if item.menu_item_id == menu_item_id:
                item.update_note(note)
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
<<<<<<< Updated upstream
        self.updated_at = datetime.now().isoformat()
=======
        self._touch()
        self.preparing_started_at = None
>>>>>>> Stashed changes
        return True

    def cancel(self) -> bool:
        """Hủy đơn hàng (Trong phạm vi dự án, chỉ cho phép hủy khi PENDING)."""
        if self.status != "PENDING":
            return False
        return self.change_status("CANCELLED")

<<<<<<< Updated upstream
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
=======
    # ---------- Chuyển đổi dữ liệu ----------

    def to_dict(self):
        items_data = DoublyLinkedList()
        node = self.items.head
        while node is not None:
            items_data.add_last(node.data.to_dict())
            node = node.next

        data = HashTable()
        data.put("id", self.id)
        data.put("table_id", self.table_id)
        data.put("status", self.status)
        data.put("created_at", self.created_at)
        data.put("updated_at", self.updated_at)
        data.put("preparing_started_at", self.preparing_started_at)
        data.put("items", items_data)
        data.put("notes", self.notes)
        data.put("discount_amount", self.discount_amount)
        data.put("total_amount", self.total_amount)
        data.put("final_amount", self.final_amount)
        return data

    @classmethod
    def from_dict(cls, data):
        items = DoublyLinkedList()
        items_data = data.get("items")
        if items_data is not None:
            for item_data in items_data:
                if isinstance(item_data, OrderItem):
                    items.add_last(item_data)
                else:
                    items.add_last(OrderItem.from_dict(item_data))

        status = data.get("status")
        if status is None:
            status = "PENDING"
        discount_amount = data.get("discount_amount")
        if discount_amount is None:
            discount_amount = 0

        return cls(
            id=data.get("id"),
            table_id=data.get("table_id"),
            items=items,
            notes=data.get("notes"),
            status=status,
            discount_amount=discount_amount,
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            preparing_started_at=data.get("preparing_started_at"),
        )


    @classmethod
    def from_cart(cls, order_id, table_id, cart_items, notes=""):
        order_items = DoublyLinkedList()
        node = cart_items.head
        while node is not None:
            order_items.add_last(OrderItem.from_dict(node.data))
            node = node.next
>>>>>>> Stashed changes

        return cls(
            id=order_id,
            table_id=table_id,
            items=order_items,
            notes=notes,
            status="PENDING"
        )
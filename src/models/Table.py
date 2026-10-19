from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, Set

VALID_TABLE_STATUSES: Set[str] = {"AVAILABLE", "OCCUPIED", "RESERVED"}


class TableStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    RESERVED = "RESERVED"


@dataclass
class Table:
    id: int
    name: str
    capacity: int
    status: str = "AVAILABLE"
    current_order_id: Optional[str] = None

    def __post_init__(self):
        try:
            self.id = int(self.id)
        except (ValueError, TypeError):
            raise ValueError("ID bàn ăn phải là số nguyên dương.")
        if self.id <= 0:
            raise ValueError("ID bàn ăn phải là số nguyên dương (> 0).")

        if not self.name or len(str(self.name).strip()) < 1:
            raise ValueError("Tên bàn ăn không được để trống.")
        self.name = str(self.name).strip()

        try:
            self.capacity = int(self.capacity)
        except (ValueError, TypeError):
            raise ValueError("Sức chứa của bàn phải là số nguyên dương.")
        if self.capacity <= 0:
            raise ValueError("Sức chứa của bàn phải lớn hơn 0.")

        self.status = str(self.status).upper().strip()
        if self.status not in VALID_TABLE_STATUSES:
            raise ValueError(
                f"Trạng thái bàn '{self.status}' không hợp lệ. Phải thuộc {VALID_TABLE_STATUSES}."
            )

        if self.current_order_id is not None:
            self.current_order_id = str(self.current_order_id).strip()
            if not self.current_order_id:
                self.current_order_id = None

        if self.status == "AVAILABLE" and self.current_order_id is not None:
            raise ValueError("Bàn ở trạng thái AVAILABLE thì current_order_id bắt buộc là None.")

        if self.status == "OCCUPIED" and self.current_order_id is None:
            raise ValueError("Bàn ở trạng thái OCCUPIED thì bắt buộc phải có current_order_id.")

    def occupy(self, order_id: str) -> bool:
        """Gắn đơn hàng vào bàn và đổi trạng thái sang OCCUPIED."""
        if not order_id or not str(order_id).strip():
            raise ValueError("Mã đơn hàng gắn vào bàn không được để trống.")
        clean_order_id = str(order_id).strip()
        self.status = "OCCUPIED"
        self.current_order_id = clean_order_id
        return True

    def vacate(self) -> bool:
        """Giải phóng bàn về trạng thái AVAILABLE."""
        self.status = "AVAILABLE"
        self.current_order_id = None
        return True

    def release(self) -> bool:
        """Alias cho vacate."""
        return self.vacate()

    def reserve(self) -> bool:
        """Đặt trước bàn (RESERVED)."""
        self.status = "RESERVED"
        self.current_order_id = None
        return True

    def update_status(self, new_status: str, order_id: Optional[str] = None) -> bool:
        """
        Cập nhật trạng thái bàn an toàn (Atomic Update):
        Validate toàn bộ dữ liệu trước khi thay đổi trạng thái thực tế.
        """
        target_status = str(new_status).upper().strip()
        target_order_id = str(order_id).strip() if order_id else None
        try:
            temp_table = Table(
                id=self.id,
                name=self.name,
                capacity=self.capacity,
                status=target_status,
                current_order_id=target_order_id
            )
            self.status = temp_table.status
            self.current_order_id = temp_table.current_order_id
            return True
        except ValueError as e:
            print(f"[Lỗi cập nhật bàn {self.id}] {e}")
            return False

    def to_dict(self) -> dict:
        return asdict(self)

    def model_dump(self) -> dict:
        return asdict(self)

    def dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Table":
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            capacity=data.get("capacity", 4),
            status=data.get("status", "AVAILABLE"),
            current_order_id=data.get("current_order_id")
        )
    @property
    def is_available(self) -> bool:
        """Kiểm tra xem bàn có đang thực sự trống (AVAILABLE) và không có đơn hàng không."""
        return self.status == "AVAILABLE" and self.current_order_id is None

    @property
    def is_occupied(self) -> bool:
        return self.status == "OCCUPIED"

    def release(self) -> bool:
        return self.vacate()

    def check_and_occupy(self, order_id: str) -> bool:
        """
        Kiểm tra bàn trước khi đặt:
        - Nếu bàn đang bận (OCCUPIED) hoặc đã đặt trước (RESERVED), từ chối và báo lỗi.
        - Nếu bàn trống, tiến hành gắn đơn hàng và chuyển sang trạng thái OCCUPIED.
        """
        if not self.is_available:
            raise ValueError(
                f"Lỗi: Bàn '{self.name}' (ID: {self.id}) hiện đang ở trạng thái '{self.status}' "
                f"hoặc đã có đơn hàng liên kết. Không thể đặt bàn này!"
            )
        return self.occupy(order_id)

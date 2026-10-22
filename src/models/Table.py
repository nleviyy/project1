from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional


class TableStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    RESERVED = "RESERVED"


VALID_TABLE_STATUSES: tuple[str, ...] = (
    TableStatus.AVAILABLE.value,
    TableStatus.OCCUPIED.value,
    TableStatus.RESERVED.value,
)



@dataclass
class Table:
    id: int
    name: str
    capacity: int
    status: str = TableStatus.AVAILABLE.value
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

        # Chuẩn hóa status thành chuỗi khớp TableStatus
        if isinstance(self.status, TableStatus):
            self.status = self.status.value
        else:
            self.status = str(self.status).upper().strip()

        if self.status not in VALID_TABLE_STATUSES:
            raise ValueError(
                f"Trạng thái bàn '{self.status}' không hợp lệ. Phải thuộc {VALID_TABLE_STATUSES}."
            )

        if self.current_order_id is not None:
            self.current_order_id = str(self.current_order_id).strip()
            if not self.current_order_id:
                self.current_order_id = None

        if self.status == TableStatus.AVAILABLE.value and self.current_order_id is not None:
            raise ValueError("Bàn ở trạng thái AVAILABLE thì current_order_id bắt buộc là None.")

        if self.status == TableStatus.OCCUPIED.value and self.current_order_id is None:
            raise ValueError("Bàn ở trạng thái OCCUPIED thì bắt buộc phải có current_order_id.")

    def occupy(self, order_id: str) -> bool:
        """Gắn đơn hàng vào bàn và đổi trạng thái sang OCCUPIED."""
        if not order_id or not str(order_id).strip():
            raise ValueError("Mã đơn hàng gắn vào bàn không được để trống.")
        clean_order_id = str(order_id).strip()

        # Kiểm tra không được chiếm bàn đang OCCUPIED bởi đơn khác
        if self.status == TableStatus.OCCUPIED.value and self.current_order_id != clean_order_id:
            raise ValueError(
                f"Bàn '{self.name}' đang được sử dụng bởi đơn '{self.current_order_id}', "
                f"không thể gán cho đơn '{clean_order_id}'."
            )

        self.status = TableStatus.OCCUPIED.value
        self.current_order_id = clean_order_id
        return True

    def vacate(self) -> bool:
        """Giải phóng bàn về trạng thái AVAILABLE."""
        self.status = TableStatus.AVAILABLE.value
        self.current_order_id = None
        return True

    # release là alias cho vacate để thống nhất
    release = vacate

    def reserve(self) -> bool:
        """Đặt trước bàn (chuyển sang RESERVED). Không được đặt bàn đang OCCUPIED."""
        if self.status == TableStatus.OCCUPIED.value:
            raise ValueError(
                f"Bàn '{self.name}' đang có khách phục vụ (đơn {self.current_order_id}), "
                f"không thể đặt trước."
            )
        self.status = TableStatus.RESERVED.value
        self.current_order_id = None
        return True

    def update_status(self, new_status: str, order_id: Optional[str] = None) -> bool:
        """
        Cập nhật trạng thái bàn an toàn (Atomic Update):
        Validate toàn bộ dữ liệu trước khi thay đổi trạng thái thực tế. Ném ValueError nếu không hợp lệ.
        """
        target_status = str(new_status).upper().strip()
        target_order_id = str(order_id).strip() if order_id else None
        temp_table = Table(
            id=self.id,
            name=self.name,
            capacity=self.capacity,
            status=target_status,
            current_order_id=target_order_id,
        )
        self.status = temp_table.status
        self.current_order_id = temp_table.current_order_id
        return True

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Table":
        if "capacity" not in data or data["capacity"] is None:
            raise ValueError("Bàn ăn bắt buộc phải có thông tin sức chứa (capacity).")
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            capacity=data["capacity"],
            status=data.get("status", TableStatus.AVAILABLE.value),
            current_order_id=data.get("current_order_id"),
        )

    @property
    def is_available(self) -> bool:
        """Kiểm tra xem bàn có đang thực sự trống (AVAILABLE) và không có đơn hàng không."""
        return self.status == TableStatus.AVAILABLE.value and self.current_order_id is None

    @property
    def is_occupied(self) -> bool:
        return self.status == TableStatus.OCCUPIED.value

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

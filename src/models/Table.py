"""
Model Table và TableStatus: Quản lý thông tin và trạng thái bàn ăn.
Hiện thực hóa kiến trúc được Mentor phê duyệt:
- Bàn có trạng thái AVAILABLE, OCCUPIED, RESERVED.
- Liên kết với Order thông qua current_order_id.
"""
from typing import Any, Dict, Optional


class TableStatus:
    AVAILABLE = "AVAILABLE"    # Bàn trống, sẵn sàng đón khách
    OCCUPIED = "OCCUPIED"      # Đang có khách ngồi / đang phục vụ đơn
    RESERVED = "RESERVED"      # Bàn đã được đặt trước

    ALL = {AVAILABLE, OCCUPIED, RESERVED}

    LABELS = {
        AVAILABLE: "Bàn trống",
        OCCUPIED: "Đang có khách",
        RESERVED: "Đã đặt trước",
    }

    @staticmethod
    def get_label(status: str) -> str:
        return TableStatus.LABELS.get(status, str(status))


class Table:
    """
    Đại diện cho một bàn ăn trong nhà hàng/quán cafe.
    """

    def __init__(
        self,
        id: int,
        name: str,
        capacity: int = 4,
        status: str = TableStatus.AVAILABLE,
        current_order_id: Optional[str] = None,
    ):
        self.id: int = int(id)
        self.name: str = str(name).strip()
        self.capacity: int = int(capacity)
        self.status: str = status.upper().strip() if status else TableStatus.AVAILABLE
        self.current_order_id: Optional[str] = str(current_order_id).strip() if current_order_id else None

        if self.status not in TableStatus.ALL:
            raise ValueError(f"Trạng thái bàn '{self.status}' không hợp lệ. Phải thuộc {TableStatus.ALL}")

    @property
    def is_available(self) -> bool:
        return self.status == TableStatus.AVAILABLE

    @property
    def is_occupied(self) -> bool:
        return self.status == TableStatus.OCCUPIED

    @property
    def is_reserved(self) -> bool:
        return self.status == TableStatus.RESERVED

    def occupy(self, order_id: str) -> None:
        """Chiếm bàn khi khách vào ngồi và tạo đơn."""
        if not order_id:
            raise ValueError("Cần cung cấp mã đơn hàng khi chiếm bàn.")
        self.status = TableStatus.OCCUPIED
        self.current_order_id = str(order_id).strip()

    def release(self) -> None:
        """Giải phóng bàn sau khi khách thanh toán xong hoặc đơn bị hủy."""
        self.status = TableStatus.AVAILABLE
        self.current_order_id = None

    def reserve(self) -> None:
        """Đặt trước bàn."""
        if self.status == TableStatus.OCCUPIED:
            raise ValueError(f"Bàn '{self.name}' đang có khách, không thể đặt trước.")
        self.status = TableStatus.RESERVED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "capacity": self.capacity,
            "status": self.status,
            "current_order_id": self.current_order_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Table":
        return cls(
            id=int(data.get("id", 0)),
            name=str(data.get("name", "")),
            capacity=int(data.get("capacity", 4)),
            status=str(data.get("status", TableStatus.AVAILABLE)),
            current_order_id=data.get("current_order_id"),
        )

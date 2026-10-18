import sys
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')


class OrderItem(BaseModel):
    """
    Model đại diện cho từng món ăn/thức uống trong một đơn hàng (Order).
    Tuân thủ đặc tả JSON schema trong data/orders.json và Data Contract.
    """
    model_config = ConfigDict(
        validate_assignment=True,
        str_strip_whitespace=True
    )

    menu_item_id: str = Field(..., min_length=1, description="Mã định danh món tham chiếu menu.id (ví dụ: M01)")
    item_name: str = Field(..., min_length=1, description="Tên món ăn tại thời điểm gọi (Snapshot)")
    unit_price: int = Field(..., ge=0, description="Đơn giá tại thời điểm gọi tính bằng VNĐ (>= 0)")
    quantity: int = Field(..., gt=0, description="Số lượng món gọi (> 0)")
    subtotal: int = Field(default=0, ge=0, description="Thành tiền = unit_price * quantity")
    note: str = Field(default="", description="Ghi chú riêng cho món (ví dụ: 'Ít đường', 'Không đá')")

    @model_validator(mode="before")
    @classmethod
    def calculate_subtotal_before(cls, data: Any) -> Any:
        """Tự động tính toán hoặc kiểm tra subtotal khi khởi tạo."""
        if isinstance(data, dict):
            unit_price = int(data.get("unit_price", 0))
            quantity = int(data.get("quantity", 1))
            # Tự động tính lại thành tiền nếu không được truyền hoặc truyền sai lệch
            data["subtotal"] = unit_price * quantity
            if "note" not in data or data["note"] is None:
                data["note"] = ""
        return data

    def update_quantity(self, new_quantity: int) -> None:
        """
        Cập nhật số lượng món và tự động tính lại thành tiền (subtotal).
        :param new_quantity: Số lượng mới (> 0)
        """
        if not isinstance(new_quantity, int) or new_quantity <= 0:
            raise ValueError(f"Số lượng món phải là số nguyên dương (> 0), nhận được: {new_quantity}")
        self.quantity = new_quantity
        self.subtotal = self.unit_price * self.quantity

    def update_note(self, new_note: str) -> None:
        """
        Cập nhật ghi chú chế biến cho món.
        :param new_note: Ghi chú mới
        """
        self.note = (new_note or "").strip()

    def to_dict(self) -> Dict[str, Any]:
        """
        Xuất object thành dictionary chuẩn hóa theo đúng Data Contract JSON.
        """
        return {
            "menu_item_id": self.menu_item_id,
            "item_name": self.item_name,
            "unit_price": int(self.unit_price),
            "quantity": int(self.quantity),
            "subtotal": int(self.subtotal),
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderItem":
        """
        Khởi tạo đối tượng OrderItem từ dictionary đọc từ JSON hoặc request.
        """
        if not isinstance(data, dict):
            raise TypeError("Dữ liệu đầu vào phải là một dictionary.")
        
        unit_price = int(data.get("unit_price", 0))
        quantity = int(data.get("quantity", 1))
        
        return cls(
            menu_item_id=str(data.get("menu_item_id", "")),
            item_name=str(data.get("item_name", "")),
            unit_price=unit_price,
            quantity=quantity,
            subtotal=unit_price * quantity,
            note=str(data.get("note", "") or "")
        )

    @classmethod
    def from_menu_item(cls, menu_item: Any, quantity: int = 1, note: str = "") -> "OrderItem":
        """
        Tiện ích tạo OrderItem trực tiếp từ một đối tượng MenuItem.
        """
        item_id = getattr(menu_item, "id", None) or getattr(menu_item, "item_id", "")
        item_name = getattr(menu_item, "name", "")
        price = getattr(menu_item, "price", None)
        if price is None:
            price = getattr(menu_item, "unit_price", 0)
            
        return cls(
            menu_item_id=str(item_id),
            item_name=str(item_name),
            unit_price=int(price),
            quantity=int(quantity),
            subtotal=int(price) * int(quantity),
            note=note
        )

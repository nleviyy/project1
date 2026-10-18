from dataclasses import dataclass, field, asdict
from typing import Optional

@dataclass
class MenuItem:
    id: str
    name: str
    category: str
    price: float
    unit: str
    is_available: bool = True
    description: Optional[str] = ""
    prep_time: Optional[int] = 0

    def __post_init__(self):
        if not self.id or len(str(self.id).strip()) < 2:
            raise ValueError("ID món ăn phải có ít nhất 2 ký tự.")
        if not self.name or len(str(self.name).strip()) < 1:
            raise ValueError("Tên món không được để trống.")
        if not self.category or len(str(self.category).strip()) < 1:
            raise ValueError("Phân loại (category) không được để trống.")
        try:
            self.price = float(self.price)
        except (ValueError, TypeError):
            raise ValueError("Đơn giá phải là số hợp lệ.")
        if self.price < 0:
            raise ValueError("Đơn giá phải lớn hơn hoặc bằng 0.")
        if not self.unit or len(str(self.unit).strip()) < 1:
            raise ValueError("Đơn vị tính không được để trống.")
        if self.prep_time is not None:
            self.prep_time = int(self.prep_time)
            if self.prep_time < 0:
                raise ValueError("Thời gian chế biến không được âm.")
        
        self.id = str(self.id).strip()
        self.name = str(self.name).strip()
        self.category = str(self.category).strip()
        self.unit = str(self.unit).strip()

    def update(self, **kwargs):
        """Cập nhật dữ liệu an toàn: Chỉ áp dụng khi toàn bộ dữ liệu mới hợp lệ."""
        old_state = asdict(self)
        try:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            self.__post_init__()
        except Exception as e:
            for key, value in old_state.items():
                setattr(self, key, value)
            raise ValueError(f"Cập nhật thất bại, đã khôi phục dữ liệu ban đầu. Lỗi: {e}")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MenuItem":
        return cls(
            id=str(data.get("id", data.get("item_id", ""))),
            name=str(data.get("name", "")),
            category=str(data.get("category", data.get("item_type", "Chưa phân loại"))),
            price=float(data.get("price", data.get("unit_price", 0))),
            unit=str(data.get("unit", "phần")),
            is_available=bool(data.get("is_available", data.get("status", True))),
            description=data.get("description", ""),
            prep_time=int(data.get("prep_time", 0))
        )
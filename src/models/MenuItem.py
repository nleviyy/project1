from dataclasses import dataclass
from typing import Optional


def _read_value(
    data: dict,
    key: str,
    default: object,
    alias: Optional[str] = None,
) -> object:
    if key in data:
        return data[key]
    if alias is not None and alias in data:
        return data[alias]
    return default


@dataclass
class MenuItem:
    id: str
    name: str
    category: str
    price: int
    unit: str
    is_available: bool = True
    description: Optional[str] = ""
    prep_time: Optional[int] = 0
    image: Optional[str] = ""
    color: Optional[str] = "#68452f"

    def __post_init__(self):
        if not self.id or len(str(self.id).strip()) < 2:
            raise ValueError("ID món ăn phải có ít nhất 2 ký tự.")
        if not self.name or len(str(self.name).strip()) < 1:
            raise ValueError("Tên món không được để trống.")
        if not self.category or len(str(self.category).strip()) < 1:
            raise ValueError("Phân loại (category) không được để trống.")
        try:
            price = float(self.price)
        except (ValueError, TypeError):
            raise ValueError("Đơn giá phải là số hợp lệ.")
        if not price.is_integer():
            raise ValueError("Đơn giá phải là số nguyên (VNĐ).")
        self.price = int(price)
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
        old_state = self.to_dict()
        try:
            for key, value in kwargs.items():
                if key in old_state:
                    self.__dict__[key] = value
            self.__post_init__()
        except Exception as e:
            for key in old_state:
                self.__dict__[key] = old_state[key]
            raise ValueError(f"Cập nhật thất bại, đã khôi phục dữ liệu ban đầu. Lỗi: {e}")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "price": self.price,
            "unit": self.unit,
            "is_available": self.is_available,
            "description": self.description,
            "prep_time": self.prep_time,
            "image": self.image,
            "color": self.color,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MenuItem":
        return cls(
            id=str(_read_value(data, "id", "", "item_id")),
            name=str(_read_value(data, "name", "")),
            category=str(
                _read_value(data, "category", "Chưa phân loại", "item_type")
            ),
            price=_read_value(data, "price", 0, "unit_price"),
            unit=str(_read_value(data, "unit", "phần")),
            is_available=bool(_read_value(data, "is_available", True, "status")),
            description=_read_value(data, "description", ""),
            prep_time=int(_read_value(data, "prep_time", 0)),
            image=_read_value(data, "image", ""),
            color=_read_value(data, "color", "#68452f"),
        )
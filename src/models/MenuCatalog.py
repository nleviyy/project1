from typing import Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

class MenuItem(BaseModel):
    id: str = Field(..., description="Mã định danh món (VD: M01)", min_length=2)
    name: str = Field(..., description="Tên món", min_length=1)
    category: str = Field(..., description="Loại món (Đồ uống, Món chính, Ăn vặt,...)")
    price: float = Field(..., description="Giá bán", gt=0)
    unit: str = Field(..., description="Đơn vị tính (ly, phần, dĩa...)")
    is_available: bool = Field(default=True, description="Trạng thái còn/hết hàng")
    description: Optional[str] = Field(default="", description="Mô tả chi tiết món ăn")
    prep_time: Optional[int] = Field(default=0, description="Thời gian chuẩn bị (phút)", ge=0)
class MenuCatalog:
    def __init__(self):
        self._items: Dict[str, MenuItem] = {}

    def load_from_dict(self, data: dict):
        """Tải dữ liệu từ Dictionary, có hỗ trợ convert các key cũ sang key chuẩn mới"""
        self._items.clear()
        if not data:
            return

        for key, info in data.items():
            try:
                item_data = {
                    "id": info.get("id", info.get("item_id", info.get("Item_id", key))),
                    "name": info.get("name", info.get("Name", "")),
                    "category": info.get("category", info.get("item_type", info.get("Item_type", "Chưa phân loại"))),
                    "price": info.get("price", info.get("unit_price", info.get("Unit_price", 1))),
                    "unit": info.get("unit", info.get("Unit", "phần")),
                    "is_available": info.get("is_available", info.get("status", info.get("Status_of_menuItem", True))),
                    "description": info.get("description", info.get("Description", "")),
                    "prep_time": info.get("prep_time", info.get("Prep_time", 0))
                }
                item = MenuItem(**item_data)
                self._items[item.id] = item
            except ValueError as e:
                print(f"[Cảnh báo] Bỏ qua món ID {key} do dữ liệu không hợp lệ: {e}")

    def to_dict(self) -> dict:
        """Xuất danh mục ra Dictionary nhờ hàm .model_dump() / .dict() của Pydantic"""
        return {
            item_id: item.dict() 
            for item_id, item in self._items.items()
        }

    def add_item(self, item: MenuItem) -> bool:
        """Thêm món mới"""
        if not isinstance(item, MenuItem):
            raise TypeError("Đối tượng thêm vào phải thuộc lớp MenuItem.")
        
        if item.id in self._items:
            return False
        
        self._items[item.id] = item
        return True

    def update_item(self, item_id: str, **kwargs) -> bool:
        """Cập nhật thông tin món ăn"""
        item = self.get_item(item_id)
        if not item:
            return False

        key_mapping = {
            "unit_price": "price",
            "status": "is_available",
            "item_type": "category"
        }

        for k, v in kwargs.items():
            actual_key = key_mapping.get(k, k)
            if hasattr(item, actual_key):
                setattr(item, actual_key, v)

        return True

    def remove_item(self, item_id: str) -> bool:
        """Xóa món theo ID"""
        return self._items.pop(item_id, None) is not None

    def get_item(self, item_id: str) -> Optional[MenuItem]:
        """Lấy 1 món theo ID"""
        return self._items.get(item_id)

    def get_all_items(self) -> List[MenuItem]:
        """Lấy danh sách tất cả các món"""
        return list(self._items.values())

    def search_items(self, keyword: str) -> List[MenuItem]:
        """Tìm kiếm tương đối theo tên món hoặc mã món"""
        kw = keyword.lower().strip()
        return [
            item for item in self._items.values()
            if kw in item.name.lower() or kw in item.id.lower()
        ]

    def filter_by_type(self, item_type: str) -> List[MenuItem]:
        """Lọc danh sách theo loại món (category)"""
        target_type = item_type.lower().strip()
        return [
            item for item in self._items.values()
            if item.category.lower() == target_type
        ]
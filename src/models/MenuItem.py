import sys
from typing import Optional
from pydantic import BaseModel, Field

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

class MenuItem(BaseModel):
    id: str = Field(..., description="Mã định danh món (VD: M01)", min_length=2)
    name: str = Field(..., description="Tên món", min_length=1)
    category: str = Field(..., description="Loại món (Đồ uống, Món chính, Ăn vặt,...)")
    price: float = Field(..., description="Giá bán", gt=0)
    unit: str = Field(..., description="Đơn vị tính (ly, phần, dĩa...)")
    is_available: bool = Field(default=True, description="Trạng thái còn/hết hàng")
    description: Optional[str] = Field(default="", description="Mô tả chi tiết món ăn")
    prep_time: Optional[int] = Field(default=0, description="Thời gian chuẩn bị (phút)", ge=0)


if __name__ == "__main__":
    item = MenuItem(id="M01", name="Cà phê sữa đá", category="Đồ uống", price=29000, unit="ly")
    print(f"[MenuItem Test] Khởi tạo thành công: {item.name} ({item.id}) - Giá: {item.price:,.0f} VND/{item.unit}")
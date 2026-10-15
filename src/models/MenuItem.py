from typing import Optional
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
"""
Package core: Xử lý logic nghiệp vụ và hướng đối tượng OOP.
- OrderService: Quản lý vòng đời đơn hàng, xác nhận đơn, tránh thanh toán trùng.
- TableManager: Quản lý bàn ăn, chiếm bàn và giải phóng bàn.
"""
from .OrderService import OrderService
from .TableManager import TableManager

__all__ = ["OrderService", "TableManager"]

"""
Package core: Xử lý logic nghiệp vụ và hướng đối tượng OOP.
- OrderService: Quản lý vòng đời đơn hàng, xác nhận đơn, tránh thanh toán trùng.
"""
from .OrderService import OrderService

__all__ = ["OrderService"]

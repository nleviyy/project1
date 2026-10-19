"""Backward-compatible shim for kitchen module."""
from src.core.KitchenManager import KitchenManager
from src.models.KitchenOrder import KitchenOrder as Order
from src.models.Order import OrderStatus

__all__ = ["KitchenManager", "Order", "OrderStatus"]

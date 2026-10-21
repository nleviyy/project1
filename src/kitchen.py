"""Backward-compatible shim for kitchen module."""
from src.core.KitchenManager import KitchenManager
from src.models.Order import Order, OrderStatus

__all__ = ["KitchenManager", "Order", "OrderStatus"]

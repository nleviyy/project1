"""
Package models: Định nghĩa các cấu trúc dữ liệu và Data Class (Phụ trách: Quỳnh)
- MenuItem, MenuCatalog, JSONStorage...
"""
from importlib import import_module

from .MenuItem import MenuItem
from .MenuCatalog import MenuCatalog
from .JSONStorage import JSONStorage

__all__ = ["MenuItem", "MenuCatalog", "JSONStorage", "Order", "OrderItem", "OrderStatus"]


def __getattr__(name):
    module_map = {
        "Order": ".Order",
        "OrderItem": ".OrderItem",
        "OrderStatus": ".OrderStatus",
    }
    if name in module_map:
        module = import_module(module_map[name], __name__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


"""
Kiểm thử tự động xác nhận cấu trúc thư mục và hợp đồng dữ liệu JSON (Data Contract).
"""
from datetime import datetime
from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

def test_project_structure():
    """Kiểm tra sự tồn tại của các thư mục cốt lõi."""
    assert (BASE_DIR / "src").is_dir(), "Thư mục src/ phải tồn tại"
    assert (BASE_DIR / "src" / "models").is_dir(), "Thư mục src/models/ phải tồn tại"
    assert (BASE_DIR / "src" / "core").is_dir(), "Thư mục src/core/ phải tồn tại"
    assert (BASE_DIR / "src" / "ui").is_dir(), "Thư mục src/ui/ phải tồn tại"
    assert (BASE_DIR / "data").is_dir(), "Thư mục data/ phải tồn tại"
    assert (BASE_DIR / "src" / "app.py").is_file(), "File src/app.py phải tồn tại"

def test_menu_schema():
    """Kiểm tra cấu trúc và kiểu dữ liệu của menu.json."""
    menu_file = DATA_DIR / "menu.json"
    assert menu_file.is_file(), "File menu.json phải tồn tại"
    with open(menu_file, "r", encoding="utf-8") as f:
        items = json.load(f)
    assert isinstance(items, list) and len(items) > 0
    for item in items:
        assert isinstance(item["id"], str)
        assert isinstance(item["name"], str)
        assert isinstance(item["category"], str)
        assert isinstance(item["price"], (int, float)) and item["price"] >= 0
        assert isinstance(item["unit"], str)
        assert isinstance(item["is_available"], bool)

def test_tables_schema():
    """Kiểm tra cấu trúc và kiểu dữ liệu của tables.json."""
    tables_file = DATA_DIR / "tables.json"
    assert tables_file.is_file(), "File tables.json phải tồn tại"
    valid_statuses = {"AVAILABLE", "OCCUPIED", "RESERVED"}
    with open(tables_file, "r", encoding="utf-8") as f:
        tables = json.load(f)
    assert isinstance(tables, list) and len(tables) > 0
    for table in tables:
        assert isinstance(table["id"], int)
        assert isinstance(table["name"], str)
        assert isinstance(table["capacity"], int) and table["capacity"] > 0
        assert table["status"] in valid_statuses
        assert table["current_order_id"] is None or isinstance(table["current_order_id"], str)

def test_orders_schema():
    """Kiểm tra cấu trúc và kiểu dữ liệu của orders.json."""
    orders_file = DATA_DIR / "orders.json"
    assert orders_file.is_file(), "File orders.json phải tồn tại"
    valid_statuses = {"PENDING", "PREPARING", "SERVED", "COMPLETED", "CANCELLED"}
    with open(orders_file, "r", encoding="utf-8") as f:
        orders = json.load(f)
    assert isinstance(orders, list) and len(orders) > 0
    for order in orders:
        assert isinstance(order["id"], str)
        assert isinstance(order["table_id"], int)
        assert order["status"] in valid_statuses
        # Kiểm tra chuẩn thời gian ISO 8601
        datetime.fromisoformat(order["created_at"])
        datetime.fromisoformat(order["updated_at"])
        assert isinstance(order["items"], list) and len(order["items"]) > 0
        for item in order["items"]:
            assert isinstance(item["menu_item_id"], str)
            assert isinstance(item["item_name"], str)
            assert isinstance(item["unit_price"], (int, float))
            assert isinstance(item["quantity"], int) and item["quantity"] > 0
            assert item["subtotal"] == item["unit_price"] * item["quantity"]
        assert order["final_amount"] == order["total_amount"] - order["discount_amount"]

def test_payments_schema():
    """Kiểm tra cấu trúc và kiểu dữ liệu của payments.json."""
    payments_file = DATA_DIR / "payments.json"
    assert payments_file.is_file(), "File payments.json phải tồn tại"
    valid_methods = {"CASH", "BANK_TRANSFER", "CARD"}
    valid_statuses = {"SUCCESS", "FAILED", "REFUNDED"}
    with open(payments_file, "r", encoding="utf-8") as f:
        payments = json.load(f)
    assert isinstance(payments, list) and len(payments) > 0
    for pay in payments:
        assert isinstance(pay["id"], str)
        assert isinstance(pay["order_id"], str)
        assert isinstance(pay["table_id"], int)
        assert isinstance(pay["amount_paid"], (int, float)) and pay["amount_paid"] > 0
        assert pay["method"] in valid_methods
        assert pay["status"] in valid_statuses
        datetime.fromisoformat(pay["payment_time"])
        assert isinstance(pay["cashier_name"], str)

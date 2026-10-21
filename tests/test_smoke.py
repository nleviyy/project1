from datetime import datetime
from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

def test_project_structure():
    assert (BASE_DIR / "src").is_dir(), "Thư mục src/ phải tồn tại"
    assert (BASE_DIR / "src" / "models").is_dir(), "Thư mục src/models/ phải tồn tại"
    assert (BASE_DIR / "src" / "core").is_dir(), "Thư mục src/core/ phải tồn tại"
    assert (BASE_DIR / "src" / "ui").is_dir(), "Thư mục src/ui/ phải tồn tại"
    assert (BASE_DIR / "data").is_dir(), "Thư mục data/ phải tồn tại"
    assert (BASE_DIR / "src" / "app.py").is_file(), "File src/app.py phải tồn tại"

def test_menu_schema():
    menu_file = DATA_DIR / "menu.json"
    assert menu_file.is_file(), "File menu.json phải tồn tại"
    with open(menu_file, "r", encoding="utf-8") as f:
        items = json.load(f)
    assert isinstance(items, list) and len(items) > 0
    for item in items:
        assert isinstance(item["id"], str)
        assert isinstance(item["name"], str)
        assert isinstance(item["category"], str)
        assert isinstance(item["price"], int) and item["price"] >= 0
        assert isinstance(item["unit"], str)
        assert isinstance(item["is_available"], bool)
        assert isinstance(item["prep_time"], int) and item["prep_time"] >= 0

def test_tables_schema():
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
    orders_file = DATA_DIR / "orders.json"
    assert orders_file.is_file(), "File orders.json phải tồn tại"
    valid_statuses = {"PENDING", "PREPARING", "SERVED", "COMPLETED", "CANCELLED"}
    with open(orders_file, "r", encoding="utf-8") as f:
        orders = json.load(f)
    assert isinstance(orders, list) and len(orders) > 0
    order_fields = {
        "id", "table_id", "created_at", "updated_at", "status", "items",
        "total_amount", "discount_amount", "final_amount", "notes",
<<<<<<< Updated upstream
        "kitchen_note", "preparing_started_at", "priority_at",
=======
        "preparing_started_at",
>>>>>>> Stashed changes
    }

    item_fields = {
        "menu_item_id", "item_name", "unit_price", "quantity", "subtotal",
        "note", "prep_time",
    }
    for order in orders:
        assert set(order) == order_fields
        assert isinstance(order["id"], str)
        assert isinstance(order["table_id"], int)
        assert order["status"] in valid_statuses
        datetime.fromisoformat(order["created_at"])
        datetime.fromisoformat(order["updated_at"])
        assert isinstance(order["items"], list) and len(order["items"]) > 0
        for item in order["items"]:
            assert set(item) == item_fields
            assert isinstance(item["menu_item_id"], str)
            assert isinstance(item["item_name"], str)
            assert isinstance(item["unit_price"], (int, float))
            assert isinstance(item["quantity"], int) and item["quantity"] > 0
            assert item["subtotal"] == item["unit_price"] * item["quantity"]
            assert isinstance(item["prep_time"], int) and item["prep_time"] >= 0
        assert order["final_amount"] == order["total_amount"] - order["discount_amount"]

def test_payments_schema():
    payments_file = DATA_DIR / "payments.json"
    assert payments_file.is_file(), "File payments.json phải tồn tại"
    valid_methods = {"CASH", "BANK_TRANSFER", "CARD"}
    valid_statuses = {"SUCCESS", "FAILED", "REFUNDED"}
    payment_fields = {
        "id", "order_id", "table_id", "payment_time", "amount", "discount_rate",
        "amount_paid", "method", "status", "cashier_name", "transaction_code",
        "note", "cash_received", "change_due",
    }
    with open(payments_file, "r", encoding="utf-8") as f:
        payments = json.load(f)
    assert isinstance(payments, list) and len(payments) > 0
    for pay in payments:
        assert set(pay) == payment_fields
        assert isinstance(pay["id"], str)
        assert isinstance(pay["order_id"], str)
        assert isinstance(pay["table_id"], int)
        assert isinstance(pay["amount_paid"], (int, float)) and pay["amount_paid"] > 0
        assert isinstance(pay["amount"], int) and pay["amount"] >= 0
        assert isinstance(pay["discount_rate"], (int, float))
        assert 0 <= pay["discount_rate"] <= 1
        assert pay["cash_received"] is None or isinstance(pay["cash_received"], int)
        assert isinstance(pay["change_due"], int) and pay["change_due"] >= 0
        assert pay["method"] in valid_methods
        assert pay["status"] in valid_statuses
        datetime.fromisoformat(pay["payment_time"])
        assert isinstance(pay["cashier_name"], str)

def test_invoices_schema():
    invoices_file = DATA_DIR / "invoices.json"
    assert invoices_file.is_file(), "File invoices.json phải tồn tại"
    with open(invoices_file, "r", encoding="utf-8") as f:
        invoices = json.load(f)
    assert isinstance(invoices, list)
    for inv in invoices:
        assert isinstance(inv["id"], str)
        assert isinstance(inv["payment_id"], str)
        assert isinstance(inv["order_id"], str)
        assert isinstance(inv["table_id"], int)
        datetime.fromisoformat(inv["issued_at"])
        assert isinstance(inv["items"], list)
        assert isinstance(inv["total_amount"], int)
        assert isinstance(inv["discount_amount"], int)
        assert isinstance(inv["final_amount"], int)

def test_ui_components_importable():
    from src.ui import (
        apply_custom_styles,
        render_dashboard_component,
        render_kitchen_component,
        render_ordering_component,
        render_orders_component,
        render_payment_component,
        render_settings_component,
        render_tables_component,
    )
    assert callable(render_ordering_component)
    assert callable(render_kitchen_component)
    assert callable(render_orders_component)
    assert callable(render_payment_component)
    assert callable(render_tables_component)
    assert callable(render_dashboard_component)
    assert callable(render_settings_component)

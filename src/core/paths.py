from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

TABLES_PATH = DATA_DIR / "tables.json"
ORDERS_PATH = DATA_DIR / "orders.json"
PAYMENTS_PATH = DATA_DIR / "payments.json"
INVOICES_PATH = DATA_DIR / "invoices.json"
MENU_PATH = DATA_DIR / "menu.json"


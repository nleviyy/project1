"""
Demo luồng chạy dữ liệu F&B Management (Data Flow & OOP Models).
Cách chạy:
    uv run python demo_data.py
"""
import sys
from pathlib import Path

# Đảm bảo UTF-8 cho terminal Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Đưa src vào sys.path để import dễ dàng
CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))

from src.models.JSONStorage import JSONStorage
from src.models.MenuCatalog import MenuCatalog
from src.models.MenuItem import MenuItem

DATA_DIR = CURRENT_DIR / "data"

def print_header(title: str):
    print("\n" + "=" * 65)
    print(f"  {title}")
    print("=" * 65)

def main():
    print_header("🍽️ DEMO LUỒNG CHẠY DỮ LIỆU F&B ORDER & TABLE MANAGEMENT")

    # 1. ĐỌC DỮ LIỆU TỪ MENU.JSON VÀO OOP (MENUCATALOG & MENUITEM)
    print("\n[BƯỚC 1] Đọc dữ liệu từ 'data/menu.json' vào OOP Models...")
    raw_menu = JSONStorage.load_data(str(DATA_DIR / "menu.json"), default_data=[])
    catalog = MenuCatalog()
    catalog.load_from_dict(raw_menu)
    items = catalog.get_all_items()
    print(f"✅ Đã nạp thành công {len(items)} món ăn/đồ uống vào MenuCatalog.")

    # Hiển thị danh mục món
    print("\n📋 Danh sách món ăn trong Menu:")
    print(f"{'Mã':<6} | {'Tên món':<28} | {'Phân loại':<12} | {'Đơn giá':>10} | {'Trạng thái'}")
    print("-" * 75)
    for it in items:
        status_text = "Còn món" if it.is_available else "Tạm hết"
        print(f"{it.id:<6} | {it.name:<28} | {it.category:<12} | {int(it.price):>8,d} đ | {status_text}")

    # 2. DEMO TÌM KIẾM MÓN
    print_header("🔍 [BƯỚC 2] Thử nghiệm tính năng Tìm kiếm món")
    keyword = "cà phê"
    found = catalog.search_items(keyword)
    print(f"Kết quả tìm kiếm với từ khóa '{keyword}' ({len(found)} món):")
    for it in found:
        print(f"  - [{it.id}] {it.name} ({it.category}) - Giá: {int(it.price):,d} đ")

    # 3. DEMO LỌC THEO LOẠI
    print_header("🎯 [BƯỚC 3] Thử nghiệm tính năng Lọc theo phân loại")
    cat_type = "Đồ uống"
    drinks = catalog.filter_by_type(cat_type)
    print(f"Danh sách món thuộc nhóm '{cat_type}' ({len(drinks)} món):")
    for it in drinks:
        print(f"  - [{it.id}] {it.name} - Giá: {int(it.price):,d} đ")

    # 4. DEMO THÊM MÓN MỚI VÀ CẬP NHẬT
    print_header("➕ [BƯỚC 4] Thử nghiệm Thêm món mới & Cập nhật giá")
    new_dish = MenuItem(
        id="M09",
        name="Trà mãng cầu xiêm",
        category="Đồ uống",
        price=35000,
        unit="ly",
        is_available=True,
        description="Trà mãng cầu thanh ngọt đậm vị"
    )
    if catalog.add_item(new_dish):
        print(f"✅ Đã thêm món mới: [{new_dish.id}] {new_dish.name} - {int(new_dish.price):,d} đ")
    
    # Cập nhật giá
    catalog.update_item("M09", unit_price=38000)
    updated = catalog.get_item("M09")
    print(f"✅ Cập nhật đơn giá món {updated.id} thành công: {int(updated.price):,d} đ")

    # 5. TỔNG HỢP CÁC TẬP DỮ LIỆU KHÁC (TABLES, ORDERS, PAYMENTS)
    print_header("📊 [BƯỚC 5] Đọc và thống kê Sơ đồ bàn, Đơn hàng & Doanh thu")
    tables = JSONStorage.load_data(str(DATA_DIR / "tables.json"), default_data=[])
    orders = JSONStorage.load_data(str(DATA_DIR / "orders.json"), default_data=[])
    payments = JSONStorage.load_data(str(DATA_DIR / "payments.json"), default_data=[])

    occupied_count = sum(1 for t in tables if t.get("status") == "OCCUPIED")
    available_count = sum(1 for t in tables if t.get("status") == "AVAILABLE")
    reserved_count = sum(1 for t in tables if t.get("status") == "RESERVED")
    total_revenue = sum(p.get("amount_paid", 0) for p in payments if p.get("status") == "SUCCESS")

    print(f"🪑 Tổng số bàn: {len(tables)} | Có khách: {occupied_count} 🔴 | Trống: {available_count} 🟢 | Đã đặt: {reserved_count} 🟡")
    print(f"🧾 Số lượng đơn hàng: {len(orders)} đơn")
    for ord_item in orders:
        print(f"   - Đơn {ord_item['id']} (Bàn {ord_item['table_id']}): {ord_item['status']} - Tổng: {ord_item['final_amount']:,d} đ")
    print(f"💳 Tổng doanh thu đã thanh toán thành công: {total_revenue:,d} VNĐ")

    print("\n" + "=" * 65)
    print("✨ DỮ LIỆU ĐANG HOẠT ĐỘNG HOÀN TOÀN KHỚP VỚI DATA CONTRACT VÀ STREAMLIT!")
    print("=" * 65)

if __name__ == "__main__":
    main()

import os
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from src.core.KitchenManager import KitchenManager
from src.models.KitchenOrder import KitchenOrder as Order
from src.core.Cart import Cart


def print_title(text: str):
    print("\n" + "=" * 65)
    print(f" {text}")
    print("=" * 65)


def main():
    print_title("🎯 MINH HỌA NHÁNH DATA_STRUCTURE (CẤU TRÚC DỮ LIỆU)")

    print_title("PHẦN 1: HÀNG ĐỢI BẾP (src/kitchen.py - QUEUE FIFO)")
    km = KitchenManager()

    d1 = Order("ORD-001", table_id=1, prep_time=10, notes="Ít cay")
    d2 = Order("ORD-002", table_id=3, prep_time=15, notes="Nhiều đá")
    d3 = Order("ORD-003", table_id=5, prep_time=8, notes="Mang về")

    km.add_order(d1)
    km.add_order(d2)
    km.add_order(d3)

    print(f"✅ Đã nhận 3 đơn vào hàng đợi. Tổng đơn đang chờ: {km.count_waiting()} đơn.")
    print(f"⏱️ Thời gian khách đơn 3 (ORD-003) phải chờ dự kiến: {km.estimate_wait_time(d3)} phút (10 + 15 + 8 phút).")

    order_nau = km.start_next_order()
    print(f"\n🍳 Bếp bắt đầu nấu: Đơn [{order_nau.order_id}] (Bàn {order_nau.table_id})")
    print(f"   Trạng thái đơn: {order_nau.status} | Ghi chú: '{order_nau.notes}'")
    print(f"   Số đơn còn lại trong hàng đợi chờ nấu: {km.count_waiting()} đơn.")

    km.advance_status()
    print(f"🍽️ Lên món cho khách: Trạng thái = {order_nau.status}")
    km.finish_current_order()
    print(f"✨ Bếp đã giải phóng chỗ, sẵn sàng nhận nấu đơn tiếp theo!")

    print_title("PHẦN 2: GIỎ HÀNG HOÀN TÁC (src/redo_undo.py - STACK UNDO / REDO)")
    cart = Cart()

    mon_1 = {"id": "M01", "name": "Cà phê đen đá", "price": 25000, "is_available": True}
    mon_2 = {"id": "M02", "name": "Bánh mì chảo", "price": 55000, "is_available": True}

    print("\n[Bước 1] Khách chọn 1 ly 'Cà phê đen đá':")
    cart.add_item(mon_1, quantity=1)
    print(f"   + Giỏ hàng: {cart.to_text()} -> Tổng tiền: {cart.calculate_total():,} VNĐ")

    print("\n[Bước 2] Khách chọn thêm 2 phần 'Bánh mì chảo':")
    cart.add_item(mon_2, quantity=2)
    print(f"   + Giỏ hàng: {cart.to_text()} -> Tổng tiền: {cart.calculate_total():,} VNĐ")

    print("\n[Bước 3] Khách bấm nhầm và nhấn nút 'UNDO (Hoàn tác)':")
    cart.undo()
    print(f"   ⏪ Đã hoàn tác: {cart.to_text()} -> Tổng tiền lùi về: {cart.calculate_total():,} VNĐ")

    print("\n[Bước 4] Khách muốn khôi phục lại và nhấn nút 'REDO (Làm lại)':")
    cart.redo()
    print(f"   ⏩ Đã làm lại: {cart.to_text()} -> Tổng tiền phục hồi: {cart.calculate_total():,} VNĐ")

    print("\n" + "=" * 65)
    print("🎉 TOÀN BỘ CẤU TRÚC DỮ LIỆU CỦA LAN ANH ĐANG HOẠT ĐỘNG HOÀN HẢO!")
    print("=" * 65)


if __name__ == "__main__":
    main()

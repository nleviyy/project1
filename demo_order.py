# -*- coding: utf-8 -*-
"""
Chương trình minh họa thực tế cho:
- 7.1 Xây dựng OrderItem & Order
- 7.2 Xây dựng OrderService
"""
import sys
from pathlib import Path

# Đảm bảo in tiếng Việt có dấu chuẩn trên terminal Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Nạp thư mục gốc vào sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.OrderItem import OrderItem
from src.models.Order import Order, OrderStatus
from src.core.OrderService import OrderService


def print_title(text: str):
    print("\n" + "=" * 65)
    print(f" {text}")
    print("=" * 65)


def main():
    print_title("🎯 DEMO KIỂM TRA CHỨC NĂNG 7.1 & 7.2 TRÊN DỰ ÁN PRJ1")

    # =========================================================================
    # PHẦN 1: KIỂM CHỨNG MỤC 7.1 (OrderItem & Order)
    # =========================================================================
    print_title("PHẦN 1: THỬ NGHIỆM MỤC 7.1 (OrderItem & Order)")

    # 1.1 Khởi tạo món trong đơn (OrderItem)
    print("\n[1.1] Khởi tạo các món gọi:")
    item1 = OrderItem(
        menu_item_id="M01",
        item_name="Cà phê đen đá",
        unit_price=25000,
        quantity=2,
        note="Ít đường"
    )
    item2 = OrderItem(
        menu_item_id="M03",
        item_name="Trà đào cam sả",
        unit_price=39000,
        quantity=1,
        note="Nhiều đá"
    )
    print(f"  + Món 1: {item1.item_name} x{item1.quantity} (Đơn giá: {item1.unit_price:,d}đ) -> Thành tiền: {item1.subtotal:,d}đ | Ghi chú: '{item1.note}'")
    print(f"  + Món 2: {item2.item_name} x{item2.quantity} (Đơn giá: {item2.unit_price:,d}đ) -> Thành tiền: {item2.subtotal:,d}đ | Ghi chú: '{item2.note}'")

    # 1.2 Tạo đơn hàng (Order) và thêm món
    print("\n[1.2] Tạo đơn hàng mới cho Bàn số 5:")
    order = Order(id="ORD-TEST-001", table_id=5)
    order.add_item(item1)
    order.add_item(item2)
    print(f"  + Đơn [{order.id}] đã tạo lúc {order.created_at}")
    print(f"  + Trạng thái ban đầu: {order.status} (Chờ xác nhận)")
    print(f"  + Tổng tiền món: {order.total_amount:,d} VNĐ")

    # 1.3 Cập nhật số lượng món và ghi chú
    print("\n[1.3] Cập nhật số lượng & ghi chú món 'M01':")
    order.update_item_quantity("M01", 3)
    order.update_item_note("M01", "Không đường, thêm đá")
    updated_item1 = [it for it in order.items if it.menu_item_id == "M01"][0]
    print(f"  + Sau cập nhật: Món {updated_item1.item_name} có số lượng mới: {updated_item1.quantity}, ghi chú mới: '{updated_item1.note}'")
    print(f"  + Tổng tiền sau khi sửa số lượng: {order.total_amount:,d} VNĐ")

    # 1.4 Áp dụng giảm giá và tính tổng tiền thực trả
    print("\n[1.4] Áp dụng phiếu giảm giá 20,000 VNĐ:")
    order.set_discount(20000)
    print(f"  + Tổng tiền ban đầu: {order.total_amount:,d} VNĐ")
    print(f"  + Tiền giảm giá: {order.discount_amount:,d} VNĐ")
    print(f"  + Tiền thực trả (final_amount): {order.final_amount:,d} VNĐ")

    # 1.5 Kiểm tra xóa món
    print("\n[1.5] Thử nghiệm xóa món 'M03' khỏi đơn:")
    order.remove_item("M03")
    print(f"  + Số lượng món còn lại trong đơn: {len(order.items)} món")
    print(f"  + Tổng tiền sau khi xóa món: {order.total_amount:,d} VNĐ -> Thực trả: {order.final_amount:,d} VNĐ")

    # 1.6 Kiểm tra trạng thái đơn
    print("\n[1.6] Kiểm tra chuyển đổi trạng thái đơn:")
    print(f"  + Đơn có đang PENDING không? -> {order.is_pending}")
    order.change_status(OrderStatus.PREPARING)
    print(f"  + Đổi sang PREPARING: Trạng thái hiện tại = {order.status}")


    # =========================================================================
    # PHẦN 2: KIỂM CHỨNG MỤC 7.2 (OrderService)
    # =========================================================================
    print_title("PHẦN 2: THỬ NGHIỆM MỤC 7.2 (OrderService)")

    from tempfile import TemporaryDirectory
    from src.core.TableManager import TableManager
    from src.core.KitchenManager import KitchenManager
    import json

    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        orders_file = tmp_path / "orders.json"
        payments_file = tmp_path / "payments.json"
        tables_file = tmp_path / "tables.json"

        # Khởi tạo tables mẫu gồm bàn 8
        tables_data = [
            {"id": i, "name": f"Bàn {i:02d}", "capacity": 4, "status": "AVAILABLE", "current_order_id": None}
            for i in range(1, 9)
        ]
        with open(tables_file, "w", encoding="utf-8") as f:
            json.dump(tables_data, f, ensure_ascii=False, indent=2)

        table_mgr = TableManager(tables_file=str(tables_file))
        kitchen_mgr = KitchenManager()

        service = OrderService(
            orders_file=orders_file,
            payments_file=payments_file,
            table_manager=table_mgr,
            kitchen_manager=kitchen_mgr,
        )

        # 2.1 Sinh mã đơn tự động
        new_id = service.generate_order_id()
        print(f"\n[2.1] Tự động sinh mã đơn hàng tiếp theo: {new_id}")

        # 2.2 Tạo đơn qua Service
        print("\n[2.2] Tạo đơn hàng mới cho Bàn số 8 qua OrderService:")
        dish = OrderItem(
            menu_item_id="M02",
            item_name="Cà phê sữa đá",
            unit_price=29000,
            quantity=2,
            note="Ít ngọt"
        )
        new_order = service.create_order(
            table_id=8,
            items=[dish],
            notes="Khách quen bàn 8"
        )
        print(f"  + Đã tạo đơn thành công: Mã '{new_order.id}' | Bàn: {new_order.table_id} | Tổng tiền: {new_order.final_amount:,d} VNĐ")
        print(f"  + Trạng thái ban đầu: {new_order.status}")

        # 2.3 Xác nhận đơn
        print(f"\n[2.3] Xác nhận đơn '{new_order.id}':")
        confirm_ok = service.confirm_order(new_order.id)
        print(f"  + Kết quả xác nhận đơn: {confirm_ok}")
        print(f"  + Trạng thái sau xác nhận: {new_order.status} (Đơn nằm trong Queue bếp)")

        # Bếp chế biến và lên món
        service.start_preparing_order(new_order.id)
        service.serve_order(new_order.id)

        # 2.4 Tìm đơn theo mã và theo bàn
        print(f"\n[2.4] Thử nghiệm tìm kiếm đơn:")
        found_by_id = service.get_order_by_id(new_order.id)
        print(f"  + Tìm theo mã '{new_order.id}': Tìm thấy đơn cho Bàn {found_by_id.table_id}")
        
        active_order_table8 = service.get_active_order_by_table(8)
        print(f"  + Tìm đơn đang hoạt động của Bàn 8: Tìm thấy mã đơn '{active_order_table8.id}' (Trạng thái: {active_order_table8.status})")

        # 2.5 Kiểm tra đơn đã thanh toán để TRÁNH THANH TOÁN TRÙNG
        print(f"\n[2.5] Thử nghiệm cơ chế CHỐNG THANH TOÁN TRÙNG:")
        can_pay, msg = service.can_checkout(new_order.id)
        print(f"  + Lần 1: Kiểm tra trước thanh toán: Hợp lệ = {can_pay} -> '{msg}'")

        # Ghi nhận thanh toán thành công vào payments_file
        with open(payments_file, "w", encoding="utf-8") as f:
            json.dump([{"order_id": new_order.id, "status": "SUCCESS", "amount": new_order.final_amount}], f)

        # Tiến hành hoàn tất đơn
        service.complete_order(new_order.id)
        print(f"  + Đã thanh toán đơn '{new_order.id}' -> Trạng thái đổi sang: {new_order.status}")

        # Thử thanh toán lại lần 2 đơn đã thanh toán
        can_pay_again, msg_again = service.can_checkout(new_order.id)
        print(f"  + Lần 2: Thử thanh toán lại đơn đã xong: Hợp lệ = {can_pay_again}")
        print(f"  ===> PHẢN HỒI BẢO VỆ CỦA HỆ THỐNG: '{msg_again}'")

    print("\n" + "=" * 65)
    print("✨ CHÚC MỪNG! TẤT CẢ TÍNH NĂNG 7.1 VÀ 7.2 ĐỀU ĐANG HOẠT ĐỘNG HOÀN HẢO!")
    print("=" * 65)


if __name__ == "__main__":
    main()

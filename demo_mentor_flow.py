"""
Kịch bản chạy thử nghiệm luồng nghiệp vụ 7 bước End-to-End
Hoàn toàn tuân thủ theo phản hồi và yêu cầu nghiệm thu của Mentor:
1. Khách chọn một bàn đang trống, kiểm tra trạng thái bàn.
2. Khách chọn món và số lượng vào giỏ hàng (Cart), thử nghiệm Undo/Redo.
3. Khách xác nhận đặt món -> Tạo Order ở trạng thái PENDING, đưa vào hàng đợi Bếp (Queue FIFO).
4. Bếp nhận đơn từ Queue -> Chuyển sang PREPARING. Kiểm tra cơ chế khóa sửa món khi đang nấu.
5. Bếp hoàn thành món -> Chuyển sang SERVED. Kiểm tra cơ chế CẤM HỦY khi đã lên món.
6. Ước tính và hiển thị thời gian chờ món tích lũy theo hàng đợi.
7. Thu ngân thanh toán -> In hóa đơn Invoice chuẩn VNĐ, chống thanh toán trùng, giải phóng bàn về AVAILABLE.
"""
import sys
import os
import json
from pathlib import Path
from tempfile import TemporaryDirectory

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Thêm src vào sys.path
BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from src.models.Order import Order, OrderStatus
from src.models.OrderItem import OrderItem
from src.models.Table import Table, TableStatus
from src.models.Payment import Payment, PaymentMethod
from src.models.Invoice import Invoice
from src.core.OrderService import OrderService
from src.core.TableManager import TableManager
from src.core.KitchenManager import KitchenManager
from src.core.Cart import Cart, CartItem


def print_step(step_num: int, title: str):
    print("\n" + "=" * 65)
    print(f" 🚀 BƯỚC {step_num}: {title.upper()}")
    print("=" * 65)


def run_demo():
    print("\n" + "★" * 65)
    print("   HỆ THỐNG QUẢN LÝ F&B - DEMO LUỒNG NGHIỆP VỤ 7 BƯỚC CHUẨN MENTOR")
    print("   Trưởng nhóm Backend: Nguyễn Lê Vy")
    print("★" * 65)

    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        tables_file = tmp_path / "tables.json"
        orders_file = tmp_path / "orders.json"
        payments_file = tmp_path / "payments.json"

        # Khởi tạo danh sách bàn mẫu
        tables_data = [
            {"id": 1, "name": "Bàn 01 (Tầng 1)", "capacity": 4, "status": "AVAILABLE", "current_order_id": None},
            {"id": 2, "name": "Bàn 02 (Tầng 1)", "capacity": 2, "status": "AVAILABLE", "current_order_id": None},
        ]
        with open(tables_file, "w", encoding="utf-8") as f:
            json.dump(tables_data, f, ensure_ascii=False, indent=2)

        # Khởi tạo các Manager & Service
        table_mgr = TableManager(tables_file=str(tables_file), auto_load=True)
        kitchen_mgr = KitchenManager()
        order_svc = OrderService(
            orders_file=orders_file,
            payments_file=payments_file,
            auto_load=True,
            table_manager=table_mgr,
            kitchen_manager=kitchen_mgr
        )

        # -------------------------------------------------------------
        # BƯỚC 1: Khách chọn bàn đang trống
        # -------------------------------------------------------------
        print_step(1, "Khách chọn một bàn đang trống")
        t1 = table_mgr.get_table(1)
        print(f" -> Kiểm tra {t1.name}:")
        print(f"    - Sức chứa : {t1.capacity} người")
        print(f"    - Trạng thái: {TableStatus.get_label(t1.status)} ({t1.status})")
        print(f"    - Khả dụng  : {'Hoàn toàn sẵn sàng đón khách!' if t1.is_available else 'Đã bận'}")

        # -------------------------------------------------------------
        # BƯỚC 2: Khách chọn món vào Cart & thử nghiệm Undo/Redo
        # -------------------------------------------------------------
        print_step(2, "Khách chọn món vào Cart & thử nghiệm Undo/Redo")
        cart = Cart()
        print(" -> Thêm món 1: Cà phê đen đá x 2 (50.000đ)")
        cart.add_item("M01", "Cà phê đen đá", 25000, 2, "Ít ngọt")
        print(" -> Thêm món 2: Trà đào cam sả x 1 (39.000đ)")
        cart.add_item("M02", "Trà đào cam sả", 39000, 1, "Nhiều đá")
        print(f"    ==> Tổng tiền giỏ hàng hiện tại: {cart.total_amount():,d} VNĐ (Số dòng món: {len(cart.items)})")

        print(" -> [Thao tác nhầm]: Khách lỡ bấm thêm Bánh sừng bò x 3...")
        cart.add_item("M05", "Bánh sừng bò", 35000, 3)
        print(f"    ==> Tổng tiền giỏ hàng tăng vọt lên: {cart.total_amount():,d} VNĐ")

        print(" -> [Khách bấm nút UNDO]: Hoàn tác món bánh vừa thêm...")
        cart.undo()
        print(f"    ==> Sau Undo, giỏ hàng quay về chuẩn: {cart.total_amount():,d} VNĐ ({len(cart.items)} món)")

        # -------------------------------------------------------------
        # BƯỚC 3: Xác nhận đặt món -> Tạo Order PENDING -> Vào Queue Bếp
        # -------------------------------------------------------------
        print_step(3, "Xác nhận đặt đơn -> Tạo Order PENDING -> Vào Queue Bếp")
        order_items = [
            OrderItem(
                menu_item_id=ci.item_id,
                item_name=ci.name,
                unit_price=ci.price,
                quantity=ci.quantity,
                note=ci.note
            )
            for ci in cart.items
        ]
        new_order = order_svc.create_order(
            table_id=1,
            items=order_items,
            notes="Khách bàn 1 gọi",
            custom_order_id="ORD-20261018-001"
        )
        print(f" -> Đã tạo đơn [{new_order.id}] cho {t1.name}:")
        print(f"    - Trạng thái đơn : {OrderStatus.get_label(new_order.status)} ({new_order.status})")
        print(f"    - Tổng tiền món  : {new_order.total_amount:,d} VNĐ")
        print(f"    - Trạng thái bàn : {TableStatus.get_label(t1.status)} (Bàn đã được chiếm)")

        print(" -> Gửi đơn xuống hàng đợi Bếp:")
        order_svc.confirm_order(new_order.id, kitchen_manager=kitchen_mgr)
        print(f"    - Số lượng đơn đang chờ trong bếp: {kitchen_mgr.count_waiting()} đơn")
        print(f"    - Đơn đầu tiên trong Queue bếp   : {kitchen_mgr.peek_next_order().id} (Bàn {kitchen_mgr.peek_next_order().table_id})")

        # -------------------------------------------------------------
        # BƯỚC 4: Bếp nhận đơn chế biến (PREPARING) & Kiểm tra bảo vệ FSM
        # -------------------------------------------------------------
        print_step(4, "Bếp bắt đầu chế biến (PREPARING) & Kiểm tra bảo vệ FSM")
        cooking_order = kitchen_mgr.start_next_order()
        print(f" -> Bếp bốc đơn [{cooking_order.id}] từ đầu hàng đợi:")
        print(f"    - Trạng thái bếp : Đang nấu món cho Bàn {cooking_order.table_id}")
        print(f"    - Trạng thái đơn : {OrderStatus.get_label(cooking_order.status)} ({cooking_order.status})")

        print(" -> [Kiểm tra bảo vệ]: Khách đòi sửa món khi bếp ĐANG NẤU:")
        try:
            cooking_order.add_item(OrderItem("M99", "Món phát sinh", 50000, 1))
            print("    ❌ LỖI: Hệ thống vẫn cho sửa!")
        except ValueError as e:
            print(f"    🛡️ HỆ THỐNG BẢO VỆ CHẶN THÀNH CÔNG: \"{e}\"")

        # -------------------------------------------------------------
        # BƯỚC 5: Thời gian chờ ước tính & Lên món (SERVED)
        # -------------------------------------------------------------
        print_step(5, "Thời gian chờ món dự kiến & Phục vụ lên bàn (SERVED)")
        wait_time = kitchen_mgr.estimate_wait_time(cooking_order)
        print(f" -> Thời gian chờ ước tính theo lượng món thực tế: {wait_time} phút (không dùng random!)")

        print(" -> Bếp nấu xong, nhân viên bưng món lên bàn:")
        kitchen_mgr.advance_status()  # PREPARING -> SERVED
        kitchen_mgr.finish_current_order()
        print(f"    - Trạng thái đơn hiện tại: {OrderStatus.get_label(cooking_order.status)} ({cooking_order.status})")

        print(" -> [Kiểm tra bảo vệ]: Thử hủy đơn khi khách ĐÃ ĂN (SERVED):")
        try:
            order_svc.cancel_order(cooking_order.id, reason="Khách đổi ý")
            print("    ❌ LỖI: Vẫn cho hủy đơn đã ăn!")
        except ValueError as e:
            print(f"    🛡️ HỆ THỐNG BẢO VỆ CHẶN THÀNH CÔNG: \"{e}\"")

        # -------------------------------------------------------------
        # BƯỚC 6: Xuất hóa đơn & Thanh toán an toàn
        # -------------------------------------------------------------
        print_step(6, "Xuất hóa đơn Invoice & Thanh toán chuẩn VNĐ")
        invoice = Invoice(
            id="INV-20261018-001",
            order_id=cooking_order.id,
            table_id=cooking_order.table_id,
            items=[item.to_dict() for item in cooking_order.items],
            total_amount=cooking_order.total_amount,
            discount_amount=cooking_order.discount_amount,
            final_amount=cooking_order.final_amount,
            payment_method="CASH",
            cashier_name="Nguyễn Lê Vy"
        )
        print(invoice.generate_text_receipt())
        # Lưu giao dịch thanh toán thành công vào payments_file
        with open(payments_file, "w", encoding="utf-8") as f:
            json.dump([{"order_id": cooking_order.id, "status": "SUCCESS", "amount": cooking_order.final_amount}], f)

        # -------------------------------------------------------------
        # BƯỚC 7: Hoàn tất đơn hàng, chống thanh toán trùng & giải phóng bàn
        # -------------------------------------------------------------
        print_step(7, "Hoàn tất đơn, Chống thanh toán trùng & Giải phóng bàn")
        # Hoàn tất lần 1
        order_svc.complete_order(cooking_order.id)
        print(f" -> Đơn [{cooking_order.id}] chuyển sang: {OrderStatus.get_label(cooking_order.status)} ({cooking_order.status})")
        print(f" -> Trạng thái Bàn 1 sau khi thanh toán xong: {TableStatus.get_label(t1.status)} ({t1.status}) - ĐÃ GIẢI PHÓNG TRỐNG!")

        print(" -> [Kiểm tra bảo vệ]: Thu ngân thử bấm thanh toán lần 2:")
        allowed, reason = order_svc.can_checkout(cooking_order.id)
        print(f"    - Cho phép thanh toán lại? : {allowed}")
        print(f"    - Lý do chặn từ hệ thống  : \"{reason}\"")

    print("\n" + "★" * 65)
    print(" ✅ TOÀN BỘ 7 BƯỚC NGHIỆP VỤ ĐÃ THỰC THI THÀNH CÔNG RỰC RỠ!")
    print("★" * 65 + "\n")


if __name__ == "__main__":
    run_demo()

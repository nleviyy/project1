"""
Bộ kiểm thử đơn vị cho Task 7.1 (OrderItem & Order) và Task 7.2 (OrderService).
"""
import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.models.OrderItem import OrderItem
from src.models.Order import Order, OrderStatus
from src.core.OrderService import OrderService


# =====================================================================
# 1. KIỂM THỬ TASK 7.1: OrderItem
# =====================================================================
class TestOrderItem:
    def test_create_order_item_and_calculate_subtotal(self):
        """Kiểm tra khởi tạo món và tự động tính thành tiền."""
        item = OrderItem(
            menu_item_id="M01",
            item_name="Cà phê đen đá",
            unit_price=25000,
            quantity=2,
            note="Không đường"
        )
        assert item.menu_item_id == "M01"
        assert item.item_name == "Cà phê đen đá"
        assert item.unit_price == 25000
        assert item.quantity == 2
        assert item.subtotal == 50000
        assert item.note == "Không đường"

    def test_update_quantity_recalculates_subtotal(self):
        """Kiểm tra cập nhật số lượng và tính lại subtotal."""
        item = OrderItem(
            menu_item_id="M02",
            item_name="Cà phê sữa đá",
            unit_price=29000,
            quantity=1
        )
        assert item.subtotal == 29000
        item.update_quantity(3)
        assert item.quantity == 3
        assert item.subtotal == 87000

        with pytest.raises(ValueError):
            item.update_quantity(0)
        with pytest.raises(ValueError):
            item.update_quantity(-1)

    def test_update_note(self):
        """Kiểm tra cập nhật ghi chú."""
        item = OrderItem(
            menu_item_id="M03",
            item_name="Trà đào cam sả",
            unit_price=39000,
            quantity=1
        )
        assert item.note == ""
        item.update_note("Nhiều đá, ít ngọt")
        assert item.note == "Nhiều đá, ít ngọt"

    def test_order_item_serialization(self):
        """Kiểm tra to_dict và from_dict."""
        original_dict = {
            "menu_item_id": "M05",
            "item_name": "Bánh mì chảo đặc biệt",
            "unit_price": 55000,
            "quantity": 2,
            "subtotal": 110000,
            "note": "Trứng lòng đào"
        }
        item = OrderItem.from_dict(original_dict)
        assert item.menu_item_id == "M05"
        assert item.quantity == 2
        assert item.subtotal == 110000
        assert item.note == "Trứng lòng đào"

        exported = item.to_dict()
        assert exported == original_dict


# =====================================================================
# 2. KIỂM THỬ TASK 7.1: Order
# =====================================================================
class TestOrder:
    def test_create_order_empty_items(self):
        """Tạo đơn hàng rỗng ban đầu."""
        order = Order(id="ORD-20261016-001", table_id=3)
        assert order.id == "ORD-20261016-001"
        assert order.table_id == 3
        assert order.status == OrderStatus.PENDING
        assert order.total_amount == 0
        assert order.discount_amount == 0
        assert order.final_amount == 0
        assert order.is_pending is True
        assert order.is_active is True

    def test_add_and_merge_items(self):
        """Thêm món và cộng dồn số lượng nếu cùng món và cùng ghi chú."""
        order = Order(id="ORD-20261016-002", table_id=2)
        
        item1 = OrderItem(menu_item_id="M01", item_name="Cà phê đen", unit_price=25000, quantity=1, note="Ít đá")
        order.add_item(item1)
        assert len(order.items) == 1
        assert order.total_amount == 25000
        assert order.final_amount == 25000

        # Thêm cùng món và cùng ghi chú -> cộng dồn
        item2 = OrderItem(menu_item_id="M01", item_name="Cà phê đen", unit_price=25000, quantity=2, note="Ít đá")
        order.add_item(item2)
        assert len(order.items) == 1
        assert order.items[0].quantity == 3
        assert order.total_amount == 75000

        # Thêm cùng món nhưng khác ghi chú -> tạo dòng riêng
        item3 = OrderItem(menu_item_id="M01", item_name="Cà phê đen", unit_price=25000, quantity=1, note="Không đá")
        order.add_item(item3)
        assert len(order.items) == 2
        assert order.total_amount == 100000

    def test_remove_item_and_update_quantity(self):
        """Xóa món và cập nhật số lượng."""
        order = Order(id="ORD-20261016-003", table_id=1)
        order.add_item(OrderItem(menu_item_id="M01", item_name="Cà phê", unit_price=25000, quantity=1))
        order.add_item(OrderItem(menu_item_id="M02", item_name="Trà đào", unit_price=35000, quantity=2))
        assert order.total_amount == 25000 + 70000

        # Cập nhật số lượng món M02 thành 1
        order.update_item_quantity("M02", 1)
        assert order.total_amount == 25000 + 35000

        # Xóa món M01
        assert order.remove_item("M01") is True
        assert len(order.items) == 1
        assert order.total_amount == 35000

    def test_discount_calculation(self):
        """Kiểm tra áp dụng voucher giảm giá."""
        order = Order(id="ORD-20261016-004", table_id=4)
        order.add_item(OrderItem(menu_item_id="M01", item_name="Món 1", unit_price=100000, quantity=1))
        assert order.final_amount == 100000

        order.set_discount(20000)
        assert order.discount_amount == 20000
        assert order.final_amount == 80000

        # Giảm giá vượt tổng tiền -> final_amount tối thiểu là 0
        order.set_discount(150000)
        assert order.final_amount == 0

    def test_status_transitions(self):
        """Kiểm tra luồng chuyển đổi trạng thái (FSM)."""
        order = Order(id="ORD-20261016-005", table_id=5)
        assert order.status == OrderStatus.PENDING

        # PENDING -> PREPARING (Hợp lệ)
        assert order.change_status(OrderStatus.PREPARING) is True
        assert order.is_preparing is True

        # PREPARING -> COMPLETED (Không hợp lệ, phải qua SERVED)
        assert order.change_status(OrderStatus.COMPLETED) is False
        assert order.status == OrderStatus.PREPARING

        # PREPARING -> SERVED (Hợp lệ)
        assert order.change_status(OrderStatus.SERVED) is True
        assert order.is_served is True

        # SERVED -> COMPLETED (Hợp lệ)
        assert order.change_status(OrderStatus.COMPLETED) is True
        assert order.is_completed is True
        assert order.is_active is False
        assert order.can_modify is False

        # Đơn đã COMPLETED thì không được sửa món
        with pytest.raises(ValueError):
            order.add_item(OrderItem(menu_item_id="M01", item_name="Món", unit_price=10000, quantity=1))


# =====================================================================
# 3. KIỂM THỬ TASK 7.2: OrderService
# =====================================================================
class TestOrderService:
    @pytest.fixture
    def service_with_tmp_storage(self):
        """Fixture tạo môi trường test file tạm độc lập."""
        with TemporaryDirectory() as tmp_dir:
            orders_path = Path(tmp_dir) / "orders.json"
            payments_path = Path(tmp_dir) / "payments.json"

            # Khởi tạo payments.json với 1 đơn đã thanh toán thành công
            payments_data = [
                {
                    "id": "PAY-20261014-001",
                    "order_id": "ORD-20261014-003",
                    "table_id": 1,
                    "payment_time": "2026-10-14T19:20:00",
                    "amount_paid": 25000,
                    "method": "CASH",
                    "status": "SUCCESS",
                    "cashier_name": "Vy"
                }
            ]
            with open(payments_path, "w", encoding="utf-8") as f:
                json.dump(payments_data, f)

            service = OrderService(
                orders_file=orders_path,
                payments_file=payments_path,
                auto_load=True
            )
            yield service

    def test_generate_order_id(self, service_with_tmp_storage):
        """Kiểm tra sinh mã đơn tự động theo thứ tự."""
        id1 = service_with_tmp_storage.generate_order_id("20261016")
        assert id1 == "ORD-20261016-001"

        # Tạo đơn với mã id1
        service_with_tmp_storage.create_order(table_id=1, custom_order_id=id1)

        id2 = service_with_tmp_storage.generate_order_id("20261016")
        assert id2 == "ORD-20261016-002"

    def test_create_and_confirm_order(self, service_with_tmp_storage):
        """Kiểm tra tạo đơn và xác nhận đơn."""
        item = OrderItem(menu_item_id="M01", item_name="Cà phê đen đá", unit_price=25000, quantity=2)
        order = service_with_tmp_storage.create_order(table_id=3, items=[item], notes="Giao nhanh")

        assert order.status == OrderStatus.PENDING
        assert order.table_id == 3
        assert order.total_amount == 50000

        # Xác nhận đơn thành công -> chuyển sang PREPARING
        assert service_with_tmp_storage.confirm_order(order.id) is True
        assert order.status == OrderStatus.PREPARING

    def test_find_order_by_id_and_by_table(self, service_with_tmp_storage):
        """Kiểm tra tìm đơn theo mã và theo bàn."""
        order1 = service_with_tmp_storage.create_order(
            table_id=5,
            items=[OrderItem(menu_item_id="M02", item_name="Trà", unit_price=30000, quantity=1)]
        )

        found_order = service_with_tmp_storage.get_order_by_id(order1.id)
        assert found_order is not None
        assert found_order.id == order1.id

        orders_table_5 = service_with_tmp_storage.get_orders_by_table(5)
        assert len(orders_table_5) == 1
        assert orders_table_5[0].id == order1.id

        active_order = service_with_tmp_storage.get_active_order_by_table(5)
        assert active_order is not None
        assert active_order.id == order1.id

    def test_prevent_duplicate_payment(self, service_with_tmp_storage):
        """
        Kiểm tra nghiệp vụ quan trọng: Tránh thanh toán trùng lặp.
        """
        # Đơn 1: Đã thanh toán (có trong payments.json với status SUCCESS)
        order_paid = service_with_tmp_storage.create_order(
            table_id=1,
            custom_order_id="ORD-20261014-003",
            items=[OrderItem(menu_item_id="M01", item_name="Cà phê", unit_price=25000, quantity=1)]
        )
        assert service_with_tmp_storage.is_order_paid(order_paid.id) is True
        allowed, reason = service_with_tmp_storage.can_checkout(order_paid.id)
        assert allowed is False
        assert "trước đó" in reason or "trùng" in reason

        # Đơn 2: Đơn mới chưa thanh toán
        order_new = service_with_tmp_storage.create_order(
            table_id=2,
            items=[OrderItem(menu_item_id="M02", item_name="Trà đào", unit_price=35000, quantity=1)]
        )
        assert service_with_tmp_storage.is_order_paid(order_new.id) is False
        allowed, _ = service_with_tmp_storage.can_checkout(order_new.id)
        assert allowed is True

        # Sau khi hoàn tất thanh toán lần đầu -> đánh dấu COMPLETED
        assert service_with_tmp_storage.complete_order(order_new.id) is True
        assert order_new.status == OrderStatus.COMPLETED

        # Kiểm tra lại: Không thể thanh toán lần 2 (chống thanh toán trùng)
        assert service_with_tmp_storage.is_order_paid(order_new.id) is True
        allowed2, reason2 = service_with_tmp_storage.can_checkout(order_new.id)
        assert allowed2 is False
        assert "trùng" in reason2

    def test_cancel_order(self, service_with_tmp_storage):
        """Kiểm tra hủy đơn hàng."""
        order = service_with_tmp_storage.create_order(table_id=4)
        assert service_with_tmp_storage.cancel_order(order.id, reason="Khách đổi ý") is True
        assert order.status == OrderStatus.CANCELLED
        assert "[Hủy: Khách đổi ý]" in order.notes

        # Không thể thanh toán đơn đã hủy
        allowed, reason = service_with_tmp_storage.can_checkout(order.id)
        assert allowed is False
        assert "bị hủy" in reason

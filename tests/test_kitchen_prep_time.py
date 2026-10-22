from src.core.KitchenManager import KitchenManager
from src.models.Order import Order
import json

from src.core.OrderService import OrderService
from src.core.PaymentService import PaymentService
from src.core.TableManager import TableManager
from src.models.OrderItem import OrderItem

def test_order_prep_time_uses_each_items_quantity():
    order = Order(
        "A",
        items=[
            {"menu_item_id": "M01", "quantity": 2, "prep_time": 5},
            {"menu_item_id": "M02", "quantity": 3, "prep_time": 4},
        ],
    )

    assert order.calculate_prep_time() == 22


def test_wait_time_includes_current_and_earlier_queued_orders():
    kitchen = KitchenManager()
    current = Order("A", items=[{"menu_item_id": "M01", "quantity": 2, "prep_time": 5}])
    waiting = Order("B", items=[{"menu_item_id": "M02", "sl": 1, "prep_time": 4}])
    kitchen.add_order(current)
    kitchen.start_next_order()
    kitchen.add_order(waiting)

    new_order = Order("C", items=[{"menu_item_id": "M03", "sl": 3, "prep_time": 6}])
    estimate = kitchen.estimate_wait_time(new_order)

    assert estimate == 32
    kitchen.add_order(new_order)
    assert kitchen.count_waiting() == 2
    assert kitchen.peek_next_order() is waiting


def test_order_kitchen_payment_and_table_lifecycle(tmp_path):
    orders_file = tmp_path / "orders.json"
    payments_file = tmp_path / "payments.json"
    invoices_file = tmp_path / "invoices.json"
    tables_file = tmp_path / "tables.json"
    tables_file.write_text(
        json.dumps(
            [
                {
                    "id": 1,
                    "name": "Table 1",
                    "capacity": 2,
                    "status": "AVAILABLE",
                    "current_order_id": None,
                }
            ]
        ),
        encoding="utf-8",
    )
    kitchen = KitchenManager()
    table_manager = TableManager(tables_file=tables_file)
    order_service = OrderService(
        orders_file=orders_file,
        payments_file=payments_file,
        table_manager=table_manager,
        kitchen_manager=kitchen,
    )

    order = order_service.create_order(
        table_id=1,
        items=[
            OrderItem(
                menu_item_id="M01",
                item_name="Coffee",
                unit_price=10000,
                quantity=2,
                prep_time=5,
            )
        ],
        check_existing_active=True,
    )
    assert order.status == "PENDING"
    assert not table_manager.is_table_available(1)
    assert order_service.confirm_order(order.id)
    assert kitchen.count_waiting() == 1
    assert kitchen.estimate_wait_time(order) == 10

    assert kitchen.start_next_order() is order
    assert order.status == "PREPARING"
    assert order_service.save_orders()
    assert kitchen.advance_status() == "SERVED"
    assert kitchen.finish_current_order() is order
    assert order_service.save_orders()

    result = PaymentService(
        payments_path=payments_file,
        invoices_path=invoices_file,
        orders_path=orders_file,
        tables_path=tables_file,
    ).pay_order(order.id, "CASH", "Cashier", cash_received=20000)

    assert result.invoice is not None
    persisted_order = json.loads(orders_file.read_text(encoding="utf-8"))[0]
    assert persisted_order["status"] == "COMPLETED"
    assert persisted_order["total_amount"] == 20000
    assert persisted_order["items"][0]["prep_time"] == 5
    assert json.loads(tables_file.read_text(encoding="utf-8"))[0]["status"] == "AVAILABLE"


def test_kitchen_restore_orders():
    kitchen = KitchenManager()
    order_preparing = Order("ORD-0001", items=[{"menu_item_id": "M01", "quantity": 1, "prep_time": 5}], status="PREPARING")
    order_pending1 = Order("ORD-0002", items=[{"menu_item_id": "M02", "quantity": 2, "prep_time": 3}], status="PENDING", created_at="2026-10-20T01:00:00")
    order_pending2 = Order("ORD-0003", items=[{"menu_item_id": "M03", "quantity": 1, "prep_time": 4}], status="PENDING", created_at="2026-10-20T01:05:00")
    order_completed = Order("ORD-0004", items=[{"menu_item_id": "M04", "quantity": 1, "prep_time": 2}], status="COMPLETED")

    orders_list = [order_completed, order_pending2, order_preparing, order_pending1]
    kitchen.restore_orders(orders_list)

    assert kitchen.get_current_order() is order_preparing
    assert kitchen.count_waiting() == 2
    assert kitchen.peek_next_order() is order_pending1
    waiting = kitchen.get_waiting_orders()
    assert waiting[0] is order_pending1
    assert waiting[1] is order_pending2


from KitchenManage import KitchenManager, Order
import json

from src.core.OrderService import OrderService
from src.core.PaymentService import PaymentService
from src.core.TableManager import TableManager
from src.models.OrderItem import OrderItem

def test_order_prep_time_uses_each_items_quantity():
    order = Order(
        "A",
        items=[
            {"quantity": 2, "prep_time": 5},
            {"quantity": 3, "prep_time": 4},
        ],
    )

    assert order.calculate_prep_time() == 22


def test_wait_time_includes_current_and_earlier_queued_orders():
    kitchen = KitchenManager()
    current = Order("A", items=[{"quantity": 2, "prep_time": 5}])
    waiting = Order("B", items=[{"sl": 1, "prep_time": 4}])
    kitchen.add_order(current)
    kitchen.start_next_order()
    kitchen.add_order(waiting)

    estimate = kitchen.receive_order(
        table_id="Bàn số 1",
        items={"M03": {"sl": 3, "prep_time": 6}},
    )

    assert estimate == 32
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

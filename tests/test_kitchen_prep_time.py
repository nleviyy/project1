import json
from datetime import datetime, timedelta

from src.core.KitchenManager import KitchenManager
from src.models.Order import Order
from src.models.OrderItem import OrderItem

from src.core.OrderService import OrderService
from src.core.PaymentService import PaymentService
from src.core.TableManager import TableManager

def test_order_prep_time_uses_each_items_quantity():
    order = Order(
        id="A",
        table_id=0,
        items=[
            OrderItem(
                menu_item_id="M01",
                item_name="Món 1",
                unit_price=0,
                quantity=2,
                prep_time=5,
            ),
            OrderItem(
                menu_item_id="M02",
                item_name="Món 2",
                unit_price=0,
                quantity=3,
                prep_time=4,
            ),
        ],
    )

    assert order.calculate_prep_time() == 22


def test_wait_time_includes_current_and_earlier_queued_orders():
    kitchen = KitchenManager()
    current = Order(
        id="A",
        table_id=0,
        items=[
            OrderItem(
                menu_item_id="M01",
                item_name="Món 1",
                unit_price=0,
                quantity=2,
                prep_time=5,
            )
        ],
    )
    waiting = Order(
        id="B",
        table_id=0,
        items=[
            OrderItem(
                menu_item_id="M02",
                item_name="Món 2",
                unit_price=0,
                quantity=1,
                prep_time=4,
            )
        ],
    )
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
    received_order = kitchen.get_waiting_orders()[1]
    assert isinstance(received_order, Order)
    assert received_order.calculate_prep_time() == 18


def test_wait_time_uses_elapsed_time_for_current_order():
    kitchen = KitchenManager()
    current = Order(
        id="CURRENT",
        table_id=0,
        items=[
            OrderItem(
                menu_item_id="M01",
                item_name="Món 1",
                unit_price=0,
                quantity=1,
                prep_time=5,
            )
        ],
        status="PREPARING",
        preparing_started_at=(
            datetime.now() - timedelta(minutes=2)
        ).isoformat(timespec="seconds"),
    )
    waiting = Order(
        id="WAITING",
        table_id=0,
        items=[
            OrderItem(
                menu_item_id="M02",
                item_name="Món 2",
                unit_price=0,
                quantity=1,
                prep_time=4,
            )
        ],
    )
    kitchen.restore_orders([current, waiting])

    assert kitchen.estimate_wait_time(current) == 3
    assert kitchen.estimate_wait_time(waiting) == 7


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
                unit_price=25000,
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

    assert order_service.start_preparing_order(order.id)
    assert order.status == "PREPARING"
    assert order.preparing_started_at is not None
    assert order_service.serve_order(order.id)
    assert order.status == "SERVED"
    assert kitchen.get_current_order() is None

    result = PaymentService(
        payments_path=payments_file,
        invoices_path=invoices_file,
        orders_path=orders_file,
        tables_path=tables_file,
    ).pay_order(order.id, "CASH", "Cashier", cash_received=50000)

    assert result.invoice is not None
    persisted_order = json.loads(orders_file.read_text(encoding="utf-8"))[0]
    assert persisted_order["status"] == "COMPLETED"
    assert persisted_order["total_amount"] == 50000
    assert persisted_order["items"][0]["prep_time"] == 5
    assert json.loads(tables_file.read_text(encoding="utf-8"))[0]["status"] == "AVAILABLE"


def test_kitchen_restore_orders():
    kitchen = KitchenManager()
    order_preparing = Order(
        id="ORD-0001",
        table_id=1,
        items=[
            {
                "menu_item_id": "M01",
                "item_name": "Món 1",
                "unit_price": 0,
                "quantity": 1,
                "prep_time": 5,
            }
        ],
        status="PREPARING",
    )
    order_pending1 = Order(
        id="ORD-0002",
        table_id=1,
        items=[
            {
                "menu_item_id": "M02",
                "item_name": "Món 2",
                "unit_price": 0,
                "quantity": 2,
                "prep_time": 3,
            }
        ],
        status="PENDING",
        created_at="2026-10-20T01:00:00",
    )
    order_pending2 = Order(
        id="ORD-0003",
        table_id=1,
        items=[
            {
                "menu_item_id": "M03",
                "item_name": "Món 3",
                "unit_price": 0,
                "quantity": 1,
                "prep_time": 4,
            }
        ],
        status="PENDING",
        created_at="2026-10-20T01:05:00",
    )
    order_completed = Order(
        id="ORD-0004",
        table_id=1,
        items=[
            {
                "menu_item_id": "M04",
                "item_name": "Món 4",
                "unit_price": 0,
                "quantity": 1,
                "prep_time": 2,
            }
        ],
        status="COMPLETED",
    )

    kitchen.restore_orders(
        [order_completed, order_pending2, order_preparing, order_pending1]
    )

    assert kitchen.get_current_order() is order_preparing
    assert kitchen.count_waiting() == 2
    assert kitchen.peek_next_order() is order_pending1
    assert kitchen.get_waiting_orders() == [order_pending1, order_pending2]


def test_preparing_start_timestamp_survives_order_serialization():
    started_at = "2026-10-20T10:00:00"
    order = Order(
        id="ORD-PREPARING",
        table_id=0,
        status="PREPARING",
        preparing_started_at=started_at,
    )

    restored = Order.from_dict(order.to_dict())

    assert restored.preparing_started_at == started_at

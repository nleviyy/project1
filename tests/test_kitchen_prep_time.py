from src.core.KitchenManager import KitchenManager
from src.models.Order import Order
from src.models.OrderItem import OrderItem


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

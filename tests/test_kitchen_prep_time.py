from kitchen import KitchenManager, Order


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

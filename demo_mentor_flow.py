import json
from pathlib import Path
from tempfile import TemporaryDirectory

from src.core.Cart import Cart
from src.core.KitchenManager import KitchenManager
from src.core.OrderService import OrderService
from src.core.PaymentService import PaymentService
from src.core.TableManager import TableManager
from src.models.MenuCatalog import MenuCatalog
from src.models.OrderItem import OrderItem


def main() -> None:
    menu = MenuCatalog()
    if not menu.load_from_file():
        raise FileNotFoundError("Không thể tải data/menu.json.")

    cart = Cart()
    coffee = menu.get_item("M01")
    if coffee is None or not coffee.is_available:
        raise ValueError("Món M01 không tồn tại hoặc đã hết.")
    cart.add_item(coffee, quantity=2, note="Ít đường")
    cart.undo()
    cart.redo()

    cart_items = [
        OrderItem(
            menu_item_id=item["menu_item_id"],
            item_name=item["item_name"],
            unit_price=item["unit_price"],
            quantity=item["quantity"],
            note=item["note"],
            prep_time=item.get("prep_time", 0),
        )
        for item in cart.get_order_items()
    ]

    with TemporaryDirectory() as directory:
        data_dir = Path(directory)
        tables_path = data_dir / "tables.json"
        tables_path.write_text(
            json.dumps(
                [
                    {
                        "id": 1,
                        "name": "Bàn demo",
                        "capacity": 2,
                        "status": "AVAILABLE",
                        "current_order_id": None,
                    }
                ]
            ),
            encoding="utf-8",
        )
        kitchen = KitchenManager()
        tables = TableManager(tables_file=str(tables_path))
        orders_path = data_dir / "orders.json"
        payments_path = data_dir / "payments.json"
        invoices_path = data_dir / "invoices.json"
        orders = OrderService(
            orders_file=orders_path,
            payments_file=payments_path,
            table_manager=tables,
            kitchen_manager=kitchen,
        )

        order = orders.create_order(table_id=1, items=cart_items)
        assert orders.confirm_order(order.id)
        assert orders.start_preparing_order(order.id)
        assert orders.serve_order(order.id)

        payment = PaymentService(
            payments_path=payments_path,
            invoices_path=invoices_path,
            orders_path=orders_path,
            tables_path=tables_path,
        ).pay_order(
            order.id,
            method="CASH",
            cashier_name="Thu ngân demo",
            cash_received=order.final_amount,
        )
        assert payment.invoice is not None
        assert payment.payment.is_successful
        orders.load_orders()
        tables.load_tables()
        completed_order = orders.get_order_by_id(order.id)
        assert completed_order is not None and completed_order.status == "COMPLETED"
        assert tables.is_table_available(1)

        print(f"Đơn {order.id}: {completed_order.status}")
        print(payment.invoice.generate_text_receipt())


if __name__ == "__main__":
    main()

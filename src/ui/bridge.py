import json
from pathlib import Path
import sys
from src.core.sorting import merge_sort

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _load_json(path: Path, default: list) -> list:
    try:
        with path.open(encoding="utf-8") as source:
            value = json.load(source)
    except FileNotFoundError:
        return default
    if not isinstance(value, list):
        raise ValueError(f"{path.name} chứa dữ liệu không đúng định dạng.")
    return value


def _make_runtime(data_directory: Path):
    from src.core.KitchenManager import KitchenManager
    from src.core.OrderService import OrderService
    from src.core.TableManager import TableManager

    table_manager = TableManager(tables_file=data_directory / "tables.json")
    kitchen_manager = KitchenManager()
    order_service = OrderService(
        orders_file=data_directory / "orders.json",
        payments_file=data_directory / "payments.json",
        table_manager=table_manager,
        kitchen_manager=kitchen_manager,
    )
    kitchen_manager.restore_orders(order_service.get_all_orders())
    return order_service, table_manager, kitchen_manager


def handle(request: dict, data_directory: Path) -> list | dict | None:
    operation = request.get("operation")

    if operation == "menu":
        from src.models.MenuCatalog import MenuCatalog

        raw_menu = _load_json(data_directory / "menu.json", [])
        catalog = MenuCatalog()
        catalog.load_from_dict(raw_menu)
        if len(catalog.get_all_items()) != len(raw_menu):
            raise ValueError("Thực đơn có dữ liệu không hợp lệ hoặc mã món bị trùng.")
        return catalog.to_dict()

    if operation == "tables":
        from src.core.TableManager import TableManager

        manager = TableManager(tables_file=data_directory / "tables.json")
        return [table.to_dict() for table in manager.get_all_tables()]

    if operation == "payments":
        return _load_json(data_directory / "payments.json", [])

    if operation == "orders":
        order_service, _, kitchen_manager = _make_runtime(data_directory)
        orders = merge_sort(
            order_service.get_all_orders(),
            key=lambda order: str(order.created_at),
            reverse=True,
        )
        records = []
        for order in orders:
            record = order.to_dict()
            record["estimated_wait_minutes"] = (
                kitchen_manager.estimate_wait_time(order)
                if order.status in ("PENDING", "PREPARING")
                else 0
            )
            records.append(record)
        return records

    if operation == "create_order":
        from src.models.MenuCatalog import MenuCatalog
        from src.models.OrderItem import OrderItem

        table_id = request.get("table_id")
        inputs = request.get("items")
        if (
            not isinstance(table_id, (int, str))
            or isinstance(table_id, bool)
            or not isinstance(inputs, list)
            or not inputs
        ):
            raise ValueError("Cần chọn bàn và ít nhất một món hợp lệ.")

        raw_menu = _load_json(data_directory / "menu.json", [])
        catalog = MenuCatalog()
        catalog.load_from_dict(raw_menu)
        order_items = []
        for item in inputs:
            if (
                not isinstance(item, dict)
                or not isinstance(item.get("menu_item_id"), str)
                or isinstance(item.get("quantity"), bool)
                or not isinstance(item.get("quantity"), int)
                or item["quantity"] <= 0
                or not isinstance(item.get("note", ""), str)
            ):
                raise ValueError(
                    "Mỗi món cần mã món, số lượng nguyên dương và ghi chú hợp lệ."
                )
            menu_item = catalog.get_item(item["menu_item_id"])
            if menu_item is None or not menu_item.is_available:
                raise ValueError(
                    f"Món '{item['menu_item_id']}' không tồn tại hoặc đã hết."
                )
            order_items.append(
                OrderItem(
                    menu_item_id=menu_item.id,
                    item_name=menu_item.name,
                    unit_price=menu_item.price,
                    quantity=item["quantity"],
                    note=item.get("note", ""),
                    prep_time=menu_item.prep_time or 0,
                )
            )

        order_service, table_manager, kitchen_manager = _make_runtime(data_directory)
        order = order_service.place_order(
            table_id=table_id,
            items=order_items,
            notes=request.get("notes", ""),
            table_manager=table_manager,
            kitchen_manager=kitchen_manager,
        )
        record = order.to_dict()
        record["estimated_wait_minutes"] = kitchen_manager.estimate_wait_time(order)
        return record

    if operation in ("start_next_order", "finish_current_order", "cancel_order"):
        order_service, _, kitchen_manager = _make_runtime(data_directory)
        if operation == "start_next_order":
            order = kitchen_manager.start_next_order()
            if order is None:
                return None
        elif operation == "finish_current_order":
            order = kitchen_manager.get_current_order()
            if order is None:
                raise ValueError("Bếp chưa có đơn đang chế biến.")
            kitchen_manager.advance_status()
            order = kitchen_manager.finish_current_order()
        else:
            order_id = request.get("order_id")
            if not isinstance(order_id, str) or not order_id:
                raise ValueError("Mã đơn hàng không hợp lệ.")
            order_service.cancel_order(
                order_id,
                reason=request.get("reason", ""),
                kitchen_manager=kitchen_manager,
            )
            order = order_service.get_order_by_id(order_id)
            if order is None:
                raise ValueError(f"Không tìm thấy đơn hàng '{order_id}'.")
            return order.to_dict()

        if not order_service.save_orders():
            raise OSError(f"Không thể lưu trạng thái đơn '{order.id}'.")
        return order.to_dict()

    if operation == "pay_order":
        from src.core.PaymentService import PaymentService

        service = PaymentService(
            payments_path=data_directory / "payments.json",
            invoices_path=data_directory / "invoices.json",
            orders_path=data_directory / "orders.json",
            tables_path=data_directory / "tables.json",
        )
        result = service.pay_order(
            order_id=request.get("order_id"),
            method=request.get("method"),
            cashier_name=request.get("cashier_name"),
            cash_received=request.get("cash_received"),
            transaction_code=request.get("transaction_code"),
            transaction_successful=request.get("transaction_successful"),
        )
        return {
            "payment": result.payment.model_dump(mode="json"),
            "invoice": result.invoice.model_dump(mode="json")
            if result.invoice
            else None,
        }

    raise ValueError("Thao tác không được hỗ trợ.")

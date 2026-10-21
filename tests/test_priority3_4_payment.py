import json
import threading
import pytest
from pathlib import Path

from src.core.PaymentService import PaymentService
from src.core.TableManager import TableManager
from src.core.OrderService import OrderService
from src.models.Payment import PaymentMethod
from src.models.Table import Table


def setup_test_environment(tmp_path):
    tables_file = tmp_path / "tables.json"
    orders_file = tmp_path / "orders.json"
    payments_file = tmp_path / "payments.json"
    invoices_file = tmp_path / "invoices.json"

    tables = [
        {"id": 1, "name": "Bàn 01", "capacity": 4, "status": "OCCUPIED", "current_order_id": "ORD-001"}
    ]
    orders = [
        {
            "id": "ORD-001",
            "table_id": 1,
            "status": "SERVED",
            "items": [{"menu_item_id": "M01", "item_name": "Cà phê", "unit_price": 25000, "quantity": 2, "subtotal": 50000}],
            "total_amount": 50000,
            "discount_amount": 0,
            "final_amount": 50000,
        }
    ]
    tables_file.write_text(json.dumps(tables), encoding="utf-8")
    orders_file.write_text(json.dumps(orders), encoding="utf-8")
    payments_file.write_text(json.dumps([]), encoding="utf-8")
    invoices_file.write_text(json.dumps([]), encoding="utf-8")

    tm = TableManager(tables_file=tables_file, auto_load=True)
    os_service = OrderService(orders_file=orders_file, payments_file=payments_file, auto_load=True, table_manager=tm)

    ps = PaymentService(
        payments_path=payments_file,
        invoices_path=invoices_file,
        orders_path=orders_file,
        tables_path=tables_file,
        table_manager=tm,
        order_service=os_service,
    )
    return tm, os_service, ps


def test_payment_updates_live_table_manager_and_order_service(tmp_path):
    """
    Thanh toán một đơn xong, TableManager trong bộ nhớ thấy bàn ở trạng thái AVAILABLE;
    gọi lưu bàn sau đó không làm mất kết quả.
    """
    tm, os_service, ps = setup_test_environment(tmp_path)

    # Trước thanh toán: bàn OCCUPIED
    assert tm.get_table(1).status == "OCCUPIED"

    # Thanh toán
    result = ps.pay_order(
        order_id="ORD-001",
        method=PaymentMethod.CASH,
        cashier_name="Thu ngân 1",
        cash_received=50000,
    )
    assert result.payment.is_successful is True

    # Sau thanh toán: TableManager trong bộ nhớ thấy bàn AVAILABLE
    assert tm.get_table(1).status == "AVAILABLE"
    assert tm.get_table(1).current_order_id is None

    # OrderService trong bộ nhớ thấy đơn COMPLETED
    assert os_service.get_order("ORD-001").status == "COMPLETED"

    # Gọi save_tables sau đó vẫn giữ nguyên AVAILABLE trên đĩa
    tm.save_tables()
    reloaded_tm = TableManager(tables_file=tm.tables_file, auto_load=True)
    assert reloaded_tm.get_table(1).status == "AVAILABLE"


def test_concurrent_pay_order_prevents_duplicate_payment(tmp_path):
    """
    Gọi pay_order hai lần song song trên cùng order_id bằng threading:
    đúng một lần SUCCESS, lần còn lại ném ValueError.
    """
    tm, os_service, ps = setup_test_environment(tmp_path)

    results = []
    errors = []

    def _worker():
        try:
            res = ps.pay_order(
                order_id="ORD-001",
                method=PaymentMethod.CASH,
                cashier_name="Thu ngân Concurrent",
                cash_received=50000,
            )
            results.append(res)
        except Exception as err:
            errors.append(err)

    t1 = threading.Thread(target=_worker)
    t2 = threading.Thread(target=_worker)

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    # Đúng một lần thành công và một lần gặp ValueError
    assert len(results) == 1
    assert results[0].payment.is_successful is True
    assert len(errors) == 1
    assert isinstance(errors[0], ValueError)
    assert "đã được thanh toán" in str(errors[0])


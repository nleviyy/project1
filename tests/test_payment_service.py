import json
import os
from pathlib import Path

import pytest

from src.core.PaymentService import PaymentService
from src.models.Order import Order
from src.models.Payment import Payment


def build_service(tmp_path, *, status="SERVED"):
    paths = {
        "payments_path": tmp_path / "payments.json",
        "invoices_path": tmp_path / "invoices.json",
        "orders_path": tmp_path / "orders.json",
        "tables_path": tmp_path / "tables.json",
    }
    paths["payments_path"].write_text("[]", encoding="utf-8")
    paths["invoices_path"].write_text("[]", encoding="utf-8")
    paths["orders_path"].write_text(
        json.dumps(
            [
                {
                    "id": "ORD-1",
                    "table_id": 1,
                    "status": status,
                    "items": [
                        {
                            "menu_item_id": "M1",
                            "item_name": "Coffee",
                            "unit_price": 10000,
                            "quantity": 2,
                            "subtotal": 20000,
                            "note": "",
                        }
                    ],
                    "total_amount": 20000,
                    "discount_amount": 2000,
                    "final_amount": 18000,
                }
            ]
        ),
        encoding="utf-8",
    )
    paths["tables_path"].write_text(
        json.dumps(
            [
                {
                    "id": 1,
                    "name": "Table 1",
                    "capacity": 2,
                    "status": "OCCUPIED",
                    "current_order_id": "ORD-1",
                }
            ]
        ),
        encoding="utf-8",
    )
    return PaymentService(**paths), paths


@pytest.mark.parametrize(
    ("method", "kwargs"),
    [
        ("CASH", {"cash_received": 20000}),
        ("BANK_TRANSFER", {"transaction_successful": True}),
        ("CARD", {"transaction_successful": True}),
    ],
)
def test_successful_payment_creates_invoice_completes_order_and_releases_table(
    tmp_path, method, kwargs
):
    service, paths = build_service(tmp_path)

    result = service.pay_order("ORD-1", method, "Cashier", **kwargs)

    assert result.payment.status == "SUCCESS"
    assert result.payment.amount_paid == 18000
    assert result.payment.amount == 20000
    assert result.payment.discount_rate == 0.1
    assert result.invoice is not None
    assert result.invoice.total_amount == 18000
    assert result.payment.change_due == (2000 if method == "CASH" else 0)
    assert json.loads(paths["orders_path"].read_text(encoding="utf-8"))[0]["status"] == "COMPLETED"
    table = json.loads(paths["tables_path"].read_text(encoding="utf-8"))[0]
    assert table["status"] == "AVAILABLE"
    assert table["current_order_id"] is None
    assert len(json.loads(paths["invoices_path"].read_text(encoding="utf-8"))) == 1
    saved_payment = json.loads(
        paths["payments_path"].read_text(encoding="utf-8")
    )[0]
    assert set(saved_payment) == {
        "id", "order_id", "table_id", "payment_time", "amount", "discount_rate",
        "amount_paid", "method", "status", "cashier_name", "transaction_code",
        "note", "cash_received", "change_due",
    }
    assert Payment.model_validate(saved_payment).amount_paid == 18000


def test_successful_payment_rolls_back_all_files_if_a_write_fails(
    tmp_path, monkeypatch
):
    service, paths = build_service(tmp_path)
    originals = {
        path: path.read_bytes()
        for path in paths.values()
    }
    real_replace = os.replace
    failed = False

    def fail_orders_replacement(source, destination):
        nonlocal failed
        if Path(destination) == paths["orders_path"] and not failed:
            failed = True
            raise OSError("simulated replace failure")
        return real_replace(source, destination)

    monkeypatch.setattr(
        "src.core.PaymentService.os.replace",
        fail_orders_replacement,
    )

    with pytest.raises(OSError, match="simulated replace failure"):
        service.pay_order(
            "ORD-1", "CARD", "Cashier", transaction_successful=True
        )

    assert all(path.read_bytes() == contents for path, contents in originals.items())


def test_failed_electronic_payment_does_not_complete_or_release_table(tmp_path):
    service, paths = build_service(tmp_path)

    result = service.pay_order(
        "ORD-1", "BANK_TRANSFER", "Cashier", transaction_successful=False
    )

    assert result.payment.status == "FAILED"
    assert result.payment.amount_paid == 0
    assert result.invoice is None
    assert json.loads(paths["orders_path"].read_text(encoding="utf-8"))[0]["status"] == "SERVED"
    assert json.loads(paths["tables_path"].read_text(encoding="utf-8"))[0]["status"] == "OCCUPIED"
    assert json.loads(paths["invoices_path"].read_text(encoding="utf-8")) == []


def test_successful_payment_cannot_be_recorded_twice(tmp_path):
    service, _ = build_service(tmp_path)
    service.pay_order("ORD-1", "CARD", "Cashier", transaction_successful=True)

    with pytest.raises(ValueError, match="đã được thanh toán thành công"):
        service.pay_order("ORD-1", "CARD", "Cashier", transaction_successful=True)


def test_cash_payment_rejects_insufficient_tender_without_writing(tmp_path):
    service, paths = build_service(tmp_path)

    with pytest.raises(ValueError, match="đủ thanh toán"):
        service.pay_order("ORD-1", "CASH", "Cashier", cash_received=17999)

    assert json.loads(paths["payments_path"].read_text(encoding="utf-8")) == []


def test_payment_is_only_allowed_after_order_is_served(tmp_path):
    service, paths = build_service(tmp_path, status="PREPARING")

    with pytest.raises(ValueError, match="trạng thái SERVED"):
        service.pay_order("ORD-1", "CARD", "Cashier", transaction_successful=True)

    assert json.loads(paths["payments_path"].read_text(encoding="utf-8")) == []


def test_electronic_payment_requires_processor_result(tmp_path):
    service, paths = build_service(tmp_path)

    with pytest.raises(ValueError, match="cổng thanh toán"):
        service.pay_order("ORD-1", "CARD", "Cashier")

    assert json.loads(paths["payments_path"].read_text(encoding="utf-8")) == []


def test_payment_does_not_complete_order_when_table_is_not_associated(tmp_path):
    service, paths = build_service(tmp_path)
    paths["tables_path"].write_text(
        json.dumps(
            [
                {
                    "id": 1,
                    "name": "Table 1",
                    "capacity": 2,
                    "status": "OCCUPIED",
                    "current_order_id": "ORD-OTHER",
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="không được liên kết"):
        service.pay_order(
            "ORD-1", "CARD", "Cashier", transaction_successful=True
        )

    assert json.loads(paths["payments_path"].read_text(encoding="utf-8")) == []
    assert json.loads(paths["orders_path"].read_text(encoding="utf-8"))[0]["status"] == "SERVED"


def test_order_requires_matching_successful_payment_to_complete():
    order = Order(id="ORD-1", table_id=1, status="SERVED")
    failed = Payment(
        payment_id="PAY-1",
        order_id="ORD-1",
        table_id=1,
        amount=1000,
        amount_paid=0,
        status="FAILED",
        cashier_name="Cashier",
    )
    successful_for_other_order = Payment(
        payment_id="PAY-2",
        order_id="ORD-2",
        table_id=1,
        amount=1000,
        amount_paid=1000,
        status="SUCCESS",
        cashier_name="Cashier",
    )

    with pytest.raises(ValueError, match="thanh toán SUCCESS"):
        order.mark_completed(failed)
    with pytest.raises(ValueError, match="thanh toán SUCCESS"):
        order.mark_completed(successful_for_other_order)

    with pytest.raises(ValueError, match="thanh toán thành công"):
        order.change_status("COMPLETED")

    successful = Payment(
        payment_id="PAY-3",
        order_id="ORD-1",
        table_id=1,
        amount=1000,
        amount_paid=1000,
        status="SUCCESS",
        cashier_name="Cashier",
    )
    assert order.mark_completed(successful)
    assert order.status == "COMPLETED"

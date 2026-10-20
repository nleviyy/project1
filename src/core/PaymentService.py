from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from src.models.Invoice import Invoice
from src.models.Payment import Payment, PaymentMethod


@dataclass(frozen=True)
class PaymentResult:
    payment: Payment
    invoice: Invoice | None


class PaymentService:
    def __init__(
        self,
        payments_path: str | Path | None = None,
        invoices_path: str | Path | None = None,
        orders_path: str | Path | None = None,
        tables_path: str | Path | None = None,
    ) -> None:
        data_dir = Path(__file__).resolve().parents[2] / "data"
        self.payments_path = Path(payments_path or data_dir / "payments.json")
        self.invoices_path = Path(invoices_path or data_dir / "invoices.json")
        self.orders_path = Path(orders_path or data_dir / "orders.json")
        self.tables_path = Path(tables_path or data_dir / "tables.json")
        self.menu_path = data_dir / "menu.json"

    def pay_order(
        self,
        order_id: str,
        method: PaymentMethod,
        cashier_name: str,
        *,
        cash_received: int | None = None,
        transaction_code: str | None = None,
        transaction_successful: bool | None = None,
    ) -> PaymentResult:
        if method not in ("CASH", "BANK_TRANSFER", "CARD"):
            raise ValueError("Phương thức thanh toán phải là CASH, BANK_TRANSFER hoặc CARD.")
        if not isinstance(cashier_name, str) or not cashier_name.strip():
            raise ValueError("Tên thu ngân không được để trống.")

        payments = self._normalize_payments(self._read_json(self.payments_path))
        invoices = self._read_json(self.invoices_path)
        orders = self._read_json(self.orders_path)
        self._normalize_order_prep_times(orders)
        tables = self._read_json(self.tables_path)
        order = next((row for row in orders if row.get("id") == order_id), None)
        if order is None:
            raise ValueError(f"Không tìm thấy đơn hàng '{order_id}'.")
        if any(
            row.get("order_id") == order_id and row.get("status") == "SUCCESS"
            for row in payments
        ):
            raise ValueError(f"Đơn hàng '{order_id}' đã được thanh toán thành công.")
        if order.get("status") != "SERVED":
            raise ValueError("Chỉ có thể thanh toán đơn ở trạng thái SERVED.")

        subtotal = self._order_subtotal(order)
        discount = self._nonnegative_int(order.get("discount_amount", 0), "Tiền giảm giá")
        total = self._nonnegative_int(
            order.get("final_amount", subtotal - discount), "Tổng thanh toán"
        )
        if discount < 0 or total < 0 or total != subtotal - discount:
            raise ValueError(f"Tổng tiền đơn hàng '{order_id}' không hợp lệ.")

        change_due = 0
        if method == "CASH":
            if (
                isinstance(cash_received, bool)
                or not isinstance(cash_received, int)
                or cash_received < total
            ):
                raise ValueError("Tiền mặt khách đưa phải là số nguyên và đủ thanh toán.")
            change_due = cash_received - total
            transaction_successful = True
        elif cash_received is not None:
            raise ValueError("cash_received chỉ được dùng cho phương thức CASH.")
        elif transaction_successful is None:
            raise ValueError(
                "Cần kết quả xác nhận từ cổng thanh toán cho chuyển khoản hoặc thẻ."
            )
        elif not isinstance(transaction_successful, bool):
            raise ValueError("Kết quả từ cổng thanh toán phải là true hoặc false.")

        status = "SUCCESS" if transaction_successful else "FAILED"
        payment = Payment(
            payment_id=f"PAY-{uuid4().hex.upper()}",
            order_id=order_id,
            table_id=order.get("table_id", "Mang về"),
            amount=subtotal,
            discount_rate=discount / subtotal if subtotal else 0,
            amount_paid=total if transaction_successful else 0,
            method=method,
            status=status,
            cashier_name=cashier_name.strip(),
            transaction_code=transaction_code,
            cash_received=cash_received if method == "CASH" else None,
            change_due=change_due if transaction_successful else 0,
        )
        payment_record = payment.to_dict()
        updated_payments = [*payments, payment_record]

        if not payment.is_successful:
            self._write_json_updates({self.payments_path: updated_payments})
            return PaymentResult(payment=payment, invoice=None)

        invoice = Invoice(
            id=f"INV-{uuid4().hex.upper()}",
            payment_id=payment.id,
            order_id=order_id,
            table_id=payment.table_id,
            items=order.get("items", []),
            subtotal=subtotal,
            discount_amount=discount,
            total_amount=total,
            payment_method=method,
            cashier_name=payment.cashier_name,
        )

        order["status"] = "COMPLETED"
        order["updated_at"] = datetime.now().isoformat(timespec="seconds")
        self._release_table(tables, order)
        self._write_json_updates(
            {
                self.payments_path: updated_payments,
                self.invoices_path: [*invoices, invoice.model_dump()],
                self.orders_path: orders,
                self.tables_path: tables,
            }
        )
        return PaymentResult(payment=payment, invoice=invoice)

    @staticmethod
    def _order_subtotal(order: dict) -> int:
        if "total_amount" in order:
            subtotal = order["total_amount"]
        else:
            subtotal = sum(
                PaymentService._nonnegative_int(item["subtotal"], "Thành tiền món")
                for item in order.get("items", [])
            )
        return PaymentService._nonnegative_int(subtotal, "Tổng tiền trước giảm giá")

    @staticmethod
    def _nonnegative_int(value: object, label: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{label} phải là số nguyên VNĐ không âm.")
        return value

    @staticmethod
    def _release_table(tables: list[dict], order: dict) -> None:
        table_id = order.get("table_id")
        if not isinstance(table_id, int) and not str(table_id).isdigit():
            return
        table = next(
            (row for row in tables if str(row.get("id")) == str(table_id)),
            None,
        )
        if table is None:
            raise ValueError(f"Không tìm thấy bàn '{table_id}' để giải phóng.")
        if (
            table.get("status") != "OCCUPIED"
            or table.get("current_order_id") != order.get("id")
        ):
            raise ValueError(
                f"Bàn '{table_id}' không được liên kết với đơn '{order.get('id')}'."
            )
        table["status"] = "AVAILABLE"
        table["current_order_id"] = None

    @staticmethod
    def _read_json(path: Path) -> list[dict]:
        try:
            with path.open(encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError:
            return []
        if not isinstance(data, list):
            raise ValueError(f"Expected a JSON list in {path}.")
        if any(not isinstance(row, dict) for row in data):
            raise ValueError(f"Expected every entry in {path} to be a JSON object.")
        return data

    @staticmethod
    def _normalize_payments(payments: list[dict]) -> list[dict]:
        normalized = []
        for payment in payments:
            payment_data = {
                **payment,
                "amount": payment.get("amount", payment.get("amount_paid", 0)),
                "discount_rate": payment.get("discount_rate", 0),
                "cash_received": payment.get("cash_received"),
                "change_due": payment.get("change_due", 0),
            }
            normalized.append(Payment.from_dict(payment_data).to_dict())
        return normalized

    def _normalize_order_prep_times(self, orders: list[dict]) -> None:
        menu_items = self._read_json(self.menu_path)
        prep_times = {
            str(item.get("id", item.get("item_id", ""))): item.get("prep_time", 0)
            for item in menu_items
        }
        for order in orders:
            items = order.get("items", [])
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                prep_time = item.get("prep_time")
                if prep_time is None:
                    prep_time = prep_times.get(str(item.get("menu_item_id", "")), 0)
                item["prep_time"] = self._nonnegative_int(
                    prep_time, "Thời gian chế biến"
                )

    @staticmethod
    def _write_json_updates(updates: dict[Path, list[dict]]) -> None:
        staged: dict[Path, Path] = {}
        originals: dict[Path, bytes | None] = {}
        replaced: list[Path] = []
        try:
            for target, data in updates.items():
                target.parent.mkdir(parents=True, exist_ok=True)
                originals[target] = target.read_bytes() if target.exists() else None
                temporary = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
                staged[target] = temporary
                temporary.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            for target, temporary in staged.items():
                os.replace(temporary, target)
                replaced.append(target)
        except OSError as write_error:
            rollback_errors = []
            for target in reversed(replaced):
                try:
                    original = originals[target]
                    if original is None:
                        target.unlink(missing_ok=True)
                    else:
                        rollback = target.with_name(
                            f".{target.name}.{uuid4().hex}.rollback"
                        )
                        rollback.write_bytes(original)
                        os.replace(rollback, target)
                except OSError as rollback_error:
                    rollback_errors.append(
                        f"{target}: {rollback_error}"
                    )
            if rollback_errors:
                raise RuntimeError(
                    f"Không thể ghi đồng bộ các file JSON ({write_error}); "
                    "lỗi khi khôi phục: " + "; ".join(rollback_errors)
                ) from write_error
            raise
        finally:
            for temporary in staged.values():
                temporary.unlink(missing_ok=True)

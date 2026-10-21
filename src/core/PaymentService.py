from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

from src.models.Invoice import Invoice, InvoiceItem
from src.models.Payment import Payment, PaymentMethod
from src.models.HashTable import HashTable
from src.core.paths import PAYMENTS_PATH, INVOICES_PATH, ORDERS_PATH, TABLES_PATH
from src.core.JSONStorage import load_data, save_data, write_json_updates
from src.core.TableManager import TableManager
from src.core.OrderService import OrderService


@dataclass(frozen=True)
class PaymentResult:
    payment: Payment
    invoice: Invoice | None


class PaymentService:
    _lock = threading.Lock()

    def __init__(
        self,
        payments_path: str | Path | None = None,
        invoices_path: str | Path | None = None,
        orders_path: str | Path | None = None,
        tables_path: str | Path | None = None,
        table_manager: Optional[TableManager] = None,
        order_service: Optional[OrderService] = None,
    ) -> None:
        self.payments_path = Path(payments_path or PAYMENTS_PATH)
        self.invoices_path = Path(invoices_path or INVOICES_PATH)
        self.orders_path = Path(orders_path or ORDERS_PATH)
        self.tables_path = Path(tables_path or TABLES_PATH)

        self.table_manager = table_manager
        self.order_service = order_service

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
        with self._lock:
            # 1. Đọc và kiểm tra tính hợp lệ của request và đơn hàng
            order_dict, payments, invoices, orders, tables = self._validate_request(
                order_id=order_id,
                method=method,
                cashier_name=cashier_name,
            )

            # 2. Thống nhất tính tổng tiền duy nhất từ order
            subtotal, discount, total = self._calculate_totals(order_dict)

            # Kiểm tra phương thức và tiền mặt khách đưa
            change_due, is_success = self._validate_payment_method(
                method=method,
                total=total,
                cash_received=cash_received,
                transaction_successful=transaction_successful,
            )

            # 3. Tạo model Payment
            payment = self._build_payment(
                order_id=order_id,
                order_dict=order_dict,
                method=method,
                cashier_name=cashier_name,
                total=total,
                is_success=is_success,
                cash_received=cash_received,
                change_due=change_due,
                transaction_code=transaction_code,
            )

            # 4. Tạo model Invoice nếu thanh toán thành công
            invoice = None
            if is_success:
                invoice = self._build_invoice(
                    payment=payment,
                    order_id=order_id,
                    order_dict=order_dict,
                    method=method,
                    subtotal=subtotal,
                    discount=discount,
                    total=total,
                )

            # 5. Lưu trữ đồng bộ (Persist)
            self._persist(
                payment=payment,
                invoice=invoice,
                order_id=order_id,
                order_dict=order_dict,
                payments=payments,
                invoices=invoices,
                orders=orders,
                tables=tables,
                is_success=is_success,
            )

            return PaymentResult(payment=payment, invoice=invoice)

    def _validate_request(
        self,
        order_id: str,
        method: Any,
        cashier_name: str,
    ) -> Tuple[dict, list, list, list, list]:
        if method not in ("CASH", "BANK_TRANSFER", "CARD"):
            raise ValueError("Phương thức thanh toán phải là CASH, BANK_TRANSFER hoặc CARD.")
        if not isinstance(cashier_name, str) or not cashier_name.strip():
            raise ValueError("Tên thu ngân không được để trống.")

        payments = self._read_json(self.payments_path)
        invoices = self._read_json(self.invoices_path)

        # Lấy orders qua OrderService nếu có, ngược lại đọc file
        if self.order_service is not None:
            orders = [o.to_dict() for o in self.order_service.get_all_orders()]
        else:
            orders = self._read_json(self.orders_path)

        # Lấy tables qua TableManager nếu có, ngược lại đọc file
        if self.table_manager is not None:
            tables = [t.to_dict() for t in self.table_manager.get_all_tables()]
        else:
            tables = self._read_json(self.tables_path)

        # Tìm order bằng vòng lặp tuyến tính
        order_dict = None
        for row in orders:
            if row.get("id") == order_id:
                order_dict = row
                break

        if order_dict is None:
            raise ValueError(f"Không tìm thấy đơn hàng '{order_id}'.")

        # Kiểm tra đã thanh toán SUCCESS chưa
        for row in payments:
            if row.get("order_id") == order_id and row.get("status") == "SUCCESS":
                raise ValueError(f"Đơn hàng '{order_id}' đã được thanh toán thành công.")

        if order_dict.get("status") != "SERVED":
            raise ValueError("Chỉ có thể thanh toán đơn ở trạng thái SERVED.")

        return order_dict, payments, invoices, orders, tables

    @staticmethod
    def _calculate_totals(order: dict) -> Tuple[int, int, int]:
        """
        Thống nhất nguồn tổng tiền duy nhất từ order:
        (subtotal, discount, total_amount)
        """
        if "total_amount" in order:
            subtotal = int(order["total_amount"])
        else:
            subtotal = 0
            for item in order.get("items", []):
                subtotal += PaymentService._nonnegative_int(item.get("subtotal", 0), "Thành tiền món")

        subtotal = PaymentService._nonnegative_int(subtotal, "Tổng tiền trước giảm giá")
        discount = PaymentService._nonnegative_int(order.get("discount_amount", 0), "Tiền giảm giá")
        
        # Nếu order có final_amount thì dùng, nếu không lấy subtotal - discount
        if "final_amount" in order:
            total = PaymentService._nonnegative_int(order["final_amount"], "Tổng thanh toán")
        else:
            total = PaymentService._nonnegative_int(subtotal - discount, "Tổng thanh toán")

        if discount < 0 or total < 0 or total != subtotal - discount:
            raise ValueError(f"Tổng tiền đơn hàng '{order.get('id')}' không hợp lệ.")

        return subtotal, discount, total

    @staticmethod
    def _validate_payment_method(
        method: str,
        total: int,
        cash_received: int | None,
        transaction_successful: bool | None,
    ) -> Tuple[int, bool]:
        change_due = 0
        if method == "CASH":
            if (
                isinstance(cash_received, bool)
                or not isinstance(cash_received, int)
                or cash_received < total
            ):
                raise ValueError("Tiền mặt khách đưa phải là số nguyên và đủ thanh toán.")
            change_due = cash_received - total
            is_success = True
        elif cash_received is not None:
            raise ValueError("cash_received chỉ được dùng cho phương thức CASH.")
        elif transaction_successful is None:
            raise ValueError(
                "Cần kết quả xác nhận từ cổng thanh toán cho chuyển khoản hoặc thẻ."
            )
        elif not isinstance(transaction_successful, bool):
            raise ValueError("Kết quả từ cổng thanh toán phải là true hoặc false.")
        else:
            is_success = transaction_successful

        return change_due, is_success

    @staticmethod
    def _build_payment(
        order_id: str,
        order_dict: dict,
        method: PaymentMethod,
        cashier_name: str,
        total: int,
        is_success: bool,
        cash_received: int | None,
        change_due: int,
        transaction_code: str | None,
    ) -> Payment:
        status = "SUCCESS" if is_success else "FAILED"
        return Payment(
            payment_id=f"PAY-{uuid4().hex.upper()}",
            order_id=order_id,
            table_id=order_dict.get("table_id", "Mang về"),
            amount=total,
            amount_paid=total if is_success else 0,
            method=method,
            status=status,
            cashier_name=cashier_name.strip(),
            transaction_code=transaction_code,
            cash_received=cash_received if method == "CASH" else None,
            change_due=change_due if is_success else 0,
        )

    @staticmethod
    def _build_invoice(
        payment: Payment,
        order_id: str,
        order_dict: dict,
        method: PaymentMethod,
        subtotal: int,
        discount: int,
        total: int,
    ) -> Invoice:
        raw_items = order_dict.get("items", [])
        invoice_items = []
        for it in raw_items:
            invoice_items.append(InvoiceItem.parse_item(it))

        return Invoice(
            id=f"INV-{uuid4().hex.upper()}",
            payment_id=payment.id,
            order_id=order_id,
            table_id=payment.table_id,
            items=invoice_items,
            subtotal=subtotal,
            discount_amount=discount,
            total_amount=total,
            final_amount=total,
            payment_method=method,
            cashier_name=payment.cashier_name,
        )

    def _persist(
        self,
        payment: Payment,
        invoice: Invoice | None,
        order_id: str,
        order_dict: dict,
        payments: list,
        invoices: list,
        orders: list,
        tables: list,
        is_success: bool,
    ) -> None:
        payment_record = payment.model_dump(mode="json")
        updated_payments = [*payments, payment_record]

        if not is_success:
            write_json_updates({self.payments_path: updated_payments})
            return

        updated_invoices = [*invoices, invoice.model_dump(mode="json")]

        # Cập nhật order
        order_dict["status"] = "COMPLETED"
        order_dict["updated_at"] = datetime.now().isoformat(timespec="seconds")

        # Đồng bộ qua OrderService và TableManager nếu có instance
        if self.order_service is not None:
            live_order = self.order_service.get_order(order_id)
            if live_order:
                live_order.status = "COMPLETED"
                live_order.updated_at = order_dict["updated_at"]

        table_id = order_dict.get("table_id")
        if self.table_manager is not None:
            if table_id is not None and str(table_id).isdigit():
                self.table_manager.release_table(int(table_id), order_id=order_id)
            # Ghi cả 4 file đồng bộ
            updates = {
                self.payments_path: updated_payments,
                self.invoices_path: updated_invoices,
            }
            write_json_updates(updates)
            # Lưu orders và tables qua service quản lý tương ứng
            if self.order_service is not None:
                self.order_service.save_orders()
            else:
                write_json_updates({self.orders_path: orders})
            self.table_manager.save_tables()
        else:
            self._release_table(tables, order_dict)
            updates = {
                self.payments_path: updated_payments,
                self.invoices_path: updated_invoices,
                self.orders_path: orders,
                self.tables_path: tables,
            }
            write_json_updates(updates)

    @staticmethod
    def _order_subtotal(order: dict) -> int:
        subtotal, _, _ = PaymentService._calculate_totals(order)
        return subtotal

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
        table = None
        for row in tables:
            if str(row.get("id")) == str(table_id):
                table = row
                break

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
            data = load_data(path, default_data=[])
        except Exception as e:
            raise ValueError(f"Không thể đọc file {path}: {e}") from e

        if not isinstance(data, list):
            raise ValueError(f"Expected a JSON list in {path}.")
        if any(not isinstance(row, dict) for row in data):
            raise ValueError(f"Expected every entry in {path} to be a JSON object.")
        return data

    @staticmethod
    def _write_json_updates(updates: dict[Path, list[dict]]) -> None:
        write_json_updates(updates)

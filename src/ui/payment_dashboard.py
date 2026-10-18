import json
from pathlib import Path

import streamlit as st

from src.core.PaymentService import PaymentService

st.set_page_config(page_title="Hệ Thống Thanh Toán & Dashboard", layout="wide")

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def load_json(file_name: str) -> list[dict]:
    path = DATA_DIR / file_name
    try:
        with path.open(encoding="utf-8") as data_file:
            data = json.load(data_file)
    except FileNotFoundError:
        return []
    if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
        raise ValueError(f"{path} phải chứa danh sách các JSON object.")
    return data


st.title("💳 Giao diện Thu Ngân: Thanh Toán & Dashboard Doanh Thu")
st.markdown("---")

col_payment, col_dashboard = st.columns([1.2, 1.8], gap="large")

with col_payment:
    st.subheader("🧾 Xử lý hóa đơn & thanh toán")
    served_orders = [
        order
        for order in load_json("orders.json")
        if order.get("status") == "SERVED"
    ]
    if served_orders:
        with st.form("dashboard_payment_form"):
            selected_order = st.selectbox(
                "Đơn đã lên món",
                served_orders,
                format_func=lambda order: (
                    f"{order['id']} · Bàn {order['table_id']} · "
                    f"{order['final_amount']:,} VNĐ"
                ),
            )
            payment_method = st.selectbox(
                "Phương thức thanh toán",
                ["CASH", "BANK_TRANSFER", "CARD"],
                format_func=lambda method: {
                    "CASH": "Tiền mặt",
                    "BANK_TRANSFER": "Chuyển khoản",
                    "CARD": "Thẻ",
                }[method],
            )
            cashier_name = st.text_input("Tên thu ngân")
            cash_received = None
            transaction_code = None
            transaction_successful = None
            if payment_method == "CASH":
                cash_received = st.number_input(
                    "Số tiền khách đưa (VNĐ)",
                    min_value=0,
                    value=int(selected_order["final_amount"]),
                    step=1000,
                )
            else:
                transaction_code = st.text_input("Mã giao dịch")
                transaction_successful = st.checkbox(
                    "Cổng thanh toán đã xác nhận giao dịch SUCCESS"
                )
            submitted = st.form_submit_button(
                "Xác nhận thanh toán & lập hóa đơn",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            try:
                result = PaymentService().pay_order(
                    order_id=selected_order["id"],
                    method=payment_method,
                    cashier_name=cashier_name,
                    cash_received=cash_received,
                    transaction_code=transaction_code or None,
                    transaction_successful=transaction_successful,
                )
            except ValueError as error:
                st.error(str(error))
            else:
                if result.invoice is None:
                    st.error("Thanh toán chưa thành công; đơn và bàn chưa được cập nhật.")
                else:
                    st.success(
                        f"Đã thanh toán thành công và tạo hóa đơn {result.invoice.id}. "
                        "Đơn đã hoàn tất, bàn đã được giải phóng."
                    )
                    if result.payment.change_due:
                        st.info(f"Tiền thối lại: {result.payment.change_due:,} VNĐ")
    else:
        st.info("Không có đơn nào ở trạng thái Đã lên món để thanh toán.")

with col_dashboard:
    st.subheader("📊 Dashboard doanh thu")
    payments = load_json("payments.json")
    successful_payments = [
        payment for payment in payments if payment.get("status") == "SUCCESS"
    ]
    total_revenue = sum(int(payment.get("amount_paid", 0)) for payment in successful_payments)
    transaction_count = len(successful_payments)

    metric_revenue, metric_transactions, metric_average = st.columns(3)
    metric_revenue.metric("Tổng doanh thu", f"{total_revenue:,} VNĐ")
    metric_transactions.metric("Giao dịch thành công", str(transaction_count))
    metric_average.metric(
        "Trung bình/giao dịch",
        f"{total_revenue // max(1, transaction_count):,} VNĐ",
    )

    st.markdown("##### 🕒 Lịch sử thanh toán")
    if successful_payments:
        st.dataframe(successful_payments, use_container_width=True, hide_index=True)
    else:
        st.info("Chưa có giao dịch thanh toán thành công.")

    invoices = load_json("invoices.json")
    if invoices:
        st.markdown("##### 🧾 Hóa đơn đã lập")
        st.dataframe(invoices, use_container_width=True, hide_index=True)

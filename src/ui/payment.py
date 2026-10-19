"""Component giao diện Thu ngân & Thanh toán hóa đơn."""
import json
from pathlib import Path
from typing import Optional
import streamlit as st

from src.core.OrderService import OrderService
from src.core.PaymentService import PaymentService
from src.core.TableManager import TableManager


def _load_data_file(filename: str) -> list[dict]:
    p = Path(__file__).resolve().parents[2] / "data" / filename
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    return []


def render_payment_component(
    payment_service: Optional[PaymentService] = None,
    order_service: Optional[OrderService] = None,
    table_manager: Optional[TableManager] = None,
):
    """Render giao diện xử lý thanh toán cho thu ngân và thống kê doanh thu."""
    if payment_service is None:
        payment_service = st.session_state.get("payment_service") or PaymentService()
    if order_service is None:
        order_service = st.session_state.get("order_service") or OrderService()
    if table_manager is None:
        table_manager = st.session_state.get("table_manager") or TableManager()

    st.subheader("💳 Giao diện Thu ngân: Thanh toán & Hóa đơn")

    col_pay, col_dash = st.columns([1.2, 1.8], gap="large")

    served_orders = [
        o for o in order_service.get_all_orders()
        if o.status == "SERVED"
    ]

    with col_pay:
        st.markdown("### 🧾 Xử lý hóa đơn đơn hàng")
        paid_inv = st.session_state.get("paid_receipt_invoice")
        if paid_inv:
            with st.container(border=True):
                st.success(
                    f"🎉 **Thanh toán thành công!**\n\n"
                    f"- Mã hóa đơn: **`{paid_inv.id}`**\n"
                    f"- Đơn hàng **`{paid_inv.order_id}`** đã hoàn tất!"
                )
                change_due = st.session_state.get("paid_change_due", 0)
                if change_due:
                    st.info(f"💵 **Tiền thối lại cho khách:** `{change_due:,} VNĐ`")

                receipt_text = paid_inv.generate_text_receipt()
                st.text_area("📄 Chi tiết phiếu thu hóa đơn:", receipt_text, height=220)
                st.download_button(
                    label="📥 Xuất / Tải hóa đơn (TXT)",
                    data=receipt_text,
                    file_name=f"hoadon_{paid_inv.id}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
                if st.button("Đóng phiếu thu này", key="btn_close_paid_receipt"):
                    del st.session_state["paid_receipt_invoice"]
                    if "paid_change_due" in st.session_state:
                        del st.session_state["paid_change_due"]
                    st.rerun()
            st.divider()

        if not served_orders:
            st.info("Hiện không có đơn nào ở trạng thái **Đã lên món (SERVED)** sẵn sàng thanh toán.")
        else:
            with st.form("form_payment_process"):
                selected_order = st.selectbox(
                    "Chọn đơn cần thanh toán:",
                    served_orders,
                    format_func=lambda o: f"{o.id} • Bàn {o.table_id} • {o.final_amount:,} VNĐ",
                )
                method = st.selectbox(
                    "Phương thức thanh toán:",
                    ["CASH", "BANK_TRANSFER", "CARD"],
                    format_func=lambda m: {
                        "CASH": "💵 Tiền mặt",
                        "BANK_TRANSFER": "📱 Chuyển khoản / VietQR",
                        "CARD": "💳 Quẹt thẻ POS",
                    }[m],
                )
                cashier_name = st.text_input("Tên nhân viên thu ngân:", value="Thu ngân chính")

                cash_received = None
                transaction_code = None
                transaction_successful = None

                if method == "CASH":
                    cash_received = st.number_input(
                        "Tiền khách đưa (VNĐ):",
                        min_value=0,
                        value=int(selected_order.final_amount),
                        step=1000,
                    )
                else:
                    transaction_code = st.text_input("Mã giao dịch / Mã chuẩn chi:")
                    transaction_successful = st.checkbox("Cổng thanh toán xác nhận SUCCESS", value=True)

                submitted = st.form_submit_button("💰 Xác nhận thanh toán & Lập hóa đơn", type="primary", use_container_width=True)

            if submitted:
                try:
                    result = payment_service.pay_order(
                        order_id=selected_order.id,
                        method=method,
                        cashier_name=cashier_name,
                        cash_received=cash_received,
                        transaction_code=transaction_code or None,
                        transaction_successful=transaction_successful,
                    )
                    if result.invoice is None:
                        st.error("Thanh toán chưa thành công; đơn và bàn chưa được cập nhật.")
                    else:
                        st.session_state["paid_receipt_invoice"] = result.invoice
                        st.session_state["paid_change_due"] = result.payment.change_due
                        # Đồng bộ lại bộ nhớ order_service và table_manager
                        order_service.load_orders()
                        table_manager.load_tables()
                        st.rerun()
                except Exception as e:
                    st.error(f"Lỗi thanh toán: {e}")

    with col_dash:
        st.markdown("### 📊 Thống kê & Xuất hóa đơn")
        payments_data = _load_data_file("payments.json")
        invoices_data = _load_data_file("invoices.json")
        success_pays = [p for p in payments_data if p.get("status") == "SUCCESS"]

        total_rev = sum(p.get("amount_paid", 0) for p in success_pays)
        total_tx = len(success_pays)
        avg_tx = total_rev // max(1, total_tx)

        m1, m2, m3 = st.columns(3)
        m1.metric("Tổng doanh thu thực nhận", f"{total_rev:,} VNĐ")
        m2.metric("Giao dịch thành công", f"{total_tx}/{len(payments_data)}")
        m3.metric("Trung bình/đơn", f"{avg_tx:,} VNĐ")

        st.divider()
        st.markdown("##### 🖨️ Tra cứu & Xuất hóa đơn đã lưu")
        if invoices_data:
            from src.models.Invoice import Invoice
            inv_choices = [
                (i["id"], f"{i['id']} • Đơn {i['order_id']} • {i.get('final_amount', i.get('total_amount', 0)):,} đ ({i.get('issued_at', '')[:16]})")
                for i in reversed(invoices_data)
            ]
            selected_inv_id = st.selectbox(
                "Chọn hóa đơn cần xem lại / xuất file:",
                options=[c[0] for c in inv_choices],
                format_func=lambda x: next((c[1] for c in inv_choices if c[0] == x), x),
            )
            raw_inv = next((i for i in invoices_data if i["id"] == selected_inv_id), None)
            if raw_inv:
                try:
                    inv_obj = Invoice.model_validate(raw_inv)
                    receipt_str = inv_obj.generate_text_receipt()
                    st.download_button(
                        label=f"📥 Tải hóa đơn {inv_obj.id}",
                        data=receipt_str,
                        file_name=f"hoadon_{inv_obj.id}.txt",
                        mime="text/plain",
                        key=f"dl_inv_{inv_obj.id}",
                        use_container_width=True,
                    )
                except Exception:
                    st.json(raw_inv)
        else:
            st.caption("Chưa có hóa đơn nào trong hệ thống.")

        st.divider()
        st.markdown("##### 🕒 Lịch sử thanh toán gần nhất")
        if payments_data:
            st.dataframe(payments_data, use_container_width=True)
        else:
            st.caption("Chưa có lịch sử giao dịch.")

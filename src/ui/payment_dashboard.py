import streamlit as st
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Hệ Thống Thanh Toán & Dashboard", layout="wide")

if "total_revenue" not in st.session_state:
    st.session_state.total_revenue = 1450000  
if "transaction_count" not in st.session_state:
    st.session_state.transaction_count = 12
if "paid_orders" not in st.session_state:
    st.session_state.paid_orders = [
        {"order_id": "ORD-20261016-001", "table": "Bàn 02", "amount": 105000, "time": "12:05:00"},
        {"order_id": "ORD-20261016-002", "table": "Bàn VIP 01", "amount": 320000, "time": "12:30:15"}
    ]

st.title("💳 Giao diện Thu Ngân: Thanh Toán & Dashboard Doanh Thu")
st.markdown("---")

col_payment, col_dashboard = st.columns([1.2, 1.8], gap="large")

with col_payment:
    st.subheader("🧾 Xử Lý Hóa Đơn & Thanh Toán")
    
    order_id_input = st.text_input("Mã đơn hàng / Mã bàn", value="ORD-20261016-003", help="Nhập mã đơn hàng của khách hàng")
    table_selected = st.selectbox("Chọn bàn thanh toán", ["Bàn 02 (Đang phục vụ)", "Bàn 10 (Đang phục vụ)", "Bàn VIP 01"])
    
    st.markdown("---")
    st.markdown("##### Chi Tiết Món Ăn Trong Đơn")

    sample_invoice_items = [
        {"name": "Cà phê sữa đá", "qty": 2, "price": 29000, "amount": 58000},
        {"name": "Bánh mì chảo đặc biệt", "qty": 1, "price": 55000, "amount": 55000},
        {"name": "Khoai tây chiên lắc phô mai", "qty": 1, "price": 32000, "amount": 32000}
    ]
    df_invoice = pd.DataFrame(sample_invoice_items)
    st.dataframe(df_invoice, use_container_width=True, hide_index=True)
    
    subtotal = sum(item["amount"] for item in sample_invoice_items)
    discount = st.number_input("Giảm giá (VNĐ)", min_value=0, value=0, step=5000)
    final_total = max(0, subtotal - discount)
    
    st.markdown(f"### 💰 Tổng tiền cần thanh toán: `{final_total:,.0f} VNĐ`")
    
    st.markdown("---")
    st.markdown("##### Nhập Tiền Khách Trả")
    
    # Phương thức thanh toán
    payment_method = st.radio("Phương thức thanh toán", ["Tiền mặt (CASH)", "Chuyển khoản (BANK_TRANSFER)", "Thẻ (CREDIT_CARD)"], horizontal=True)
    
    cash_given = 0.0
    if "Tiền mặt" in payment_method:
        cash_given = st.number_input("Số tiền khách đưa (VNĐ)", min_value=0.0, value=200000.0, step=10000.0)
        change_due = cash_given - final_total
        
        if cash_given > 0:
            if change_due >= 0:
                st.info(f"💵 **Tiền thối lại cho khách:** `{change_due:,.0f} VNĐ`")
            else:
                st.warning(f"⚠️ Số tiền khách đưa còn thiếu: `{abs(change_due):,.0f} VNĐ`")
    else:
        cash_given = final_total
        change_due = 0.0
        st.success("💳 Thanh toán điện tử: Khớp chính xác số tiền hóa đơn.")

    st.markdown("")
    
    if st.button("✅ Xác Nhận Thanh Toán & In Hóa Đơn", type="primary", use_container_width=True):
        if "Tiền mặt" in payment_method and cash_given < final_total:
            st.error("❌ **Thanh toán thất bại!** Số tiền khách đưa không đủ để thanh toán hóa đơn.")
        else:
            st.session_state.total_revenue += final_total
            st.session_state.transaction_count += 1
            
            current_time = datetime.now().strftime("%H:%M:%S")
            st.session_state.paid_orders.insert(0, {
                "order_id": order_id_input,
                "table": table_selected.split(" ")[0] + " " + table_selected.split(" ")[1],
                "amount": final_total,
                "time": current_time
            })
            
            st.success(f"🎉 **Thanh toán thành công!** Đã ghi nhận doanh thu, cập nhật trạng thái đơn thành **COMPLETED** và giải phóng bàn.")
            st.balloons()

with col_dashboard:
    st.subheader("📊 Dashboard Doanh Thu & Báo Cáo Nhanh")
    
    # Hiển thị các chỉ số tổng quan (Metrics)
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(label="Tổng Doanh Thu Ngày", value=f"{st.session_state.total_revenue:,.0f} VNĐ", delta="+12.5%")
    with m2:
        st.metric(label="Tổng Số Giao Dịch", value=f"{st.session_state.transaction_count} đơn", delta="+3")
    with m3:
        st.metric(label="Giá Trị Trung Bình/Đơn", value=f"{st.session_state.total_revenue / max(1, st.session_state.transaction_count):,.0f} VNĐ")
        
    st.markdown("---")
    st.markdown("##### 🕒 Lịch Sử Giao Dịch Đã Thanh Toán Trong Ngày")
    
    if st.session_state.paid_orders:
        df_history = pd.DataFrame(st.session_state.paid_orders)
        df_history.columns = ["Mã Đơn Hàng", "Bàn", "Số Tiền (VNĐ)", "Thời Gian Thanh Toán"]
        st.dataframe(df_history, use_container_width=True, hide_index=True)
    else:
        st.info("Chưa có giao dịch thanh toán nào trong ca làm việc này.")
        
    st.markdown("---")
    st.markdown("##### 💡 Ghi chú vận hành hệ thống")
    st.info(
        "• **Thuật toán tích lũy doanh thu:** Doanh thu mới = Doanh thu hiện tại + Tổng tiền hóa đơn (Đạt độ phức tạp $O(1)$).\n"
        "• **Đồng bộ trạng thái:** Sau khi bấm xác nhận thanh toán, đơn hàng tự động chuyển sang `COMPLETED` và bàn ăn chuyển trạng thái về `AVAILABLE`."
    )
"""Component giao diện Tổng quan hệ thống (Dashboard)."""
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


def render_dashboard_component(
    order_service: Optional[OrderService] = None,
    table_manager: Optional[TableManager] = None,
    payment_service: Optional[PaymentService] = None,
):
    """Render dashboard tổng quan hiệu năng nhà hàng và tiến độ dự án."""
    if order_service is None:
        order_service = st.session_state.get("order_service") or OrderService()
    if table_manager is None:
        table_manager = st.session_state.get("table_manager") or TableManager()

    # Luôn làm mới dữ liệu từ backend storage
    table_manager.load_tables()
    order_service.load_orders()

    st.subheader("📊 Tổng quan hoạt động Nhà Hàng & Báo cáo số liệu")

    tables = table_manager.get_all_tables()
    orders = order_service.get_all_orders()
    payments_data = _load_data_file("payments.json")

    occupied = sum(1 for t in tables if t.status == "OCCUPIED")
    active_orders = sum(1 for o in orders if o.is_active)
    total_rev = sum(p.get("amount_paid", 0) for p in payments_data if p.get("status") == "SUCCESS")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tổng số bàn", len(tables))
    k2.metric("Bàn đang phục vụ", f"{occupied} bàn")
    k3.metric("Đơn chưa thanh toán", f"{active_orders} đơn")
    k4.metric("Tổng doanh thu", f"{total_rev:,} VNĐ")

    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🪑 Trạng thái bàn ăn")
        avl = sum(1 for t in tables if t.status == "AVAILABLE")
        res = sum(1 for t in tables if t.status == "RESERVED")
        occ_pct = int((occupied / max(1, len(tables))) * 100)
        st.progress(occupied / max(1, len(tables)), text=f"Tỷ lệ lấp đầy: {occupied}/{len(tables)} bàn ({occ_pct}%)")
        st.write(f"- 🟢 **Bàn trống sẵn sàng đón khách:** `{avl}` bàn")
        st.write(f"- 🔴 **Bàn đang có khách dùng bữa:** `{occupied}` bàn")
        st.write(f"- 🟡 **Bàn đã được đặt trước:** `{res}` bàn")


    with c2:
        st.markdown("### 🧾 Trạng thái đơn hàng")
        pnd = sum(1 for o in orders if o.status == "PENDING")
        prp = sum(1 for o in orders if o.status == "PREPARING")
        srv = sum(1 for o in orders if o.status == "SERVED")
        cmp = sum(1 for o in orders if o.status == "COMPLETED")
        cnc = sum(1 for o in orders if o.status == "CANCELLED")
        st.write(f"- ⏳ **Chờ xác nhận:** `{pnd}` đơn")
        st.write(f"- 🍳 **Đang chế biến trong bếp:** `{prp}` đơn")
        st.write(f"- 🍽️ **Đã lên món (chờ thanh toán):** `{srv}` đơn")
        st.write(f"- ✅ **Đã thanh toán & hoàn tất:** `{cmp}` đơn")
        st.write(f"- ❌ **Đã hủy:** `{cnc}` đơn")

    st.divider()

    st.markdown("### 💳 Phân bổ Doanh thu theo Phương thức")
    cash_rev = sum(p.get("amount_paid", 0) for p in payments_data if p.get("status") == "SUCCESS" and p.get("method") == "CASH")
    bank_rev = sum(p.get("amount_paid", 0) for p in payments_data if p.get("status") == "SUCCESS" and p.get("method") == "BANK_TRANSFER")
    card_rev = sum(p.get("amount_paid", 0) for p in payments_data if p.get("status") == "SUCCESS" and p.get("method") == "CARD")

    rc1, rc2, rc3 = st.columns(3)
    rc1.metric("💵 Tiền mặt (CASH)", f"{cash_rev:,} VNĐ")
    rc2.metric("📱 Chuyển khoản (VietQR)", f"{bank_rev:,} VNĐ")
    rc3.metric("💳 Quẹt thẻ (POS)", f"{card_rev:,} VNĐ")

    st.divider()
    st.markdown("### 🏗️ Kiến trúc Hệ thống Phân tầng (Clean Architecture)")
    st.markdown("""
    - **Tầng Models (`src/models/`):** Định nghĩa cấu trúc dữ liệu (`MenuItem`, `Order`, `OrderItem`, `Table`, `Payment`, `Invoice`, `JSONStorage`).
    - **Tầng Core Nghiệp vụ (`src/core/`):** Xử lý toàn bộ logic nghiệp vụ tập trung (`Cart`, `KitchenManager`, `OrderService`, `TableManager`, `PaymentService`).
    - **Tầng Giao diện (`src/ui/`):** Các component độc lập hiển thị và tiếp nhận tương tác người dùng, gọi trực tiếp các phương thức từ tầng Core.
    - **Entry Point Duy nhất (`src/app.py`):** Khởi tạo dịch vụ, tích hợp giao diện điều phối Streamlit thống nhất.
    """)

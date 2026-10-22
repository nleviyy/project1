"""Streamlit entry point for the DŨNG MINION management system."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from src.core.Cart import Cart
from src.core.KitchenManager import KitchenManager
from src.core.OrderService import OrderService
from src.core.PaymentService import PaymentService
from src.core.TableManager import TableManager
from src.ui import (
    apply_custom_styles,
    render_dashboard_component,
    render_kitchen_component,
    render_ordering_component,
    render_orders_component,
    render_payment_component,
    render_tables_component,
)

PAGE_OPTIONS = (
    "🍽️  Thực đơn",
    "🧾  Đơn hàng",
    "🍳  Bếp",
    "💳  Thanh toán",
    "📈  Thống kê",
    "🪑  Quản lý bàn",
)
PAGE_LABELS = {
    "🍽️  Thực đơn": "Thực đơn",
    "🧾  Đơn hàng": "Đơn hàng",
    "🍳  Bếp": "Bếp",
    "💳  Thanh toán": "Thanh toán",
    "📈  Thống kê": "Thống kê",
    "🪑  Quản lý bàn": "Quản lý bàn",
}

st.set_page_config(
    page_title="DŨNG MINION · Quản lý nhà hàng",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_custom_styles()
st.markdown(
    """
<style>
[data-testid="stAppViewContainer"] { background: #f8fafc; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stAppDeployButton"], [data-testid="stMainMenu"] { display: none; }
section[data-testid="stSidebar"] {
    width: 270px !important;
    min-width: 270px !important;
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    border-right: 1px solid #334155;
}
.main h1, .main h2, .main h3, .main h4,
.main p, .main label, .main [data-testid="stCaptionContainer"] {
    color: #0f172a;
}
.main [data-baseweb="select"] > div,
.main [data-testid="stTextInput"] input,
.main [data-testid="stTextArea"] textarea,
.main [data-testid="stNumberInput"] input {
    border: 1px solid #cbd5e1;
    border-radius: 10px;
    color: #0f172a;
    background: #ffffff;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}
.main [data-baseweb="select"] > div:focus-within,
.main [data-testid="stTextInput"] input:focus,
.main [data-testid="stTextArea"] textarea:focus,
.main [data-testid="stNumberInput"] input:focus {
    border-color: #2563eb;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
}
.main [data-testid="stRadio"] label,
.main [data-testid="stRadio"] label p {
    color: #334155;
}
.main [data-testid="stRadioOption"] > div > div:first-child,
[data-testid="stSidebar"] [data-testid="stRadioOption"] > div > div:first-child {
    display: none;
}
.main [data-testid="stRadioOption"] {
    padding: .45rem .8rem;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    background: #ffffff;
    transition: all .15s ease;
}
.main [data-testid="stRadioOption"]:hover {
    border-color: #cbd5e1;
    background: #f8fafc;
}
.main [data-testid="stRadioOption"]:has(input:checked) {
    border-color: #2563eb;
    background: #eff6ff;
    color: #1d4ed8;
    font-weight: 600;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 {
    color: #f8fafc;
    font-size: 1.2rem;
    line-height: 1.35;
    font-weight: 700;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    min-height: 2.65rem;
    margin: .2rem 0;
    padding: .6rem .85rem;
    border: 1px solid transparent;
    border-radius: 10px;
    color: #cbd5e1;
    font-weight: 500;
    transition: all .15s ease;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    border-color: rgba(255,255,255,.15);
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    color: #ffffff;
    font-weight: 600;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(255,255,255,.08);
    color: #ffffff;
}
[data-testid="stSidebar"] [data-testid="stRadioOption"] > div > div:first-child {
    display: none !important;
}
[data-testid="stSidebar"] [data-baseweb="radio"] > div:first-child,
[data-testid="stSidebar"] [data-baseweb="radio"] > label > div:first-child,
[data-testid="stSidebar"] [role="radiogroup"] > label > div:first-child {
    display: none !important;
}
[data-testid="stSidebar"] [data-testid="stRadioOption"] > div:first-child {
    display: none !important;
}
[data-testid="stSidebar"] [data-testid="stRadioOption"] > div {
    justify-content: flex-start;
}
.sidebar-brand {
    display: flex;
    align-items: center;
    gap: .8rem;
    margin: .2rem 0 1.2rem;
    padding: .4rem .2rem 1.1rem;
    border-bottom: 1px solid rgba(255,255,255,.1);
}
.sidebar-logo {
    display: grid;
    width: 3.1rem;
    height: 3.1rem;
    place-items: center;
    border-radius: 12px;
    color: #ffffff;
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
    font-size: 1.05rem;
    font-weight: 800;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);
}
.sidebar-brand strong { display: block; color: #f8fafc; font-size: 1.05rem; letter-spacing: -0.01em; }
.sidebar-brand small { color: #94a3b8; font-size: 0.8rem; }
.welcome-label { color: #2563eb; font-weight: 800; }
.welcome-title { margin: 0; color: #0f172a; font-size: clamp(1.35rem, 2vw, 1.8rem); font-weight: 800; }
[data-testid="stRadio"] > label { color: #334155; }
</style>
""",
    unsafe_allow_html=True,
)

def get_services():
    if "table_manager" not in st.session_state:
        st.session_state.table_manager = TableManager()
    if "kitchen_manager" not in st.session_state:
        st.session_state.kitchen_manager = KitchenManager()
    if "order_service" not in st.session_state:
        st.session_state.order_service = OrderService(
            table_manager=st.session_state.table_manager,
            kitchen_manager=st.session_state.kitchen_manager,
        )
    if "payment_service" not in st.session_state:
        st.session_state.payment_service = PaymentService()
    if "cart" not in st.session_state:
        st.session_state.cart = Cart()

    # Luôn làm mới dữ liệu từ backend storage (JSON) để đảm bảo đồng bộ
    st.session_state.table_manager.load_tables()
    st.session_state.order_service.load_orders()

    km = st.session_state.kitchen_manager
    os_service = st.session_state.order_service

    active_orders = os_service.get_all_orders()
    km.synchronize_orders(active_orders)

    return (
        st.session_state.table_manager,
        st.session_state.kitchen_manager,
        st.session_state.order_service,
        st.session_state.payment_service,
        st.session_state.cart,
    )

(
    table_manager,
    kitchen_manager,
    order_service,
    payment_service,
    cart,
) = get_services()

with st.sidebar:
    st.markdown(
        """
<div class="sidebar-brand">
    <span class="sidebar-logo">DM</span>
    <span><strong>DŨNG<br>MINION</strong><small>Quản lý nhà hàng</small></span>
</div>
""",
        unsafe_allow_html=True,
    )
    selected_page = st.radio(
        "Điều hướng",
        PAGE_OPTIONS,
        key="system_page",
        label_visibility="collapsed",
    )
    st.divider()
    available_tables = table_manager.get_available_tables()
    total_tables = table_manager.get_all_tables()
    st.markdown(
        f"""
<div style="display:flex;flex-direction:column;gap:0.45rem;margin-top:0.2rem;">
    <div style="display:flex;justify-content:space-between;align-items:center;padding:0.45rem 0.75rem;border-radius:8px;background:rgba(255,255,255,0.06);color:#e2e8f0;font-size:0.85rem;">
        <span>🪑 Bàn trống</span>
        <span style="font-weight:700;color:#38bdf8;">{len(available_tables)} / {len(total_tables)}</span>
    </div>
    <div style="display:flex;justify-content:space-between;align-items:center;padding:0.45rem 0.75rem;border-radius:8px;background:rgba(255,255,255,0.06);color:#e2e8f0;font-size:0.85rem;">
        <span>🍳 Bếp</span>
        <span style="font-weight:700;color:#fbbf24;">{1 if kitchen_manager.get_current_order() else 0} nấu · {kitchen_manager.count_waiting()} chờ</span>
    </div>
    <div style="display:flex;justify-content:space-between;align-items:center;padding:0.45rem 0.75rem;border-radius:8px;background:rgba(255,255,255,0.06);color:#e2e8f0;font-size:0.85rem;">
        <span>🛒 Giỏ hàng</span>
        <span style="font-weight:700;color:#60a5fa;">{len(cart.get_order_items())} món</span>
    </div>
</div>
<div style="margin-top:1.8rem;padding:0.9rem;border-radius:12px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);color:#f8fafc;">
    <b style="color:#ffffff;font-size:0.9rem;">Hệ thống DŨNG MINION</b><br>
    <small style="color:#94a3b8;font-size:0.78rem;">Vận hành nhà hàng chuyên nghiệp</small>
</div>
""",
        unsafe_allow_html=True,
    )

if "checkout_notice" in st.session_state:
    st.success(st.session_state.pop("checkout_notice"))
if "payment_notice" in st.session_state:
    st.success(st.session_state.pop("payment_notice"))

if selected_page == "🍽️  Thực đơn":
    st.title("Thực đơn")
    render_ordering_component(
        cart=cart,
        order_service=order_service,
        table_manager=table_manager,
        kitchen_manager=kitchen_manager,
    )
elif selected_page == "🧾  Đơn hàng":
    st.title(PAGE_LABELS[selected_page])
    render_orders_component(
        order_service=order_service,
        kitchen_manager=kitchen_manager,
        table_manager=table_manager,
    )
elif selected_page == "🍳  Bếp":
    st.title("Điều phối bếp")
    if st.button("↻ Cập nhật hàng đợi", key="refresh_kitchen_queue"):
        order_service.load_orders()
        kitchen_manager.restore_orders(order_service.get_all_orders())
        st.toast("Đã tải lại đơn hàng.")
    render_kitchen_component(
        kitchen_manager=kitchen_manager,
        order_service=order_service,
    )
    served_orders = order_service.filter_orders_by_status("SERVED")
    if served_orders:
        with st.expander(f"🍽️ Đã lên món · chờ thanh toán ({len(served_orders)})"):
            for order in sorted(
                served_orders,
                key=lambda item: str(item.created_at),
                reverse=True,
            ):
                st.write(
                    f"**{order.id}** · Bàn {order.table_id} · "
                    f"{order.final_amount:,} VNĐ"
                )
elif selected_page == "💳  Thanh toán":
    st.title("Thanh toán & lịch sử giao dịch")
    render_payment_component(
        payment_service=payment_service,
        order_service=order_service,
        table_manager=table_manager,
    )
elif selected_page == "📈  Thống kê":
    st.title("Thống kê")
    render_dashboard_component(
        order_service=order_service,
        table_manager=table_manager,
        payment_service=payment_service,
    )
elif selected_page == "🪑  Quản lý bàn":
    st.title("Quản lý bàn")
    render_tables_component(
        table_manager=table_manager,
        order_service=order_service,
    )
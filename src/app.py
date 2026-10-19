"""Streamlit entry point for the DŨNG FATFOOD management system."""

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
    "⚙️  Cài đặt",
)
PAGE_LABELS = {
    "🍽️  Thực đơn": "Thực đơn",
    "🧾  Đơn hàng": "Đơn hàng",
    "🍳  Bếp": "Bếp",
    "💳  Thanh toán": "Thanh toán",
    "📈  Thống kê": "Thống kê",
    "🪑  Quản lý bàn": "Quản lý bàn",
    "⚙️  Cài đặt": "Cài đặt",
}

st.set_page_config(
    page_title="DŨNG FATFOOD · Quản lý nhà hàng",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_custom_styles()
st.markdown(
    """
<style>
[data-testid="stAppViewContainer"] { background: #f7f3ff; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stAppDeployButton"], [data-testid="stMainMenu"] { display: none; }
section[data-testid="stSidebar"] {
    width: 260px !important;
    min-width: 260px !important;
}
.main h1, .main h2, .main h3, .main h4,
.main p, .main label, .main [data-testid="stCaptionContainer"] {
    color: #25154f;
}
.main [data-baseweb="select"] > div,
.main [data-testid="stTextInput"] input,
.main [data-testid="stTextArea"] textarea {
    border-color: #e1d2ff;
    color: #25154f;
    background: #fff;
}
.main [data-testid="stRadio"] label,
.main [data-testid="stRadio"] label p {
    color: #5b4b79;
}
.main [data-testid="stRadioOption"] > div > div:first-child,
[data-testid="stSidebar"] [data-testid="stRadioOption"] > div > div:first-child {
    display: none;
}
.main [data-testid="stRadioOption"] {
    padding: .4rem .7rem;
    border: 1px solid #eee5ff;
    border-radius: 12px;
    background: #fff;
}
.main [data-testid="stRadioOption"]:has(input:checked) {
    border-color: #d8c0ff;
    background: #eee5ff;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #321456 0%, #3d176f 60%, #5420c8 100%);
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 {
    color: #fff;
    font-size: 1.2rem;
    line-height: 1.35;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    min-height: 2.65rem;
    margin: .12rem 0;
    padding: .62rem .8rem;
    border: 1px solid transparent;
    border-radius: 12px;
    color: rgba(255,255,255,.9);
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    border-color: rgba(255,255,255,.15);
    background: linear-gradient(100deg, #8c43f5, #7540df);
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(255,255,255,.12);
}
[data-testid="stSidebar"] [data-testid="stRadioOption"] > div > div:first-child {
    display: none !important;
}
[data-testid="stSidebar"] [data-testid="stRadioOption"] > div {
    justify-content: flex-start;
}
.sidebar-brand {
    display: flex;
    align-items: center;
    gap: .75rem;
    margin: .2rem 0 1.2rem;
    padding: .3rem .1rem 1.1rem;
    border-bottom: 1px solid rgba(255,255,255,.16);
}
.sidebar-logo {
    display: grid;
    width: 3rem;
    height: 3rem;
    place-items: center;
    border-radius: 14px;
    color: #fff;
    background: rgba(255,255,255,.18);
    font-size: 1rem;
    font-weight: 800;
}
.sidebar-brand strong { display: block; color: #fff; font-size: 1.05rem; }
.sidebar-brand small { color: rgba(255,255,255,.68); }
.welcome-label { color: #7033d3; font-weight: 800; }
.welcome-title { margin: 0; color: #25154f; font-size: clamp(1.35rem, 2vw, 1.8rem); font-weight: 800; }
[data-testid="stRadio"] > label { color: #5b4b79; }
</style>
""",
    unsafe_allow_html=True,
)


def get_services():
    """Create per-session services and restore active kitchen orders."""
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

    table_manager = st.session_state.table_manager
    kitchen_manager = st.session_state.kitchen_manager
    order_service = st.session_state.order_service
    order_service.table_manager = table_manager
    order_service.kitchen_manager = kitchen_manager
    table_manager.load_tables()
    order_service.load_orders()
    if hasattr(kitchen_manager, "restore_orders"):
        kitchen_manager.restore_orders(order_service.get_all_orders())
    return (
        table_manager,
        kitchen_manager,
        order_service,
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
    <span class="sidebar-logo">DF</span>
    <span><strong>DŨNG<br>FATFOOD</strong><small>Quản lý nhà hàng</small></span>
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
    st.caption(f"🟢 Bàn trống  {len(available_tables)} / {len(total_tables)}")
    st.caption(
        f"🍳 Bếp  "
        f"{1 if kitchen_manager.get_current_order() else 0} đang nấu · "
        f"{kitchen_manager.count_waiting()} chờ"
    )
    st.caption(f"🛒 Giỏ hàng  {cart.count_lines()} món")
    st.markdown(
        '<div style="margin-top:2rem;padding:.8rem;border-radius:14px;'
        'background:rgba(255,255,255,.12);color:#fff">'
        '<b>Ngon hơn mỗi ngày</b><br><small>cùng DŨNG FATFOOD</small></div>',
        unsafe_allow_html=True,
    )

if "checkout_notice" in st.session_state:
    st.success(st.session_state.pop("checkout_notice"))
if "payment_notice" in st.session_state:
    st.success(st.session_state.pop("payment_notice"))
if "payment_receipt" in st.session_state:
    with st.expander("🧾 Xem hóa đơn vừa thanh toán"):
        st.code(st.session_state.pop("payment_receipt"))

header_left, header_search = st.columns(
    [1.1, 1],
    vertical_alignment="center",
)
header_left.markdown(
    '<div><span class="welcome-label">Xin chào!</span>'
    '<h2 class="welcome-title">Chúc bạn có một bữa ăn ngon miệng!</h2></div>',
    unsafe_allow_html=True,
)
header_search.text_input(
    "Tìm món ăn theo tên hoặc mã món",
    placeholder="⌕  Tìm món ăn theo tên hoặc mã món",
    key="header_menu_search",
    label_visibility="collapsed",
)

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
        st.toast("Đã tải lại đơn hàng từ data/orders.json.")
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
else:
    st.title("Cài đặt")
    with st.container(border=True):
        st.subheader("Thông tin hệ thống")
        st.text_input("Tên cửa hàng", value="DŨNG FATFOOD", disabled=True)
        st.text_input("Thư mục dữ liệu", value=str(PROJECT_ROOT / "data"), disabled=True)
        st.caption(
            "Giao diện hiện sử dụng dữ liệu dùng chung trong thư mục data "
            "và các nghiệp vụ từ service hiện có của dự án."
        )

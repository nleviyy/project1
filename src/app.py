"""
Hệ thống Quản lý Đơn hàng & Bàn ăn F&B bằng Python
Entry point duy nhất của ứng dụng:
    python -m streamlit run src/app.py
    hoặc: uv run streamlit run src/app.py
"""
import sys
from pathlib import Path

# Đảm bảo đường dẫn gốc của project có trong sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

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

# 1. Cấu hình trang Streamlit (Duy nhất cho toàn ứng dụng)
st.set_page_config(
    page_title="F&B Order & Table Management",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Áp dụng CSS giao diện hiện đại & đồng bộ
apply_custom_styles()


# 3. Khởi tạo trạng thái dịch vụ nghiệp vụ (Singleton trong session)
def get_services():
    """Khởi tạo và lưu trữ các service nghiệp vụ trong st.session_state."""
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

    # Đồng bộ các đơn PENDING/PREPARING vào hàng đợi bếp nếu bếp đang trống
    if km.is_empty():
        active_orders = [
            order for order in os_service.get_all_orders()
            if order.status in ("PENDING", "PREPARING")
        ]
        active_orders.sort(key=lambda o: str(o.created_at))
        for ord_obj in active_orders:
            if ord_obj.status == "PREPARING" and km.get_current_order() is None:
                km._current_order = ord_obj
            elif ord_obj.status == "PENDING":
                try:
                    km.add_order(ord_obj)
                except ValueError:
                    pass
    else:
        # Làm sạch đơn đã hủy/đã thanh toán khỏi bếp nếu có
        active_ids = {o.id for o in os_service.get_all_orders() if o.status in ("PENDING", "PREPARING")}
        if km.get_current_order() and km.get_current_order().id not in active_ids:
            km._current_order = None
        if hasattr(km, "_queue") and km._queue:
            from collections import deque
            km._queue = deque([o for o in km._queue if o.id in active_ids])

    return (
        st.session_state.table_manager,
        st.session_state.kitchen_manager,
        st.session_state.order_service,
        st.session_state.payment_service,
        st.session_state.cart,
    )


table_manager, kitchen_manager, order_service, payment_service, cart = get_services()


# 4. Sidebar: Thông tin hệ thống và chỉ số nhanh
with st.sidebar:
    st.markdown("## 🍽️ F&B Management")
    st.caption("Hệ Thống Quản Lý Đơn Hàng & Bàn Ăn")
    st.divider()

    # Chỉ số nhanh
    st.markdown("### ⚡ Trạng thái nhanh")
    avl_tables = len(table_manager.get_available_tables())
    total_tables = len(table_manager.get_all_tables())
    st.write(f"🟢 **Bàn trống:** `{avl_tables}/{total_tables}`")

    waiting_k = kitchen_manager.count_waiting()
    cur_k = 1 if kitchen_manager.get_current_order() is not None else 0
    st.write(f"🍳 **Bếp:** `{cur_k}` đang nấu • `{waiting_k}` chờ")

    cart_lines = cart.count_lines()
    st.write(f"🛒 **Giỏ hàng:** `{cart_lines}` món • `{cart.calculate_total():,} đ`")
    st.divider()

    st.subheader("👥 Phân công thành viên")
    st.markdown("""
    * **Vy:** Git, khởi tạo dự án & tích hợp code
    * **Quỳnh:** Models (Data Classes) & Lưu trữ JSON
    * **Anh:** OOP & Xử lý nghiệp vụ bàn ăn / đơn hàng
    * **Thắng:** Thiết kế giao diện tương tác Streamlit
    """)
    st.divider()

    st.caption("Python 3.11+ • Clean Architecture: Models - Core - UI")


# 5. Nội dung chính: Tích hợp các Tabs nghiệp vụ
st.title("🍽️ Hệ Thống Quản Lý Đơn Hàng & Bàn Ăn F&B")

tabs = st.tabs([
    "🛒 Gọi món & Giỏ hàng",
    "🪑 Sơ đồ bàn",
    "🍳 Điều phối bếp (KDS)",
    "🧾 Danh sách đơn hàng",
    "💳 Thu ngân & Thanh toán",
    "📊 Tổng quan & Báo cáo",
])

# Tab 1: Đặt món
with tabs[0]:
    render_ordering_component(
        cart=cart,
        order_service=order_service,
        table_manager=table_manager,
        kitchen_manager=kitchen_manager,
    )

# Tab 2: Sơ đồ bàn
with tabs[1]:
    render_tables_component(
        table_manager=table_manager,
        order_service=order_service,
    )

# Tab 3: Bếp
with tabs[2]:
    render_kitchen_component(
        kitchen_manager=kitchen_manager,
        order_service=order_service,
    )

# Tab 4: Đơn hàng
with tabs[3]:
    render_orders_component(
        order_service=order_service,
        kitchen_manager=kitchen_manager,
        table_manager=table_manager,
    )

# Tab 5: Thanh toán
with tabs[4]:
    render_payment_component(
        payment_service=payment_service,
        order_service=order_service,
        table_manager=table_manager,
    )

# Tab 6: Tổng quan
with tabs[5]:
    render_dashboard_component(
        order_service=order_service,
        table_manager=table_manager,
        payment_service=payment_service,
    )

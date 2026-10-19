"""Component giao diện Quản lý Danh sách Đơn hàng."""
from typing import Optional
import streamlit as st

from src.core.KitchenManager import KitchenManager
from src.core.OrderService import OrderService
from src.core.TableManager import TableManager
from src.models.Order import ORDER_STATUS_LABELS, OrderStatus

STATUS_BADGE_MAP = {
    "PENDING": ("Chờ xác nhận", "⏳", "badge-pending"),
    "PREPARING": ("Đang chế biến", "🍳", "badge-preparing"),
    "SERVED": ("Đã lên món", "🍽️", "badge-served"),
    "COMPLETED": ("Hoàn thành", "✅", "badge-completed"),
    "CANCELLED": ("Đã hủy", "❌", "badge-cancelled"),
}


def render_orders_component(
    order_service: Optional[OrderService] = None,
    kitchen_manager: Optional[KitchenManager] = None,
    table_manager: Optional[TableManager] = None,
):
    """Render danh sách các đơn hàng, tìm kiếm, lọc và hủy đơn."""
    if order_service is None:
        order_service = st.session_state.get("order_service") or OrderService()
    if kitchen_manager is None:
        kitchen_manager = st.session_state.get("kitchen_manager") or KitchenManager()
    if table_manager is None:
        table_manager = st.session_state.get("table_manager") or TableManager()

    st.subheader("🧾 Quản lý danh sách Đơn hàng")

    orders = order_service.get_all_orders()
    if not orders:
        st.info("Chưa có đơn hàng nào được tạo trong hệ thống.")
        return

    # Bộ lọc
    c_filter, c_search = st.columns([1.5, 2])
    with c_filter:
        status_opts = ["Tất cả"] + list(ORDER_STATUS_LABELS.keys())
        selected_status = st.selectbox(
            "Lọc theo trạng thái:",
            status_opts,
            format_func=lambda s: "Tất cả" if s == "Tất cả" else f"{STATUS_BADGE_MAP.get(s, (s, ''))[1]} {ORDER_STATUS_LABELS.get(s, s)}",
        )
    with c_search:
        search_query = st.text_input("Tìm kiếm theo Mã đơn hoặc Số bàn:", placeholder="VD: ORD-2026... hoặc 2")

    filtered_orders = orders
    if selected_status != "Tất cả":
        filtered_orders = [o for o in filtered_orders if o.status == selected_status]
    if search_query:
        q = search_query.strip().lower()
        filtered_orders = [
            o for o in filtered_orders
            if q in o.id.lower() or q == str(o.table_id).lower()
        ]

    # Sắp xếp theo created_at mới nhất lên đầu
    filtered_orders.sort(key=lambda o: str(o.created_at), reverse=True)

    st.caption(f"Hiển thị: **{len(filtered_orders)}/{len(orders)}** đơn hàng")

    for order in filtered_orders:
        st_label, st_icon, badge_cls = STATUS_BADGE_MAP.get(order.status, (order.status, "⚪", ""))
        title = (
            f"{st_icon} Đơn hàng: **{order.id}** | Bàn: **{order.table_id}** | "
            f"Trạng thái: **{st_label}** | Tổng: **{order.final_amount:,} VNĐ**"
        )

        with st.expander(title):
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"🕒 **Thời gian tạo:** `{order.created_at}`")
                st.write(f"🔄 **Cập nhật gần nhất:** `{order.updated_at}`")
            with c2:
                st.markdown(f"Trạng thái: <span class='status-badge {badge_cls}'>{st_label}</span>", unsafe_allow_html=True)
                if order.notes:
                    st.caption(f"📝 Ghi chú: {order.notes}")

            # Bảng món
            if order.items:
                items_table_data = [
                    {
                        "Mã món": item.menu_item_id,
                        "Tên món": item.item_name,
                        "Đơn giá": f"{item.unit_price:,} đ",
                        "SL": item.quantity,
                        "Thành tiền": f"{item.subtotal:,} đ",
                        "Ghi chú": item.note or "-",
                    }
                    for item in order.items
                ]
                st.table(items_table_data)

            st.write(
                f"**Tổng tiền:** `{order.total_amount:,} VNĐ` • "
                f"**Giảm giá:** `{order.discount_amount:,} VNĐ` • "
                f"**Khách phải trả:** `{order.final_amount:,} VNĐ`"
            )

            # Nút hủy đơn nếu đơn chưa lên món
            if order.status in ("PENDING", "PREPARING"):
                st.write("")
                if st.button("❌ Hủy đơn hàng này", key=f"cancel_btn_{order.id}"):
                    try:
                        order_service.cancel_order(
                            order.id,
                            reason="Khách yêu cầu hủy qua giao diện",
                            kitchen_manager=kitchen_manager,
                        )
                        st.success(f"Đã hủy đơn `{order.id}` thành công!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi: {e}")

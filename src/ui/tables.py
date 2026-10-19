"""Component giao diện Quản lý Sơ đồ bàn ăn."""
from typing import Optional
import streamlit as st

from src.core.OrderService import OrderService
from src.core.TableManager import TableManager

TABLE_STATUS_MAP = {
    "AVAILABLE": ("Trống", "🟢", "badge-available"),
    "OCCUPIED": ("Có khách", "🔴", "badge-occupied"),
    "RESERVED": ("Đã đặt trước", "🟡", "badge-reserved"),
}


def render_tables_component(
    table_manager: Optional[TableManager] = None,
    order_service: Optional[OrderService] = None,
):
    """Render sơ đồ bàn ăn trực quan và hỗ trợ thao tác đặt/giải phóng bàn."""
    if table_manager is None:
        table_manager = st.session_state.get("table_manager") or TableManager()
    if order_service is None:
        order_service = st.session_state.get("order_service") or OrderService()

    # Luôn làm mới dữ liệu bàn từ backend
    table_manager.load_tables()

    st.subheader("🪑 Sơ đồ bàn ăn nhà hàng")

    tables = table_manager.get_all_tables()
    if not tables:
        st.warning("Chưa có dữ liệu bàn ăn.")
        return

    # Thống kê nhanh
    tot = len(tables)
    avl = sum(1 for t in tables if t.status == "AVAILABLE")
    occ = sum(1 for t in tables if t.status == "OCCUPIED")
    res = sum(1 for t in tables if t.status == "RESERVED")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tổng số bàn", tot)
    m2.metric("🟢 Bàn trống", avl)
    m3.metric("🔴 Đang có khách", occ)
    m4.metric("🟡 Đã đặt trước", res)
    st.divider()

    # Hiển thị dạng lưới 3 cột
    num_cols = 3
    cols = st.columns(num_cols)
    for idx, table in enumerate(tables):
        col_target = cols[idx % num_cols]
        with col_target:
            with st.container(border=True):
                status_raw = table.status
                label, icon, badge_cls = TABLE_STATUS_MAP.get(status_raw, (status_raw, "⚪", ""))
                st.markdown(f"### {icon} {table.name}")
                st.caption(f"Sức chứa: **{table.capacity}** khách")
                st.markdown(f"Trạng thái: <span class='status-badge {badge_cls}'>{label}</span>", unsafe_allow_html=True)

                if table.current_order_id:
                    st.markdown(f"Đơn hiện tại: **`{table.current_order_id}`**")
                    order = order_service.get_order_by_id(table.current_order_id)
                    if order:
                        st.caption(f"Tổng tiền: **{order.final_amount:,} đ** • Trạng thái đơn: `{order.status}`")
                else:
                    st.caption("Chưa có đơn hàng")

                # Thao tác bàn
                st.write("")
                if table.status == "AVAILABLE":
                    if st.button("🔖 Đặt trước", key=f"reserve_btn_{table.id}", use_container_width=True):
                        table_manager.reserve_table(table.id)
                        st.toast(f"Đã đặt trước {table.name}!")
                        st.rerun()
                elif table.status == "RESERVED":
                    if st.button("🔓 Hủy đặt trước", key=f"vacate_btn_{table.id}", use_container_width=True):
                        table_manager.vacate_table(table.id)
                        st.toast(f"Đã giải phóng {table.name} về trạng thái trống!")
                        st.rerun()
                elif table.status == "OCCUPIED":
                    st.info("Bàn đang phục vụ khách.")

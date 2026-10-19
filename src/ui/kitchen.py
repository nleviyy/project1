"""Component giao diện Điều phối Nhà bếp (Kitchen Display System - FIFO)."""
from typing import Optional
import streamlit as st

from src.core.KitchenManager import KitchenManager
from src.core.OrderService import OrderService
from src.models.Order import OrderStatus


def render_kitchen_component(
    kitchen_manager: Optional[KitchenManager] = None,
    order_service: Optional[OrderService] = None,
):
    """Render giao diện điều phối bếp FIFO, bắt đầu chế biến và lên món."""
    if kitchen_manager is None:
        kitchen_manager = st.session_state.get("kitchen_manager") or KitchenManager()
    if order_service is None:
        order_service = st.session_state.get("order_service") or OrderService()

    st.subheader("🍳 Điều phối chế biến Nhà Bếp (KDS - Hàng đợi FIFO)")

    col_cur, col_queue = st.columns([1.2, 1.8], gap="large")

    current_order = kitchen_manager.get_current_order()
    waiting_orders = kitchen_manager.get_waiting_orders()

    # ==============================
    # CỘT 1: ĐƠN ĐANG CHẾ BIẾN
    # ==============================
    with col_cur:
        st.markdown("### 🔥 Đơn đang chế biến")
        if current_order:
            with st.container(border=True):
                c_id = getattr(current_order, "id", getattr(current_order, "order_id", "---"))
                c_tbl = getattr(current_order, "table_id", "---")
                c_notes = getattr(current_order, "notes", "")
                c_status = getattr(current_order, "status", OrderStatus.PREPARING)
                c_prep = (
                    current_order.calculate_prep_time()
                    if hasattr(current_order, "calculate_prep_time")
                    else 0
                )

                st.markdown(f"#### 🍽️ Đơn: `{c_id}` • Bàn: `{c_tbl}`")
                st.markdown(
                    f"Trạng thái: <span class='status-badge badge-preparing'>"
                    f"{OrderStatus.get_label(c_status)}</span>",
                    unsafe_allow_html=True,
                )
                st.caption(f"⏱️ Thời gian chế biến ước tính: **{c_prep} phút**")
                st.progress(0.75, text=f"Tiến độ: Đang chế biến (~{c_prep} phút)")
                if c_notes:
                    st.info(f"📝 Ghi chú: {c_notes}")

                st.markdown("**Danh sách món cần nấu:**")
                items = getattr(current_order, "items", [])
                for item in items:
                    if isinstance(item, dict):
                        name = item.get("item_name", item.get("ten", "Món ăn"))
                        qty = item.get("quantity", item.get("sl", 1))
                        note = item.get("note", item.get("ghi_chu", ""))
                    else:
                        name = getattr(item, "item_name", "Món ăn")
                        qty = getattr(item, "quantity", 1)
                        note = getattr(item, "note", "")

                    st.write(f"- **{qty}x** {name}" + (f" *(Ghi chú: {note})*" if note else ""))

                st.write("")
                if st.button("🍽️ Đã nấu xong & Lên món cho khách", type="primary", use_container_width=True):
                    try:
                        kitchen_manager.advance_status()  # PREPARING -> SERVED
                        kitchen_manager.finish_current_order()
                        order_service.serve_order(c_id)
                        st.success(f"✅ Đơn `{c_id}` đã được lên bàn phục vụ!")
                        st.toast(f"Đơn {c_id} đã lên món!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi: {e}")
        else:
            st.info("Bếp hiện đang trống. Sẵn sàng tiếp nhận đơn tiếp theo từ hàng đợi!")

    # ==============================
    # CỘT 2: HÀNG ĐỢI ĐƠN CHỜ NẤU
    # ==============================
    with col_queue:
        q_count = len(waiting_orders)
        st.markdown(f"### ⏳ Hàng đợi chờ nấu ({q_count} đơn đang chờ)")

        # Nút lấy đơn tiếp theo vào nấu
        btn_disabled = (current_order is not None) or (q_count == 0)
        btn_label = "▶️ Bắt đầu nấu đơn tiếp theo (FIFO)" if current_order is None else "⚠️ Hãy hoàn tất đơn đang nấu trước"

        if st.button(btn_label, type="secondary", disabled=btn_disabled, use_container_width=True):
            try:
                next_order = kitchen_manager.peek_next_order()
                if next_order:
                    o_id = getattr(next_order, "id", getattr(next_order, "order_id", "---"))
                    if not order_service.start_preparing_order(o_id):
                        st.error("Không thể bắt đầu đơn; hãy kiểm tra lại thứ tự Queue.")
                    else:
                        st.toast(f"Bắt đầu nấu đơn {o_id}!")
                        st.rerun()
            except Exception as e:
                st.error(f"Lỗi: {e}")

        if not waiting_orders:
            st.caption("Chưa có đơn hàng nào trong hàng đợi.")
        else:
            for idx, order in enumerate(waiting_orders):
                o_id = getattr(order, "id", getattr(order, "order_id", f"ORD-{idx}"))
                o_tbl = getattr(order, "table_id", "---")
                o_notes = getattr(order, "notes", "")
                o_prep = (
                    order.calculate_prep_time()
                    if hasattr(order, "calculate_prep_time")
                    else 0
                )
                wait_est = kitchen_manager.estimate_wait_time(order)

                with st.expander(f"#{idx+1} [FIFO] Đơn: **`{o_id}`** • Bàn: **{o_tbl}** • Chờ ước tính: ~**{wait_est} phút**"):
                    if o_notes:
                        st.caption(f"📝 Ghi chú: {o_notes}")
                    st.caption(f"⏱️ Thời gian nấu món này: {o_prep} phút")
                    items = getattr(order, "items", [])
                    for item in items:
                        if isinstance(item, dict):
                            name = item.get("item_name", item.get("ten", "Món ăn"))
                            qty = item.get("quantity", item.get("sl", 1))
                        else:
                            name = getattr(item, "item_name", "Món ăn")
                            qty = getattr(item, "quantity", 1)
                        st.write(f"- {qty}x {name}")

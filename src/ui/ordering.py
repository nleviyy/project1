"""Component giao diện Gọi món & Giỏ hàng."""
import json
from pathlib import Path
from typing import Optional
import streamlit as st

from src.core.Cart import Cart
from src.core.KitchenManager import KitchenManager
from src.core.OrderService import OrderService
from src.core.TableManager import TableManager
from src.models.MenuCatalog import MenuCatalog
from src.models.Order import ORDER_STATUS_LABELS, OrderStatus
from src.models.OrderItem import OrderItem
from src.ui.common import get_menu_catalog


def render_ordering_component(
    menu_catalog: Optional[MenuCatalog] = None,
    cart: Optional[Cart] = None,
    order_service: Optional[OrderService] = None,
    table_manager: Optional[TableManager] = None,
    kitchen_manager: Optional[KitchenManager] = None,
):
    """Render giao diện chọn món và giỏ hàng kết nối với các class nghiệp vụ."""
    if menu_catalog is None:
        menu_catalog = get_menu_catalog()
    if cart is None:
        if "cart" not in st.session_state:
            st.session_state.cart = Cart()
        cart = st.session_state.cart
    if order_service is None:
        order_service = st.session_state.get("order_service") or OrderService()
    if table_manager is None:
        table_manager = st.session_state.get("table_manager") or TableManager()
    if kitchen_manager is None:
        kitchen_manager = st.session_state.get("kitchen_manager") or KitchenManager()

    # Luôn làm mới danh sách bàn từ backend để phản ánh chính xác trạng thái thực tế
    table_manager.load_tables()


    if "cart_rev" not in st.session_state:
        st.session_state.cart_rev = 0

    col_menu, col_cart = st.columns([1.6, 1.2], gap="large")

    # ==========================
    # CỘT TRÁI: THỰC ĐƠN MÓN ĂN
    # ==========================
    with col_menu:
        st.subheader("📜 Thực đơn nhà hàng")
        all_items = menu_catalog.get_all_items()
        categories = ["Tất cả"] + sorted(list({item.category for item in all_items if item.category}))

        selected_cat = st.pills("Danh mục món:", categories, default="Tất cả")
        filtered_items = (
            all_items
            if selected_cat == "Tất cả"
            else [i for i in all_items if i.category == selected_cat]
        )

        for item in filtered_items:
            with st.container(border=True):
                c_img, c_info, c_action = st.columns([1, 2.2, 1.3], vertical_alignment="center")
                with c_img:
                    if getattr(item, "image", None):
                        st.image(item.image, use_container_width=True)
                    else:
                        st.markdown("### 🍽️")

                with c_info:
                    st.markdown(f"**{item.name}**")
                    st.caption(f"Loại: {item.category} • Thời gian nấu: ~{item.prep_time} phút")
                    st.markdown(f"<span class='item-price'>{item.price:,} VNĐ</span>", unsafe_allow_html=True)
                    if getattr(item, "description", None):
                        st.caption(item.description)

                with c_action:
                    if not item.is_available:
                        st.warning("Hết món")
                    else:
                        qty = st.number_input(
                            "SL",
                            min_value=1,
                            max_value=20,
                            value=1,
                            step=1,
                            key=f"qty_input_{item.id}_{st.session_state.cart_rev}",
                        )
                        note = st.text_input(
                            "Ghi chú",
                            placeholder="Ít cay, không hành...",
                            key=f"note_input_{item.id}_{st.session_state.cart_rev}",
                        )
                        if st.button("➕ Thêm vào giỏ", key=f"btn_add_{item.id}_{st.session_state.cart_rev}", type="primary", use_container_width=True):
                            try:
                                cart.add_item(item, quantity=qty, note=note)
                                st.session_state.cart_rev += 1
                                st.toast(f"Đã thêm {qty}x {item.name} vào giỏ!")
                                st.rerun()
                            except ValueError as e:
                                st.error(str(e))

    # ==========================
    # CỘT PHẢI: GIỎ HÀNG & ĐẶT MÓN
    # ==========================
    with col_cart:
        st.subheader("🛒 Giỏ hàng của bạn")
        
        # Nút Undo / Redo
        u_col, r_col, clr_col = st.columns(3)
        with u_col:
            if st.button("↶ Undo", disabled=not cart.can_undo(), use_container_width=True):
                cart.undo()
                st.session_state.cart_rev += 1
                st.rerun()
        with r_col:
            if st.button("↷ Redo", disabled=not cart.can_redo(), use_container_width=True):
                cart.redo()
                st.session_state.cart_rev += 1
                st.rerun()
        with clr_col:
            if st.button("🗑️ Xóa hết", disabled=cart.is_empty(), use_container_width=True):
                cart.clear()
                st.session_state.cart_rev += 1
                st.rerun()

        cart_items = cart.get_order_items()

        if not cart_items:
            st.info("Giỏ hàng đang trống. Hãy chọn món từ thực đơn bên trái!")
        else:
            with st.container(border=True):
                for item in cart_items:
                    c1, c2, c3 = st.columns([2.5, 1, 1], vertical_alignment="center")
                    with c1:
                        st.markdown(f"**{item['item_name']}**")
                        st.caption(f"{item['unit_price']:,} đ × {item['quantity']} = **{item['subtotal']:,} đ**")
                        if item.get("note"):
                            st.caption(f"📝 {item['note']}")
                    with c2:
                        new_q = st.number_input(
                            "SL",
                            min_value=1,
                            max_value=20,
                            value=int(item["quantity"]),
                            step=1,
                            key=f"cart_q_{item['menu_item_id']}_{st.session_state.cart_rev}",
                            label_visibility="collapsed",
                        )
                        if new_q != item["quantity"]:
                            cart.update_quantity(item["menu_item_id"], new_q)
                            st.session_state.cart_rev += 1
                            st.rerun()
                    with c3:
                        if st.button("❌", key=f"del_{item['menu_item_id']}_{st.session_state.cart_rev}", help="Xóa món"):
                            cart.remove_item(item["menu_item_id"])
                            st.session_state.cart_rev += 1
                            st.rerun()
                    st.divider()

                total_amount = cart.calculate_total()
                st.markdown(f"### 💰 Tổng tiền: `{total_amount:,} VNĐ`")

            # Phần chọn bàn và ghi chú đơn hàng
            st.markdown("#### 🪑 Chọn bàn phục vụ")
            all_tables = table_manager.get_all_tables()
            available_tables = [t for t in all_tables if t.is_available]

            table_options = [(t.id, f"{t.name} (Sức chứa: {t.capacity} người) - 🟢 Trống") for t in available_tables]
            # Nếu bàn đã có khách, hiển thị thêm lựa chọn nếu muốn
            table_options.append((0, "🛍️ Mang về (Takeaway)"))

            if not available_tables:
                st.warning("⚠️ Hiện tại không còn bàn trống trong nhà hàng. Quý khách có thể chọn Mang về!")

            selected_table_choice = st.selectbox(
                "Bàn ăn đón khách:",
                options=table_options,
                format_func=lambda opt: opt[1],
            )
            selected_table_id = selected_table_choice[0]

            order_notes = st.text_area("Ghi chú cho cả đơn hàng:", placeholder="Khách bàn 2 cần ăn sớm...")

            if st.button("🚀 XÁC NHẬN ĐẶT MÓN", type="primary", use_container_width=True):
                # 1. Chuyển cart_items thành OrderItem models
                order_items_list = []
                for ci in cart_items:
                    order_items_list.append(
                        OrderItem(
                            menu_item_id=ci["menu_item_id"],
                            item_name=ci["item_name"],
                            unit_price=ci["unit_price"],
                            quantity=ci["quantity"],
                            subtotal=ci["subtotal"],
                            note=ci.get("note", ""),
                            prep_time=ci.get("prep_time", 0),
                        )
                    )

                # 2. Tạo đơn qua OrderService
                try:
                    table_id_to_use = selected_table_id
                    order = order_service.place_order(
                        table_id=table_id_to_use,
                        items=order_items_list,
                        notes=order_notes,
                        kitchen_manager=kitchen_manager,
                    )

                    # Ước tính thời gian chờ sau khi đơn đã được xếp hàng.
                    wait_time = kitchen_manager.estimate_wait_time(order)

                    cart.clear()
                    st.session_state.cart_rev += 1
                    st.session_state["placed_order_info"] = {
                        "id": order.id,
                        "table_id": table_id_to_use,
                        "wait_time": wait_time,
                    }
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi khi tạo đơn hàng: {e}")

    # ====================================================
    # PHẦN THEO DÕI TRẠNG THÁI ĐƠN HÀNG (YÊU CẦU ĐẶT MÓN)
    # ====================================================
    st.divider()
    c_recent, c_track = st.columns([1.5, 1.5], gap="large")

    with c_recent:
        st.markdown("#### 📌 Đơn hàng vừa đặt của bạn")
        placed_info = st.session_state.get("placed_order_info")
        if placed_info:
            recent_order = order_service.get_order_by_id(placed_info["id"])
            if recent_order:
                tbl_txt = f"Bàn số {recent_order.table_id}" if recent_order.table_id > 0 else "Mang về"
                st_label = ORDER_STATUS_LABELS.get(recent_order.status, recent_order.status)
                with st.container(border=True):
                    st.success(f"🎉 Đơn hàng **`{recent_order.id}`** đang được xử lý!")
                    st.write(f"- 🪑 **Địa điểm:** {tbl_txt}")
                    st.write(f"- ⏱️ **Thời gian chờ dự kiến:** ~`{placed_info.get('wait_time', 15)} phút`")
                    st.write(f"- 🏷️ **Trạng thái thời gian thực:** `{st_label}` ({recent_order.status})")
                    st.write(f"- 💰 **Tổng tiền:** `{recent_order.final_amount:,} VNĐ`")
                    if st.button("Đóng thông báo này", key="btn_close_recent_order"):
                        del st.session_state["placed_order_info"]
                        st.rerun()
            else:
                st.caption("Không tìm thấy thông tin chi tiết đơn hàng vừa đặt.")
        else:
            st.info("Chưa có đơn hàng mới nào vừa được đặt từ phiên làm việc này.")

    with c_track:
        st.markdown("#### 🔍 Tra cứu trạng thái đơn hàng")
        with st.container(border=True):
            track_id = st.text_input("Nhập mã đơn cần tra cứu:", placeholder="VD: ORD-2026...")
            if track_id:
                searched_order = order_service.get_order_by_id(track_id.strip())
                if searched_order:
                    s_label = ORDER_STATUS_LABELS.get(searched_order.status, searched_order.status)
                    s_tbl = f"Bàn số {searched_order.table_id}" if searched_order.table_id > 0 else "Mang về"
                    st.markdown(f"**Mã đơn:** `{searched_order.id}` • **{s_tbl}**")
                    st.markdown(f"Trạng thái: **`{s_label}`** • Tạo lúc: `{searched_order.created_at}`")
                    st.caption(f"Số lượng món: {len(searched_order.items)} món • Tổng tiền: {searched_order.final_amount:,} đ")
                else:
                    st.warning(f"Không tìm thấy đơn hàng với mã '{track_id}'.")


"""Streamlit components for the restaurant ordering and management system."""

import json
from html import escape
from pathlib import Path
from typing import Optional

import streamlit as st

from src.core.Cart import Cart
from src.core.KitchenManager import KitchenManager
from src.core.OrderService import OrderService
from src.core.PaymentService import PaymentService
from src.core.TableManager import TableManager
from src.core.paths import (
    PROJECT_ROOT,
    DATA_DIR,
    MENU_PATH,
    TABLES_PATH,
    ORDERS_PATH,
    PAYMENTS_PATH,
    INVOICES_PATH,
)
from src.core.JSONStorage import load_data
from src.core.sorting import merge_sort
from src.models.HashTable import HashTable
from src.models.MenuCatalog import MenuCatalog
from src.models.MenuItem import MenuItem
from src.models.Order import Order
from src.models.Payment import Payment

PAYMENT_METHODS = {
    "Tiền mặt": "CASH",
    "Chuyển khoản": "BANK_TRANSFER",
    "Thẻ": "CARD",
}
ORDER_STATUS_LABELS = {
    "PENDING": "Chờ chế biến",
    "PREPARING": "Đang nấu",
    "SERVED": "Đã lên món",
    "COMPLETED": "Đã thanh toán",
    "CANCELLED": "Đã hủy",
}


def _select_menu_suggestion(item_name: str) -> None:
    st.session_state["header_menu_search"] = item_name



def apply_custom_styles() -> None:
    """Apply the lavender and purple dashboard theme."""
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');
:root {
    --purple-900: #5420c8;
    --purple-700: #6b35dc;
    --purple-600: #7c3aed;
    --purple-500: #a855f7;
    --lavender: #e9ddff;
    --canvas: #f7f3ff;
    --ink: #25154f;
    --muted: #81769c;
}
html, body, [class*="css"], .stApp {
    font-family: "Be Vietnam Pro", sans-serif;
}
.stApp {
    color: var(--ink);
    background: var(--canvas);
}
.block-container {
    max-width: 95%; /* Mở rộng tối đa chiều rộng trang */
    padding-top: 1.35rem;
    padding-bottom: 3rem;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #652bd4 0%, #5420c8 55%, #4820ad 100%);
}
[data-testid="stSidebar"] * {
    color: #fff;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    border-radius: 12px;
    padding: .45rem .65rem;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(255,255,255,.15);
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,.22);
}
h1, h2, h3, h4 {
    color: var(--ink);
    letter-spacing: -.035em;
}
[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid rgba(124,58,237,.10);
    border-radius: 20px;
    background: #fff;
    box-shadow: 0 10px 28px rgba(84,32,200,.08);
}
[data-testid="stMetric"] {
    padding: .8rem 1rem;
    border: 1px solid rgba(124,58,237,.10);
    border-radius: 16px;
    background: #fff;
    box-shadow: 0 8px 22px rgba(84,32,200,.06);
}
[data-testid="stMetricLabel"] {
    color: var(--muted);
}
[data-testid="stImage"] img {
    width: 100%;
    height: 100px;
    aspect-ratio: 4 / 3;
    object-fit: cover;
    border-radius: 12px;
}
.menu-item-title {
    overflow: hidden;
    font-size: .875rem;
    font-weight: 700;
    line-height: 1.25;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.menu-item-price {
    font-size: .65rem;
    font-weight: 700;
    white-space: nowrap;
}
[class*="st-key-add_menu_"] button {
    min-height: 1.8rem;
    padding: .15rem .2rem;
    border: 0;
    border-radius: 999px;
    color: #fff;
    background: #155c45;
    font-size: .55rem;
    white-space: nowrap;
}
[class*="st-key-add_menu_"] button:hover {
    border-color: transparent;
    color: #fff;
    background: #104b39;
    box-shadow: none;
}
[data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]:nth-child(4)) {
    display: grid !important;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: .75rem;
}
[data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]:nth-child(4)) > [data-testid="stColumn"] {
    width: auto !important;
    min-width: 0;
    flex: none !important;
}
[data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]:nth-child(4)) [data-testid="stVerticalBlockBorderWrapper"] {
    padding: .5rem;
}
[data-testid="stHorizontalBlock"]:has(.menu-item-price) {
    gap: .25rem;
}
@media (max-width: 700px) {
    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]:nth-child(4)) {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}
.stButton > button, .stFormSubmitButton > button {
    min-height: 2.55rem;
    border: 1px solid transparent;
    border-radius: 12px;
    color: #fff;
    background: linear-gradient(135deg, var(--purple-600), var(--purple-900));
    font-weight: 700;
    transition: transform .15s ease, box-shadow .15s ease;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    border-color: transparent;
    color: #fff;
    background: linear-gradient(135deg, var(--purple-500), var(--purple-700));
    box-shadow: 0 7px 16px rgba(84,32,200,.2);
    transform: translateY(-1px);
}
.stButton > button:disabled {
    color: #81769c;
    background: #eee8fa;
}
[data-testid="stExpander"] {
    overflow: hidden;
    border: 1px solid var(--lavender);
    border-radius: 15px;
    background: #fff;
}
[data-testid="stExpander"] summary:hover {
    color: var(--purple-900);
}
[data-testid="stDataFrame"], [data-testid="stTable"] {
    border: 1px solid var(--lavender);
    border-radius: 14px;
    overflow: hidden;
}
[data-testid="stAlert"] {
    border-radius: 14px;
}
@media (max-width: 700px) {
    .block-container {
        padding: 1rem .8rem 2rem;
    }
}
</style>
""",
        unsafe_allow_html=True,
    )


def _load_menu_catalog() -> MenuCatalog:
    if not MENU_PATH.exists():
        raise FileNotFoundError(f"Không tìm thấy thực đơn: {MENU_PATH}")
    records = load_data(MENU_PATH, default_data=[])
    if not isinstance(records, list):
        raise ValueError("Dữ liệu thực đơn phải là một danh sách.")
    catalog = MenuCatalog()
    catalog.load_from_dict(records)
    if len(catalog.get_all_items()) != len(records):
        raise ValueError("Thực đơn có món không hợp lệ hoặc mã món bị trùng.")
    return catalog



def _ensure_kitchen_synced(order_service: OrderService, kitchen_manager: KitchenManager) -> None:
    """Khôi phục hàng đợi bếp từ file một lần cho mỗi phiên làm việc."""
    if not st.session_state.get("kitchen_synced"):
        order_service.sync_kitchen(kitchen_manager)
        st.session_state.kitchen_synced = True


def _money(value: int | float) -> str:
    return f"{value:,.0f} VNĐ"


def _table_label(table_id: int | str) -> str:
    return f"Bàn {table_id}" if str(table_id).isdigit() else str(table_id)


def _read_payment_records(payment_service: PaymentService) -> list[dict]:
    path = Path(payment_service.payments_path)
    if not path.exists():
        return []
    records = load_data(path, default_data=[])
    if not isinstance(records, list) or any(not isinstance(row, dict) for row in records):
        raise ValueError(f"Dữ liệu thanh toán trong {path.name} không hợp lệ.")
    return records



def render_ordering_component(
    menu_catalog: Optional[MenuCatalog] = None,
    cart: Optional[Cart] = None,
    order_service: Optional[OrderService] = None,
    table_manager: Optional[TableManager] = None,
    kitchen_manager: Optional[KitchenManager] = None,
) -> None:
    """Render the menu and cart, then create orders through OrderService."""
    menu_catalog = menu_catalog or _load_menu_catalog()
    cart = cart or st.session_state.get("cart") or Cart()
    order_service = order_service or st.session_state.get("order_service") or OrderService()
    table_manager = table_manager or st.session_state.get("table_manager") or TableManager()
    kitchen_manager = kitchen_manager or st.session_state.get("kitchen_manager") or KitchenManager()
    _ensure_kitchen_synced(order_service, kitchen_manager)
    if notice := st.session_state.pop("checkout_notice", None):
        st.success(notice)
    tab_order = st.container()

    with tab_order:
        menu_column = st.container()
        with menu_column:
            st.subheader("📜 Thực đơn")
            items = menu_catalog.get_all_items()

            col_search, col_pills = st.columns([1, 1], vertical_alignment="bottom")
            with col_search:
                search_query = st.text_input(
                    "Tìm món theo tên",
                    key="header_menu_search",
                    placeholder="Gõ tên món...",
                )
            with col_pills:
                categories = ["Tất cả", *menu_catalog.get_categories()]
                if hasattr(st, "pills"):
                    selected_category = st.pills(
                        "Danh mục",
                        categories,
                        default="Tất cả",
                        key="menu_category_pills",
                    ) or "Tất cả"
                else:
                    selected_category = st.selectbox(
                        "Danh mục món",
                        categories,
                        key="menu_category_select",
                    )

            search = search_query.strip()
            suggestions = menu_catalog.autocomplete_items(search, max_results=5) if search else []
            if suggestions:
                st.caption("Gợi ý món (bấm để chọn nhanh):")
                suggestion_columns = st.columns(len(suggestions))
                for index, s_item in enumerate(suggestions):
                    suggestion_columns[index].button(
                        f"{s_item.name} · {s_item.id}",
                        key=f"menu_suggestion_{s_item.id}",
                        on_click=_select_menu_suggestion,
                        args=(s_item.name,),
                        width="stretch",
                    )

            filtered = [
                item
                for item in items
                if (selected_category == "Tất cả" or item.category == selected_category)
                and (
                    not search
                    or search.casefold() in item.name.casefold()
                    or search.casefold() in item.id.casefold()
                )
            ]
            for index, item in enumerate(filtered):
                if index % 4 == 0:
                    cards = st.columns(4, gap="small")
                with cards[index % 4]:
                    with st.container(border=True):
                        if item.image:
                            st.image(item.image, width="stretch")
                        st.caption(
                            f"{item.category} · "
                            f"{'🟢 Còn món' if item.is_available else '🔴 Tạm hết'}"
                        )
                        st.markdown(
                            f'<div class="menu-item-title">{escape(item.name)}</div>',
                            unsafe_allow_html=True,
                        )
                        price_columns = st.columns(
                            [1.25, 1.4],
                            vertical_alignment="center",
                        )
                        price_columns[0].markdown(
                            f'<div class="menu-item-price">{item.price:,.0f} đ</div>',
                            unsafe_allow_html=True,
                        )
                        if item.is_available:
                            with price_columns[1]:
                                if st.button(
                                    "+ Thêm giỏ",
                                    key=f"add_menu_{item.id}",
                                    help="Thêm vào giỏ",
                                    width="stretch",
                                ):
                                    try:
                                        cart.add_item(item)
                                    except ValueError as error:
                                        st.error(str(error))
                                    else:
                                        st.toast(f"Đã thêm {item.name} vào giỏ.")
                                        st.rerun()
                        st.caption(f"◷ {item.prep_time} phút · {item.unit}")
                        if item.description:
                            with st.expander("Mô tả món"):
                                st.write(item.description)
                        if not item.is_available:
                            st.button(
                                "Tạm hết món",
                                key=f"unavailable_{item.id}",
                                disabled=True,
                                width="stretch",
                            )


def render_tables_component(
    table_manager: Optional[TableManager] = None,
    order_service: Optional[OrderService] = None,
) -> None:
    """Render table availability and the active order associated with each table."""
    table_manager = table_manager or st.session_state.get("table_manager") or TableManager()
    order_service = order_service or st.session_state.get("order_service") or OrderService()
    st.subheader("🪑 Sơ đồ bàn ăn")
    tables = table_manager.get_all_tables()
    available = sum(table.is_available for table in tables)
    occupied = sum(table.status == "OCCUPIED" for table in tables)
    reserved = sum(table.status == "RESERVED" for table in tables)
    metrics = st.columns(3)
    metrics[0].metric("Bàn trống", f"{available}/{len(tables)}")
    metrics[1].metric("Đang phục vụ", occupied)
    metrics[2].metric("Đã đặt trước", reserved)
    orders_by_id = HashTable()
    for order in order_service.get_all_orders():
        orders_by_id.put(order.id, order)
    columns = st.columns(3, gap="large")
    for index, table in enumerate(tables):
        with columns[index % len(columns)]:
            with st.container(border=True):
                status_label = {
                    "AVAILABLE": "🟢 Bàn trống",
                    "OCCUPIED": "🔵 Đang sử dụng",
                    "RESERVED": "🟠 Đã đặt trước",
                }.get(table.status, table.status)
                st.markdown(f"### {table.name}")
                st.caption(f"{status_label} · Sức chứa {table.capacity} người")
                active_order = orders_by_id.get(table.current_order_id)

                if active_order is not None:
                    st.write(
                        f"Đơn **{active_order.id}** · "
                        f"{ORDER_STATUS_LABELS.get(active_order.status, active_order.status)}"
                    )
                    st.caption(
                        ", ".join(
                            f"{item.item_name} × {item.quantity}"
                            for item in active_order.items
                        )
                    )


def render_kitchen_component(
    kitchen_manager: Optional[KitchenManager] = None,
    order_service: Optional[OrderService] = None,
) -> None:
    """Render the FIFO kitchen queue and persist its state transitions."""
    kitchen_manager = kitchen_manager or st.session_state.get("kitchen_manager") or KitchenManager()
    order_service = order_service or st.session_state.get("order_service") or OrderService()
    _ensure_kitchen_synced(order_service, kitchen_manager)
    st.subheader("🍳 Điều phối bếp · Hàng đợi FIFO")
    current_order = kitchen_manager.get_current_order()
    waiting_orders = kitchen_manager.get_waiting_orders()
    metrics = st.columns(3)
    metrics[0].metric("Đang chờ", len(waiting_orders))
    metrics[1].metric("Đang chế biến", current_order.id if current_order else "—")
    metrics[2].metric("Thời gian nấu", f"{current_order.calculate_prep_time()} phút" if current_order else "—")

    if current_order is not None:
        with st.container(border=True):
            st.markdown(
                f"### 🔥 Đơn đang chế biến · {current_order.id} · "
                f"{_table_label(current_order.table_id)}"
            )
            if current_order.notes:
                st.info(current_order.notes)
            st.dataframe(
                [
                    {
                        "Món": item.item_name,
                        "Số lượng": item.quantity,
                        "Ghi chú": item.note or "",
                    }
                    for item in current_order.items
                ],
                hide_index=True,
                width="stretch",
            )
            col_k_finish, col_k_cancel = st.columns([1.5, 1])
            if col_k_finish.button("✓ Hoàn tất chế biến · Lên món", type="primary", width="stretch"):
                try:
                    order_service.kitchen_advance(kitchen_manager)
                    order_service.kitchen_finish(kitchen_manager)
                except (KeyError, OSError, ValueError) as error:
                    st.error(f"Không thể cập nhật bếp: {error}")
                else:
                    st.success(f"Đơn {current_order.id} đã được lên món.")
                    st.rerun()
            if col_k_cancel.button("✕ Hủy đơn đang chế biến", width="stretch"):
                try:
                    order_service.cancel_order(
                        current_order.id,
                        reason="Hủy từ điều phối bếp",
                        kitchen_manager=kitchen_manager,
                    )
                except Exception as error:
                    st.error(f"Không thể hủy: {error}")
                else:
                    st.warning(f"Đã hủy đơn {current_order.id}.")
                    st.rerun()
    elif waiting_orders:
        st.markdown("### ⏳ Hàng đợi chờ chế biến")
        for position, order in enumerate(waiting_orders, start=1):
            with st.container(border=True):
                st.markdown(
                    f"**#{position} · {order.id} · {_table_label(order.table_id)}**"
                )
                st.caption(
                    f"Chờ ước tính: {kitchen_manager.estimate_wait_time(order)} phút · "
                    f"Chế biến: {order.calculate_prep_time()} phút"
                )
                col_o_info, col_o_btn = st.columns([3, 1])
                with col_o_info:
                    st.write(
                        ", ".join(
                            f"{item.quantity} × {item.item_name}"
                            + (f" ({item.note})" if item.note else "")
                            for item in order.items
                        )
                    )
                with col_o_btn:
                    if st.button("Hủy đơn", key=f"cancel_wait_{order.id}", width="stretch"):
                        order_service.cancel_order(
                            order.id,
                            reason="Khách hủy trong lúc chờ bếp",
                            kitchen_manager=kitchen_manager,
                        )
                        st.toast(f"Đã hủy đơn chờ {order.id}.")
                        st.rerun()
        if st.button("▶ Bắt đầu đơn tiếp theo", type="primary"):
            try:
                order_service.kitchen_start_next(kitchen_manager)
            except (OSError, ValueError) as error:
                st.error(f"Không thể bắt đầu chế biến: {error}")
            else:
                st.rerun()
    else:
        st.info(
            "Hàng đợi đang trống. Đơn mới sẽ xuất hiện tại đây khi được xác nhận "
            "ở mục Thực đơn."
        )


def render_orders_component(
    order_service: Optional[OrderService] = None,
    kitchen_manager: Optional[KitchenManager] = None,
    table_manager: Optional[TableManager] = None,
) -> None:
    """Render searchable order history and cancellation controls."""
    order_service = order_service or st.session_state.get("order_service") or OrderService()
    kitchen_manager = kitchen_manager or st.session_state.get("kitchen_manager") or KitchenManager()
    table_manager = table_manager or st.session_state.get("table_manager") or TableManager()
    st.subheader("🧾 Danh sách đơn hàng")
    orders = order_service.get_all_orders()
    filter_column, search_column = st.columns([1, 2])
    statuses = ["Tất cả", "PENDING", "PREPARING", "SERVED", "COMPLETED", "CANCELLED"]
    selected_status = filter_column.selectbox(
        "Trạng thái",
        statuses,
        format_func=lambda status: (
            "Tất cả" if status == "Tất cả" else ORDER_STATUS_LABELS.get(status, status)
        ),
    )
    query = search_column.text_input("Tìm mã đơn hoặc mã bàn")
    filtered_orders = [
        order
        for order in orders
        if (selected_status == "Tất cả" or order.status == selected_status)
        and (
            not query.strip()
            or query.strip().casefold() in order.id.casefold()
            or query.strip().casefold() in str(order.table_id).casefold()
        )
    ]
    filtered_orders = merge_sort(
        filtered_orders,
        key=lambda order: str(order.created_at),
        reverse=True,
    )

    st.caption(f"Hiển thị {len(filtered_orders)} / {len(orders)} đơn hàng")
    if not filtered_orders:
        st.info("Không tìm thấy đơn hàng phù hợp.")
    for order in filtered_orders:
        _render_order_details(
            order,
            order_service=order_service,
            kitchen_manager=kitchen_manager,
            table_manager=table_manager,
            allow_cancel=True,
        )


def _render_order_details(
    order: Order,
    *,
    order_service: OrderService,
    kitchen_manager: KitchenManager,
    table_manager: TableManager,
    allow_cancel: bool,
) -> None:
    title = (
        f"{order.id} · {_table_label(order.table_id)} · "
        f"{ORDER_STATUS_LABELS.get(order.status, order.status)} · "
        f"{_money(order.final_amount)}"
    )
    with st.expander(title):
        st.caption(f"Tạo lúc {order.created_at} · Cập nhật {order.updated_at or '—'}")
        if order.notes:
            st.write(f"Ghi chú: {order.notes}")
        st.dataframe(
            [
                {
                    "Món": item.item_name,
                    "Số lượng": item.quantity,
                    "Đơn giá": _money(item.unit_price),
                    "Thành tiền": _money(item.subtotal),
                    "Ghi chú": item.note or "",
                }
                for item in order.items
            ],
            hide_index=True,
            width="stretch",
        )
        st.caption(
            f"Tổng tiền thanh toán: {_money(order.final_amount)}"
        )
        if allow_cancel and order.status in ("PENDING", "PREPARING"):
            if st.button("Hủy đơn hàng", key=f"cancel_order_{order.id}"):
                try:
                    order_service.cancel_order(
                        order.id,
                        reason="Hủy từ giao diện quản lý",
                        kitchen_manager=kitchen_manager,
                    )
                    table_manager.load_tables()
                except (KeyError, OSError, ValueError) as error:
                    st.error(f"Không thể hủy đơn: {error}")
                else:
                    st.success(f"Đã hủy đơn {order.id}.")
                    st.rerun()


def render_payment_component(
    payment_service: Optional[PaymentService] = None,
    order_service: Optional[OrderService] = None,
    table_manager: Optional[TableManager] = None,
) -> None:
    """Render checkout for served orders and recent transaction history."""
    payment_service = payment_service or st.session_state.get("payment_service") or PaymentService()
    order_service = order_service or st.session_state.get("order_service") or OrderService()
    table_manager = table_manager or st.session_state.get("table_manager") or TableManager()
    st.subheader("💳 Thu ngân & thanh toán")

    if "payment_notice" in st.session_state and st.session_state.payment_notice:
        st.success(st.session_state.payment_notice)
        if st.button("✕ Đóng thông báo", key="btn_close_payment_notice"):
            st.session_state.pop("payment_notice", None)
            st.rerun()

    payment_column, history_column = st.columns([1, 1.25], gap="large")
    served_orders = order_service.filter_orders_by_status("SERVED")
    with payment_column:
        st.markdown("### 🧾 Thanh toán đơn")
        if not served_orders:
            st.info("Chưa có đơn đã lên món cần thanh toán.")
        else:
            with st.form("payment_checkout"):
                selected_order = st.selectbox(
                    "Chọn đơn hàng",
                    served_orders,
                    format_func=lambda order: (
                        f"{order.id} · {_table_label(order.table_id)} · "
                        f"{_money(order.final_amount)}"
                    ),
                )
                st.info(f"Khách cần thanh toán: **{_money(selected_order.final_amount)}**")
                method_label = st.selectbox("Phương thức", list(PAYMENT_METHODS))
                cashier_name = st.text_input("Tên nhân viên thu ngân", value="Thu ngân chính")
                cash_received = None
                transaction_code = None
                transaction_successful = None
                method = PAYMENT_METHODS[method_label]
                if method == "CASH":
                    cash_received = st.number_input(
                        "Tiền khách đưa (VNĐ)",
                        min_value=0,
                        value=selected_order.final_amount,
                        step=1000,
                    )
                    change = cash_received - selected_order.final_amount
                    if change >= 0:
                        st.caption(f"💵 Tiền thừa trả lại: **{_money(change)}**")
                    else:
                        st.caption(f"⚠️ Chưa đủ (thiếu {_money(abs(change))})")
                else:
                    transaction_code = st.text_input("Mã giao dịch")
                    transaction_successful = st.checkbox(
                        "Cổng thanh toán xác nhận thành công",
                        value=True,
                    )
                submitted = st.form_submit_button(
                    "✓ Xác nhận thanh toán",
                    type="primary",
                    width="stretch",
                )
            if submitted:
                try:
                    result = payment_service.pay_order(
                        order_id=selected_order.id,
                        method=method,
                        cashier_name=cashier_name,
                        cash_received=(
                            int(cash_received) if method == "CASH" else None
                        ),
                        transaction_code=transaction_code or None,
                        transaction_successful=transaction_successful,
                    )
                except (KeyError, OSError, ValueError) as error:
                    st.error(f"Không thể thanh toán: {error}")
                else:
                    if not result.payment.is_successful:
                        st.error(
                            "Thanh toán chưa thành công; đơn và bàn chưa được cập nhật."
                        )
                    else:
                        order_service.load_orders()
                        table_manager.load_tables()
                        order_service.sync_kitchen(
                            st.session_state.get("kitchen_manager") or KitchenManager()
                        )
                        st.session_state.payment_notice = (
                            f"Thanh toán thành công cho đơn {selected_order.id} (Mã GD: {result.payment.id})."
                        )
                        st.rerun()

    with history_column:
        st.markdown("### 🕒 Giao dịch thanh toán gần đây (payments.json)")
        try:
            payment_records = _read_payment_records(payment_service)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            st.error(f"Không thể đọc lịch sử thanh toán: {error}")
        else:
            successful = [
                record for record in payment_records
                if record.get("status") == "SUCCESS"
            ]
            revenue = Payment.calculate_revenue(
                [
                    Payment.model_validate(record)
                    for record in successful
                    if record.get("cashier_name")
                ]
            )
            metrics = st.columns(2)
            metrics[0].metric("Doanh thu thực nhận", _money(revenue["total_revenue"]))
            metrics[1].metric("Đơn đã thanh toán", revenue["paid_orders_count"])
            if payment_records:
                st.dataframe(
                    [
                        {
                            "Mã GD": row.get("id", row.get("payment_id", "—")),
                            "Mã đơn": row.get("order_id", "—"),
                            "Bàn": _table_label(row.get("table_id", "—")),
                            "Thời gian": row.get("payment_time", "—"),
                            "Số tiền": _money(
                                row.get("amount_paid", row.get("amount", 0))
                            ),
                            "Phương thức": row.get("method", "—"),
                            "Thu ngân": row.get("cashier_name", "—"),
                            "Trạng thái": row.get("status", "—"),
                        }
                        for row in merge_sort(
                            payment_records,
                            key=lambda record: str(record.get("payment_time", "")),
                            reverse=True,
                        )[:10]
                    ],
                    hide_index=True,
                    width="stretch",
                )
            else:
                st.caption("Chưa có giao dịch thanh toán.")


def render_dashboard_component(
    order_service: Optional[OrderService] = None,
    table_manager: Optional[TableManager] = None,
    payment_service: Optional[PaymentService] = None,
) -> None:
    """Render at-a-glance restaurant, kitchen, and revenue metrics."""
    order_service = order_service or st.session_state.get("order_service") or OrderService()
    table_manager = table_manager or st.session_state.get("table_manager") or TableManager()
    payment_service = payment_service or st.session_state.get("payment_service") or PaymentService()
    st.caption("Theo dõi hoạt động và hiệu quả kinh doanh của DŨNG MINION.")

    orders = order_service.get_all_orders()
    try:
        payment_records = _read_payment_records(payment_service)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        st.error(f"Không thể đọc doanh thu: {error}")
        payment_records = []
    unique_paid_orders = HashTable()
    revenue = 0
    method_revenue = HashTable()
    method_revenue.put("CASH", 0)
    method_revenue.put("BANK_TRANSFER", 0)
    method_revenue.put("CARD", 0)
    for record in payment_records:
        order_id = record.get("order_id")
        if (
            record.get("status") == "SUCCESS"
            and isinstance(order_id, str)
            and not unique_paid_orders.contains(order_id)
        ):
            unique_paid_orders.put(order_id, True)
            amount = int(record.get("amount_paid", record.get("amount", 0)) or 0)
            revenue += amount
            m = record.get("method", "CASH")
            prev_m = method_revenue.get(m, 0)
            method_revenue.put(m, prev_m + amount)

    metrics = st.columns(4)
    metrics[0].metric("Doanh thu tổng", _money(revenue))
    metrics[1].metric("Đơn đã thanh toán", unique_paid_orders.size)
    metrics[2].metric(
        "Đơn chờ bếp",
        sum(order.status == "PENDING" for order in orders),
    )
    metrics[3].metric(
        "Bàn trống",
        f"{len(table_manager.get_available_tables())}/{len(table_manager.get_all_tables())}",
    )

    left, right = st.columns([1.45, 1], gap="large")
    with left:
        st.markdown("### 🔥 Đơn hàng gần đây (data/orders.json)")
        recent_orders = merge_sort(
            orders,
            key=lambda order: str(order.created_at),
            reverse=True,
        )[:8]

        if not recent_orders:
            st.info("Chưa có đơn hàng.")
        else:
            st.dataframe(
                [
                    {
                        "Mã đơn": order.id,
                        "Bàn": _table_label(order.table_id),
                        "Trạng thái": ORDER_STATUS_LABELS.get(
                            order.status, order.status
                        ),
                        "Tổng tiền": _money(order.final_amount),
                    }
                    for order in recent_orders
                ],
                hide_index=True,
                width="stretch",
            )
    with right:
        st.markdown("### 🪑 Trạng thái bàn (data/tables.json)")
        tables = table_manager.get_all_tables()
        if not tables:
            st.info("Chưa có bàn trong hệ thống.")
        else:
            st.dataframe(
                [
                    {
                        "Bàn": table.name,
                        "Sức chứa": table.capacity,
                        "Trạng thái": {
                            "AVAILABLE": "🟢 Trống",
                            "OCCUPIED": "🔵 Đang sử dụng",
                            "RESERVED": "🟠 Đã đặt trước",
                        }.get(table.status, table.status),
                    }
                    for table in tables
                ],
                hide_index=True,
                width="stretch",
            )

    st.divider()
    col_methods = st.container()
    with col_methods:
        st.markdown("### 💳 Doanh thu theo phương thức")
        pm_labels = {
            "CASH": "💵 Tiền mặt",
            "BANK_TRANSFER": "🏦 Chuyển khoản",
            "CARD": "💳 Quẹt thẻ",
        }
        st.dataframe(
            [
                {
                    "Phương thức": pm_labels.get(k, k),
                    "Doanh thu": _money(v),
                    "Tỷ lệ": f"{(v / revenue * 100):.1f}%" if revenue > 0 else "0.0%",
                }
                for k, v in method_revenue.items()
            ],
            hide_index=True,
            width="stretch",
        )


def render_settings_component(*args, **kwargs) -> None:
    st.info("Trang Cài đặt đã được gỡ khỏi phạm vi dự án.")


def render_cart_component(
    cart: Optional[Cart] = None,
    order_service: Optional[OrderService] = None,
    table_manager: Optional[TableManager] = None,
    kitchen_manager: Optional[KitchenManager] = None,
    menu_catalog: Optional[MenuCatalog] = None,
) -> None:
    """Hiển thị giỏ hàng trên header của ứng dụng."""
    cart = cart or st.session_state.get("cart") or Cart()
    order_service = order_service or st.session_state.get("order_service") or OrderService()
    table_manager = table_manager or st.session_state.get("table_manager") or TableManager()
    kitchen_manager = kitchen_manager or st.session_state.get("kitchen_manager") or KitchenManager()
    menu_catalog = menu_catalog or _load_menu_catalog()

    cart_items = cart.get_order_items()
    cart_total = cart.calculate_total()

    label = f"🛒 Giỏ hàng ({len(cart_items)} món · {_money(cart_total)})"
    with st.expander(label, expanded=not cart.is_empty()):
        undo_col, redo_col, clear_col = st.columns(3)
        if undo_col.button("↶ Hoàn tác", disabled=not cart.can_undo(), key="h_cart_undo", width="stretch"):
            cart.undo()
            st.rerun()
        if redo_col.button("↷ Làm lại", disabled=not cart.can_redo(), key="h_cart_redo", width="stretch"):
            cart.redo()
            st.rerun()
        if clear_col.button("Xóa giỏ", disabled=cart.is_empty(), key="h_cart_clear", width="stretch"):
            cart.clear()
            st.rerun()

        if not cart_items:
            st.info("Giỏ hàng đang trống. Hãy chọn món từ thực đơn.")
            return

        for item in cart_items:
            with st.container(border=True):
                details, quantity_column, remove_column = st.columns(
                    [3, 2, 2],
                    vertical_alignment="center",
                )
                details.markdown(f"**{item['item_name']}**")
                details.caption(
                    f"{_money(item['unit_price'])} × {item['quantity']} = "
                    f"**{_money(item['subtotal'])}**"
                )
                if item.get("note"):
                    details.caption(f"📝 {item['note']}")
                qty = quantity_column.number_input(
                    "SL",
                    min_value=1,
                    max_value=20,
                    value=int(item["quantity"]),
                    key=f"h_cart_qty_{item['menu_item_id']}",
                    width="stretch",
                    label_visibility="collapsed",
                )
                if qty != item["quantity"]:
                    try:
                        cart.update_quantity(item["menu_item_id"], int(qty))
                    except ValueError as error:
                        st.error(str(error))
                    else:
                        st.rerun()
                if remove_column.button(
                    "Xóa",
                    key=f"h_cart_remove_{item['menu_item_id']}",
                    width="stretch",
                ):
                    cart.remove_item(item["menu_item_id"])
                    st.rerun()

        st.metric("Tổng tiền thanh toán", _money(cart_total))

        available_tables = table_manager.get_available_tables()
        table_choices = [*available_tables, "Mang về (Takeaway)"]
        selected_table = st.selectbox(
            "🪑 Chọn bàn hoặc mang về",
            table_choices,
            format_func=lambda table: (
                f"{table.name} · {table.capacity} chỗ"
                if not isinstance(table, str)
                else table
            ),
            key="h_cart_table_select",
        )
        order_notes = st.text_area("Ghi chú đơn hàng", key="h_cart_order_notes")
        if st.button(
            "✓ Xác nhận đơn hàng",
            type="primary",
            key="h_cart_confirm_order",
            width="stretch",
        ):
            unavailable_items = [
                item["item_name"]
                for item in cart_items
                if (
                    menu_catalog.get_item(item["menu_item_id"]) is None
                    or not menu_catalog.get_item(item["menu_item_id"]).is_available
                )
            ]
            if unavailable_items:
                st.error("Món đã hết hoặc không còn: " + ", ".join(unavailable_items))
            else:
                table_id = selected_table if isinstance(selected_table, str) else selected_table.id
                order_items = [
                    {
                        "menu_item_id": item["menu_item_id"],
                        "item_name": item["item_name"],
                        "unit_price": item["unit_price"],
                        "quantity": item["quantity"],
                        "subtotal": item["subtotal"],
                        "note": item.get("note", ""),
                        "prep_time": item.get("prep_time", 0) or 0,
                    }
                    for item in cart_items
                ]
                try:
                    order = order_service.place_order(
                        table_id,
                        order_items,
                        notes=order_notes,
                        table_manager=table_manager,
                        kitchen_manager=kitchen_manager,
                    )
                except (KeyError, OSError, ValueError) as error:
                    st.error(f"Không thể tạo đơn: {error}")
                else:
                    wait_time = kitchen_manager.estimate_wait_time(order)
                    cart.clear()
                    st.session_state.checkout_notice = (
                        f"Đã tạo đơn {order.id} và đưa vào hàng đợi bếp. "
                        f"Thời gian chờ dự kiến: {wait_time} phút."
                    )
                    st.rerun()


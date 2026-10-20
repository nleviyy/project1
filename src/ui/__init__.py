
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
from src.models.JSONStorage import JSONStorage
from src.models.MenuCatalog import MenuCatalog
from src.models.MenuItem import MenuItem
from src.models.Order import Order
from src.models.OrderItem import OrderItem
from src.models.Payment import Payment

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
MENU_PATH = DATA_DIR / "menu.json"
TABLES_PATH = DATA_DIR / "tables.json"
ORDERS_PATH = DATA_DIR / "orders.json"
PAYMENTS_PATH = DATA_DIR / "payments.json"

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

def _select_menu_suggestion(item_id: str) -> None:
    st.session_state["header_menu_search"] = item_id

def apply_custom_styles() -> None:
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
    max-width: 1500px;
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
    records = JSONStorage.load_data(
        str(MENU_PATH),
        default_data=[],
        strict=True,
    )
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
    if str(table_id) == "0":
        return "Mang về (Takeaway)"
    return f"Bàn {table_id}" if str(table_id).isdigit() else str(table_id)

def _refresh_cart_widgets() -> None:
    st.session_state["cart_widget_revision"] = (
        int(st.session_state.get("cart_widget_revision", 0)) + 1
    )

def _read_payment_records(payment_service: PaymentService) -> list[dict]:
    path = Path(payment_service.payments_path)
    records = JSONStorage.load_data(str(path), default_data=[], strict=True)
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
        cart_columns = st.columns([4, 2], gap="large")
        cart_column = cart_columns[0]
        menu_column = st.container()
        with menu_column:
            st.subheader("📜 Thực đơn")
            items = menu_catalog.get_all_items()
            search = str(st.session_state.get("header_menu_search", "")).strip()
            suggestions = menu_catalog.autocomplete_items(search)
            if suggestions:
                st.caption("Gợi ý món (chọn một món để lọc nhanh):")
                suggestion_columns = st.columns(len(suggestions))
                for index, item in enumerate(suggestions):
                    suggestion_columns[index].button(
                        f"{item.name} · {item.id}",
                        key=f"menu_suggestion_{item.id}",
                        on_click=_select_menu_suggestion,
                        args=(item.id,),
                        width="stretch",
                    )

            categories = ["Tất cả", *menu_catalog.get_categories()]
            selected_category = st.selectbox("Danh mục món", categories)
            filtered = [
                item
                for item in items
                if (selected_category == "Tất cả" or item.category == selected_category)
                and (
                    not search.strip()
                    or search.strip().casefold() in item.name.casefold()
                    or search.strip().casefold() in item.id.casefold()
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
                                    "＋ Thêm món",
                                    key=f"add_menu_{item.id}",
                                    help="Thêm vào giỏ",
                                    width="stretch",
                                ):
                                    try:
                                        cart.add_item(item)
                                    except ValueError as error:
                                        st.error(str(error))
                                    else:
                                        _refresh_cart_widgets()
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

        with cart_column:
            st.subheader("🛒 Giỏ hàng của bạn")
            cart_widget_revision = int(
                st.session_state.get("cart_widget_revision", 0)
            )
            undo_column, redo_column, clear_column = st.columns(3)
            if undo_column.button("↶ Hoàn tác", disabled=not cart.can_undo(), width="stretch"):
                cart.undo()
                _refresh_cart_widgets()
                st.rerun()
            if redo_column.button("↷ Làm lại", disabled=not cart.can_redo(), width="stretch"):
                cart.redo()
                _refresh_cart_widgets()
                st.rerun()
            if clear_column.button("Xóa giỏ", disabled=cart.is_empty(), width="stretch"):
                cart.clear()
                _refresh_cart_widgets()
                st.rerun()

            cart_items = cart.get_order_items()
            if not cart_items:
                st.info("Giỏ hàng đang trống. Hãy chọn món từ thực đơn.")
            else:
                for item in cart_items:
                    with st.container(border=True):
                        details, actions = st.columns(
                            [3, 4],
                            vertical_alignment="center",
                        )
                        details.markdown(f"**{item['item_name']}**")
                        details.caption(
                            f"{_money(item['unit_price'])} × {item['quantity']} = "
                            f"**{_money(item['subtotal'])}**"
                        )
                        if item.get("note"):
                            details.caption(f"📝 {item['note']}")
                        with actions.form(f"edit_cart_item_{item['menu_item_id']}"):
                            quantity = st.number_input(
                                "Số lượng",
                                min_value=1,
                                max_value=20,
                                value=int(item["quantity"]),
                                key=(
                                    f"cart_quantity_{item['menu_item_id']}_"
                                    f"{cart_widget_revision}"
                                ),
                            )
                            note = st.text_input(
                                "Ghi chú",
                                value=item.get("note", ""),
                                key=(
                                    f"cart_note_{item['menu_item_id']}_"
                                    f"{cart_widget_revision}"
                                ),
                            )
                            if st.form_submit_button("Cập nhật"):
                                try:
                                    cart.update_item(
                                        item["menu_item_id"],
                                        int(quantity),
                                        note,
                                    )
                                except ValueError as error:
                                    st.error(str(error))
                                else:
                                    _refresh_cart_widgets()
                                    st.rerun()
                        if actions.button("Xóa món", key=f"remove_{item['menu_item_id']}"):
                            cart.remove_item(item["menu_item_id"])
                            _refresh_cart_widgets()
                            st.rerun()

                cart_total = cart.calculate_total()
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
                )
                order_notes = st.text_area("Ghi chú đơn hàng", key="order_notes")
                if st.button(
                    "✓ Xác nhận đơn hàng",
                    type="primary",
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
                        table_id = 0 if isinstance(selected_table, str) else selected_table.id
                        if not isinstance(selected_table, str) and not table_manager.is_table_available(table_id):
                            st.error("Bàn vừa được nhận bởi đơn khác. Vui lòng chọn bàn khác.")
                        else:
                            order_items = []
                            for item in cart_items:
                                menu_item = menu_catalog.get_item(item["menu_item_id"])
                                if menu_item is None or not menu_item.is_available:
                                    st.error(
                                        f"Món '{item['item_name']}' vừa hết hoặc không còn phục vụ."
                                    )
                                    break
                                order_items.append(
                                    OrderItem(
                                        menu_item_id=menu_item.id,
                                        item_name=menu_item.name,
                                        unit_price=menu_item.price,
                                        quantity=item["quantity"],
                                        note=item.get("note", ""),
                                        prep_time=menu_item.prep_time,
                                    )
                                )
                            if len(order_items) == len(cart_items):
                                try:
                                    order = order_service.create_order(
                                        table_id=table_id,
                                        items=order_items,
                                        notes=order_notes,
                                        discount_amount=0,
                                        kitchen_manager=kitchen_manager,
                                        table_manager=table_manager,
                                    )
                                    if not order_service.confirm_order(
                                        order.id,
                                        kitchen_manager=kitchen_manager,
                                    ):
                                        raise ValueError(
                                            f"Không thể xác nhận đơn hàng '{order.id}'."
                                        )
                                except (
                                    KeyError,
                                    OSError,
                                    RuntimeError,
                                    TypeError,
                                    ValueError,
                                ) as error:
                                    st.error(f"Không thể tạo đơn: {error}")
                                else:
                                    wait_time = kitchen_manager.estimate_wait_time(order)
                                    cart.clear()
                                    st.session_state.checkout_notice = (
                                        f"Đã tạo đơn {order.id} và đưa vào hàng đợi bếp. "
                                        f"Thời gian chờ dự kiến: {wait_time} phút."
                                    )
                                    _refresh_cart_widgets()
                                    st.rerun()

def render_tables_component(
    table_manager: Optional[TableManager] = None,
    order_service: Optional[OrderService] = None,
) -> None:
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
    orders_by_id = {order.id: order for order in order_service.get_all_orders()}
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
                elif table.status == "AVAILABLE":
                    if st.button("📌 Đặt trước bàn", key=f"btn_reserve_tbl_{table.id}", width="stretch"):
                        if table_manager.reserve_table(table.id):
                            st.toast(f"Đã chuyển {table.name} sang Đã đặt trước.")
                            st.rerun()
                        else:
                            st.error(f"Không thể cập nhật trạng thái của {table.name}.")
                elif table.status == "RESERVED":
                    if st.button("🔓 Mở lại bàn trống", key=f"btn_vacate_tbl_{table.id}", width="stretch"):
                        if table_manager.vacate_table(table.id):
                            st.toast(f"Đã mở lại {table.name} thành bàn trống.")
                            st.rerun()
                        else:
                            st.error(f"Không thể cập nhật trạng thái của {table.name}.")

    st.divider()
    col_add_tbl, col_del_tbl = st.columns(2, gap="large")
    with col_add_tbl:
        with st.container(border=True):
            st.markdown("#### ➕ Thêm bàn mới (data/tables.json)")
            next_tbl_id = max([t.id for t in tables], default=0) + 1
            with st.form("form_add_table"):
                new_t_id = st.number_input("Mã số bàn (ID)", min_value=1, value=next_tbl_id, step=1)
                new_t_name = st.text_input("Tên bàn", value=f"Bàn {new_t_id:02d}")
                new_t_cap = st.number_input("Sức chứa (người)", min_value=1, max_value=20, value=4, step=1)
                if st.form_submit_button("Thêm bàn", type="primary", width="stretch"):
                    try:
                        new_table = Table(id=int(new_t_id), name=new_t_name.strip(), capacity=int(new_t_cap))
                        if not table_manager.add_table(new_table):
                                    st.error(f"Không thể thêm bàn số {new_t_id}; kiểm tra ID hoặc quyền ghi file.")
                        else:
                            st.success(f"Đã thêm {new_t_name} và lưu vào data/tables.json.")
                            st.rerun()
                    except (TypeError, ValueError, OSError) as err:
                        st.error(f"Lỗi: {err}")

    with col_del_tbl:
        with st.container(border=True):
            st.markdown("#### 🗑️ Xóa bàn ăn (data/tables.json)")
            deletable_tables = [t for t in tables if t.status != "OCCUPIED"]
            if not deletable_tables:
                st.info("Hiện không có bàn nào có thể xóa (tất cả đang có khách).")
            else:
                with st.form("form_delete_table"):
                    del_tbl = st.selectbox(
                        "Chọn bàn cần xóa",
                        deletable_tables,
                        format_func=lambda t: f"{t.name} (Sức chứa {t.capacity} chỗ - {t.status})",
                    )
                    if st.form_submit_button("Xác nhận xóa bàn", width="stretch"):
                        if table_manager.remove_table(del_tbl.id):
                            st.success(f"Đã xóa {del_tbl.name} khỏi data/tables.json.")
                            st.rerun()
                        else:
                            st.error("Không thể xóa bàn đã chọn.")

def render_kitchen_component(
    kitchen_manager: Optional[KitchenManager] = None,
    order_service: Optional[OrderService] = None,
) -> None:
    kitchen_manager = kitchen_manager or st.session_state.get("kitchen_manager") or KitchenManager()
    order_service = order_service or st.session_state.get("order_service") or OrderService()
    _ensure_kitchen_synced(order_service, kitchen_manager)
    st.subheader("🍳 Điều phối bếp · Hàng đợi FIFO")
    current_order = kitchen_manager.get_current_order()
    waiting_orders = kitchen_manager.get_waiting_orders()
    metrics = st.columns(3)
    metrics[0].metric("Đang chờ", len(waiting_orders))
    metrics[1].metric("Đang chế biến", current_order.id if current_order else "—")
    metrics[2].metric(
        "Thời gian còn lại",
        f"{kitchen_manager.estimate_wait_time(current_order)} phút"
        if current_order
        else "—",
    )

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
            if st.button("✓ Hoàn tất chế biến · Lên món", type="primary", width="stretch"):
                try:
                    order_service.serve_order(current_order.id)
                except (KeyError, OSError, RuntimeError, ValueError) as error:
                    st.error(f"Không thể cập nhật bếp: {error}")
                else:
                    st.success(f"Đơn {current_order.id} đã được lên món.")
                    st.rerun()
            st.caption("Đơn đã bắt đầu chế biến không thể hủy.")
    if waiting_orders:
        st.markdown("### ⏳ Hàng đợi chờ chế biến · FIFO")
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
                        try:
                            order_service.cancel_order(
                                order.id,
                                reason="Khách hủy trong lúc chờ bếp",
                                kitchen_manager=kitchen_manager,
                            )
                        except (KeyError, OSError, RuntimeError, ValueError) as error:
                            st.error(f"Không thể hủy đơn: {error}")
                        else:
                            st.toast(f"Đã hủy đơn chờ {order.id}.")
                            st.rerun()
        if current_order is None and st.button(
            "▶ Bắt đầu đơn tiếp theo",
            type="primary",
        ):
            try:
                order_service.start_preparing_order(waiting_orders[0].id)
            except (OSError, RuntimeError, ValueError) as error:
                st.error(f"Không thể bắt đầu chế biến: {error}")
            else:
                st.rerun()
    elif current_order is None:
        st.info(
            "Hàng đợi đang trống. Đơn mới sẽ xuất hiện tại đây khi được xác nhận "
            "ở mục Thực đơn."
        )

def render_orders_component(
    order_service: Optional[OrderService] = None,
    kitchen_manager: Optional[KitchenManager] = None,
    table_manager: Optional[TableManager] = None,
) -> None:
    order_service = order_service or st.session_state.get("order_service") or OrderService()
    kitchen_manager = kitchen_manager or st.session_state.get("kitchen_manager") or KitchenManager()
    table_manager = table_manager or st.session_state.get("table_manager") or TableManager()
    st.subheader("🧾 Danh sách đơn hàng")
    orders = order_service.get_all_orders()
    filter_column, search_column = st.columns([1, 2])
    statuses = ["Tất cả", *ORDER_STATUS_LABELS]
    selected_status = filter_column.selectbox(
        "Trạng thái",
        statuses,
        format_func=lambda status: (
            "Tất cả" if status == "Tất cả" else ORDER_STATUS_LABELS[status]
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
    filtered_orders.sort(key=lambda order: str(order.created_at), reverse=True)
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
        if allow_cancel and order.status == "PENDING":
            if st.button("Hủy đơn hàng", key=f"cancel_order_{order.id}"):
                try:
                    order_service.cancel_order(
                        order.id,
                        reason="Hủy từ giao diện quản lý",
                        kitchen_manager=kitchen_manager,
                    )
                    table_manager.load_tables()
                except (KeyError, OSError, RuntimeError, ValueError) as error:
                    st.error(f"Không thể hủy đơn: {error}")
                else:
                    st.success(f"Đã hủy đơn {order.id}.")
                    st.rerun()

def render_payment_component(
    payment_service: Optional[PaymentService] = None,
    order_service: Optional[OrderService] = None,
    table_manager: Optional[TableManager] = None,
) -> None:
    payment_service = payment_service or st.session_state.get("payment_service") or PaymentService()
    order_service = order_service or st.session_state.get("order_service") or OrderService()
    table_manager = table_manager or st.session_state.get("table_manager") or TableManager()
    st.subheader("💳 Thu ngân & thanh toán")

    if "payment_notice" in st.session_state and st.session_state.payment_notice:
        st.success(st.session_state.payment_notice)
        receipt = st.session_state.get("payment_receipt")
        if receipt:
            st.code(receipt, language="text")
            st.download_button(
                "⬇ Tải hóa đơn",
                data=receipt,
                file_name=st.session_state.get(
                    "payment_receipt_filename",
                    "invoice.txt",
                ),
                mime="text/plain",
                key="download_payment_invoice",
            )
        if st.button("✕ Đóng thông báo", key="btn_close_payment_notice"):
            st.session_state.pop("payment_notice", None)
            st.session_state.pop("payment_receipt", None)
            st.session_state.pop("payment_receipt_filename", None)
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
                except (KeyError, OSError, RuntimeError, ValueError) as error:
                    st.error(f"Không thể thanh toán: {error}")
                else:
                    if not result.payment.is_successful:
                        st.error(
                            "Thanh toán chưa thành công; đơn và bàn chưa được cập nhật."
                        )
                    elif result.invoice is None:
                        st.error(
                            "Giao dịch báo thành công nhưng không có hóa đơn; "
                            "hãy kiểm tra payments.json và invoices.json."
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
                        st.session_state.payment_receipt = (
                            result.invoice.generate_text_receipt()
                        )
                        st.session_state.payment_receipt_filename = (
                            f"{result.invoice.id}.txt"
                        )
                        st.rerun()

    with history_column:
        st.markdown("### 🕒 Giao dịch thanh toán gần đây (payments.json)")
        try:
            payment_records = _read_payment_records(payment_service)
        except (OSError, ValueError, UnicodeDecodeError) as error:
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
                        for row in sorted(
                            payment_records,
                            key=lambda record: record.get("payment_time", ""),
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
    order_service = order_service or st.session_state.get("order_service") or OrderService()
    table_manager = table_manager or st.session_state.get("table_manager") or TableManager()
    payment_service = payment_service or st.session_state.get("payment_service") or PaymentService()
    st.markdown("## Xin chào! 👋")
    st.caption("Theo dõi hoạt động và hiệu quả kinh doanh của DŨNG FATFOOD.")

    orders = order_service.get_all_orders()
    try:
        payment_records = _read_payment_records(payment_service)
    except (OSError, ValueError, UnicodeDecodeError) as error:
        st.error(f"Không thể đọc doanh thu: {error}")
        payment_records = []
    unique_paid_orders: set[str] = set()
    revenue = 0
    method_revenue: dict[str, int] = {"CASH": 0, "BANK_TRANSFER": 0, "CARD": 0}
    for record in payment_records:
        order_id = record.get("order_id")
        if (
            record.get("status") == "SUCCESS"
            and isinstance(order_id, str)
            and order_id not in unique_paid_orders
        ):
            unique_paid_orders.add(order_id)
            amount = int(record.get("amount_paid", record.get("amount", 0)) or 0)
            revenue += amount
            m = record.get("method", "CASH")
            if m in method_revenue:
                method_revenue[m] += amount
            else:
                method_revenue[m] = amount

    metrics = st.columns(4)
    metrics[0].metric("Doanh thu tổng", _money(revenue))
    metrics[1].metric("Đơn đã thanh toán", len(unique_paid_orders))
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
        recent_orders = sorted(
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
    col_dishes, col_methods = st.columns([1.2, 1], gap="large")
    with col_dishes:
        st.markdown("### 🏆 Top món bán chạy nhất")
        item_counts: dict[str, dict] = {}
        for order in orders:
            if order.id in unique_paid_orders:
                for it in order.items:
                    if it.item_name not in item_counts:
                        item_counts[it.item_name] = {
                            "quantity": 0,
                            "revenue": 0,
                        }
                    item_counts[it.item_name]["quantity"] += it.quantity
                    item_counts[it.item_name]["revenue"] += it.subtotal

        top_dishes = sorted(
            item_counts.items(),
            key=lambda x: x[1]["quantity"],
            reverse=True,
        )[:5]

        if top_dishes:
            st.dataframe(
                [
                    {
                        "Hạng": f"#{idx + 1}",
                        "Tên món": dish_name,
                        "Số lượng": f"{data['quantity']} phần",
                        "Doanh thu": _money(data["revenue"]),
                    }
                    for idx, (dish_name, data) in enumerate(top_dishes)
                ],
                hide_index=True,
                width="stretch",
            )
        else:
            st.caption("Chưa có dữ liệu món bán ra.")

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
def render_settings_component(
    order_service: Optional[OrderService] = None,
    table_manager: Optional[TableManager] = None,
    kitchen_manager: Optional[KitchenManager] = None,
    payment_service: Optional[PaymentService] = None,
    menu_catalog: Optional[MenuCatalog] = None,
) -> None:
    order_service = order_service or st.session_state.get("order_service") or OrderService()
    table_manager = table_manager or st.session_state.get("table_manager") or TableManager()
    kitchen_manager = kitchen_manager or st.session_state.get("kitchen_manager") or KitchenManager()
    payment_service = payment_service or st.session_state.get("payment_service") or PaymentService()

    st.subheader("⚙️ Quản trị hệ thống & Tệp dữ liệu (Data Storage)")
    st.caption("Quản lý trạng thái kết nối dữ liệu giữa giao diện và các tệp JSON trong thư mục data/.")

    data_files = [
        {"key": "menu", "name": "Thực đơn (menu.json)", "path": MENU_PATH},
        {"key": "tables", "name": "Bàn ăn (tables.json)", "path": TABLES_PATH},
        {"key": "orders", "name": "Đơn hàng (orders.json)", "path": ORDERS_PATH},
        {"key": "payments", "name": "Thanh toán (payments.json)", "path": PAYMENTS_PATH},
    ]

    file_info_rows = []
    for f in data_files:
        p: Path = f["path"]
        exists = p.exists()
        size_kb = f"{(p.stat().st_size / 1024):.1f} KB" if exists else "—"
        count = 0
        if exists:
            try:
                data = JSONStorage.load_data(
                    str(p),
                    default_data=[],
                    strict=True,
                )
                if isinstance(data, (list, dict)):
                    count = len(data)
                else:
                    raise ValueError(f"{p.name} chứa kiểu dữ liệu không hợp lệ.")
            except (OSError, ValueError, UnicodeDecodeError):
                count = -1
        file_info_rows.append(
            {
                "Tệp dữ liệu": f["name"],
                "Đường dẫn": str(p),
                "Kích thước": size_kb,
                "Số bản ghi": f"{count} mục" if count >= 0 else "Lỗi đọc",
                "Trạng thái": "🟢 Sẵn sàng" if exists else "🔴 Chưa tạo",
            }
        )
    st.dataframe(file_info_rows, hide_index=True, width="stretch")
    st.markdown("#### 🔄 Đồng bộ & Tải lại dữ liệu")
    col_act1, col_act2 = st.columns(2)
    with col_act1:
        if st.button("🔄 Tải lại dữ liệu từ tất cả tệp JSON", width="stretch", type="primary"):
            try:
                order_service.load_orders()
                table_manager.load_tables()
                if hasattr(kitchen_manager, "restore_orders"):
                    kitchen_manager.restore_orders(order_service.get_all_orders())
                st.session_state.cart = Cart()
                st.success("Đã đồng bộ lại toàn bộ dữ liệu từ các file JSON vào bộ nhớ hệ thống!")
                st.rerun()
            except (KeyError, OSError, RuntimeError, ValueError) as e:
                st.error(f"Lỗi khi tải lại dữ liệu: {e}")

    with col_act2:
        if st.button("🧹 Làm rỗng giỏ hàng tạm thời", width="stretch"):
            st.session_state.cart = Cart()
            _refresh_cart_widgets()
            st.toast("Đã đặt lại giỏ hàng rỗng.")
            st.rerun()

    st.divider()
    st.markdown("#### 📄 Xem chi tiết tệp dữ liệu")
    selected_file_key = st.selectbox(
        "Chọn tệp dữ liệu để xem nội dung",
        options=[f["key"] for f in data_files],
        format_func=lambda k: next(f["name"] for f in data_files if f["key"] == k),
        key="settings_selected_file_key",
    )
    selected_target = next(f for f in data_files if f["key"] == selected_file_key)
    target_path: Path = selected_target["path"]
    if target_path.exists():
        with target_path.open(encoding="utf-8") as fp:
            content_str = fp.read()
        col_meta1, col_meta2 = st.columns(2)
        col_meta1.caption(f"📁 Đường dẫn: `{target_path}`")
        col_meta2.caption(f"📊 Kích thước: {len(content_str)} ký tự")
        with st.expander(f"Xem nội dung `{target_path.name}`", expanded=True):
            st.code(content_str, language="json")
    else:
        st.warning(f"Tệp `{target_path}` chưa tồn tại.")

import html
import json
from pathlib import Path

import streamlit as st

from src.KitchenManage import KitchenManager, OrderStatus
from src.core.Cart import Cart
from src.core.OrderService import OrderService
from src.core.PaymentService import PaymentService
from src.core.TableManager import TableManager
from src.models.MenuCatalog import MenuCatalog
from src.models.OrderItem import OrderItem

st.set_page_config(
    page_title="SUPPER MENU QUÁN",
    page_icon="🍽️",
    layout="wide",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');

:root {
    --navy: #263759;
    --slate: #545e76;
    --paper: #f2f1ec;
    --ink: #26344f;
    --muted: #737b8b;
}

html, body, [class*="css"], .stApp {
    font-family: "Be Vietnam Pro", sans-serif !important;
}

.stApp {
    background-color: #e6e5e2;
    background-image:
        linear-gradient(90deg, rgba(38,55,89,.035) 1px, transparent 1px),
        linear-gradient(rgba(38,55,89,.035) 1px, transparent 1px);
    background-size: 44px 44px;
    color: var(--ink);
}

.block-container {
    max-width: 1120px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

.app-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 1.1rem 1.5rem;
    margin-bottom: 1.25rem;
    border-radius: 24px;
    background: var(--paper);
    box-shadow: 0 10px 28px rgba(38,55,89,.10);
}

.brand {
    display: inline-flex;
    align-items: center;
    gap: .65rem;
    color: var(--navy);
    font-size: 1.25rem;
    font-weight: 800;
    letter-spacing: -.04em;
    white-space: nowrap;
}

.brand-mark {
    display: inline-flex !important;
    flex: 0 0 auto !important;
    width: auto !important;
    min-width: 5.4rem !important;
    height: 2.2rem !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 0 .8rem !important;
    border-radius: 12px;
    color: white;
    background: var(--navy);
    font-size: .95rem;
    line-height: 1;
    letter-spacing: -.02em;
    white-space: nowrap;
}

.page-intro {
    margin: 1.6rem 0 1rem;
}

.page-intro h1 {
    margin: 0;
    color: var(--navy);
    font-size: clamp(1.8rem, 4vw, 2.6rem);
    font-weight: 800;
    letter-spacing: -.05em;
}

.page-intro p {
    margin: .35rem 0 0;
    color: var(--muted);
}

.section-title {
    margin: 1.8rem 0 .8rem;
    color: var(--navy);
    font-size: 1.35rem;
    font-weight: 800;
}

.food-price {
    color: var(--navy);
    font-size: 1.15rem;
    font-weight: 800;
}

.food-meta {
    color: var(--muted);
    font-size: .85rem;
}

.cart-total {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 1.2rem;
    border-radius: 16px;
    color: white;
    background: var(--navy);
    font-size: 1.1rem;
    font-weight: 700;
}

[data-testid="stMain"] .stRadio > label {
    display: none;
}

[data-testid="stMain"] div[role="radiogroup"] {
    gap: .55rem;
}

[data-testid="stMain"] div[role="radiogroup"] label {
    padding: .45rem .95rem;
    border: 1px solid rgba(38,55,89,.12);
    border-radius: 999px;
    background: var(--paper);
    color: var(--navy) !important;
}

[data-testid="stMain"] div[role="radiogroup"] label p {
    color: inherit !important;
}

[data-testid="stMain"] div[role="radiogroup"] label:has(input:checked) {
    color: white !important;
    background: var(--navy);
}

[data-testid="stMain"] div[role="radiogroup"] input {
    accent-color: var(--navy);
}

[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] {
    border: 0;
    border-radius: 22px;
    background: var(--paper);
    box-shadow: 0 10px 24px rgba(38,55,89,.09);
}

.stButton > button {
    min-height: 2.7rem;
    border: 0;
    border-radius: 12px;
    color: white;
    background: var(--navy);
    font-weight: 700;
}

.stButton > button:hover {
    border: 0;
    color: white;
    background: var(--slate);
}

.stButton > button:disabled {
    color: var(--navy) !important;
    background: #d6d9e0 !important;
    opacity: 1 !important;
}

[data-testid="stExpander"] {
    border: 1px solid rgba(38,55,89,.12);
    border-radius: 14px;
    overflow: hidden;
    background: var(--paper);
}

[data-testid="stExpander"] details > summary {
    color: #fff !important;
    background: var(--navy) !important;
}

[data-testid="stExpander"] details > summary p,
[data-testid="stExpander"] details > summary span,
[data-testid="stExpander"] details > summary svg {
    color: #fff !important;
    fill: #fff !important;
}

[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    background: var(--paper) !important;
}

[data-testid="stExpander"] label,
[data-testid="stExpander"] label p {
    color: var(--navy) !important;
}

[data-testid="stExpander"] input,
[data-testid="stExpander"] textarea {
    color: var(--navy) !important;
    background: #fff !important;
    border-color: rgba(38,55,89,.28) !important;
}

[data-testid="stExpander"] input::placeholder,
[data-testid="stExpander"] textarea::placeholder {
    color: var(--muted) !important;
}

[data-testid="stExpander"] [data-testid="stNumberInput"] button {
    color: #fff !important;
    background: var(--navy) !important;
}

@media (max-width: 700px) {
    .block-container {
        padding: 1rem .8rem 3rem;
    }
    .app-header {
        padding: .9rem 1rem;
        border-radius: 18px;
    }
}
</style>
""",
    unsafe_allow_html=True,
)

MENU_PATH = Path(__file__).resolve().parents[2] / "data" / "menu.json"
with MENU_PATH.open(encoding="utf-8") as menu_file:
    menu_data = json.load(menu_file)
if not isinstance(menu_data, list):
    raise ValueError(f"Menu data at {MENU_PATH} must be a JSON list.")

menu_catalog = MenuCatalog()
menu_catalog.load_from_dict(menu_data)
MENU = menu_catalog.get_all_items()
if len(MENU) != len(menu_data):
    raise ValueError(f"Menu data at {MENU_PATH} contains invalid or duplicate records.")
MENU_BY_ID = {item.id: item for item in MENU}

if "cart" not in st.session_state:
    st.session_state.cart = Cart()
if "cart_revision" not in st.session_state:
    st.session_state.cart_revision = 0
if "table_manager" not in st.session_state:
    st.session_state.table_manager = TableManager()
else:
    st.session_state.table_manager.load_tables()
if "kitchen" not in st.session_state:
    st.session_state.kitchen = KitchenManager()
if "order_service" not in st.session_state:
    st.session_state.order_service = OrderService(
        table_manager=st.session_state.table_manager,
        kitchen_manager=st.session_state.kitchen,
    )
else:
    st.session_state.order_service.table_manager = st.session_state.table_manager
    st.session_state.order_service.kitchen_manager = st.session_state.kitchen
    st.session_state.order_service.load_orders()
st.session_state.kitchen.restore_orders(
    st.session_state.order_service.get_all_orders()
)
cart = st.session_state.cart
table_manager = st.session_state.table_manager
kitchen = st.session_state.kitchen
order_service = st.session_state.order_service

if "checkout_notice" in st.session_state:
    st.success(st.session_state.pop("checkout_notice"))
if "payment_notice" in st.session_state:
    st.success(st.session_state.pop("payment_notice"))
if "payment_receipt" in st.session_state:
    st.code(st.session_state.pop("payment_receipt"))

st.markdown(
    f"""
<div class="app-header">
    <div class="brand"><span class="brand-mark">NHÓM 2</span><span> DŨNG COFFE </span></div>
    <div class="food-meta">{cart.count_lines()} món trong giỏ · {cart.calculate_total():,} VNĐ</div>
</div>
""",
    unsafe_allow_html=True,
)

MENU_PAGE = "📜  Thực đơn"
CART_PAGE = "🛍️  Giỏ hàng"
ORDERS_PAGE = "🍳  Đơn hàng & Bếp"
page = st.radio(
    "Đi đến",
    [MENU_PAGE, CART_PAGE, ORDERS_PAGE],
    horizontal=True,
    label_visibility="collapsed",
    key="ordering_page",
)

undo_col, redo_col, _ = st.columns([1, 1, 5])
if undo_col.button("↶ Hoàn tác", disabled=not cart.can_undo(), use_container_width=True):
    cart.undo()
    st.session_state.cart_revision += 1
    st.rerun()
if redo_col.button("↷ Làm lại", disabled=not cart.can_redo(), use_container_width=True):
    cart.redo()
    st.session_state.cart_revision += 1
    st.rerun()

if page == MENU_PAGE:
    st.markdown(
        """
<div class="page-intro">
    <h1>Collection</h1>
    <p>Chọn món bạn yêu thích, chúng tôi sẽ chuẩn bị thật ngon.</p>
</div>
""",
        unsafe_allow_html=True,
    )

    categories = ["Tất cả"] + menu_catalog.get_categories()
    if st.session_state.get("menu_category") not in categories:
        st.session_state.menu_category = "Tất cả"
    selected_category = st.radio(
        "Danh mục món ăn",
        categories,
        horizontal=True,
        label_visibility="collapsed",
        key="menu_category",
    )
    visible_menu = (
        MENU
        if selected_category == "Tất cả"
        else menu_catalog.filter_by_category(selected_category)
    )
    cart_by_id = {
        item["menu_item_id"]: item for item in cart.get_order_items()
    }
    menu_columns = st.columns(2, gap="large")

    for index, menu_item in enumerate(visible_menu):
        with menu_columns[index % 2]:
            with st.container(border=True):
                if menu_item.image:
                    st.image(menu_item.image, use_container_width=True)
                else:
                    st.markdown("## 🍽️")

                st.caption(
                    f"{menu_item.category} · "
                    f"{'Còn món' if menu_item.is_available else 'Tạm hết'}"
                )
                st.subheader(menu_item.name)
                st.markdown(
                    f'<div class="food-price">{menu_item.price:,} VNĐ</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="food-meta">⏱ {menu_item.prep_time} phút · '
                    f'{html.escape(menu_item.unit)}</div>',
                    unsafe_allow_html=True,
                )
                st.write(menu_item.description)

                if st.button(
                    "＋ Thêm vào giỏ",
                    key=f"quick_add_{menu_item.id}_{st.session_state.cart_revision}",
                    disabled=not menu_item.is_available,
                    use_container_width=True,
                ):
                    cart.add_item(menu_item, quantity=1)
                    st.session_state.cart_revision += 1
                    st.rerun()

                current_item = cart_by_id.get(menu_item.id)
                with st.expander(
                    "Tùy chỉnh số lượng và ghi chú",
                    expanded=current_item is not None,
                ):
                    quantity = st.number_input(
                        "Số lượng",
                        min_value=0,
                        max_value=20,
                        value=current_item["quantity"] if current_item else 1,
                        key=f"menu_quantity_{menu_item.id}_{st.session_state.cart_revision}",
                        disabled=not menu_item.is_available,
                    )
                    note = st.text_input(
                        "Ghi chú món",
                        value=current_item.get("note", "") if current_item else "",
                        placeholder="Ít đá, không hành...",
                        key=f"menu_note_{menu_item.id}_{st.session_state.cart_revision}",
                        disabled=not menu_item.is_available,
                    )
                    if st.button(
                        "Lưu lựa chọn",
                        key=f"save_menu_{menu_item.id}_{st.session_state.cart_revision}",
                        disabled=not menu_item.is_available,
                        use_container_width=True,
                    ):
                        if not menu_item.is_available:
                            st.error(f"{menu_item.name} hiện đã hết.")
                        elif quantity == 0:
                            if current_item is not None:
                                cart.remove_item(menu_item.id)
                        elif current_item is None:
                            cart.add_item(menu_item, quantity, note)
                        else:
                            cart.update_item(menu_item.id, quantity, note)
                        st.session_state.cart_revision += 1
                        st.rerun()

elif page == CART_PAGE:
    st.markdown(
        """
<div class="page-intro">
    <h1>My cart</h1>
    <p>Kiểm tra món ăn và hoàn tất đơn hàng của bạn.</p>
</div>
""",
        unsafe_allow_html=True,
    )
    cart_items = cart.get_order_items()
    if not cart_items:
        st.info("Giỏ hàng đang trống. Hãy quay lại thực đơn để chọn món.")
    else:
        st.markdown('<div class="section-title">Order Summary</div>', unsafe_allow_html=True)
        for item in cart_items:
            menu_item = MENU_BY_ID.get(item["menu_item_id"])
            with st.container(border=True):
                image_col, details_col, quantity_col, note_col, action_col = st.columns(
                    [1.2, 2.2, 1, 1.8, 1.1],
                    vertical_alignment="center",
                )
                with image_col:
                    if menu_item and menu_item.image:
                        st.image(menu_item.image, use_container_width=True)
                    else:
                        st.markdown("🍽️")
                with details_col:
                    st.markdown(f"**{item['item_name']}**")
                    st.caption(f"{item['unit_price']:,} VNĐ / phần")
                    st.markdown(f"**{item['subtotal']:,} VNĐ**")
                with quantity_col:
                    quantity = st.number_input(
                        "SL",
                        min_value=1,
                        max_value=20,
                        value=item["quantity"],
                        key=f"cart_quantity_{item['menu_item_id']}_{st.session_state.cart_revision}",
                    )
                with note_col:
                    note = st.text_input(
                        "Ghi chú",
                        value=item.get("note", ""),
                        key=f"cart_note_{item['menu_item_id']}_{st.session_state.cart_revision}",
                    )
                with action_col:
                    if st.button(
                        "Lưu",
                        key=f"cart_update_{item['menu_item_id']}_{st.session_state.cart_revision}",
                        use_container_width=True,
                    ):
                        if menu_item is None or not menu_item.is_available:
                            st.error(f"{item['item_name']} hiện đã hết hoặc không còn trong menu.")
                        else:
                            cart.update_item(item["menu_item_id"], quantity, note)
                            st.session_state.cart_revision += 1
                            st.rerun()
                    if st.button(
                        "Xóa",
                        key=f"cart_remove_{item['menu_item_id']}_{st.session_state.cart_revision}",
                        use_container_width=True,
                    ):
                        cart.remove_item(item["menu_item_id"])
                        st.session_state.cart_revision += 1
                        st.rerun()

        st.markdown(
            f"""
<div class="cart-total">
    <span>Total · {cart.count_lines()} món</span>
    <span>{cart.calculate_total():,} VNĐ</span>
</div>
""",
            unsafe_allow_html=True,
        )
        estimated_prep_time = sum(
            item.get("prep_time", 0) * item["quantity"] for item in cart_items
        )
        st.caption(f"Thời gian chế biến ước tính: khoảng {estimated_prep_time} phút")
        available_tables = table_manager.get_available_tables()
        table_options = [*available_tables, "Mang về (Takeaway)"]
        selected_table = st.selectbox(
            "Chọn bàn còn trống hoặc mang về",
            table_options,
            format_func=lambda table: (
                f"{table.name} · {table.capacity} chỗ"
                if not isinstance(table, str)
                else table
            ),
        )
        if not available_tables:
            st.info("Hiện không có bàn trống; khách vẫn có thể chọn mang về.")

        if st.button(
            "Đặt món ngay",
            type="primary",
            use_container_width=True,
        ):
            unavailable_items = [
                item["item_name"]
                for item in cart_items
                if (
                    item["menu_item_id"] not in MENU_BY_ID
                    or not MENU_BY_ID[item["menu_item_id"]].is_available
                )
            ]
            if unavailable_items:
                st.error(
                    "Không thể xác nhận đơn vì món đã hết hoặc không còn trong menu: "
                    + ", ".join(unavailable_items)
                )
            else:
                selected_table_id = (
                    selected_table
                    if isinstance(selected_table, str)
                    else selected_table.id
                )
                table_available = isinstance(selected_table, str) or (
                    table_manager.is_table_available(selected_table_id)
                )
                if not table_available:
                    st.error("Bàn vừa được nhận bởi đơn khác. Vui lòng chọn lại bàn.")
                else:
                    try:
                        order_items = [
                            OrderItem(
                                menu_item_id=item["menu_item_id"],
                                item_name=item["item_name"],
                                unit_price=item["unit_price"],
                                quantity=item["quantity"],
                                subtotal=item["subtotal"],
                                note=item.get("note", ""),
                                prep_time=item.get("prep_time", 0),
                            )
                            for item in cart_items
                        ]
                        order = order_service.create_order(
                            table_id=selected_table_id,
                            items=order_items,
                            check_existing_active=True,
                        )
                        order_service.confirm_order(order.id)
                    except (OSError, ValueError, KeyError) as error:
                        st.error(f"Không thể xác nhận đơn hàng: {error}")
                    else:
                        wait_time = kitchen.estimate_wait_time(order)
                        st.session_state.checkout_notice = (
                            f"Đã tạo đơn {order.id} ở trạng thái PENDING và đưa vào "
                            f"hàng đợi bếp. Thời gian lên món dự kiến: {wait_time} phút."
                        )
                        cart.clear()
                        st.session_state.cart_revision += 1
                        st.rerun()

else:
    st.markdown(
        """
<div class="page-intro">
    <h1>Order & Kitchen</h1>
    <p>Theo dõi hàng đợi, chế biến, phục vụ và thanh toán đơn hàng.</p>
</div>
""",
        unsafe_allow_html=True,
    )

    current_order = kitchen.get_current_order()
    waiting_orders = kitchen.get_waiting_orders()
    order_columns = st.columns(3)
    order_columns[0].metric("Đang chờ bếp", len(waiting_orders))
    order_columns[1].metric(
        "Đang chế biến",
        current_order.id if current_order else "Không có",
    )
    order_columns[2].metric(
        "Chờ thanh toán",
        len(order_service.filter_orders_by_status("SERVED")),
    )

    if current_order:
        st.markdown("### Đơn đang chế biến")
        st.write(
            f"**{current_order.id}** · Bàn {current_order.table_id} · "
            f"{current_order.final_amount:,} VNĐ"
        )
        st.table([item.model_dump(mode="json") for item in current_order.items])
        if st.button("Đã chế biến xong · Chuyển sang SERVED", type="primary"):
            try:
                kitchen.advance_status()
                kitchen.finish_current_order()
                if not order_service.save_orders():
                    raise OSError(f"Không thể lưu đơn '{current_order.id}'.")
            except (OSError, ValueError) as error:
                st.error(f"Không thể cập nhật hàng đợi bếp: {error}")
            else:
                st.rerun()
    elif waiting_orders:
        st.markdown("### Hàng đợi bếp")
        for position, waiting_order in enumerate(waiting_orders, start=1):
            estimate = kitchen.estimate_wait_time(waiting_order)
            st.write(
                f"{position}. **{waiting_order.id}** · Bàn {waiting_order.table_id} · "
                f"{waiting_order.calculate_prep_time()} phút chế biến · "
                f"ước tính chờ {estimate} phút"
            )
        if st.button("Bếp bắt đầu đơn tiếp theo", type="primary"):
            try:
                started_order = kitchen.start_next_order()
                if started_order is not None and not order_service.save_orders():
                    raise OSError(f"Không thể lưu đơn '{started_order.id}'.")
            except (OSError, ValueError) as error:
                st.error(f"Không thể bắt đầu chế biến: {error}")
            else:
                st.rerun()
    else:
        st.info("Hàng đợi bếp hiện đang trống.")

    st.markdown('<div class="section-title">Đơn hàng</div>', unsafe_allow_html=True)
    all_orders = sorted(
        order_service.get_all_orders(),
        key=lambda order: order.created_at,
        reverse=True,
    )
    if all_orders:
        for order in all_orders:
            status_label = {
                OrderStatus.PENDING: "Đang chờ bếp",
                OrderStatus.PREPARING: "Đang chế biến",
                OrderStatus.SERVED: "Đã phục vụ · chờ thanh toán",
                OrderStatus.COMPLETED: "Đã thanh toán · hoàn tất",
                OrderStatus.CANCELLED: "Đã hủy",
            }.get(order.status, order.status)
            with st.expander(
                f"{order.id} · Bàn {order.table_id} · {status_label} · "
                f"{order.final_amount:,} VNĐ"
            ):
                st.table([item.model_dump(mode="json") for item in order.items])
                if order.notes:
                    st.caption(order.notes)
    else:
        st.info("Chưa có đơn hàng.")

    st.markdown('<div class="section-title">Thanh toán</div>', unsafe_allow_html=True)
    served_orders = order_service.filter_orders_by_status("SERVED")
    if not served_orders:
        st.info("Chỉ đơn đã SERVED mới có thể thanh toán.")
    else:
        selected_order = st.selectbox(
            "Chọn đơn đã phục vụ",
            served_orders,
            format_func=lambda order: (
                f"{order.id} · Bàn {order.table_id} · {order.final_amount:,} VNĐ"
            ),
            key="payment_order",
        )
        payment_method = st.selectbox(
            "Phương thức thanh toán",
            ["CASH", "BANK_TRANSFER", "CARD"],
            format_func=lambda method: {
                "CASH": "Tiền mặt",
                "BANK_TRANSFER": "Chuyển khoản",
                "CARD": "Thẻ",
            }[method],
            key="ordering_payment_method",
        )
        cashier_name = st.text_input("Tên thu ngân", key="ordering_cashier")
        cash_received = None
        transaction_code = None
        transaction_successful = None
        if payment_method == "CASH":
            cash_received = st.number_input(
                "Tiền khách đưa (VNĐ)",
                min_value=0,
                value=selected_order.final_amount,
                step=1000,
                key=f"cash_received_{selected_order.id}",
            )
        else:
            transaction_code = st.text_input(
                "Mã giao dịch", key=f"transaction_code_{selected_order.id}"
            )
            transaction_successful = st.checkbox(
                "Cổng thanh toán đã xác nhận giao dịch SUCCESS",
                key=f"transaction_success_{selected_order.id}",
            )
        if st.button("Xác nhận thanh toán", type="primary"):
            try:
                result = PaymentService().pay_order(
                    order_id=selected_order.id,
                    method=payment_method,
                    cashier_name=cashier_name,
                    cash_received=int(cash_received) if cash_received is not None else None,
                    transaction_code=transaction_code or None,
                    transaction_successful=transaction_successful,
                )
            except ValueError as error:
                st.error(str(error))
            else:
                if result.invoice is None:
                    st.error(
                        "Thanh toán chưa thành công; đơn vẫn ở trạng thái SERVED "
                        "và bàn chưa được giải phóng."
                    )
                else:
                    order_service.load_orders()
                    table_manager.load_tables()
                    kitchen.restore_orders(order_service.get_all_orders())
                    st.session_state.payment_notice = (
                        f"Thanh toán thành công · hóa đơn {result.invoice.id} · "
                        f"đơn {result.invoice.order_id} đã COMPLETED."
                    )
                    st.session_state.payment_receipt = (
                        result.invoice.generate_text_receipt()
                    )
                    if result.payment.change_due:
                        st.session_state.payment_notice += (
                            f" Tiền thối lại: {result.payment.change_due:,} VNĐ."
                        )
                    st.rerun()

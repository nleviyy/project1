import json
import time
from pathlib import Path

import streamlit as st

from src.KitchenManage import KitchenManager
from src.core.Cart import Cart
from src.models.MenuCatalog import MenuCatalog

# ==========================================
# 1. CÀI ĐẶT STREAMLIT
# ==========================================

st.set_page_config(
    page_title="SUPPER MENU QUÁN",
    page_icon="🍔",
    layout="wide",
)

# Khởi tạo KitchenManager vào session_state
if "kitchen" not in st.session_state:
    st.session_state.kitchen = KitchenManager()


# ==========================================
# 2. CSS GIAO DIỆN
# ==========================================

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700&display=swap');

html,
body,
[class*="css"],
.stApp {
    font-family: "Be Vietnam Pro", sans-serif !important;
}

/* Nền toàn trang */
.stApp {
    background:
        radial-gradient(
            circle at top left,
            rgba(73, 50, 103, 0.78) 0%,
            transparent 34%
        ),
        radial-gradient(
            circle at bottom right,
            rgba(22, 78, 99, 0.78) 0%,
            transparent 34%
        ),
        linear-gradient(
            135deg,
            #0f172a,
            #111827,
            #1e1b4b
        );

    background-attachment: fixed;
}

/* Tên quán */
.brand-title {
    margin: 8px 0 28px 0;
    color: #ffffff;
    font-family: "Playfair Display", serif !important;
    font-size: 42px;
    font-weight: 700;
    letter-spacing: 1px;
    text-shadow: 0 4px 18px rgba(0, 0, 0, 0.35);
}

.brand-title span {
    color: #ffc857;
}

/* Header menu */
.menu-header {
    padding: 32px 38px;
    margin: 12px 0 32px 0;
    border-radius: 28px;
    background:
        linear-gradient(
            135deg,
            rgba(255, 123, 84, 0.96),
            rgba(142, 45, 226, 0.92)
        );
    box-shadow:
        0 18px 40px rgba(0, 0, 0, 0.35),
        inset 0 1px 0 rgba(255, 255, 255, 0.25);
}

.menu-title {
    margin: 0;
    color: #ffffff;
    font-family: "Playfair Display", serif !important;
    font-size: 46px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}

.menu-subtitle {
    margin-top: 12px;
    color: #fff9ef;
    font-size: 17px;
    font-weight: 500;
}

/* Tên món */
.food-card-title {
    margin: 10px 0 14px 0;
    color: #ffffff;
    font-size: 30px;
    font-weight: 800;
    line-height: 1.25;
    letter-spacing: -0.6px;
    text-shadow: 0 3px 12px rgba(0, 0, 0, 0.45);
}

.food-card-title::after {
    content: "";
    display: block;
    width: 75px;
    height: 4px;
    margin-top: 10px;
    border-radius: 10px;
    background: linear-gradient(
        90deg,
        #ffc857,
        #ff7b54
    );
}

/* Nhóm món */
.food-category {
    display: inline-block;
    padding: 6px 14px;
    border: 1px solid rgba(255, 255, 255, 0.25);
    border-radius: 20px;
    color: #ffffff;
    background: rgba(255, 255, 255, 0.14);
    font-size: 13px;
    font-weight: 700;
}

/* Giá */
.food-price {
    display: inline-block;
    padding: 9px 18px;
    border-radius: 24px;
    color: #8a5900;
    background: linear-gradient(
        135deg,
        #fff4c2,
        #ffd166
    );
    font-size: 18px;
    font-weight: 800;
    box-shadow: 0 5px 12px rgba(0, 0, 0, 0.15);
}

/* Mô tả */
.food-description {
    margin-top: 17px;
    color: #f1f1f1;
    font-size: 16px;
    line-height: 1.7;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background:
        linear-gradient(
            180deg,
            #171923 0%,
            #242633 100%
        );
}

section[data-testid="stSidebar"] h1 {
    color: #ffffff !important;
    font-size: 25px !important;
    font-weight: 800 !important;
}

section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #ffffff !important;
    font-size: 19px !important;
    font-weight: 700 !important;
}

section[data-testid="stSidebar"] label p,
section[data-testid="stSidebar"]
div[data-testid="stMarkdownContainer"] p {
    color: #f5f5f5 !important;
    font-size: 15px !important;
    font-weight: 500 !important;
}

/* Ô số lượng */
div[data-testid="stNumberInput"] input {
    text-align: center;
    font-size: 20px;
    font-weight: 800;
}

div[data-testid="stNumberInput"] label,
div[data-testid="stTextArea"] label {
    color: #ffffff !important;
    font-size: 15px !important;
    font-weight: 700 !important;
}

/* Ô ghi chú */
div[data-testid="stTextArea"] textarea {
    min-height: 90px;
    border-radius: 14px;
    font-family: "Be Vietnam Pro", sans-serif !important;
    font-size: 14px;
}

/* Tiêu đề giỏ hàng */
.cart-title {
    margin: 20px 0 28px 0;
    color: #ffffff;
    font-family: "Playfair Display", serif !important;
    font-size: 40px;
    font-weight: 700;
}

/* Món trong giỏ hàng */
.cart-item {
    padding: 17px;
    margin: 10px 0;
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-radius: 16px;
    color: #ffffff;
    background: rgba(255, 255, 255, 0.09);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.18);
    line-height: 1.8;
}

/* Nút */
.stButton > button {
    border: none;
    border-radius: 13px;
    font-family: "Be Vietnam Pro", sans-serif !important;
    font-weight: 700;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 18px rgba(0, 0, 0, 0.25);
}

/* Hiển thị trên điện thoại */
@media (max-width: 768px) {
    .brand-title {
        font-size: 30px;
    }

    .menu-title {
        font-size: 34px;
    }

    .food-card-title {
        font-size: 24px;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# 3. KHỞI TẠO GIỎ HÀNG VÀ THỰC ĐƠN
# ==========================================

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
cart = st.session_state.cart

# ==========================================
# 6. TIÊU ĐỀ QUÁN
# ==========================================

st.markdown(
    """
<div class="brand-title">
    🍔 SUPPER <span>MENU QUÁN</span>
</div>
""",
    unsafe_allow_html=True,
)


# ==========================================
# 7. MENU ĐIỀU HƯỚNG
# ==========================================

TRANG_THUC_DON = "📜  Thực đơn gọi món"
TRANG_GIO_HANG = "🛒  Giỏ hàng của bạn"

st.sidebar.title("🍽️ Thực đơn lựa chọn")

trang_hien_tai = st.sidebar.radio(
    "Đi đến:",
    [
        TRANG_THUC_DON,
        TRANG_GIO_HANG,
    ],
)

st.sidebar.divider()

st.sidebar.subheader("🛒 Giỏ hàng của bạn")

cart_items = cart.get_order_items()
st.sidebar.write(f"Đang chọn: **{cart.count_lines()} món**")
st.sidebar.write(f"Tổng tiền: **{cart.calculate_total():,} đ**")
undo_col, redo_col = st.sidebar.columns(2)
if undo_col.button("↶ Undo", disabled=not cart.can_undo(), use_container_width=True):
    cart.undo()
    st.session_state.cart_revision += 1
    st.rerun()
if redo_col.button("↷ Redo", disabled=not cart.can_redo(), use_container_width=True):
    cart.redo()
    st.session_state.cart_revision += 1
    st.rerun()


# ==========================================
# 8. TRANG THỰC ĐƠN
# ==========================================

if trang_hien_tai == TRANG_THUC_DON:

    st.markdown(
        """
<div class="menu-header">
    <div class="menu-title">🍽️ Thực đơn hôm nay</div>
    <div class="menu-subtitle">
        Chọn số lượng và nhập yêu cầu riêng cho từng món.
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    cart_by_id = {item["menu_item_id"]: item for item in cart_items}
    for mon in MENU:
        existing = cart_by_id.get(mon.id, {})
        so_luong_cu = existing.get("quantity", 0)
        ghi_chu_cu = existing.get("note", "")

        with st.container(border=True):

            cot_anh, cot_thong_tin, cot_dat_mon = st.columns(
                [1.5, 4.2, 2.4],
                vertical_alignment="center",
            )

            # Hình ảnh
            with cot_anh:
                st.markdown(
                    f"""
<div style="
    padding: 12px;
    border-radius: 22px;
    background: linear-gradient(
        135deg,
        {mon.color},
        #171923
    );
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.28);
">
""",
                    unsafe_allow_html=True,
                )

                if mon.image:
                    st.image(mon.image, width=230)
                else:
                    st.markdown("## 🍽️")

                st.markdown(
                    """
</div>
""",
                    unsafe_allow_html=True,
                )

            # Thông tin món
            with cot_thong_tin:
                st.markdown(
                    f"""
<div class="food-category">{mon.category}</div>

<div class="food-card-title">{mon.name}</div>

<div class="food-price">
    💰 {mon.price:,} đ
</div>

<div class="food-description">
    ⏱️ Thời gian chế biến: khoảng {mon.prep_time} phút / phần
</div>

<div class="food-description">
    {mon.description}
</div>
""",
                    unsafe_allow_html=True,
                )

            # Chọn số lượng và ghi chú
            with cot_dat_mon:

                so_luong_moi = st.number_input(
                    "Số lượng",
                    min_value=0,
                    max_value=20,
                    value=so_luong_cu,
                    step=1,
                    disabled=not mon.is_available,
                    key=f"quantity_{mon.id}_{st.session_state.cart_revision}",
                )

                ghi_chu_moi = st.text_area(
                    "Yêu cầu thêm",
                    value=ghi_chu_cu,
                    placeholder=(
                        "Ví dụ: ít đá, ít ngọt, "
                        "không hành, không cay..."
                    ),
                    height=100,
                    disabled=not mon.is_available,
                    key=f"note_{mon.id}_{st.session_state.cart_revision}",
                )

                if not mon.is_available:
                    st.warning("Món này hiện đã hết.")
                if st.button(
                    "Cập nhật giỏ hàng",
                    key=f"apply_{mon.id}_{st.session_state.cart_revision}",
                    disabled=not mon.is_available,
                    use_container_width=True,
                ):
                    current = next(
                        (
                            item for item in cart.get_order_items()
                            if item["menu_item_id"] == mon.id
                        ),
                        None,
                    )
                    if not mon.is_available:
                        st.error(f"{mon.name} hiện đã hết.")
                    elif so_luong_moi == 0:
                        if current is not None:
                            cart.remove_item(mon.id)
                    elif current is None:
                        cart.add_item(mon, so_luong_moi, ghi_chu_moi)
                    else:
                        cart.update_item(mon.id, so_luong_moi, ghi_chu_moi)
                    st.session_state.cart_revision += 1
                    st.rerun()


# ==========================================
# 9. TRANG GIỎ HÀNG
# ==========================================

elif trang_hien_tai == TRANG_GIO_HANG:

    st.markdown(
        """
<div class="cart-title">
    🧾 Kiểm tra đơn hàng
</div>
""",
        unsafe_allow_html=True,
    )

    cart_items = cart.get_order_items()
    if not cart_items:

        st.warning(
            "⚠️ Giỏ hàng đang trống! "
            "Vui lòng quay lại phần Thực đơn để chọn món."
        )

    else:

        st.subheader("📋 Chi tiết các món đã chọn")

        for item in cart_items:
            menu_item = MENU_BY_ID.get(item["menu_item_id"])
            st.markdown(
                f"""
<div class="cart-item">
    <b>🍽️ {item["item_name"]}</b><br>
    Đơn giá: {item["unit_price"]:,} đ<br>
    Thành tiền: {item["subtotal"]:,} đ
</div>
""",
                unsafe_allow_html=True,
            )
            quantity_col, note_col, update_col, remove_col = st.columns(
                [1, 2, 1, 1],
                vertical_alignment="bottom",
            )
            with quantity_col:
                quantity = st.number_input(
                    "Số lượng",
                    min_value=1,
                    max_value=20,
                    value=item["quantity"],
                    step=1,
                    key=f"cart_quantity_{item['menu_item_id']}_{st.session_state.cart_revision}",
                )
            with note_col:
                note = st.text_input(
                    "Ghi chú",
                    value=item.get("note", ""),
                    key=f"cart_note_{item['menu_item_id']}_{st.session_state.cart_revision}",
                )
            with update_col:
                if st.button(
                    "Lưu sửa",
                    key=f"cart_update_{item['menu_item_id']}_{st.session_state.cart_revision}",
                    use_container_width=True,
                ):
                    if menu_item is None or not menu_item.is_available:
                        st.error(f"{item['item_name']} hiện đã hết hoặc không có trong menu.")
                    else:
                        cart.update_item(item["menu_item_id"], quantity, note)
                        st.session_state.cart_revision += 1
                        st.rerun()
            with remove_col:
                if st.button(
                    "Xóa",
                    key=f"cart_remove_{item['menu_item_id']}_{st.session_state.cart_revision}",
                    use_container_width=True,
                ):
                    cart.remove_item(item["menu_item_id"])
                    st.session_state.cart_revision += 1
                    st.rerun()

        st.divider()

        st.subheader(
            f"💰 Tổng cộng: "
            f"{cart.calculate_total():,} VNĐ"
        )

        ban_ngoi = st.selectbox(
            "🪑 Bạn chọn ngồi ở đâu?",
            [
                "Bàn số 1",
                "Bàn số 2",
                "Bàn số 3",
                "Mang về (Takeaway)",
            ],
        )

        if st.button("🚀 XÁC NHẬN ĐẶT MÓN", type="primary", use_container_width=True):
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
                with st.spinner("Đang gửi thông tin xuống bếp..."):
                    time.sleep(1)
                    thoi_gian_doi = st.session_state.kitchen.receive_order(
                        table_id=ban_ngoi,
                        items=cart_items,
                    )
                st.success(
                    f"✅ Đơn đã được tiếp nhận. Thời gian lên món dự kiến: "
                    f"**{thoi_gian_doi} phút**."
                )
                st.balloons()
                cart.clear()
                st.session_state.cart_revision += 1
                st.rerun()
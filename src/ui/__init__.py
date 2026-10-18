import time
import streamlit as st
from kitchen import KitchenManager
from src.models.OrderItem import OrderItem
from src.models.Order import Order
import json
import os
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
# 3. CLASS GIỎ HÀNG
# ==========================================

class GioHang:

    def __init__(self):
        self.danh_sach_mon = {}
        self.ban_ngoi = "Chưa chọn bàn"

    def cap_nhat_mon(
        self,
        mon_id,
        ten_mon,
        gia,
        so_luong,
        hinh_anh,
        ghi_chu="",
        prep_time=0,
    ):
        if so_luong > 0:
            self.danh_sach_mon[mon_id] = {
                "ten": ten_mon,
                "gia": gia,
                "sl": so_luong,
                "img": hinh_anh,
                "ghi_chu": ghi_chu.strip(),
                "prep_time": prep_time,
            }
        else:
            self.danh_sach_mon.pop(mon_id, None)

    def tinh_tong_tien(self):
        return sum(
            mon["gia"] * mon["sl"]
            for mon in self.danh_sach_mon.values()
        )

    def xoa_sach_gio_hang(self):
        self.danh_sach_mon.clear()
        self.ban_ngoi = "Chưa chọn bàn"


# ==========================================
# 4. KHỞI TẠO GIỎ HÀNG
# ==========================================

if "gio_hang" not in st.session_state:
    st.session_state.gio_hang = GioHang()

gio_hang = st.session_state.gio_hang


# ==========================================
# 5. DỮ LIỆU MENU
# ==========================================

@st.cache_data
def load_menu():
    file_path = "menu.json"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        st.error(f"❌ Không tìm thấy file `{file_path}`! Vui lòng kiểm tra lại thư mục.")
        return []
MENU = load_menu()

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

st.sidebar.write(
    f"Đang chọn: "
    f"**{len(gio_hang.danh_sach_mon)} món**"
)

st.sidebar.write(
    f"Tổng tiền: "
    f"**{gio_hang.tinh_tong_tien():,} đ**"
)


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

    for mon in MENU:

        mon_id = mon["id"]

        thong_tin_cu = gio_hang.danh_sach_mon.get(
            mon_id,
            {},
        )

        so_luong_cu = thong_tin_cu.get("sl", 0)
        ghi_chu_cu = thong_tin_cu.get("ghi_chu", "")

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
        {mon["color"]},
        #171923
    );
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.28);
">
""",
                    unsafe_allow_html=True,
                )

                st.image(
                    mon["image"],
                    width=230,
                )

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
<div class="food-category">{mon["category"]}</div>

<div class="food-card-title">{mon["name"]}</div>

<div class="food-price">
    💰 {mon["price"]:,} đ
</div>

<div class="food-description">
    ⏱️ Thời gian chế biến: khoảng {mon["prep_time"]} phút / phần
</div>

<div class="food-description">
    {mon["description"]}
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
                    key=f"so_luong_{mon_id}",
                )

                ghi_chu_moi = st.text_area(
                    "Yêu cầu thêm",
                    value=ghi_chu_cu,
                    placeholder=(
                        "Ví dụ: ít đá, ít ngọt, "
                        "không hành, không cay..."
                    ),
                    height=100,
                    key=f"ghi_chu_{mon_id}",
                )

                gio_hang.cap_nhat_mon(
                    mon_id=mon_id,
                    ten_mon=mon["name"],
                    gia=mon["price"],
                    so_luong=so_luong_moi,
                    hinh_anh=mon["image"],
                    ghi_chu=ghi_chu_moi,
                    prep_time=mon["prep_time"],
                )


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

    if not gio_hang.danh_sach_mon:

        st.warning(
            "⚠️ Giỏ hàng đang trống! "
            "Vui lòng quay lại phần Thực đơn để chọn món."
        )

    else:

        st.subheader("📋 Chi tiết các món đã chọn")

        for mon_id, thong_tin in gio_hang.danh_sach_mon.items():

            thanh_tien = (
                thong_tin["gia"] * thong_tin["sl"]
            )

            ghi_chu = (
                thong_tin.get("ghi_chu", "").strip()
                or "Không có yêu cầu thêm"
            )

            st.markdown(
                f"""
<div class="cart-item">
    <b>🍽️ {thong_tin["ten"]}</b><br>
    Số lượng: {thong_tin["sl"]}<br>
    Thành tiền: {thanh_tien:,} đ<br>
    📝 Yêu cầu: {ghi_chu}
</div>
""",
                unsafe_allow_html=True,
            )

        st.divider()

        st.subheader(
            f"💰 Tổng cộng: "
            f"{gio_hang.tinh_tong_tien():,} VNĐ"
        )

        gio_hang.ban_ngoi = st.selectbox(
            "🪑 Bạn chọn ngồi ở đâu?",
            [
                "Bàn số 1",
                "Bàn số 2",
                "Bàn số 3",
                "Mang về (Takeaway)",
            ],
        )

        if st.button("🚀 XÁC NHẬN ĐẶT MÓN", type="primary", use_container_width=True):
            with st.spinner("Đang gửi thông tin xuống bếp..."):
                time.sleep(1)
            # BƯỚC 1: Đóng gói từ Giỏ hàng sang danh sách OrderItem
            danh_sach_order_items = []
            tong_thoi_gian_nau = 0
            for mon_id, info in gio_hang.danh_sach_mon.items():
                item = OrderItem(
                    menu_item_id=mon_id,
                    item_name=info["ten"],
                    unit_price=float(info["gia"]),
                    quantity=int(info["sl"]),
                    subtotal=float(info["gia"] * info["sl"]),
                    note=info.get("ghi_chu", "")
                )
                danh_sach_order_items.append(item)
                tong_thoi_gian_nau += info.get("prep_time", 5) * info["sl"]
            # BƯỚC 2: Tạo đối tượng Order chính thức (Trạng thái PENDING)
            ma_don = f"ORD-{int(time.time())}"
            don_hang_moi = Order(
                id=ma_don,
                table_id=gio_hang.ban_ngoi,
                status="PENDING",
                items=danh_sach_order_items,
                notes=f"Đơn đặt tại {gio_hang.ban_ngoi}"
            )
            # Gán thêm thời gian nấu để KitchenManager tính toán
            don_hang_moi.prep_time = tong_thoi_gian_nau 
            # BƯỚC 3: Kết nối với KitchenManager chuẩn qua hàm add_order và estimate_wait_time
            kitchen: KitchenManager = st.session_state.kitchen
            
            # Tính thời gian chờ thực tế dựa trên Order vừa tạo
            thoi_gian_doi = kitchen.estimate_wait_time(don_hang_moi)
            
            # Đẩy Order vào hàng đợi của Bếp
            kitchen.add_order(don_hang_moi)
            # BƯỚC 4: Thông báo thành công
            st.success(f"🎉 Đã tạo đơn **{don_hang_moi.id}** cho **{don_hang_moi.table_id}**!")
            st.success(f"✅ Bếp đã tiếp nhận đơn hàng! Thời gian lên món dự kiến: **{thoi_gian_doi} phút**.")
            st.balloons()
            # Dọn dẹp giỏ hàng
            gio_hang.xoa_sach_gio_hang()
            for mon in MENU:
                st.session_state.pop(f"so_luong_{mon['id']}", None)
                st.session_state.pop(f"ghi_chu_{mon['id']}", None)
            time.sleep(2)
            st.rerun()
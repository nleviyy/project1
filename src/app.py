"""
Hệ thống Quản lý Đơn hàng & Bàn ăn F&B bằng Python
Module 1 - Đồ án thực hành

File chạy chính ứng dụng Streamlit:
    python -m uv run streamlit run src/app.py
    hoặc: uv run streamlit run src/app.py
"""
import json
from pathlib import Path
import streamlit as st

# Thiết lập cấu hình trang Streamlit
st.set_page_config(
    page_title="F&B Order & Table Management",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

def load_json(file_path: Path):
    """Đọc dữ liệu JSON an toàn."""
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# Mappings chuẩn hóa hiển thị giao diện
TABLE_STATUS_MAP = {
    "AVAILABLE": ("Trống", "🟢"),
    "OCCUPIED": ("Có khách", "🔴"),
    "RESERVED": ("Đã đặt trước", "🟡"),
}

ORDER_STATUS_MAP = {
    "PENDING": ("Chờ xác nhận", "⏳"),
    "PREPARING": ("Đang chế biến", "🍳"),
    "SERVED": ("Đã lên món", "🍽️"),
    "COMPLETED": ("Hoàn thành", "✅"),
    "CANCELLED": ("Đã hủy", "❌"),
}

PAYMENT_METHOD_MAP = {
    "CASH": "Tiền mặt",
    "BANK_TRANSFER": "Chuyển khoản / VietQR",
    "CARD": "Thẻ POS 💳",
}

# Sidebar
with st.sidebar:
    st.title("F&B Management")
    st.caption("Đồ án Python Module 1")
    st.divider()

    st.subheader("👥 Phân công thành viên")
    st.markdown("""
    * **Vy:** Git, khởi tạo dự án & tích hợp code
    * **Quỳnh:** Models (Data Classes) & Lưu trữ JSON
    * **Anh:** OOP & Xử lý nghiệp vụ bàn ăn / đơn hàng
    * **Thắng:** Thiết kế giao diện tương tác Streamlit
    """)
    st.divider()
    
    st.subheader("📅 Kế hoạch mốc thời gian")
    st.info("**Thứ Bảy (17/10/2026):** Hoàn thành 50% đồ án\n\n**Thứ Ba (20/10/2026):** Báo cáo tiến độ")

# Main Content
st.title("🍽️ Hệ Thống Quản Lý Đơn Hàng & Bàn Ăn F&B")
st.success("Hợp đồng dữ liệu JSON (Data Contract) đã được thống nhất và kiểm thử tự động 100%!")

tabs = st.tabs([
    "📊 Tổng quan hệ thống", 
    "📋 Thực đơn (menu.json)", 
    "🪑 Sơ đồ bàn (tables.json)", 
    "🧾 Đơn hàng (orders.json)", 
    "💳 Thanh toán (payments.json)"
])

# Tab 1: Tổng quan
with tabs[0]:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Môi trường", "Python + uv")
    with c2:
        st.metric("Giao diện", "Streamlit")
    with c3:
        st.metric("Mục tiêu nộp 50%", "17/10/2026")
    with c4:
        st.metric("Trạng thái kiểm thử", "51/51 Tests Passed ✅")

    st.markdown("### 🎯 Tiến độ thực hiện đồ án (Tổng hợp cả nhóm)")
    st.markdown("""
    - [x] **Mục 5 (Vy):** Khởi tạo Repo GitHub, cấu hình `uv`, cấu trúc thư mục, `.gitignore` và chốt Schema JSON.
    - [x] **Mục 1 (Quỳnh):** Hiện thực hóa Data Classes (`MenuItem`, `Order`, `Table`, `Payment`) dựa trên Schema.
    - [x] **Mục 2 (Anh):** Viết logic OOP quản lý trạng thái (`kitchen.py`, `redo_undo.py`, `OrderService`).
    - [x] **Mục 3 (Thắng):** Nối giao diện Streamlit với các Class nghiệp vụ để tạo đơn và đổi trạng thái bàn.
    """)

    st.divider()
    st.markdown("### 📊 Thống kê nhanh hoạt động nhà hàng")
    tables_list = load_json(DATA_DIR / "tables.json")
    orders_list = load_json(DATA_DIR / "orders.json")
    payments_list = load_json(DATA_DIR / "payments.json")

    occupied = sum(1 for t in tables_list if t.get("status") == "OCCUPIED")
    active_orders = sum(1 for o in orders_list if o.get("status") not in ("COMPLETED", "CANCELLED"))
    total_rev = sum(p.get("amount_paid", 0) for p in payments_list if p.get("status") == "SUCCESS")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Tổng số bàn", len(tables_list))
    with k2:
        st.metric("Bàn đang phục vụ", f"{occupied} bàn")
    with k3:
        st.metric("Đơn chưa thanh toán", f"{active_orders} đơn")
    with k4:
        st.metric("Tổng doanh thu", f"{total_rev:,} VNĐ")

# Tab 2: Thực đơn
with tabs[1]:
    st.subheader("📋 Danh mục món ăn (`data/menu.json`)")
    menu_data = load_json(DATA_DIR / "menu.json")
    if menu_data:
        st.dataframe(menu_data, use_container_width=True)
    else:
        st.warning("Chưa tìm thấy file data/menu.json")

# Tab 3: Sơ đồ bàn
with tabs[2]:
    st.subheader("🪑 Sơ đồ bàn ăn (`data/tables.json`)")
    tables_data = load_json(DATA_DIR / "tables.json")
    if tables_data:
        tot = len(tables_data)
        occ = sum(1 for t in tables_data if t.get("status") == "OCCUPIED")
        avl = sum(1 for t in tables_data if t.get("status") == "AVAILABLE")
        res = sum(1 for t in tables_data if t.get("status") == "RESERVED")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Tổng số bàn", tot)
        m2.metric("🟢 Bàn trống", avl)
        m3.metric("🔴 Có khách", occ)
        m4.metric("🟡 Đã đặt trước", res)
        st.divider()

        # Hiển thị dạng lưới 3 cột trực quan
        num_cols = 3
        cols = st.columns(num_cols)
        for idx, table in enumerate(tables_data):
            col_target = cols[idx % num_cols]
            with col_target:
                with st.container(border=True):
                    status_raw = table.get("status", "AVAILABLE")
                    label, icon = TABLE_STATUS_MAP.get(status_raw, (status_raw, "⚪"))
                    st.markdown(f"### {icon} {table['name']}")
                    st.caption(f"Sức chứa: **{table['capacity']}** khách")
                    st.write(f"Trạng thái: **{label}**")
                    if table.get("current_order_id"):
                        st.badge(f"Đơn: {table['current_order_id']}", color="red")
                    else:
                        st.caption("Chưa có đơn hàng")
    else:
        st.warning("Chưa tìm thấy file data/tables.json")

# Tab 4: Đơn hàng
with tabs[3]:
    st.subheader("🧾 Danh sách đơn hàng (`data/orders.json`)")
    orders_data = load_json(DATA_DIR / "orders.json")
    if orders_data:
        for ord_item in orders_data:
            st_raw = ord_item.get("status", "PENDING")
            st_label, st_icon = ORDER_STATUS_MAP.get(st_raw, (st_raw, "⚪"))
            with st.expander(f"{st_icon} Đơn hàng: **{ord_item['id']}** | Bàn: **{ord_item['table_id']}** | Trạng thái: **{st_label}** | Tổng: **{ord_item['final_amount']:,}đ**"):
                st.write(f"🕒 **Thời gian tạo:** `{ord_item['created_at']}` | **Cập nhật:** `{ord_item['updated_at']}`")
                if ord_item.get("notes"):
                    st.caption(f"📝 Ghi chú: {ord_item['notes']}")
                st.table(ord_item["items"])
    else:
        st.warning("Chưa tìm thấy file data/orders.json")

# Tab 5: Thanh toán
with tabs[4]:
    st.subheader("💳 Lịch sử giao dịch thanh toán (`data/payments.json`)")
    payments_data = load_json(DATA_DIR / "payments.json")
    if payments_data:
        total_rev = sum(p.get("amount_paid", 0) for p in payments_data if p.get("status") == "SUCCESS")
        success_count = sum(1 for p in payments_data if p.get("status") == "SUCCESS")
        
        p1, p2 = st.columns(2)
        with p1:
            st.metric("Tổng doanh thu thực nhận", f"{total_rev:,} VNĐ")
        with p2:
            st.metric("Giao dịch thành công", f"{success_count}/{len(payments_data)} giao dịch")
        st.divider()

        st.dataframe(payments_data, use_container_width=True)
    else:
        st.warning("Chưa tìm thấy file data/payments.json")

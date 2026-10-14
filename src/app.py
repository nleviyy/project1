"""
Hệ thống Quản lý Đơn hàng & Bàn ăn F&B bằng Python
Module 1 - Đồ án thực hành

File chạy chính ứng dụng Streamlit:
    uv run streamlit run src/app.py
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

# Sidebar
with st.sidebar:
    st.title("🍽️ F&B Management")
    st.caption("Đồ án Python Module 1 - Nhóm 4 thành viên")
    st.divider()

    st.subheader("👥 Phân công thành viên")
    st.markdown("""
    * **Vy (Leader):** Git, khởi tạo & tích hợp code
    * **Quỳnh:** Models & Lưu trữ JSON
    * **Anh:** OOP & Cấu trúc dữ liệu
    * **Thắng:** Giao diện Streamlit
    """)
    st.divider()
    
    st.subheader("📅 Kế hoạch mốc thời gian")
    st.info("**Thứ Bảy (17/10/2026):** Hoàn thành 50% đồ án\n\n**Thứ Ba (20/10/2026):** Báo cáo tiến độ")

# Main Content
st.title("🍽️ Hệ Thống Quản Lý Đơn Hàng & Bàn Ăn F&B")
st.success("Khởi tạo môi trường `uv` và cấu trúc dự án thành công! Sẵn sàng cho việc phân nhánh code.")

tab1, tab2, tab3 = st.tabs(["📊 Tổng quan hệ thống", "📋 Thực đơn (Menu)", "🪑 Sơ đồ bàn ăn"])

with tab1:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Môi trường", "Python + uv")
    with col2:
        st.metric("Giao diện", "Streamlit")
    with col3:
        st.metric("Mục tiêu nộp 50%", "17/10/2026")
    with col4:
        st.metric("Trạng thái", "Sẵn sàng (Phase 1 OK)")

    st.markdown("### 🎯 Mục tiêu 50% đồ án (Đến ngày 17/10/2026)")
    st.markdown("""
    - [x] **Mục 5 (Vy):** Khởi tạo Repository GitHub, cấu hình `uv`, cấu trúc thư mục và `.gitignore`.
    - [ ] **Mục 1 (Quỳnh):** Thiết kế Data classes `MenuItem`, `Order`, `Table` và lưu file JSON.
    - [ ] **Mục 2 (Anh):** Xây dựng các lớp quản lý `OrderManager`, `TableManager` theo nguyên lý OOP.
    - [ ] **Mục 3 (Thắng):** Tích hợp giao diện hiển thị danh sách bàn, đặt món và thanh toán cơ bản.
    """)

with tab2:
    st.subheader("📋 Thực đơn ban đầu (Dữ liệu mẫu `data/sample_menu.json`)")
    menu_data = load_json(DATA_DIR / "sample_menu.json")
    if menu_data:
        st.dataframe(menu_data, use_container_width=True)
    else:
        st.warning("Chưa tìm thấy file dữ liệu menu mẫu.")

with tab3:
    st.subheader("🪑 Sơ đồ bàn ăn ban đầu (Dữ liệu mẫu `data/sample_tables.json`)")
    tables_data = load_json(DATA_DIR / "sample_tables.json")
    if tables_data:
        cols = st.columns(len(tables_data))
        for idx, table in enumerate(tables_data):
            with cols[idx]:
                status_color = "🟢" if table["status"] == "Trống" else ("🔴" if table["status"] == "Có khách" else "🟡")
                st.markdown(f"### {status_color} {table['name']}")
                st.caption(f"Sức chứa: {table['capacity']} người")
                st.write(f"Trạng thái: **{table['status']}**")
    else:
        st.warning("Chưa tìm thấy file dữ liệu bàn ăn mẫu.")

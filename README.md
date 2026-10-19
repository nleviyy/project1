Hệ Thống Quản Lý Đơn Hàng & Bàn Ăn F&B bằng Python

> **Đồ án Module 1** - Phát triển ứng dụng quản lý nhà hàng / quán ăn F&B bằng Python, áp dụng lập trình hướng đối tượng (OOP), lưu trữ dữ liệu JSON và xây dựng giao diện tương tác với Streamlit.

---

## 👥 Danh Sách Nhóm & Phân Công Nhiệm Vụ

| Thành viên | Vai trò | Nhiệm vụ chính |
| :--- | :--- | :--- |
| **Nguyễn Lê Vy** | **Team Leader** | Khởi tạo dự án, thiết lập `uv` & Git, quản lý repository, review Pull Request và tích hợp code. |
| **Quỳnh** | Developer | Phụ trách thư mục `src/models/`, thiết kế Data Classes (`MenuItem`, `Order`, `Table`) và xử lý đọc/ghi file JSON (`data/`). |
| **Anh** | Developer | Phụ trách thư mục `src/core/`, hiện thực hóa các lớp quản lý nghiệp vụ (`OrderManager`, `TableManager`) áp dụng nguyên lý OOP và cấu trúc dữ liệu. |
| **Thắng** | Developer | Phụ trách thư mục `src/ui/` và `src/app.py`, xây dựng giao diện người dùng tương tác bằng **Streamlit**. |

---

## 📅 Kế Hoạch & Mốc Thời Gian

* **Thứ Bảy, ngày 17/10/2026:** Hoàn thành **50% đồ án** để nộp (khung sườn kiến trúc, models cơ bản, luồng OOP sơ khởi, UI demo hiển thị dữ liệu).
* **Thứ Ba, ngày 20/10/2026:** Báo cáo tiến độ đồ án.

---

## 🏗️ Cấu Trúc Thư Mục Dự Án

```text
project1/
├── data/                   # Chứa các file dữ liệu lưu trữ dạng JSON (menu, orders, tables)
│   ├── sample_menu.json
│   └── sample_tables.json
├── src/                    # Mã nguồn chính của ứng dụng
│   ├── models/             # Định nghĩa Data Classes & cấu trúc thực thể (Quỳnh)
│   │   ├── Order.py
│   │   └── KitchenOrder.py
│   ├── core/               # Nghiệp vụ logic, OOP & cấu trúc dữ liệu (Anh)
│   │   ├── Cart.py
│   │   ├── KitchenManager.py
│   │   └── OrderService.py
│   ├── ui/                 # Các component giao diện Streamlit (Thắng)
│   │   └── __init__.py     # render_ordering_ui()
│   └── app.py              # File chạy chính của ứng dụng Streamlit
├── tests/                  # Bộ kiểm thử tự động với pytest
│   ├── __init__.py
│   └── test_smoke.py
├── .gitignore              # Loại bỏ .venv, cache, secrets (GIỮ LẠI uv.lock)
├── pyproject.toml          # Khai báo metadata dự án và thư viện phụ thuộc (PEP 621)
├── uv.lock                 # Khóa phiên bản chính xác của toàn bộ dependencies
└── README.md               # Tài liệu hướng dẫn dự án
```

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy Ứng Dụng (Dành Cho Thành Viên Mới)

Dự án sử dụng **`uv`** làm công cụ quản lý package và môi trường ảo.

### 1. Yêu cầu tiên quyết
* Đã cài đặt **Python >= 3.11** và **Git**.
* Đã cài đặt công cụ **uv**:
  ```powershell
  # Trên Windows (PowerShell):
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  # Hoặc qua pip:
  python -m pip install uv
  ```

### 2. Clone dự án về máy
```powershell
git clone https://github.com/nleviyy/project1.git
cd project1
```

### 3. Đồng bộ môi trường ảo (Cài đặt dependencies từ `uv.lock`)
Chỉ với **1 câu lệnh duy nhất**, `uv` sẽ tự tạo môi trường ảo `.venv` và cài đúng phiên bản thư viện:
```powershell
uv sync
```

### 4. Chạy ứng dụng Streamlit
```powershell
uv run streamlit run src/app.py
```
👉 Trình duyệt sẽ tự động mở địa chỉ: `http://localhost:8501`.
`src/app.py` là entry point duy nhất; các màn hình UI được render từ những component trong `src/ui/`.

### 5. Chạy bộ kiểm thử (pytest)
```powershell
uv run pytest
```

---

## 🌿 Quy Chuẩn Git & Làm Việc Nhóm

### 1. Quy tắc nhánh (Branch Rules)
* **Tuyệt đối không commit trực tiếp vào nhánh `main`**.
* Mỗi thành viên tạo nhánh riêng khi làm việc:
  * `feature/<tên>-<tính-năng>` (ví dụ: `feature/quynh-models`, `feature/thang-ui`)
  * `fix/<tên>-<lỗi>` (ví dụ: `fix/anh-order-calc`)

### 2. Quy tắc Commit (Conventional Commits)
* `feat:` Thêm tính năng mới (vd: `feat(models): dinh nghia MenuItem`)
* `fix:` Sửa lỗi (vd: `fix(core): sua loi tinh tong tien hoa don`)
* `docs:` Viết tài liệu (vd: `docs: cap nhat huong dan README`)
* `test:` Viết thêm bài kiểm thử (vd: `test: them test case cho TableManager`)
* `chore:` Cấu hình môi trường (vd: `chore: cap nhat dependencies uv`)

### 3. Quy trình Pull Request (PR)
1. Kéo code mới nhất từ `main` về trước khi code: `git pull origin main`.
2. Tạo branch, thực hiện code và commit.
3. Push branch lên GitHub: `git push -u origin feature/<tên-nhánh>`.
4. Mở **Pull Request** trên GitHub, gắn thẻ Vy (Leader) để review.
5. Sau khi review và xác nhận không có lỗi, Leader sẽ duyệt và merge vào `main`.

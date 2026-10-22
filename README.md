# DŨNG FAST FOOD — Quản lý nhà hàng

Ứng dụng quản lý nhà hàng viết bằng Python, Streamlit và JSON. Code được chia theo
trách nhiệm: `models/` biểu diễn dữ liệu, `core/` xử lý nghiệp vụ, `ui/` nhận thao
tác và hiển thị dữ liệu. Ứng dụng chỉ có một entry point Streamlit là
`src/app.py`.

## Cấu trúc dự án

```text
project1/
├── data/
│   ├── menu.json           # Thực đơn vận hành, gồm giá VNĐ và prep_time
│   ├── tables.json         # Bàn và trạng thái hiện tại
│   ├── orders.json         # Lịch sử đơn và trạng thái
│   ├── payments.json       # Giao dịch thanh toán
│   └── invoices.json       # Hóa đơn
├── src/
│   ├── app.py              # Entry point Streamlit duy nhất
│   ├── core/
│   │   ├── Cart.py
│   │   ├── KitchenManager.py
│   │   ├── OrderService.py
│   │   ├── PaymentService.py
│   │   └── TableManager.py
│   ├── models/             # Order, OrderItem, MenuItem, Table, Payment, Invoice,
│   │                       # MenuCatalog và JSONStorage
│   └── ui/
│       ├── __init__.py     # Các component Streamlit
│       └── bridge.py       # Adapter nghiệp vụ cho các thao tác JSON
├── tests/                  # Kiểm thử đơn vị và tích hợp
├── demo_data_structure.py
├── demo_order.py
├── demo_mentor_flow.py
├── pyproject.toml
└── uv.lock
```

`sample_menu.json` và `sample_tables.json` nếu được giữ trong repository chỉ là
dữ liệu minh họa; ứng dụng vận hành chỉ đọc `menu.json`, `tables.json`,
`orders.json` và `payments.json` trong `data/`.

## Cài đặt và chạy

Yêu cầu Python 3.11 trở lên và `uv`.

```powershell
uv sync
uv run streamlit run src/app.py
```

Mở địa chỉ được Streamlit in ra trong terminal (mặc định
`http://localhost:8501`). Không chạy riêng module UI; mọi khu vực đặt món, bếp,
thu ngân, bàn ăn và tổng quan được điều hướng trong cùng ứng dụng.

## Luồng nghiệp vụ

1. Chọn bàn `AVAILABLE` (hoặc mang về), chọn món còn phục vụ và thao tác giỏ.
2. Xác nhận tạo đơn `PENDING`; đơn được lưu, bàn được chiếm và đơn vào cuối queue.
3. Bếp lấy đơn theo FIFO. Chỉ khi bắt đầu chế biến đơn chuyển sang `PREPARING`;
   lên món chuyển sang `SERVED`.
4. Thu ngân chỉ thanh toán đơn `SERVED`. Thanh toán thành công tạo Payment và
   Invoice, cho phép tải hóa đơn dạng văn bản, chuyển đơn sang `COMPLETED` rồi
   giải phóng bàn.
5. Chỉ hủy được đơn `PENDING`. Thời gian chờ được tính từ `prep_time` từng món,
   số lượng và vị trí trong queue; thời gian đã trôi qua của đơn đang chế biến
   được tính sau khi khởi động lại.

`Cart` và lựa chọn giao diện có thể nằm trong `st.session_state`; đơn hàng, bàn,
thanh toán và hóa đơn được lưu trong các file JSON. `JSONStorage` phụ trách đọc
và ghi; thao tác thanh toán dùng ghi nhiều file có rollback để hạn chế dữ liệu
không nhất quán.

## Kiểm thử và demo

```powershell
uv run pytest
uv run python demo_data_structure.py
uv run python demo_order.py
uv run python demo_mentor_flow.py
```

## Quy trình Git nhóm

1. Tạo nhánh công việc từ `dev`:

   ```powershell
   git switch dev
   git pull origin dev
   git switch -c feature/<ten-tinh-nang>
   ```

2. Commit thay đổi trên nhánh riêng và push lên remote.
3. Mở Pull Request về `dev` để Leader review; chạy test trước khi merge.
4. Chỉ tích hợp từ `dev` lên `main` sau khi các thay đổi đã được review và kiểm
   thử hoàn chỉnh.

Dùng Conventional Commits, ví dụ `feat(core): add payment flow`,
`fix(ui): route kitchen actions through services`, `test: cover order lifecycle`
và `docs: update run instructions`.

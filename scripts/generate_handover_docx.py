"""
Script tự động tạo file tài liệu bàn giao đồ án Word (.docx) chuẩn nhận diện học thuật.
Đề tài: Hệ thống quản lý đơn hàng và bàn ăn F&B bằng Python.
"""
import os
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, hex_color):
    """Đặt màu nền cho ô trong bảng."""
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Thiết lập padding cho ô."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def create_handover_document(output_path: str):
    doc = Document()

    # Thiết lập lề trang chuẩn A4
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # Màu sắc nhận diện
    COLOR_PRIMARY = RGBColor(26, 54, 93)     # Navy đậm
    COLOR_SECONDARY = RGBColor(43, 108, 176) # Xanh dương
    COLOR_DARK = RGBColor(45, 55, 72)        # Chữ xám than đậm
    COLOR_MUTED = RGBColor(113, 128, 150)    # Xám ghi

    # ==========================
    # TIÊU ĐỀ TRANG BÌA / HEADER
    # ==========================
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = p_sub.add_run("BỘ GIÁO DỤC VÀ ĐÀO TẠO • ĐỒ ÁN LẬP TRÌNH PYTHON MODULE 1")
    run_sub.font.name = "Arial"
    run_sub.font.size = Pt(9.5)
    run_sub.font.bold = True
    run_sub.font.color.rgb = COLOR_MUTED

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_title.add_run("TÀI LIỆU BÀN GIAO & ĐẶC TẢ DỰ ÁN\nHỆ THỐNG QUẢN LÝ ĐƠN HÀNG VÀ BÀN ĂN F&B")
    run_title.font.name = "Arial"
    run_title.font.size = Pt(17)
    run_title.font.bold = True
    run_title.font.color.rgb = COLOR_PRIMARY
    p_title.paragraph_format.space_before = Pt(6)
    p_title.paragraph_format.space_after = Pt(4)

    p_desc = doc.add_paragraph()
    p_desc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_desc = p_desc.add_run("Quy chuẩn Git, Môi trường uv, Cấu trúc Thư mục và Hợp đồng Dữ liệu (Data Contract)")
    run_desc.font.name = "Arial"
    run_desc.font.size = Pt(10.5)
    run_desc.font.italic = True
    run_desc.font.color.rgb = COLOR_DARK
    p_desc.paragraph_format.space_after = Pt(14)

    # Box tóm tắt mốc thời gian quan trọng
    p_box = doc.add_paragraph()
    p_box.paragraph_format.left_indent = Inches(0.2)
    p_box.paragraph_format.right_indent = Inches(0.2)
    p_box.paragraph_format.space_after = Pt(14)
    run_box = p_box.add_run(
        "📌 MỐC THỜI HẠN QUAN TRỌNG:\n"
        "• Thứ Bảy, 17/10/2026: Nộp bài giai đoạn 1 (Hoàn thành tối thiểu 50% đồ án).\n"
        "• Thứ Ba, 20/10/2026: Báo cáo tiến độ và demo trước Giảng viên hướng dẫn.\n"
        "• Repository GitHub: https://github.com/nleviyy/project1.git"
    )
    run_box.font.name = "Arial"
    run_box.font.size = Pt(10)
    run_box.font.bold = True
    run_box.font.color.rgb = RGBColor(180, 83, 9)

    def add_heading_1(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(4)
        run = h.add_run(text)
        run.font.name = "Arial"
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = COLOR_PRIMARY
        return h

    def add_heading_2(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(8)
        h.paragraph_format.space_after = Pt(3)
        run = h.add_run(text)
        run.font.name = "Arial"
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.color.rgb = COLOR_SECONDARY
        return h

    # ==========================
    # 1. THÀNH VIÊN VÀ PHÂN CÔNG
    # ==========================
    add_heading_1("1. THÀNH VIÊN NHÓM VÀ PHÂN CÔNG TRÁCH NHIỆM")
    
    table_members = doc.add_table(rows=1, cols=4)
    table_members.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Thành viên", "Vai trò", "Thư mục phụ trách", "Nhiệm vụ trọng tâm"]
    hdr_cells = table_members.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].text = title
        set_cell_background(hdr_cells[i], "1A365D")
        p = hdr_cells[i].paragraphs[0]
        p.runs[0].font.name = "Arial"
        p.runs[0].font.bold = True
        p.runs[0].font.size = Pt(9.5)
        p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
        set_cell_margins(hdr_cells[i], 120, 120, 150, 150)

    members_data = [
        ("Nguyễn Lê Vy", "Leader", "Toàn bộ dự án, .vscode/", "Khởi tạo repo, quản lý Git, thiết lập uv, review Pull Request và tích hợp code."),
        ("Quỳnh", "Developer", "src/models/, data/", "Thiết kế Data Classes (MenuItem, Order, Table, Payment) và xử lý đọc/ghi JSON an toàn."),
        ("Anh", "Developer", "src/core/", "Hiện thực hóa logic nghiệp vụ OOP (OrderManager, TableManager), cấu trúc dữ liệu và tính tiền."),
        ("Thắng", "Developer", "src/ui/, src/app.py", "Thiết kế giao diện tương tác Streamlit: quản lý bàn, đặt món và bảng điều khiển tổng quan.")
    ]

    for row_idx, data in enumerate(members_data):
        row_cells = table_members.add_row().cells
        bg_col = "F7FAFC" if row_idx % 2 == 0 else "FFFFFF"
        for col_idx, text in enumerate(data):
            row_cells[col_idx].text = text
            set_cell_background(row_cells[col_idx], bg_col)
            set_cell_margins(row_cells[col_idx], 80, 80, 120, 120)
            p = row_cells[col_idx].paragraphs[0]
            if len(p.runs) > 0:
                p.runs[0].font.name = "Arial"
                p.runs[0].font.size = Pt(9)
                p.runs[0].font.color.rgb = COLOR_DARK
                if col_idx == 0:
                    p.runs[0].font.bold = True

    # ==========================
    # 2. HƯỚNG DẪN KHỞI TẠO MÁY
    # ==========================
    add_heading_1("2. HƯỚNG DẪN CÀI ĐẶT & CHẠY DỰ ÁN CHO THÀNH VIÊN MỚI")
    p_step = doc.add_paragraph()
    p_step.paragraph_format.space_after = Pt(4)
    run_step = p_step.add_run(
        "Mỗi thành viên (Quỳnh, Anh, Thắng) thực hiện tuần tự 4 bước sau trên máy tính của mình:\n\n"
        "Bước 1: Chấp nhận lời mời GitHub\n"
        "• Mở email đăng ký GitHub hoặc truy cập link https://github.com/nleviyy/project1 để bấm 'Accept invitation'.\n\n"
        "Bước 2: Clone repository về máy và mở trong VS Code\n"
        "   git clone https://github.com/nleviyy/project1.git\n"
        "   cd project1\n\n"
        "Bước 3: Đồng bộ toàn bộ môi trường và thư viện phụ thuộc bằng uv\n"
        "   uv sync\n"
        "   (Nếu máy chưa nhận lệnh uv, gõ: python -m uv sync)\n\n"
        "Bước 4: Chạy thử ứng dụng Streamlit và kiểm tra hệ thống\n"
        "   uv run streamlit run src/app.py\n"
        "   (Hoặc: python -m uv run streamlit run src/app.py)\n"
        "   -> Trình duyệt tự mở http://localhost:8501 hiển thị 5 tab giao diện F&B hoàn chỉnh.\n\n"
        "Bước 5: Chạy bộ kiểm thử tự động (Smoke Test)\n"
        "   uv run pytest  (Kết quả mong đợi: 5/5 tests passed)"
    )
    run_step.font.name = "Arial"
    run_step.font.size = Pt(9.5)
    run_step.font.color.rgb = COLOR_DARK

    # ==========================
    # 3. QUY TRÌNH GIT FLOW
    # ==========================
    add_heading_1("3. QUY TRÌNH LÀM VIỆC NHÓM VỚI GIT (GIT FLOW THU NHỎ)")
    
    p_rule = doc.add_paragraph()
    p_rule.paragraph_format.space_after = Pt(4)
    r_rule = p_rule.add_run(
        "⚠️ QUY TẮC BẤT DI BẤT DỊCH: Tuyệt đối không commit hoặc push code trực tiếp vào nhánh main.\n"
        "Nhánh main đã được thiết lập bảo vệ (Branch Protection), chỉ nhận code thông qua Pull Request (PR) sau khi Vy duyệt."
    )
    r_rule.font.name = "Arial"
    r_rule.font.size = Pt(9.5)
    r_rule.font.bold = True
    r_rule.font.color.rgb = RGBColor(197, 48, 48)

    add_heading_2("A. Quy ước đặt tên nhánh (Branch Convention):")
    p_branch = doc.add_paragraph()
    p_branch.paragraph_format.space_after = Pt(4)
    p_branch.add_run(
        "• Quỳnh: feature/quynh-models-json\n"
        "• Anh: feature/anh-core-oop\n"
        "• Thắng: feature/thang-streamlit-ui\n"
        "• Khi sửa lỗi: fix/<tên-thành-viên>-<mô-tả-lỗi>"
    ).font.size = Pt(9.5)

    add_heading_2("B. Quy ước thông điệp Commit (Conventional Commits):")
    p_com = doc.add_paragraph()
    p_com.paragraph_format.space_after = Pt(4)
    p_com.add_run(
        "• feat(scope): Thêm tính năng mới (vd: feat(models): them MenuItem va Order)\n"
        "• fix(scope): Sửa lỗi logic (vd: fix(core): sua loi tinh tien chiet khau)\n"
        "• test(scope): Thêm unit test (vd: test(core): them test case cho TableManager)\n"
        "• docs: Cập nhật tài liệu (vd: docs: cap nhat spec du lieu)"
    ).font.size = Pt(9.5)

    add_heading_2("C. 4 bước đẩy code của mỗi thành viên:")
    p_flow = doc.add_paragraph()
    p_flow.paragraph_format.space_after = Pt(4)
    p_flow.add_run(
        "1. Kéo code mới nhất từ main: git checkout main && git pull origin main\n"
        "2. Tạo nhánh riêng: git checkout -b feature/<tên-nhánh>\n"
        "3. Code, commit và push lên GitHub: git push -u origin feature/<tên-nhánh>\n"
        "4. Lên GitHub mở Pull Request (PR) -> Gắn Vy làm Reviewer để duyệt và merge."
    ).font.size = Pt(9.5)

    # ==========================
    # 4. HỢP ĐỒNG DỮ LIỆU
    # ==========================
    add_heading_1("4. HỢP ĐỒNG DỮ LIỆU CHÍNH THỨC (DATA CONTRACT - 4 BẢNG JSON)")
    
    p_spec_intro = doc.add_paragraph()
    p_spec_intro.paragraph_format.space_after = Pt(4)
    p_spec_intro.add_run(
        "Toàn bộ 4 thành viên thống nhất các quy chuẩn sau:\n"
        "1. Tên trường (Field): 100% sử dụng snake_case (chữ thường, ngăn cách bằng gạch dưới).\n"
        "2. Định dạng thời gian: Chuẩn ISO 8601 không timezone: YYYY-MM-DDTHH:MM:SS (Ví dụ: 2026-10-14T20:15:00).\n"
        "3. Trạng thái (Status): Viết hoa dạng CONSTANT_CASE tiếng Anh trong file JSON."
    ).font.size = Pt(9.5)

    # 4.1 menu.json
    add_heading_2("4.1. Bảng dữ liệu: data/menu.json (Danh mục món ăn)")
    t_menu = doc.add_table(rows=1, cols=4)
    t_menu.alignment = WD_TABLE_ALIGNMENT.CENTER
    m_headers = ["Tên trường", "Kiểu dữ liệu", "Ý nghĩa", "Ví dụ mẫu"]
    for i, title in enumerate(m_headers):
        t_menu.rows[0].cells[i].text = title
        set_cell_background(t_menu.rows[0].cells[i], "2B6CB0")
        p = t_menu.rows[0].cells[i].paragraphs[0]
        p.runs[0].font.name = "Arial"
        p.runs[0].font.bold = True
        p.runs[0].font.size = Pt(9)
        p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
        set_cell_margins(t_menu.rows[0].cells[i], 80, 80, 100, 100)

    menu_rows = [
        ("id", "str (string)", "Mã định danh món duy nhất (Mxx)", '"M01"'),
        ("name", "str (string)", "Tên món ăn / thức uống", '"Cà phê sữa đá"'),
        ("category", "str (string)", "Phân loại: Đồ uống, Món chính, Khai vị, Ăn vặt", '"Đồ uống"'),
        ("price", "int / float", "Đơn giá bán tính bằng VNĐ (>= 0)", "29000"),
        ("unit", "str (string)", "Đơn vị tính", '"ly", "dĩa", "phần"'),
        ("is_available", "bool (boolean)", "Trạng thái còn món hay hết món", "true / false"),
        ("description", "str (string)", "Mô tả ngắn gọn về thành phần món", '"Pha phin truyền thống..."')
    ]
    for r_idx, r_data in enumerate(menu_rows):
        rc = t_menu.add_row().cells
        bg = "F7FAFC" if r_idx % 2 == 0 else "FFFFFF"
        for c_idx, val in enumerate(r_data):
            rc[c_idx].text = val
            set_cell_background(rc[c_idx], bg)
            set_cell_margins(rc[c_idx], 60, 60, 100, 100)
            p = rc[c_idx].paragraphs[0]
            p.runs[0].font.name = "Arial"
            p.runs[0].font.size = Pt(8.5)

    # 4.2 tables.json
    add_heading_2("4.2. Bảng dữ liệu: data/tables.json (Danh sách bàn ăn)")
    t_tab = doc.add_table(rows=1, cols=4)
    t_tab.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, title in enumerate(m_headers):
        t_tab.rows[0].cells[i].text = title
        set_cell_background(t_tab.rows[0].cells[i], "2B6CB0")
        p = t_tab.rows[0].cells[i].paragraphs[0]
        p.runs[0].font.name = "Arial"
        p.runs[0].font.bold = True
        p.runs[0].font.size = Pt(9)
        p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
        set_cell_margins(t_tab.rows[0].cells[i], 80, 80, 100, 100)

    tables_rows = [
        ("id", "int (integer)", "Số thứ tự / Mã số bàn (khóa chính)", "1, 2, 3"),
        ("name", "str (string)", "Tên hiển thị bàn", '"Bàn 01", "Bàn VIP 01"'),
        ("capacity", "int (integer)", "Sức chứa tối đa (số người ngồi)", "2, 4, 6, 10"),
        ("status", "str (Enum)", "Trạng thái: AVAILABLE, OCCUPIED, RESERVED", '"AVAILABLE"'),
        ("current_order_id", "str / null", "Mã đơn hàng đang phục vụ (nếu có)", '"ORD-20261014-001" / null')
    ]
    for r_idx, r_data in enumerate(tables_rows):
        rc = t_tab.add_row().cells
        bg = "F7FAFC" if r_idx % 2 == 0 else "FFFFFF"
        for c_idx, val in enumerate(r_data):
            rc[c_idx].text = val
            set_cell_background(rc[c_idx], bg)
            set_cell_margins(rc[c_idx], 60, 60, 100, 100)
            p = rc[c_idx].paragraphs[0]
            p.runs[0].font.name = "Arial"
            p.runs[0].font.size = Pt(8.5)

    p_tbl_status = doc.add_paragraph()
    p_tbl_status.paragraph_format.space_before = Pt(4)
    p_tbl_status.paragraph_format.space_after = Pt(4)
    p_tbl_status.add_run(
        "• AVAILABLE (Xanh 🟢): Bàn trống, sẵn sàng nhận khách.\n"
        "• OCCUPIED (Đỏ 🔴): Bàn đang có khách ngồi, gắn với current_order_id.\n"
        "• RESERVED (Vàng 🟡): Bàn khách đã đặt lịch hẹn trước."
    ).font.size = Pt(8.5)

    # 4.3 orders.json
    add_heading_2("4.3. Bảng dữ liệu: data/orders.json (Danh sách đơn hàng)")
    t_ord = doc.add_table(rows=1, cols=4)
    t_ord.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, title in enumerate(m_headers):
        t_ord.rows[0].cells[i].text = title
        set_cell_background(t_ord.rows[0].cells[i], "2B6CB0")
        p = t_ord.rows[0].cells[i].paragraphs[0]
        p.runs[0].font.name = "Arial"
        p.runs[0].font.bold = True
        p.runs[0].font.size = Pt(9)
        p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
        set_cell_margins(t_ord.rows[0].cells[i], 80, 80, 100, 100)

    orders_rows = [
        ("id", "str (string)", "Mã đơn hàng chuẩn: ORD-YYYYMMDD-XXX", '"ORD-20261014-001"'),
        ("table_id", "int (integer)", "Mã bàn phục vụ đơn này", "2"),
        ("created_at", "str (ISO 8601)", "Thời điểm tạo đơn", '"2026-10-14T20:15:00"'),
        ("updated_at", "str (ISO 8601)", "Thời điểm cập nhật trạng thái gần nhất", '"2026-10-14T20:30:00"'),
        ("status", "str (Enum)", "PENDING, PREPARING, SERVED, COMPLETED, CANCELLED", '"SERVED"'),
        ("items", "list[dict]", "Danh sách chi tiết món (menu_item_id, quantity...)", "[{...}, {...}]"),
        ("total_amount", "int (integer)", "Tổng tiền gốc trước giảm giá (tổng subtotal)", "113000"),
        ("discount_amount", "int (integer)", "Tiền giảm giá / chiết khấu voucher (mặc định 0)", "0"),
        ("final_amount", "int (integer)", "Tiền thực thanh toán = total - discount", "113000"),
        ("notes", "str (string)", "Ghi chú chung cho toàn bộ đơn hàng", '"Khách ngồi gần cửa sổ"')
    ]
    for r_idx, r_data in enumerate(orders_rows):
        rc = t_ord.add_row().cells
        bg = "F7FAFC" if r_idx % 2 == 0 else "FFFFFF"
        for c_idx, val in enumerate(r_data):
            rc[c_idx].text = val
            set_cell_background(rc[c_idx], bg)
            set_cell_margins(rc[c_idx], 60, 60, 100, 100)
            p = rc[c_idx].paragraphs[0]
            p.runs[0].font.name = "Arial"
            p.runs[0].font.size = Pt(8.5)

    p_item_spec = doc.add_paragraph()
    p_item_spec.paragraph_format.space_before = Pt(4)
    p_item_spec.paragraph_format.space_after = Pt(4)
    p_item_spec.add_run(
        "Chi tiết cấu trúc từng món con trong mảng items[]:\n"
        "• menu_item_id (str): Tham chiếu id trong menu.json (vd: 'M02')\n"
        "• item_name (str): Snapshot tên món tại thời điểm gọi\n"
        "• unit_price (int): Snapshot đơn vị giá\n"
        "• quantity (int): Số lượng đặt (> 0)\n"
        "• subtotal (int): Thành tiền = unit_price * quantity\n"
        "• note (str): Ghi chú món (vd: 'Ít đường, không đá')"
    ).font.size = Pt(8.5)

    # 4.4 payments.json
    add_heading_2("4.4. Bảng dữ liệu: data/payments.json (Lịch sử thanh toán)")
    t_pay = doc.add_table(rows=1, cols=4)
    t_pay.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, title in enumerate(m_headers):
        t_pay.rows[0].cells[i].text = title
        set_cell_background(t_pay.rows[0].cells[i], "2B6CB0")
        p = t_pay.rows[0].cells[i].paragraphs[0]
        p.runs[0].font.name = "Arial"
        p.runs[0].font.bold = True
        p.runs[0].font.size = Pt(9)
        p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
        set_cell_margins(t_pay.rows[0].cells[i], 80, 80, 100, 100)

    pay_rows = [
        ("id", "str (string)", "Mã thanh toán: PAY-YYYYMMDD-XXX", '"PAY-20261014-001"'),
        ("order_id", "str (string)", "Mã đơn hàng được thanh toán", '"ORD-20261014-003"'),
        ("table_id", "int (integer)", "Bàn được thanh toán", "1"),
        ("payment_time", "str (ISO 8601)", "Thời điểm khách thanh toán", '"2026-10-14T19:20:00"'),
        ("amount_paid", "int (integer)", "Số tiền thực trả (bằng final_amount)", "25000"),
        ("method", "str (Enum)", "Phương thức: CASH, BANK_TRANSFER, CARD", '"CASH"'),
        ("status", "str (Enum)", "Kết quả: SUCCESS, FAILED, REFUNDED", '"SUCCESS"'),
        ("cashier_name", "str (string)", "Tên nhân viên thực hiện thu tiền", '"Vy"'),
        ("transaction_code", "str / null", "Mã giao dịch ngân hàng / POS (nếu có)", '"MB-FT26101399812" / null'),
        ("note", "str (string)", "Ghi chú giao dịch", '"Tiền mặt khách đưa 50k, thối 25k"')
    ]
    for r_idx, r_data in enumerate(pay_rows):
        rc = t_pay.add_row().cells
        bg = "F7FAFC" if r_idx % 2 == 0 else "FFFFFF"
        for c_idx, val in enumerate(r_data):
            rc[c_idx].text = val
            set_cell_background(rc[c_idx], bg)
            set_cell_margins(rc[c_idx], 60, 60, 100, 100)
            p = rc[c_idx].paragraphs[0]
            p.runs[0].font.name = "Arial"
            p.runs[0].font.size = Pt(8.5)

    # ==========================
    # 5. KẾ HOẠCH NỘP BÀI 50%
    # ==========================
    add_heading_1("5. CHECKLIST CẦN HOÀN THÀNH CHO MỐC 50% (HẠN CHÓT: 17/10/2026)")
    
    p_chk = doc.add_paragraph()
    p_chk.paragraph_format.space_after = Pt(4)
    p_chk.add_run(
        "☑ Mục 5 (Vy - Đã xong 100%): Khởi tạo GitHub repo, cấu hình uv, .gitignore, cấu trúc thư mục, chốt JSON Schema.\n"
        "☐ Mục 1 (Quỳnh): Hoàn thiện các Data Class trong src/models/ và hàm đọc/ghi 4 file JSON.\n"
        "☐ Mục 2 (Anh): Viết class TableManager (đổi trạng thái bàn) và OrderManager (tính tiền, thêm món) trong src/core/.\n"
        "☐ Mục 3 (Thắng): Hoàn thiện giao diện Streamlit: chọn bàn -> xem menu -> bấm gọi món -> xem tổng hóa đơn.\n"
        "☐ Tích hợp & Kiểm thử: Mọi thành viên tạo PR -> Vy review và merge -> chạy 'uv run pytest' kiểm tra toàn hệ thống."
    ).font.size = Pt(9.5)

    p_sign = doc.add_paragraph()
    p_sign.paragraph_format.space_before = Pt(16)
    p_sign.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_sign = p_sign.add_run(
        "TP. Hồ Chí Minh, ngày 14 tháng 10 năm 2026\n"
        "TRƯỞNG NHÓM ĐỒ ÁN\n\n\n"
        "Nguyễn Lê Vy"
    )
    r_sign.font.name = "Arial"
    r_sign.font.size = Pt(10)
    r_sign.font.bold = True
    r_sign.font.color.rgb = COLOR_PRIMARY

    doc.save(output_path)
    print("Handover document generated successfully!")

if __name__ == "__main__":
    out_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Tai_Lieu_Ban_Giao_Do_An_FnB.docx")
    create_handover_document(out_file)

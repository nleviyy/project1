# -*- coding: utf-8 -*-
"""
Script tạo file báo cáo Word (.docx) chuyên nghiệp:
BÁO CÁO TIẾN ĐỘ DỰ ÁN & KẾ HOẠCH ĐIỀU CHỈNH THEO FEEDBACK MENTOR
Dành cho: Nguyễn Lê Vy (Team Leader)
"""
import os
import sys
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>'))

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def create_report():
    doc = Document()

    # Cấu hình lề trang A4
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.9)
        section.right_margin = Inches(0.9)

    # Palette màu
    COLOR_PRIMARY = RGBColor(24, 76, 120)     # Navy Blue
    COLOR_SECONDARY = RGBColor(41, 128, 185) # Slate Blue
    COLOR_TEXT = RGBColor(44, 62, 80)         # Dark Gray
    COLOR_MUTED = RGBColor(127, 140, 141)     # Muted Gray

    # Style mặc định
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(11.5)
    normal_style.font.color.rgb = COLOR_TEXT
    normal_style.paragraph_format.line_spacing = 1.2
    normal_style.paragraph_format.space_after = Pt(4)

    # -------------------------------------------------------------
    # HEADER / TIÊU ĐỀ BÁO CÁO
    # -------------------------------------------------------------
    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_inst = p_inst.add_run("TRƯỜNG ĐẠI HỌC / ĐỒ ÁN THỰC HÀNH PYTHON - MODULE 1\nBỘ MÔN CÔNG NGHỆ THÔNG TIN")
    r_inst.font.size = Pt(10)
    r_inst.font.bold = True
    r_inst.font.color.rgb = COLOR_MUTED

    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.paragraph_format.space_before = Pt(10)
    title_p.paragraph_format.space_after = Pt(4)
    run_title = title_p.add_run("BÁO CÁO TIẾN ĐỘ DỰ ÁN & KẾ HOẠCH ĐIỀU CHỈNH\nTHEO FEEDBACK CHỈ ĐẠO CỦA MENTOR")
    run_title.font.size = Pt(17)
    run_title.font.bold = True
    run_title.font.color.rgb = COLOR_PRIMARY

    sub_p = doc.add_paragraph()
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_p.paragraph_format.space_after = Pt(16)
    sub_r = sub_p.add_run("Đề tài: Hệ Thống Quản Lý Đơn Hàng & Bàn Ăn F&B Bằng Python")
    sub_r.font.size = Pt(12.5)
    sub_r.font.italic = True
    sub_r.font.color.rgb = COLOR_SECONDARY

    # Bảng thông tin sinh viên & dự án
    table_meta = doc.add_table(rows=5, cols=2)
    table_meta.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_data = [
        ("Sinh viên báo cáo:", "Nguyễn Lê Vy"),
        ("Vai trò dự án:", "Team Leader / Core Backend Developer"),
        ("Mã nguồn dự án (GitHub):", "https://github.com/nleviyy/project1"),
        ("Nhánh cơ sở nền tảng:", "origin/Vy & nhánh tích hợp tong-hop"),
        ("Thời điểm báo cáo:", "Đánh giá tiến độ mốc 50% - Kế hoạch nghiệm thu mốc 100%"),
    ]
    for row_idx, (k, v) in enumerate(meta_data):
        row = table_meta.rows[row_idx]
        c1, c2 = row.cells[0], row.cells[1]
        c1.text = k
        c2.text = v
        c1.paragraphs[0].runs[0].font.bold = True
        c1.paragraphs[0].runs[0].font.color.rgb = COLOR_PRIMARY
        c1.width = Inches(2.2)
        c2.width = Inches(4.5)
        set_cell_background(c1, "F4F6F7")
        set_cell_background(c2, "FAFAFA")
        set_cell_margins(c1, 60, 60, 100, 100)
        set_cell_margins(c2, 60, 60, 100, 100)

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # -------------------------------------------------------------
    # 1. TIẾP THU ĐÁNH GIÁ TỔNG QUAN TỪ MENTOR
    # -------------------------------------------------------------
    h1 = doc.add_heading("1. ĐÁNH GIÁ TỔNG QUAN & TIẾP THU FEEDBACK CỦA MENTOR", level=1)
    h1.paragraph_format.space_before = Pt(14)
    h1.runs[0].font.color.rgb = COLOR_PRIMARY

    p1 = doc.add_paragraph()
    p1.add_run(
        "Nhóm phát triển và cá nhân em (Nguyễn Lê Vy) đã tiếp nhận, nghiên cứu kỹ lưỡng văn bản đánh giá chi tiết của Mentor. "
        "Em hoàn toàn đồng thuận với nhận định cốt lõi của Mentor: "
    )
    r_core_fb = p1.add_run(
        "Vấn đề lớn nhất hiện tại của dự án là các module vẫn đang hoạt động độc lập, rời rạc theo nhánh cá nhân mà chưa được tích hợp "
        "thành một hệ thống thông suốt; xuất hiện mâu thuẫn về trạng thái đơn hàng giữa các bên và giao diện vẫn còn phụ thuộc vào dữ liệu mô phỏng (hard-code). "
    )
    r_core_fb.font.bold = True

    p2 = doc.add_paragraph()
    p2.add_run(
        "Với vai trò Trưởng nhóm (Team Leader), em xác định mục tiêu tối thượng trong giai đoạn tới là: "
        "Ưu tiên hoàn thiện luồng nghiệp vụ khép kín (End-to-End Business Flow), chuẩn hóa cấu trúc dữ liệu chung theo đúng các quyết định Mentor đã chốt, "
        "thay vì tiếp tục đầu tư dàn trải vào giao diện đồ họa hoặc thêm thắt các tính năng phụ rẽ nhánh."
    )

    # -------------------------------------------------------------
    # 2. CÁC QUYẾT ĐỊNH KIẾN TRÚC & DỮ LIỆU ĐÃ THỐNG NHẤT
    # -------------------------------------------------------------
    h2 = doc.add_heading("2. CÁC QUYẾT ĐỊNH KIẾN TRÚC & DỮ LIỆU ĐÃ THỐNG NHẤT", level=1)
    h2.paragraph_format.space_before = Pt(14)
    h2.runs[0].font.color.rgb = COLOR_PRIMARY

    doc.add_paragraph(
        "Theo chỉ đạo của Mentor, toàn bộ hệ thống được thống nhất phân bổ trách nhiệm vào 3 tầng chính: "
        "src/models/ (dữ liệu & hành vi đối tượng), src/core/ (nghiệp vụ & điều phối), src/ui/ (hiển thị & bắt sự kiện). "
        "Quy tắc bắt buộc: UI không tự viết lại logic nghiệp vụ, Core không phụ thuộc vào thư viện Streamlit."
    )

    # Bảng phân công trách nhiệm các Class dùng chung
    doc.add_heading("2.1. Thống nhất các Class và Trách nhiệm cốt lõi", level=2)
    tbl_classes = doc.add_table(rows=10, cols=3)
    tbl_classes.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Class", "Trách nhiệm chính", "Quyết định thống nhất theo Mentor"]
    hdr_row = tbl_classes.rows[0]
    for i, h_text in enumerate(headers):
        hdr_row.cells[i].text = h_text
        hdr_row.cells[i].paragraphs[0].runs[0].font.bold = True
        hdr_row.cells[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        set_cell_background(hdr_row.cells[i], "1F4E79")
        set_cell_margins(hdr_row.cells[i], 80, 80, 120, 120)

    class_specs = [
        ("MenuItem", "Thông tin 1 món ăn", "Đọc từ data/menu.json, bắt buộc check is_available"),
        ("MenuCatalog", "Quản lý, tìm kiếm món", "Dùng dict (Hash Map) tra cứu mã món O(1)"),
        ("Cart", "Giỏ hàng tạm, Undo/Redo", "Dùng 2 Stack trên data_structure, bỏ class GioHang riêng của UI"),
        ("OrderItem", "Dòng món trong hóa đơn", "Giữ Snapshot đơn giá tại thời điểm đặt để menu đổi giá không sai đơn"),
        ("Order", "Thông tin, tiền & trạng thái", "Lấy bản Order.py trên nhánh Vy làm chuẩn duy nhất; bỏ Order ở kitchen.py"),
        ("OrderService", "Điều phối vòng đời đơn", "Sinh mã ORD- chuẩn, xác nhận, kiểm tra chống thanh toán trùng"),
        ("KitchenManager", "Hàng đợi bếp (Queue FIFO)", "Dùng list thuần Python theo nguyên lý FIFO (append/pop(0)), chỉ quản lý chế biến, dùng Order chuẩn"),
        ("Table / TableManager", "Quản lý tình trạng bàn", "Liên kết bàn với current_order_id, chiếm bàn & giải phóng bàn"),
        ("Payment & Invoice", "Thanh toán & Hóa đơn", "Xác nhận giao dịch, ghi nhật ký payments.json, in hóa đơn"),
    ]

    for idx, (c_name, c_resp, c_dec) in enumerate(class_specs):
        row = tbl_classes.rows[idx + 1]
        row.cells[0].text = c_name
        row.cells[1].text = c_resp
        row.cells[2].text = c_dec
        row.cells[0].paragraphs[0].runs[0].font.bold = True
        set_cell_background(row.cells[0], "F2F4F4" if idx % 2 == 0 else "FFFFFF")
        set_cell_background(row.cells[1], "F8F9F9" if idx % 2 == 0 else "FFFFFF")
        set_cell_background(row.cells[2], "F2F4F4" if idx % 2 == 0 else "FFFFFF")
        for cell in row.cells:
            set_cell_margins(cell, 60, 60, 100, 100)

    # Thống nhất luồng trạng thái
    doc.add_heading("2.2. Thống nhất Hệ thống Trạng thái & Luồng Nghiệp vụ Chuẩn", level=2)
    doc.add_paragraph(
        "Hệ thống vận hành theo một luồng Finite State Machine duy nhất và nghiêm ngặt:\n"
        "Cart ➔ Order (PENDING) ➔ Kitchen Queue ➔ PREPARING ➔ SERVED ➔ Payment ➔ COMPLETED"
    )

    p_flow_rules = doc.add_paragraph()
    p_flow_rules.add_run("Quy tắc ràng buộc bắt buộc (Khắc phục mâu thuẫn hiện tại):\n").font.bold = True
    rules = [
        "Sửa mâu thuẫn xác nhận: Khi khách xác nhận giỏ hàng, OrderService tạo Order ở trạng thái PENDING rồi đưa vào cuối Queue bếp (thay vì tự ý nhảy sang PREPARING như trước).",
        "Bếp xử lý tuần tự (FIFO): Khi bếp lấy đơn từ đầu Queue qua start_next_order(), trạng thái đơn mới chính thức đổi sang PREPARING.",
        "Lên món: Khi bếp chế biến xong toàn bộ các món trong đơn, trạng thái chuyển sang SERVED và rời khỏi bếp.",
        "Thanh toán: Chỉ chuyển sang COMPLETED khi giao dịch thanh toán thành công và được ghi nhận.",
        "Quy tắc hủy đơn: Chỉ cho phép hủy khi đơn ở trạng thái PENDING hoặc PREPARING. Nếu đơn đang trong bếp, phải hủy đồng thời ở cả Order và loại bỏ khỏi hàng đợi KitchenManager.",
        "Khóa chỉnh sửa: Tuyệt đối không cho phép sửa món khi đơn đã rời khỏi PENDING để tránh làm xáo trộn công việc của bếp.",
    ]
    for r in rules:
        doc.add_paragraph(f"• {r}")

    # -------------------------------------------------------------
    # 3. BÁO CÁO CÔNG VIỆC THỰC TẾ VY ĐÃ HOÀN THÀNH
    # -------------------------------------------------------------
    h3 = doc.add_heading("3. BÁO CÁO KỸ THUẬT CÁC PHẦN VY TRỰC TIẾP HOÀN THÀNH", level=1)
    h3.paragraph_format.space_before = Pt(14)
    h3.runs[0].font.color.rgb = COLOR_PRIMARY

    doc.add_paragraph(
        "Đối chiếu với chỉ đạo của Mentor: Phiên bản Order và OrderItem do Vy xây dựng trên nhánh 'Vy' "
        "đã được Mentor chính thức phê duyệt làm cơ sở chuẩn mực cho toàn bộ dự án. "
        "Dưới đây là chi tiết các thành phần em đã hoàn thành:"
    )

    # 3.1 OrderItem
    doc.add_heading("3.1. Class OrderItem (src/models/OrderItem.py)", level=2)
    doc.add_paragraph(
        "• Mục đích: Đại diện cho từng dòng món ăn trong hóa đơn. Áp dụng Snapshot Pattern giữ nguyên giá tại thời điểm đặt.\n"
        "• Công nghệ: Kế thừa Pydantic BaseModel, sử dụng @model_validator(mode='before') tự động tính subtotal = unit_price * quantity.\n"
        "• Phương thức: update_quantity(new_qty), update_note(note), to_dict(), from_dict(), from_menu_item().\n"
        "• Xử lý biên: Chặn số lượng <= 0, xử lý an toàn giá trị chuỗi rỗng/None cho ghi chú."
    )

    # 3.2 Order
    doc.add_heading("3.2. Class Order & OrderStatus (src/models/Order.py)", level=2)
    doc.add_paragraph(
        "• Mục đích: Quản lý toàn bộ thông tin đơn hàng, tổng tiền và luồng trạng thái FSM.\n"
        "• Máy trạng thái (FSM): Bảng VALID_STATUS_TRANSITIONS ràng buộc: PENDING -> {PREPARING, CANCELLED}; "
        "PREPARING -> {SERVED, CANCELLED}; SERVED -> {COMPLETED, CANCELLED}. Không cho phép đổi trạng thái của đơn COMPLETED hoặc CANCELLED.\n"
        "• Thao tác món thông minh (add_item): Tự động gộp số lượng (merge_same_item) nếu trùng mã món VÀ trùng ghi chú; ném ngoại lệ nếu đơn đã đóng.\n"
        "• Tính toán tiền: calculate_total() tính tổng tiền món và số tiền thực trả sau khi trừ discount_amount, đảm bảo final_amount >= 0."
    )

    # 3.3 OrderService
    doc.add_heading("3.3. Class OrderService (src/core/OrderService.py)", level=2)
    doc.add_paragraph(
        "• Sinh mã đơn tự động: generate_order_id() tự động quét mã đơn trong ngày và sinh mã dạng ORD-YYYYMMDD-XXX liên tục không trùng lặp.\n"
        "• Chống thanh toán trùng lặp (Anti-Double Payment): is_order_paid() và can_checkout() kiểm tra 2 lớp bảo vệ "
        "(trạng thái đơn trong RAM và bản ghi thanh toán SUCCESS trong data/payments.json), chặn đứng nguy cơ thu tiền 2 lần.\n"
        "• Tìm kiếm: Tra cứu đơn theo mã ID đạt O(1) qua từ điển, tìm đơn đang hoạt động của bàn theo table_id."
    )

    # -------------------------------------------------------------
    # 4. KẾT QUẢ KIỂM THỬ THỰC TẾ
    # -------------------------------------------------------------
    h4 = doc.add_heading("4. KẾT QUẢ KIỂM THỬ & CHẤT LƯỢNG MÃ NGUỒN", level=1)
    h4.paragraph_format.space_before = Pt(14)
    h4.runs[0].font.color.rgb = COLOR_PRIMARY

    doc.add_paragraph(
        "Toàn bộ mã nguồn do Vy xây dựng và phần tích hợp của nhóm đều đã được kiểm thử tự động bằng pytest. "
        "Kết quả thực thi thực tế trên môi trường máy tính Windows (PowerShell):"
    )

    tbl_test = doc.add_table(rows=4, cols=4)
    tbl_test.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_headers = ["Bộ kiểm thử", "Tệp mã nguồn kiểm thử", "Số test case", "Kết quả thực tế"]
    t_hdr_row = tbl_test.rows[0]
    for i, h_text in enumerate(t_headers):
        t_hdr_row.cells[i].text = h_text
        t_hdr_row.cells[i].paragraphs[0].runs[0].font.bold = True
        t_hdr_row.cells[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        set_cell_background(t_hdr_row.cells[i], "2E4053")
        set_cell_margins(t_hdr_row.cells[i], 60, 60, 100, 100)

    test_data = [
        ("Nghiệp vụ Đơn hàng (Vy)", "tests/test_order_logic.py", "14 tests", "14/14 PASSED (100%)"),
        ("Kiểm thử hợp đồng JSON (Vy)", "tests/test_smoke.py", "5 tests", "5/5 PASSED (100%)"),
        ("Cấu trúc dữ liệu Bếp/Giỏ hàng (Lan Anh)", "tests/test_data_structure.py", "32 tests", "32/32 PASSED (100%)"),
    ]
    for idx, (t_name, t_file, t_count, t_res) in enumerate(test_data):
        row = tbl_test.rows[idx + 1]
        row.cells[0].text = t_name
        row.cells[1].text = t_file
        row.cells[2].text = t_count
        row.cells[3].text = t_res
        row.cells[3].paragraphs[0].runs[0].font.bold = True
        set_cell_background(row.cells[0], "F8F9F9")
        set_cell_background(row.cells[1], "FFFFFF")
        set_cell_background(row.cells[2], "F8F9F9")
        set_cell_background(row.cells[3], "E8F8F5")
        for cell in row.cells:
            set_cell_margins(cell, 60, 60, 100, 100)

    p_test_sum = doc.add_paragraph()
    p_test_sum.paragraph_format.space_before = Pt(6)
    p_test_sum.add_run("👉 Tổng kết toàn dự án trên nhánh tích hợp: ").font.bold = True
    r_sum_pass = p_test_sum.add_run("51/51 bài kiểm thử tự động đạt PASSED (100%) trong 0.25 giây.")
    r_sum_pass.font.bold = True
    r_sum_pass.font.color.rgb = RGBColor(22, 163, 74)

    # -------------------------------------------------------------
    # 5. KẾ HOẠCH HÀNH ĐỘNG THEO MA TRẬN ƯU TIÊN CỦA MENTOR (P0 - P1 - P2)
    # -------------------------------------------------------------
    h5 = doc.add_heading("5. KẾ HOẠCH HÀNH ĐỘNG THEO MA TRẬN ƯU TIÊN (P0 ➔ P1 ➔ P2)", level=1)
    h5.paragraph_format.space_before = Pt(14)
    h5.runs[0].font.color.rgb = COLOR_PRIMARY

    doc.add_paragraph(
        "Nhóm cam kết tuân thủ nghiêm ngặt lộ trình nghiệm thu mà Mentor đã đề ra trong tài liệu feedback:"
    )

    tbl_roadmap = doc.add_table(rows=7, cols=4)
    tbl_roadmap.alignment = WD_TABLE_ALIGNMENT.CENTER
    r_headers = ["Ưu tiên", "Nhiệm vụ cụ thể", "Thành viên phụ trách", "Kết quả cần đạt & Tiêu chí nghiệm thu"]
    r_hdr_row = tbl_roadmap.rows[0]
    for i, h_text in enumerate(r_headers):
        r_hdr_row.cells[i].text = h_text
        r_hdr_row.cells[i].paragraphs[0].runs[0].font.bold = True
        r_hdr_row.cells[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        set_cell_background(r_hdr_row.cells[i], "1B4F72")
        set_cell_margins(r_hdr_row.cells[i], 60, 60, 100, 100)

    roadmap_data = [
        ("P0", "Xóa Order trùng trong kitchen.py, chuẩn hóa import từ src.models.Order", "Vy & Lan Anh", "Không còn 2 định nghĩa Order/OrderStatus mâu thuẫn"),
        ("P0", "Sửa confirm_order() giữ PENDING, chuyển nối vào Queue bếp", "Vy & Lan Anh", "Đơn tạo PENDING vào cuối Queue, bếp start mới PREPARING"),
        ("P0", "Loại bỏ menu hard-code và GioHang riêng trên UI, dùng MenuCatalog & Cart", "Thắng & Vy", "UI load 100% từ data/menu.json, hỗ trợ Undo/Redo"),
        ("P1", "Hoàn thiện TableManager & liên kết trạng thái bàn với đơn", "Quỳnh & Vy", "Chiếm bàn khi tạo đơn, giải phóng bàn khi COMPLETED/CANCELLED"),
        ("P1", "Tính thời gian chờ tích lũy trong Queue (bỏ random.randint)", "Lan Anh", "Cộng dồn thời gian chế biến của các đơn phía trước"),
        ("P1 & P2", "Hoàn thiện module Payment, Invoice & Kịch bản Demo 7 bước", "Cả nhóm", "Chạy thông suốt từ Gọi món ➔ Bếp ➔ Thanh toán ➔ Giải phóng bàn"),
    ]
    for idx, (prio, task, assignee, target) in enumerate(roadmap_data):
        row = tbl_roadmap.rows[idx + 1]
        row.cells[0].text = prio
        row.cells[1].text = task
        row.cells[2].text = assignee
        row.cells[3].text = target
        row.cells[0].paragraphs[0].runs[0].font.bold = True
        if prio == "P0":
            set_cell_background(row.cells[0], "FDEDEC")
            row.cells[0].paragraphs[0].runs[0].font.color.rgb = RGBColor(192, 57, 43)
        else:
            set_cell_background(row.cells[0], "EBF5FB")
            row.cells[0].paragraphs[0].runs[0].font.color.rgb = RGBColor(41, 128, 185)
        set_cell_background(row.cells[1], "FFFFFF")
        set_cell_background(row.cells[2], "F8F9F9")
        set_cell_background(row.cells[3], "FFFFFF")
        for cell in row.cells:
            set_cell_margins(cell, 60, 60, 100, 100)

    # -------------------------------------------------------------
    # 6. KỊCH BẢN TRÌNH BÀY TRỰC TIẾP VỚI MENTOR (3 - 5 PHÚT)
    # -------------------------------------------------------------
    h6 = doc.add_heading("6. KỊCH BẢN NÓI TRỰC TIẾP VỚI MENTOR (3 – 5 PHÚT)", level=1)
    h6.paragraph_format.space_before = Pt(14)
    h6.runs[0].font.color.rgb = COLOR_PRIMARY

    doc.add_paragraph(
        "Kịch bản trình bày mẫu dành riêng cho Vy (giọng văn tự nhiên, khiêm tốn, nắm chắc kỹ thuật và thể hiện rõ tinh thần cầu thị):"
    )

    script_box = doc.add_table(rows=1, cols=1)
    script_box.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_box = script_box.rows[0].cells[0]
    set_cell_background(c_box, "F4F6F7")
    set_cell_margins(c_box, 140, 140, 180, 180)

    script_text = (
        "\"Em chào Thầy/Mentor ạ! Sau khi nhận được bản nhận xét rất tâm huyết và chi tiết của Thầy, "
        "nhóm chúng em và cá nhân em với tư cách là Team Leader đã họp ngay để nhìn nhận thẳng thắn các vấn đề còn tồn tại.\n\n"
        "Tụi em nhận thấy điểm yếu lớn nhất của nhóm đúng như Thầy chỉ ra: từng cá nhân làm bài của mình khá ổn, "
        "nhưng khi ghép lại thì các module chưa kết nối thành một thể thống nhất, vẫn còn tình trạng mâu thuẫn trạng thái "
        "và giao diện còn dùng dữ liệu mô phỏng.\n\n"
        "Em xin báo cáo 3 việc nhóm đã thống nhất thực hiện ngay theo quyết định của Thầy:\n"
        "1. Về Model dữ liệu: Nhóm đã chốt sử dụng class Order và OrderItem của em làm chuẩn duy nhất cho toàn dự án. "
        "Em đã làm việc với bạn Lan Anh để loại bỏ class Order bị định nghĩa trùng trong file kitchen.py, "
        "đồng thời lấy class Cart có Undo/Redo của Lan Anh làm giỏ hàng chuẩn, yêu cầu bạn Thắng bỏ class GioHang riêng trên UI.\n\n"
        "2. Về Luồng trạng thái: Em đã rà soát lại mâu thuẫn giữa confirm_order() và KitchenManager. Nhóm đã thống nhất luồng: "
        "Khi khách xác nhận đơn, OrderService chỉ tạo đơn ở trạng thái PENDING và đẩy vào cuối Queue; "
        "chỉ khi Bếp bấm lấy đơn tiếp theo thì trạng thái mới chuyển sang PREPARING. Tuyệt đối không cho phép đổi tắt trạng thái.\n\n"
        "3. Về Dữ liệu & UI: Toàn bộ danh mục món trên UI sẽ load 100% từ file data/menu.json qua MenuCatalog thay vì hard-code; "
        "bỏ hoàn toàn việc random thời gian chờ và thay bằng công thức tính cộng dồn từ các đơn phía trước trong hàng đợi bếp.\n\n"
        "Hiện tại, toàn bộ các bài kiểm thử tự động của phần Đơn hàng (14 tests) và Schema (5 tests) đều đạt 100%. "
        "Khi tích hợp cả phần Bếp và Giỏ hàng thì toàn bộ 51/51 tests đều đã Passed. "
        "Trong tuần này, nhóm em sẽ tập trung toàn lực cho mục tiêu P0 và P1: hoàn thiện TableManager, kết nối thanh toán "
        "và chạy thông suốt kịch bản demo 7 bước mà Thầy đã yêu cầu. Nhóm em rất mong tiếp tục nhận được sự chỉ dẫn của Thầy ạ!\""
    )
    p_box = c_box.paragraphs[0]
    p_box.paragraph_format.line_spacing = 1.25
    r_box = p_box.add_run(script_text)
    r_box.font.italic = True
    r_box.font.size = Pt(11)

    # -------------------------------------------------------------
    # 7. PHẦN KÝ TÊN VÀ XÁC NHẬN
    # -------------------------------------------------------------
    doc.add_paragraph().paragraph_format.space_before = Pt(20)
    p_sign = doc.add_paragraph()
    p_sign.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_sign_date = p_sign.add_run("Hà Nội, ngày 18 tháng 10 năm 2026\n")
    r_sign_date.font.italic = True
    r_sign_role = p_sign.add_run("SINH VIÊN BÁO CÁO / TRƯỞNG NHÓM\n\n\n\n")
    r_sign_role.font.bold = True
    r_sign_name = p_sign.add_run("Nguyễn Lê Vy")
    r_sign_name.font.bold = True
    r_sign_name.font.size = Pt(13)

    # Lưu file Word
    output_filename = "Bao_Cao_Tien_Do_Do_An_Module1_NguyenLeVy.docx"
    doc.save(output_filename)
    print(f"SUCCESS: Created file {output_filename}")

if __name__ == "__main__":
    create_report()

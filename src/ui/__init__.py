import random
import time
import unicodedata
from html import escape

import streamlit as st
import streamlit.components.v1 as components

# Yêu cầu: Streamlit >= 1.39   (pip install -U streamlit)
# Chạy:    streamlit run app.py

# ==========================================
# 1. CÀI ĐẶT TRANG
# ==========================================

st.set_page_config(
    page_title="SUPPER MENU QUÁN",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================
# 2. CSS GIAO DIỆN (nền sáng, nhấn xanh lá, không phụ thuộc dark mode)
# ==========================================

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');
:root{--g:#16a34a;--gd:#15803d;--gl:#ecfdf3;--ink:#111827;--sub:#6b7280;--mut:#9ca3af;--line:#e5e7eb}

/* Nền và chữ */
.stApp,.stApp div,.stApp p,.stApp label,.stApp li,.stApp button,.stApp input{font-family:"Be Vietnam Pro",sans-serif!important}
.stApp{background:#f4f5f7;color:var(--ink);color-scheme:light}
header[data-testid="stHeader"]{background:transparent}
[data-testid="stToolbar"],[data-testid="stDecoration"],footer{display:none!important}
.block-container{padding:1.4rem 2.2rem 3rem;max-width:1600px}
.stButton,.stButton button{width:100%!important}
div[class*="st-key-"] button p{color:inherit!important}
[data-testid="stSpinner"],[data-testid="stSpinner"] *{color:var(--ink)!important}

/* Ô nhập, ô số lượng, ô chọn: ép nền trắng, chữ đậm */
.stApp [data-baseweb="input"],.stApp [data-baseweb="base-input"]{background-color:#fff!important;border-color:var(--line)!important;border-radius:14px!important}
.stApp [data-baseweb="input"]:focus-within{border-color:var(--g)!important;box-shadow:none!important}
.stApp input{background:transparent!important;color:var(--ink)!important;-webkit-text-fill-color:var(--ink)!important;caret-color:var(--g)}
.stApp input::placeholder{color:var(--mut)!important;-webkit-text-fill-color:var(--mut)!important;opacity:1}
.stApp [data-baseweb="select"] div{background-color:#fff!important;border-color:var(--line)!important;color:var(--ink)!important}
.stApp [data-baseweb="select"]>div{border-radius:14px!important}
.stApp [data-baseweb="select"]:focus-within>div{border-color:var(--g)!important}
.stApp [data-baseweb="select"] svg{fill:var(--sub)!important}
.stApp [data-testid="stNumberInput"] input{background:#fff!important;color:var(--ink)!important;-webkit-text-fill-color:var(--ink)!important;text-align:center;font-weight:700}
.stApp [data-testid="stNumberInput"] button{background:#f3f4f6!important;color:#374151!important;border:none!important;opacity:1!important}
.stApp [data-testid="stNumberInput"] button:disabled{background:#f3f4f6!important;color:var(--mut)!important;opacity:1!important}
.stApp [data-testid="stNumberInput"] button:hover:not(:disabled){background:var(--line)!important;color:var(--ink)!important}
.st-key-tim [data-baseweb="input"]{border:none!important;box-shadow:0 2px 12px rgba(17,24,39,.07)!important}
div[data-baseweb="popover"],div[data-baseweb="popover"]>div,div[data-baseweb="popover"] ul,div[data-baseweb="popover"] li{background:#fff!important;color:var(--ink)!important}
div[data-baseweb="popover"] li *{color:var(--ink)!important}
div[data-baseweb="popover"] li:hover,div[data-baseweb="popover"] li[aria-selected="true"]{background:var(--gl)!important}

/* Thanh điều hướng bên trái */
section[data-testid="stSidebar"]{width:104px!important;min-width:104px!important;background:#fff!important;border-right:1px solid #eceef1}
[data-testid="stSidebarHeader"]{display:none}
[data-testid="stSidebarUserContent"]{padding:1.2rem .6rem}
.logo{width:56px;height:56px;margin:0 auto 22px;border-radius:14px;background:linear-gradient(135deg,#ffb347,#ff4d2e);color:#fff;font-weight:800;font-size:20px;display:flex;align-items:center;justify-content:center;box-shadow:0 8px 18px rgba(255,90,40,.3)}
[class*="st-key-nav_"] button{min-height:56px!important;height:auto!important;padding:8px 4px!important;border:none!important;border-radius:14px!important;background:transparent!important;color:var(--sub)!important;box-shadow:none!important}
[class*="st-key-nav_"] button p{font-size:12px!important;font-weight:600!important;line-height:1.35!important}
[class*="st-key-nav_"] button:hover{background:#f3f4f6!important}
[class*="st-key-nav_on_"] button,[class*="st-key-nav_on_"] button:hover{background:var(--g)!important;color:#fff!important;box-shadow:0 8px 18px rgba(22,163,74,.3)!important}

/* Tiêu đề trang và tiêu đề từng phần */
.hello{font-size:13px;color:var(--mut)}
.htitle{font-size:28px;font-weight:700;line-height:1.25}
.stt{display:flex;justify-content:space-between;align-items:center;margin:22px 0 10px}
.stt.first{margin-top:0}
.stt b{font-size:19px}
.stt span{font-size:13px;color:var(--mut)}
.stt .badge{background:var(--gl);color:var(--g);border-radius:20px;padding:2px 12px;font-weight:600}
.sub{margin:18px 0 4px;font-size:13px;font-weight:600;color:var(--sub)}
.pillw{display:flex;justify-content:flex-end}
.pill{display:flex;align-items:center;gap:14px;padding:10px 18px;border-radius:14px;background:#fff;box-shadow:0 2px 12px rgba(17,24,39,.07);font-size:14px}
.pill small{color:var(--mut);font-size:12px}
.pill b:last-child{color:var(--g)}
.empty{margin-top:14px;padding:34px 16px;border:1.5px dashed var(--line);border-radius:16px;text-align:center;color:var(--mut);font-size:13px;line-height:1.6}
.empty b{display:block;margin-bottom:4px;font-size:16px;color:var(--sub)}
.ok{margin-bottom:16px;padding:16px 20px;border:1px solid #bbf7d0;border-radius:16px;background:var(--gl);color:#14532d;line-height:1.6}
.ok b{display:block;font-size:17px}

/* Danh mục */
[class*="st-key-dm_"] button{height:50px!important;border-radius:14px!important;border:2px solid transparent!important;background:#fff!important;color:#4b5563!important;box-shadow:0 2px 10px rgba(17,24,39,.05)!important}
[class*="st-key-dm_"] button p{font-size:14px!important;font-weight:600!important}
[class*="st-key-dm_"] button:hover{border-color:#bbf7d0!important;color:var(--g)!important}
[class*="st-key-dm_on_"] button,[class*="st-key-dm_on_"] button:hover{border-color:var(--g)!important;background:var(--gl)!important;color:var(--g)!important}

/* Thẻ món */
div[class*="st-key-card_"]{display:grid!important;grid-template-columns:minmax(0,1fr) minmax(0,1.4fr);gap:12px 10px!important;align-items:center;padding:16px;border-radius:20px;background:#fff;box-shadow:0 2px 14px rgba(17,24,39,.06)}
div[class*="st-key-card_"]>div{width:100%!important;min-width:0}
div[class*="st-key-card_"]>div:first-child{grid-column:1/-1}
.pcard{display:flex;gap:16px;align-items:center}
.pimg{position:relative;flex:0 0 118px;height:118px;border-radius:16px;overflow:hidden;background:linear-gradient(135deg,#fde68a,#fdba74);display:flex;align-items:center;justify-content:center;font-size:46px;font-weight:700;color:#c2410c}
.pimg i{position:absolute;inset:0;background-size:cover;background-position:center}
.pbody{min-width:0}
.pname{font-size:17px;font-weight:700}
.pdesc{margin:4px 0 8px;font-size:12.5px;line-height:1.5;color:var(--mut);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.pprice{font-size:18px;font-weight:700}
.pprice small{font-size:12px;font-weight:500;color:var(--mut)}
.het{opacity:.55}
.het .pimg::after{content:"Tạm hết";position:absolute;left:0;right:0;bottom:0;padding:4px;text-align:center;font-size:12px;font-weight:500;color:#fff;background:rgba(17,24,39,.72)}
[class*="st-key-add_"] button{height:44px!important;border-radius:12px!important;border:1.5px solid var(--g)!important;background:#fff!important;color:var(--g)!important;font-weight:600!important}
[class*="st-key-add_"] button:hover:not(:disabled){background:var(--g)!important;color:#fff!important}
[class*="st-key-add_"] button:disabled{border-color:var(--line)!important;background:#f9fafb!important;color:var(--mut)!important}

/* Giỏ hàng */
.st-key-cart{padding:22px;border-radius:22px;background:#fff;box-shadow:0 2px 14px rgba(17,24,39,.06)}
.cl{display:flex;gap:12px;align-items:flex-start;justify-content:space-between;margin-top:16px}
.cl-t{min-width:0}
.cl-t b{display:block;font-size:14px}
.cl-t small{font-size:12px;color:var(--mut)}
.cl-p{font-size:14px;font-weight:700;white-space:nowrap}
.qty{text-align:center;font-weight:700;line-height:36px}
[class*="st-key-q_"] button{height:36px!important;min-height:36px!important;padding:0!important;border-radius:10px!important;border:1.5px solid var(--line)!important;background:#fff!important;color:#374151!important;font-weight:600!important}
[class*="st-key-q_"] button:hover{border-color:var(--g)!important;color:var(--g)!important}
[class*="st-key-q_xoa_"] button{color:#dc2626!important}
[class*="st-key-q_xoa_"] button:hover{border-color:#dc2626!important;color:#dc2626!important}
.total{display:flex;justify-content:space-between;align-items:center;margin:14px 0 12px;padding-top:14px;border-top:1px dashed var(--line)}
.total span{color:var(--sub)}
.total b{font-size:21px;color:var(--g)}
.st-key-xac_nhan button{height:48px!important;border:none!important;border-radius:12px!important;background:var(--g)!important;color:#fff!important;font-weight:700!important}
.st-key-xac_nhan button:hover{background:var(--gd)!important}

/* Đơn đã đặt */
.oc{margin-bottom:14px;padding:18px 22px;border-radius:18px;background:#fff;box-shadow:0 2px 14px rgba(17,24,39,.06)}
.oc .oh{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.oc .oh span,.oc em{color:var(--mut);font-style:normal}
.oc .ol{font-size:14px;line-height:1.9}
.oc .of{display:flex;justify-content:space-between;margin-top:8px;padding-top:10px;border-top:1px dashed var(--line)}
.oc .of span{color:var(--sub)}
.oc .of b{color:var(--g)}

/* Badges trạng thái đơn hàng */
.sbadge{display:inline-flex;align-items:center;gap:4px;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;line-height:1.4}
.sbadge-prep{background:#fef3c7;color:#b45309;border:1px solid #fde68a}
.sbadge-comp{background:#dcfce7;color:#15803d;border:1px solid #bbf7d0}
.sbadge-canc{background:#fee2e2;color:#b91c1c;border:1px solid #fecaca}

div[class*="st-key-btn_pay_"] button{background:#16a34a!important;color:#fff!important;border:none!important;border-radius:10px!important;font-weight:600!important}
div[class*="st-key-btn_pay_"] button:hover{background:#15803d!important}
div[class*="st-key-btn_cancel_"] button{background:#fee2e2!important;color:#b91c1c!important;border:1px solid #fca5a5!important;border-radius:10px!important;font-weight:600!important}
div[class*="st-key-btn_cancel_"] button:hover{background:#fecaca!important}
div[class*="st-key-btn_reorder_"] button{background:#eff6ff!important;color:#1d4ed8!important;border:1px solid #bfdbfe!important;border-radius:10px!important;font-weight:600!important}


@media(min-width:992px){
div[data-testid="stColumn"]:has(.st-key-cart),div[data-testid="column"]:has(.st-key-cart){position:sticky;top:1rem;align-self:flex-start}
}
@media(max-width:768px){
.block-container{padding:1rem}
.htitle{font-size:22px}
.pimg{flex-basis:92px;height:92px}
div[data-testid="stHorizontalBlock"]:has([class*="st-key-dm_"]){flex-wrap:wrap!important;gap:8px!important}
div[data-testid="stColumn"]:has([class*="st-key-dm_"]),div[data-testid="column"]:has([class*="st-key-dm_"]){flex:1 1 calc(33% - 8px)!important;min-width:calc(33% - 8px)!important}
}
</style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 3. DỮ LIỆU MENU
# ==========================================
# Ảnh không tải được sẽ hiện chữ cái đầu của món. Muốn đổi ảnh: sửa trường "image".


def anh(ma):
    return f"https://images.unsplash.com/photo-{ma}?auto=format&fit=crop&w=400&q=80"


MENU = [
    {
        "id": "M01",
        "name": "Cà phê đen đá",
        "category": "Đồ uống",
        "price": 25000,
        "unit": "ly",
        "is_available": True,
        "description": "Cà phê Robusta truyền thống, thơm đậm vị",
        "image": anh("1514432324607-a09d9b4aefdd"),
    },
    {
        "id": "M02",
        "name": "Cà phê sữa đá",
        "category": "Đồ uống",
        "price": 29000,
        "unit": "ly",
        "is_available": True,
        "description": "Cà phê pha phin hòa quyện cùng sữa đặc béo ngậy",
        "image": anh("1517701604599-bb29b565090c"),
    },
    {
        "id": "M03",
        "name": "Trà đào cam sả",
        "category": "Đồ uống",
        "price": 39000,
        "unit": "ly",
        "is_available": True,
        "description": "Trà đen hương đào thanh mát, sả tươi và lát cam vàng",
        "image": anh("1556679343-c7306c1976bc"),
    },
    {
        "id": "M04",
        "name": "Trà sữa trân châu hoàng kim",
        "category": "Đồ uống",
        "price": 42000,
        "unit": "ly",
        "is_available": True,
        "description": "Trà sữa đậm vị kèm trân châu hoàng kim dai giòn",
        "image": anh("1558857563-b371033873b8"),
    },
    {
        "id": "M05",
        "name": "Bánh mì chảo đặc biệt",
        "category": "Món chính",
        "price": 55000,
        "unit": "phần",
        "is_available": True,
        "description": "Bò sốt tiêu, trứng ốp la, xíu mại, xúc xích và bánh mì giòn",
        "image": "https://cdn-i.doisongphapluat.com.vn/media/nguyen-thi-linh/2024/03/13/banh-my-viet-nam-dung-dau-danh-sach-top-100-mon-banh-sandwich-ngon-nhat-the-gioi-dspl1.png",
    },
    {
        "id": "M06",
        "name": "Bò lúc lắc khoai tây",
        "category": "Món chính",
        "price": 69000,
        "unit": "dĩa",
        "is_available": True,
        "description": "Bò Úc xào lửa lớn với ớt chuông, kèm khoai tây chiên",
        "image": anh("1544025162-d76694265947"),
    },
    {
        "id": "M07",
        "name": "Khoai tây chiên lắc phô mai",
        "category": "Ăn vặt",
        "price": 32000,
        "unit": "dĩa",
        "is_available": True,
        "description": "Khoai tây giòn rụm phủ lớp bột phô mai béo thơm",
        "image": anh("1576107232684-1279f390859f"),
    },
    {
        "id": "M08",
        "name": "Salad ức gà sốt mè rang",
        "category": "Khai vị",
        "price": 45000,
        "unit": "dĩa",
        "is_available": True,
        "description": "Rau xà lách tươi, cà chua bi, ức gà áp chảo sốt mè",
        "image": anh("1512621776951-a57141f2eefd"),
    },
]

DANH_MUC = ["Tất cả"] + list(dict.fromkeys(m["category"] for m in MENU))
BAN = ["Bàn số 1", "Bàn số 2", "Bàn số 3", "Mang về (Takeaway)"]
NAV = {"menu": "Thực đơn", "orders": "Đơn đã đặt"}

# Chặn Chrome tự dịch trang (nguyên nhân làm chữ bị dịch sai, số liệu không cập nhật)
JS_KHONG_DICH = """
<script>
try {
  const d = window.parent.document;
  d.documentElement.lang = "vi";
  d.documentElement.setAttribute("translate", "no");
  if (!d.querySelector('meta[name="google"]')) {
    const m = d.createElement("meta");
    m.name = "google";
    m.content = "notranslate";
    d.head.appendChild(m);
  }
} catch (e) {}
</script>
"""


def tien(x):
    return f"{x:,}".replace(",", ".") + " đ"


def bo_dau(s):
    s = unicodedata.normalize("NFD", s.replace("đ", "d").replace("Đ", "D"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def html(s):
    st.markdown(
        f'<div class="notranslate" translate="no">{s}</div>',
        unsafe_allow_html=True,
    )


# ==========================================
# 4. GIỎ HÀNG
# ==========================================


class GioHang:

    def __init__(self):
        self.mon = {}

    def them(self, m, so_luong):
        d = self.mon.setdefault(
            m["id"],
            {"ten": m["name"], "gia": m["price"], "dv": m["unit"], "sl": 0, "ghi_chu": ""},
        )
        d["sl"] = min(d["sl"] + so_luong, 20)

    def doi_sl(self, mon_id, delta):
        d = self.mon.get(mon_id)
        if not d:
            return
        d["sl"] = min(d["sl"] + delta, 20)
        if d["sl"] <= 0:
            del self.mon[mon_id]

    def tong_tien(self):
        return sum(d["gia"] * d["sl"] for d in self.mon.values())

    def tong_sl(self):
        return sum(d["sl"] for d in self.mon.values())

    def xoa_sach(self):
        self.mon.clear()


MAU_LICH_SU = [
    {
        "ma": "DH001",
        "gio": "11:20",
        "ban": "Bàn số 2",
        "phut": 10,
        "status": "PREPARING",
        "tong": 113000,
        "mon": [
            {"ten": "Cà phê sữa đá", "gia": 29000, "sl": 2, "ghi_chu": "Ít ngọt"},
            {"ten": "Bánh mì chảo đặc biệt", "gia": 55000, "sl": 1, "ghi_chu": "Trứng lòng đào"},
        ],
    },
    {
        "ma": "DH002",
        "gio": "10:45",
        "ban": "Bàn số 1",
        "phut": 0,
        "status": "COMPLETED",
        "tong": 25000,
        "mon": [
            {"ten": "Cà phê đen đá", "gia": 25000, "sl": 1, "ghi_chu": "Không đường"},
        ],
    },
    {
        "ma": "DH003",
        "gio": "09:15",
        "ban": "Mang về (Takeaway)",
        "phut": 0,
        "status": "CANCELLED",
        "tong": 39000,
        "mon": [
            {"ten": "Trà đào cam sả", "gia": 39000, "sl": 1, "ghi_chu": "Khách hủy do bận"},
        ],
    },
]

ss = st.session_state
ss.setdefault("cart", GioHang())
ss.setdefault("lich_su", [dict(x) for x in MAU_LICH_SU])
ss.setdefault("trang", "menu")
ss.setdefault("dm", "Tất cả")
ss.setdefault("loc_don", "ALL")
cart = ss.cart


def chon(khoa, gia_tri):
    st.session_state[khoa] = gia_tri


def them_vao_gio(m):
    sl = st.session_state[f"sl_{m['id']}"]
    st.session_state.cart.them(m, sl)
    st.session_state[f"sl_{m['id']}"] = 1
    st.toast(f"Đã thêm {sl} {m['name']} vào giỏ")


# ==========================================
# 5. THÀNH PHẦN GIAO DIỆN
# ==========================================


def the_mon(m):
    het = not m["is_available"]
    mo_ta = m["description"].replace(" (tạm hết)", "")
    with st.container(key=f"card_{m['id']}"):
        html(
            f'<div class="pcard{" het" if het else ""}">'
            f'<div class="pimg"><span>{m["name"][0]}</span><i style="background-image:url({m["image"]})"></i></div>'
            f'<div class="pbody"><div class="pname">{m["name"]}</div>'
            f'<div class="pdesc">{mo_ta}</div>'
            f'<div class="pprice">{tien(m["price"])} <small>/ {m["unit"]}</small></div></div></div>'
        )
        st.number_input(
            "Số lượng",
            1,
            20,
            1,
            key=f"sl_{m['id']}",
            disabled=het,
            label_visibility="collapsed",
        )
        st.button(
            "Tạm hết" if het else "Thêm vào giỏ",
            key=f"add_{m['id']}",
            disabled=het,
            on_click=them_vao_gio,
            args=(m,),
        )


def khung_gio():
    with st.container(key="cart"):
        html(f'<div class="stt first"><b>Giỏ hàng</b><span class="badge">{cart.tong_sl()} món</span></div>')

        if not cart.mon:
            html('<div class="empty"><b>Chưa có món nào</b>Chọn món ở bên trái để thêm vào giỏ hàng.</div>')
            return

        html('<div class="sub">Món đã chọn</div>')
        for mon_id, d in list(cart.mon.items()):
            html(
                f'<div class="cl"><div class="cl-t"><b>{d["ten"]}</b>'
                f'<small>{tien(d["gia"])} / {d["dv"]}</small></div>'
                f'<div class="cl-p">{tien(d["gia"] * d["sl"])}</div></div>'
            )
            c1, c2, c3, c4 = st.columns([1, 1, 1, 1.4])
            c1.button("−", key=f"q_giam_{mon_id}", on_click=cart.doi_sl, args=(mon_id, -1))
            with c2:
                html(f'<div class="qty">{d["sl"]}</div>')
            c3.button("+", key=f"q_tang_{mon_id}", on_click=cart.doi_sl, args=(mon_id, 1))
            c4.button("Xóa", key=f"q_xoa_{mon_id}", on_click=cart.doi_sl, args=(mon_id, -99))
            d["ghi_chu"] = st.text_input(
                "Ghi chú",
                value=d["ghi_chu"],
                key=f"gc_{mon_id}",
                placeholder="Ghi chú: ít đá, không cay...",
                label_visibility="collapsed",
            )

        html('<div class="sub">Chỗ ngồi</div>')
        ban = st.selectbox("Chỗ ngồi", BAN, key="ban", label_visibility="collapsed")

        html(f'<div class="total"><span>Tổng cộng</span><b>{tien(cart.tong_tien())}</b></div>')

        if st.button("Xác nhận đặt món", key="xac_nhan"):
            with st.spinner("Đang gửi đơn xuống bếp..."):
                time.sleep(2)
            ss.lich_su.insert(
                0,
                {
                    "ma": f"DH{len(ss.lich_su) + 1:03d}",
                    "gio": time.strftime("%H:%M"),
                    "ban": ban,
                    "phut": random.randint(5, 15),
                    "status": "PREPARING",
                    "tong": cart.tong_tien(),
                    "mon": [dict(d) for d in cart.mon.values()],
                },
            )
            ss.thong_bao = ss.lich_su[0]
            cart.xoa_sach()
            st.rerun()


# ==========================================
# 6. BỐ CỤC CHÍNH
# ==========================================

with st.sidebar:
    html('<div class="logo">SM</div>')
    for k, ten in NAV.items():
        st.button(
            ten,
            key=f"nav_{'on' if ss.trang == k else 'off'}_{k}",
            on_click=chon,
            args=("trang", k),
        )
    try:
        components.html(JS_KHONG_DICH, height=0)
    except Exception:
        pass

trang = ss.trang

h1, h2, h3 = st.columns([4, 4, 3], vertical_alignment="center")
with h1:
    html(
        '<div class="hello">Chào mừng đến Supper Menu Quán</div>'
        f'<div class="htitle">{"Thực đơn hôm nay" if trang == "menu" else "Đơn đã đặt"}</div>'
    )
tu_khoa = ""
if trang == "menu":
    tu_khoa = h2.text_input(
        "Tìm món",
        placeholder="Bạn đang tìm món gì?",
        key="tim",
        label_visibility="collapsed",
    )
with h3:
    html(
        '<div class="pillw"><div class="pill"><small>Giỏ hàng</small>'
        f'<b>{cart.tong_sl()} món</b><b>{tien(cart.tong_tien())}</b></div></div>'
    )

don_moi = ss.pop("thong_bao", None)
if don_moi:
    html(
        '<div class="ok"><b>Đặt món thành công</b>'
        f'Đơn {don_moi["ma"]} ({don_moi["ban"]}) đã gửi xuống bếp, '
        f'dự kiến lên món sau {don_moi["phut"]} phút.</div>'
    )
    st.balloons()

if trang == "menu":
    c_menu, c_gio = st.columns([7, 3], gap="large")

    with c_menu:
        html('<div class="stt first"><b>Danh mục</b></div>')
        for i, (col, ten) in enumerate(zip(st.columns(len(DANH_MUC)), DANH_MUC)):
            col.button(
                ten,
                key=f"dm_{'on' if ss.dm == ten else 'off'}_{i}",
                on_click=chon,
                args=("dm", ten),
            )

        ds = [
            m
            for m in MENU
            if ss.dm in ("Tất cả", m["category"])
            and bo_dau(tu_khoa) in bo_dau(m["name"] + " " + m["description"])
        ]
        tieu_de = "Tất cả món" if ss.dm == "Tất cả" else ss.dm
        html(f'<div class="stt"><b>{tieu_de}</b><span>{len(ds)} món</span></div>')

        if not ds:
            html('<div class="empty"><b>Không tìm thấy món phù hợp</b>Thử từ khóa khác hoặc chọn danh mục khác.</div>')
        for i in range(0, len(ds), 2):
            for col, m in zip(st.columns(2, gap="medium"), ds[i : i + 2]):
                with col:
                    the_mon(m)

    with c_gio:
        khung_gio()

else:
    # 1. Header & Bộ lọc trạng thái (Requirement 3: Tabs theo trạng thái)
    html('<div class="stt first"><b>Lịch sử đơn hàng</b><span>Bộ lọc theo trạng thái</span></div>')

    counts = {
        "ALL": len(ss.lich_su),
        "PREPARING": sum(1 for d in ss.lich_su if d.get("status", "PREPARING") == "PREPARING"),
        "COMPLETED": sum(1 for d in ss.lich_su if d.get("status") == "COMPLETED"),
        "CANCELLED": sum(1 for d in ss.lich_su if d.get("status") == "CANCELLED"),
    }

    c_f1, c_f2, c_f3, c_f4 = st.columns(4)
    with c_f1:
        if st.button(f"Tất cả ({counts['ALL']})", key="flt_all", type="primary" if ss.loc_don == "ALL" else "secondary", use_container_width=True):
            ss.loc_don = "ALL"
            st.rerun()
    with c_f2:
        if st.button(f"🟡 Đang chuẩn bị ({counts['PREPARING']})", key="flt_prep", type="primary" if ss.loc_don == "PREPARING" else "secondary", use_container_width=True):
            ss.loc_don = "PREPARING"
            st.rerun()
    with c_f3:
        if st.button(f"🟢 Hoàn thành ({counts['COMPLETED']})", key="flt_comp", type="primary" if ss.loc_don == "COMPLETED" else "secondary", use_container_width=True):
            ss.loc_don = "COMPLETED"
            st.rerun()
    with c_f4:
        if st.button(f"🔴 Đã hủy ({counts['CANCELLED']})", key="flt_canc", type="primary" if ss.loc_don == "CANCELLED" else "secondary", use_container_width=True):
            ss.loc_don = "CANCELLED"
            st.rerun()

    st.write("")

    # Lọc danh sách theo tab đã chọn
    ds_hien_thi = [
        d for d in ss.lich_su
        if ss.loc_don == "ALL" or d.get("status", "PREPARING") == ss.loc_don
    ]

    if not ds_hien_thi:
        html('<div class="empty"><b>Không có đơn nào trong mục này</b>Chọn bộ lọc khác để xem danh sách đơn hàng.</div>')

    for idx, d in enumerate(ds_hien_thi):
        stt = d.get("status", "PREPARING")

        # 2. Nhãn trạng thái đơn hàng (Requirement 1: Status Badge)
        badge_html = {
            "PREPARING": '<span class="sbadge sbadge-prep">🟡 Đang chuẩn bị</span>',
            "COMPLETED": '<span class="sbadge sbadge-comp">🟢 Đã lên món / Hoàn thành</span>',
            "CANCELLED": '<span class="sbadge sbadge-canc">🔴 Đã hủy</span>',
        }.get(stt, '<span class="sbadge sbadge-prep">🟡 Đang chuẩn bị</span>')

        dong = "".join(
            f'<div class="ol">{x["sl"]} × {x["ten"]}'
            + (f' <em>({escape(x.get("ghi_chu", ""))})</em>' if x.get("ghi_chu") else "")
            + "</div>"
            for x in d["mon"]
        )

        desc_time = (
            f'Dự kiến lên món sau {d.get("phut", 10)} phút'
            if stt == "PREPARING"
            else ("✅ Đơn đã hoàn tất & thanh toán" if stt == "COMPLETED" else "❌ Đơn đã hủy")
        )

        html(
            f'<div class="oc">'
            f'<div class="oh"><div><b>Đơn {d["ma"]}</b> &nbsp; <span style="font-weight:600;color:var(--ink)">({d["ban"]})</span></div>'
            f'<div><span style="font-size:12.5px;color:var(--mut);margin-right:8px">🕒 {d["gio"]}</span>{badge_html}</div></div>'
            f'{dong}'
            f'<div class="of"><span>{desc_time}</span><b>{tien(d["tong"])}</b></div>'
            f'</div>'
        )

        # 3. Nút thao tác trên đơn hàng (Requirement 2: Action Buttons)
        c_btn1, c_btn2, c_btn3 = st.columns([2.2, 1.2, 1.2])

        with c_btn1:
            with st.expander(f"📋 Chi tiết hóa đơn {d['ma']}"):
                st.write(f"**Mã đơn:** `{d['ma']}` | **Bàn:** {d['ban']} | **Thời gian:** {d['gio']}")
                st.write(f"**Trạng thái:** {stt}")
                bang_mon = [
                    {
                        "Tên món": x["ten"],
                        "Đơn giá": tien(x.get("gia", 0)),
                        "Số lượng": x["sl"],
                        "Ghi chú": x.get("ghi_chu", "") or "-",
                        "Thành tiền": tien(x.get("gia", 0) * x["sl"]),
                    }
                    for x in d["mon"]
                ]
                st.dataframe(bang_mon, use_container_width=True)
                st.markdown(f"**Tổng tiền thanh toán:** `{tien(d['tong'])}`")

        if stt == "PREPARING":
            with c_btn2:
                if st.button("💳 Thanh toán", key=f"btn_pay_{d['ma']}_{idx}", use_container_width=True):
                    d["status"] = "COMPLETED"
                    st.toast(f"✅ Đã thanh toán đơn {d['ma']} ({tien(d['tong'])})!")
                    st.rerun()
            with c_btn3:
                if st.button("❌ Hủy đơn", key=f"btn_cancel_{d['ma']}_{idx}", use_container_width=True):
                    d["status"] = "CANCELLED"
                    st.toast(f"Đã hủy đơn {d['ma']}")
                    st.rerun()
        elif stt == "CANCELLED":
            with c_btn2:
                if st.button("🔄 Đặt lại", key=f"btn_reorder_{d['ma']}_{idx}", use_container_width=True):
                    d["status"] = "PREPARING"
                    st.toast(f"Đã kích hoạt lại đơn {d['ma']}!")
                    st.rerun()
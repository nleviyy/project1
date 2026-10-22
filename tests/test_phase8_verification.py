import json
import threading
from unittest.mock import patch
import pytest

from src.core.sorting import merge_sort, binary_search
from src.core.heap import Heap, MaxHeap, MinHeap
from src.core.deque import Deque
from src.models.HashTable import HashTable
from src.models.MenuItem import MenuItem
from src.models.MenuCatalog import MenuCatalog
from src.models.Order import Order, OrderStatus
from src.models.OrderItem import OrderItem
from src.models.Payment import Payment, PaymentStatus, PaymentMethod
from src.models.Table import Table, TableStatus
from src.core.TableManager import TableManager, TableDataError
from src.core.OrderService import OrderService
from src.core.PaymentService import PaymentService
from src.core.KitchenManager import KitchenManager


# =====================================================================
# 1. THUẬT TOÁN VÀ CẤU TRÚC DỮ LIỆU
# =====================================================================

def test_merge_sort_all_cases():
    # Mảng rỗng
    assert merge_sort([]) == []

    # 1 phần tử
    assert merge_sort([42]) == [42]

    # Nhiều phần tử trùng giá trị
    duplicates = [3, 1, 3, 2, 1, 3]
    assert merge_sort(duplicates) == sorted(duplicates)

    # Đã sắp sẵn
    already_sorted = [1, 2, 3, 4, 5]
    assert merge_sort(already_sorted) == sorted(already_sorted)

    # Ngược chiều
    reversed_arr = [9, 8, 7, 6, 5, 4, 3, 2, 1]
    assert merge_sort(reversed_arr) == sorted(reversed_arr)

    # Tính ổn định (stable): các phần tử có key bằng nhau giữ nguyên thứ tự ban đầu
    items = [
        ("a", 2, 0),
        ("b", 1, 1),
        ("c", 2, 2),
        ("d", 1, 3),
        ("e", 2, 4),
    ]
    res = merge_sort(items, key=lambda x: x[1])
    # Các phần tử key=1: ('b', 1, 1) trước ('d', 1, 3)
    # Các phần tử key=2: ('a', 2, 0) trước ('c', 2, 2) trước ('e', 2, 4)
    assert res == [
        ("b", 1, 1),
        ("d", 1, 3),
        ("a", 2, 0),
        ("c", 2, 2),
        ("e", 2, 4),
    ]


def test_binary_search_all_cases():
    arr = [10, 20, 30, 40, 50, 60]

    # Tìm thấy ở đầu, cuối, giữa
    assert binary_search(arr, 10) == 0
    assert binary_search(arr, 60) == 5
    assert binary_search(arr, 30) == 2
    assert binary_search(arr, 40) == 3

    # Không tìm thấy: nhỏ hơn nhỏ nhất, lớn hơn lớn nhất, ở giữa 2 phần tử
    assert binary_search(arr, 5) == -1
    assert binary_search(arr, 100) == -1
    assert binary_search(arr, 25) == -1

    # Mảng rỗng
    assert binary_search([], 10) == -1


def test_heap_operations_and_top_k():
    # MinHeap kiểm tra thứ tự lấy ra
    min_h = MinHeap()
    elements = [45, 12, 89, 3, 77, 24, 60]
    for el in elements:
        min_h.push(el)

    popped_min = [min_h.pop() for _ in range(len(elements))]
    assert popped_min == sorted(elements)

    # MaxHeap kiểm tra thứ tự lấy ra
    max_h = MaxHeap()
    for el in elements:
        max_h.push(el)

    popped_max = [max_h.pop() for _ in range(len(elements))]
    assert popped_max == sorted(elements, reverse=True)

    # Heap rỗng ném IndexError
    empty_heap = Heap()
    with pytest.raises(IndexError):
        empty_heap.pop()

    # Kiểm tra top-k bằng MaxHeap: k phần tử lớn nhất
    k = 3
    h_top = MaxHeap()
    for el in elements:
        h_top.push(el)
    top_k = [h_top.pop() for _ in range(k)]
    expected_top_k = sorted(elements, reverse=True)[:k]
    assert top_k == expected_top_k


def test_deque_operations():
    dq = Deque()
    assert dq.is_empty() is True
    assert dq.size == 0

    # Thêm cả hai đầu
    dq.add_first(10)
    dq.add_last(20)
    dq.add_first(5)
    dq.add_last(30)
    # Thứ tự hiện tại: [5, 10, 20, 30]
    assert dq.to_list() == [5, 10, 20, 30]
    assert dq.size == 4
    assert dq.is_empty() is False

    # Bớt ở cả hai đầu
    assert dq.pop_first() == 5
    assert dq.pop_last() == 30
    assert dq.to_list() == [10, 20]

    # remove(val)
    dq.add_last(40)
    assert dq.remove(20) is True
    assert dq.remove(999) is False
    assert dq.to_list() == [10, 40]

    # pop_where
    popped = dq.pop_where(lambda x: x == 40)
    assert popped == 40
    assert dq.to_list() == [10]
    assert dq.pop_where(lambda x: x == 999) is None

    # remove_first
    assert dq.remove_first() == 10
    assert dq.is_empty() is True


def test_hash_table_comprehensive():
    ht = HashTable(capacity=4)
    assert ht.size == 0

    # Thêm và đọc
    ht.put("key1", "val1")
    ht.put("key2", "val2")
    assert ht.get("key1") == "val1"
    assert ht.get("key2") == "val2"
    assert ht.contains("key1") is True
    assert ht.contains("missing") is False

    # Sửa giá trị
    ht.put("key1", "val1_updated")
    assert ht.get("key1") == "val1_updated"
    assert ht.size == 2

    # Xóa
    assert ht.remove("key2") is True
    assert ht.get("key2") is None
    assert ht.contains("key2") is False
    assert ht.remove("nonexistent") is False

    # Kích hoạt resize tự động khi thêm nhiều phần tử
    for i in range(20):
        ht.put(f"auto_key_{i}", i)

    assert ht.size == 21
    for i in range(20):
        assert ht.get(f"auto_key_{i}") == i

    # keys, values, items
    all_keys = list(ht.keys())
    assert len(all_keys) == 21
    assert "key1" in all_keys

    all_vals = list(ht.values())
    assert len(all_vals) == 21
    assert "val1_updated" in all_vals

    all_items = list(ht.items())
    assert len(all_items) == 21
    assert ("key1", "val1_updated") in all_items

    # clear
    ht.clear()
    assert ht.size == 0
    assert len(list(ht.keys())) == 0
    assert ht.get("key1") is None


# =====================================================================
# 2. TÌM KIẾM GỢI Ý MÓN (MenuCatalog.autocomplete_items)
# =====================================================================

def test_menu_catalog_autocomplete_phase6_rules():
    catalog = MenuCatalog()
    items = [
        MenuItem(id="M01", name="Bò xào hành cần", category="Món chính", price=50000, unit="dĩa"),
        MenuItem(id="M02", name="Phở bò tái nạm", category="Món chính", price=45000, unit="tô"),
        MenuItem(id="M03", name="Bún chả cá", category="Món chính", price=40000, unit="tô"),
        MenuItem(id="M04", name="Bò sốt vang", category="Món chính", price=60000, unit="tô"),
        MenuItem(id="M05", name="Bò", category="Món chính", price=50000, unit="phần"),
    ]
    for item in items:
        catalog.add_item(item)

    # Keyword rỗng hoặc khoảng trắng trả về rỗng
    assert catalog.autocomplete_items("") == []
    assert catalog.autocomplete_items("   ") == []

    # Tìm với từ khóa "bò":
    # - M05 ("Bò") trùng hoàn toàn với từ khóa -> BỎ QUA
    # - Nhóm 0 (tên bắt đầu bằng từ khóa): "Bò sốt vang", "Bò xào hành cần"
    # - Nhóm 1 (một từ trong tên bắt đầu bằng từ khóa): "Phở bò tái nạm"
    # - Trong cùng nhóm 0, sắp xếp theo tên casefold: "Bò sốt vang" trước "Bò xào hành cần"
    results = catalog.autocomplete_items("bò")
    assert len(results) == 3
    # Nhóm 0 trước nhóm 1
    assert results[0].id == "M04"  # Bò sốt vang
    assert results[1].id == "M01"  # Bò xào hành cần
    assert results[2].id == "M02"  # Phở bò tái nạm

    # Giới hạn max_results
    assert len(catalog.autocomplete_items("bò", max_results=2)) == 2

    # Case-insensitive
    res_upper = catalog.autocomplete_items("BÒ")
    assert [r.id for r in res_upper] == ["M04", "M01", "M02"]


# =====================================================================
# 3. NGHIỆP VỤ (Order, OrderItem, Payment, Table, Services)
# =====================================================================

def test_order_restrictions_and_transitions():
    order = Order(
        id="ORD-01",
        table_id=1,
        status="PENDING",
        items=[OrderItem(menu_item_id="M01", item_name="Cà phê", unit_price=20000, quantity=1)]
    )

    # Khi PENDING: can_modify_items trả True, được phép add_item
    assert order.can_modify_items() is True
    assert order.can_modify is True
    assert order.add_item(OrderItem(menu_item_id="M02", item_name="Trà", unit_price=15000, quantity=1)) is True

    # Chuyển sang PREPARING
    assert order.change_status("PREPARING") is True
    assert order.can_modify_items() is False
    with pytest.raises(ValueError, match="Không thể sửa món"):
        order.add_item(OrderItem(menu_item_id="M03", item_name="Bánh", unit_price=10000, quantity=1))

    # Không cho phép hủy khi PREPARING
    assert order.cancel() is False
    assert order.change_status("CANCELLED") is False
    assert order.status == "PREPARING"

    # Chuyển sang SERVED
    assert order.change_status("SERVED") is True

    # Không cho phép hủy khi SERVED
    assert order.cancel() is False
    assert order.change_status("CANCELLED") is False
    assert order.status == "SERVED"

    # mark_completed yêu cầu payment SUCCESS đúng order_id
    wrong_order_pay = Payment(
        id="PAY-01",
        order_id="WRONG-ORD",
        table_id=1,
        amount_paid=35000,
        cashier_name="Thu ngân",
        status=PaymentStatus.SUCCESS,
    )
    with pytest.raises(ValueError, match="Chỉ thanh toán SUCCESS của đúng đơn"):
        order.mark_completed(wrong_order_pay)

    pending_pay = Payment(
        id="PAY-02",
        order_id="ORD-01",
        table_id=1,
        amount_paid=35000,
        cashier_name="Thu ngân",
        status=PaymentStatus.PENDING,
    )
    with pytest.raises(ValueError, match="Chỉ thanh toán SUCCESS của đúng đơn"):
        order.mark_completed(pending_pay)

    valid_pay = Payment(
        id="PAY-03",
        order_id="ORD-01",
        table_id=1,
        amount_paid=35000,
        cashier_name="Thu ngân",
        status=PaymentStatus.SUCCESS,
    )
    assert order.mark_completed(valid_pay) is True
    assert order.status == "COMPLETED"


def test_order_item_subtotal_synchronization():
    item = OrderItem(
        menu_item_id="M01",
        item_name="Phở bò",
        unit_price=40000,
        quantity=2,
    )
    assert item.subtotal == 80000

    # Cập nhật quantity qua update_quantity
    item.update_quantity(3)
    assert item.subtotal == 120000

    # Cập nhật unit_price qua update_unit_price
    item.update_unit_price(50000)
    assert item.subtotal == 150000

    # Cập nhật qua __setattr__
    item.unit_price = 45000
    assert item.subtotal == 135000

    # Khởi tạo với subtotal = 0 được bảo toàn
    zero_item = OrderItem(
        menu_item_id="M02",
        item_name="Món tặng",
        unit_price=20000,
        quantity=1,
        subtotal=0,
    )
    assert zero_item.subtotal == 0


def test_payment_default_status_and_revenue_idempotency():
    pay = Payment(
        id="PAY-10",
        order_id="ORD-10",
        table_id=1,
        amount_paid=50000,
        cashier_name="Thu ngân",
    )
    # Mặc định status là PENDING
    assert pay.status == PaymentStatus.PENDING
    assert pay.is_successful is False

    # calculate_revenue dùng HashTable không cộng trùng đơn
    p1 = Payment(id="P1", order_id="ORD-A", table_id=1, amount_paid=100000, cashier_name="A", status=PaymentStatus.SUCCESS)
    p2 = Payment(id="P2", order_id="ORD-A", table_id=1, amount_paid=100000, cashier_name="A", status=PaymentStatus.SUCCESS)
    p3 = Payment(id="P3", order_id="ORD-B", table_id=2, amount_paid=50000, cashier_name="A", status=PaymentStatus.SUCCESS)
    p4 = Payment(id="P4", order_id="ORD-C", table_id=3, amount_paid=30000, cashier_name="A", status=PaymentStatus.PENDING)

    rev_report = Payment.calculate_revenue([p1, p2, p3, p4])
    # Chỉ cộng ORD-A (1 lần) và ORD-B (1 lần), bỏ qua p4 PENDING
    assert rev_report["total_revenue"] == 150000
    assert rev_report["successful_orders_count"] == 2


def test_table_occupy_release_and_validation():
    tbl = Table(id=1, name="Bàn 1", capacity=4, status=TableStatus.AVAILABLE)
    assert tbl.status == "AVAILABLE"

    # Chiếm bàn
    tbl.occupy("ORD-001")
    assert tbl.status == "OCCUPIED"
    assert tbl.current_order_id == "ORD-001"

    # Chiếm bàn đã OCCUPIED ném ValueError
    with pytest.raises(ValueError, match="đang được sử dụng"):
        tbl.occupy("ORD-002")

    # release đưa về AVAILABLE
    tbl.release()
    assert tbl.status == "AVAILABLE"
    assert tbl.current_order_id is None

    # Cập nhật status không hợp lệ ném ValueError
    with pytest.raises(ValueError):
        tbl.update_status("INVALID_STATUS")

    # Khởi tạo capacity không hợp lệ ném ValueError
    with pytest.raises(ValueError):
        Table(id=2, name="Bàn 2", capacity=0)
    with pytest.raises(ValueError):
        Table(id=2, name="Bàn 2", capacity=-5)

    # from_dict yêu cầu capacity
    with pytest.raises(ValueError, match="sức chứa"):
        Table.from_dict({"id": 3, "name": "Bàn 3"})


def test_table_manager_rollback_on_save_error(tmp_path):
    tables_file = tmp_path / "tables.json"
    initial_tables = [
        {"id": 1, "name": "Bàn 1", "capacity": 4, "status": "AVAILABLE", "current_order_id": None},
        {"id": 2, "name": "Bàn 2", "capacity": 2, "status": "RESERVED", "current_order_id": None},
        {"id": 3, "name": "Bàn 3", "capacity": 4, "status": "OCCUPIED", "current_order_id": "ORD-EXIST"},
    ]
    tables_file.write_text(json.dumps(initial_tables), encoding="utf-8")
    tm = TableManager(tables_file=tables_file)

    # Giả lập save_tables ném TableDataError (khi _load_failed) hoặc OSError
    with patch.object(tm, "save_tables", side_effect=TableDataError("Lỗi ghi")):
        # 1. occupy_table
        with pytest.raises(TableDataError):
            tm.occupy_table(1, "ORD-999")
        assert tm.get_table(1).status == "AVAILABLE"

        # 2. release_table
        with pytest.raises(TableDataError):
            tm.release_table(3, "ORD-EXIST")
        assert tm.get_table(3).status == "OCCUPIED"

        # 3. reserve_table
        with pytest.raises(TableDataError):
            tm.reserve_table(1)
        assert tm.get_table(1).status == "AVAILABLE"

        # 4. vacate_table
        with pytest.raises(TableDataError):
            tm.vacate_table(2)
        assert tm.get_table(2).status == "RESERVED"

        # 5. add_table
        with pytest.raises(TableDataError):
            tm.add_table(Table(id=4, name="Bàn mới", capacity=4))
        assert len(tm.get_all_tables()) == 3

        # 6. remove_table
        with pytest.raises(TableDataError):
            tm.remove_table(1)
        assert tm.get_table(1) is not None

        # 7. update_table
        with pytest.raises(TableDataError):
            tm.update_table(1, capacity=10)
        assert tm.get_table(1).capacity == 4


def test_payment_service_atomic_persist_and_concurrency(tmp_path):
    tables_file = tmp_path / "tables.json"
    orders_file = tmp_path / "orders.json"
    payments_file = tmp_path / "payments.json"
    invoices_file = tmp_path / "invoices.json"

    tables_file.write_text(
        json.dumps([{"id": 1, "name": "Bàn 1", "capacity": 4, "status": "OCCUPIED", "current_order_id": "ORD-1"}]),
        encoding="utf-8"
    )
    orders_file.write_text(
        json.dumps([{
            "id": "ORD-1",
            "table_id": 1,
            "status": "SERVED",
            "items": [{"menu_item_id": "M01", "item_name": "Phở", "unit_price": 50000, "quantity": 1, "subtotal": 50000}],
            "total_amount": 50000,
            "discount_amount": 0
        }]),
        encoding="utf-8"
    )
    payments_file.write_text("[]", encoding="utf-8")
    invoices_file.write_text("[]", encoding="utf-8")

    tm = TableManager(tables_file=tables_file)
    os_service = OrderService(orders_file=orders_file, table_manager=tm)
    pay_service = PaymentService(
        payments_path=payments_file,
        invoices_path=invoices_file,
        orders_path=orders_file,
        tables_path=tables_file,
        table_manager=tm,
        order_service=os_service,
    )

    # Thanh toán đồng thời (hai luồng cùng pay_order)
    results = []
    errors = []

    def run_pay():
        try:
            res = pay_service.pay_order("ORD-1", "CASH", "Thu Ngân", cash_received=50000)
            results.append(res)
        except Exception as e:
            errors.append(e)

    t1 = threading.Thread(target=run_pay)
    t2 = threading.Thread(target=run_pay)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Chỉ đúng 1 luồng thành công, 1 luồng thất bại do đã thanh toán
    assert len(results) == 1
    assert len(errors) == 1
    assert results[0].payment.is_successful is True

    # Kiểm tra tính toàn vẹn 4 file sau persist nguyên tử
    saved_orders = json.loads(orders_file.read_text(encoding="utf-8"))
    assert saved_orders[0]["status"] == "COMPLETED"

    saved_tables = json.loads(tables_file.read_text(encoding="utf-8"))
    assert saved_tables[0]["status"] == "AVAILABLE"
    assert saved_tables[0]["current_order_id"] is None

    saved_payments = json.loads(payments_file.read_text(encoding="utf-8"))
    assert len(saved_payments) == 1

    saved_invoices = json.loads(invoices_file.read_text(encoding="utf-8"))
    assert len(saved_invoices) == 1


def test_order_service_load_create_and_place_order(tmp_path):
    orders_file = tmp_path / "orders.json"
    tables_file = tmp_path / "tables.json"

    tables_file.write_text(
        json.dumps([
            {"id": 1, "name": "Bàn 1", "capacity": 4, "status": "AVAILABLE", "current_order_id": None},
            {"id": 2, "name": "Bàn 2", "capacity": 4, "status": "AVAILABLE", "current_order_id": None},
        ]),
        encoding="utf-8"
    )
    tm = TableManager(tables_file=tables_file)
    km = KitchenManager()

    # 1. load_orders không làm mất dữ liệu khi file lỗi/không phải list
    initial_orders = [{"id": "ORD-SAFE", "table_id": 1, "status": "PENDING", "items": []}]
    orders_file.write_text(json.dumps(initial_orders), encoding="utf-8")
    svc = OrderService(orders_file=orders_file, table_manager=tm, kitchen_manager=km)
    assert svc.get_order("ORD-SAFE") is not None

    # Ghi file lỗi
    orders_file.write_text("{\"not\": \"a list\"}", encoding="utf-8")
    svc.load_orders()
    # Dữ liệu cũ trong bộ nhớ vẫn còn nguyên, không bị wipeout
    assert svc.get_order("ORD-SAFE") is not None

    # 2. create_order ném lỗi khi chiếm bàn thất bại
    tm.occupy_table(1, "EXISTING")
    with pytest.raises(ValueError, match="Không thể chiếm bàn"):
        svc.create_order(table_id=1, items=[OrderItem(menu_item_id="M01", quantity=1)])

    # Giải phóng bàn
    tm.release_table(1)

    # 3. place_order rollback bàn và không đưa vào bếp khi xảy ra lỗi lưu
    items_to_order = [OrderItem(menu_item_id="M01", item_name="Cà phê", unit_price=20000, quantity=1)]
    with patch.object(svc, "save_orders", side_effect=OSError("Lỗi đĩa")):
        with pytest.raises(OSError):
            svc.place_order(table_id=2, items=items_to_order)

        # Bàn phải được rollback về AVAILABLE
        assert tm.is_table_available(2) is True
        # Không có đơn nào lọt vào bếp
        assert km.count_waiting() == 0

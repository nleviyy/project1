import json
from pathlib import Path

import pytest
from src.models.MenuItem import MenuItem
from src.models.MenuCatalog import MenuCatalog, HashTable

def test_menu_item_valid():
    item = MenuItem(
        id="M01",
        name="Cà phê đen đá",
        category="Đồ uống",
        price=25000,
        unit="ly",
        is_available=True,
        description="Đậm đà hương vị",
        prep_time=5
    )
    assert item.id == "M01"
    assert item.name == "Cà phê đen đá"
    assert item.price == 25000
    assert item.is_available is True
    assert isinstance(item.price, int)

def test_menu_item_validation_error():
    with pytest.raises(ValueError):
        MenuItem(
            id="M",  # Quá ngắn (< 2 ký tự)
            name="", # Trống
            category="Đồ uống",
            price=-5000, # Giá âm không hợp lệ
            unit="ly"
        )

def test_menu_item_rejects_fractional_vnd_price():
    with pytest.raises(ValueError, match="số nguyên"):
        MenuItem(
            id="M01",
            name="Món thử",
            category="Đồ ăn",
            price=12500.5,
            unit="phần",
        )


def test_menu_item_serialization_uses_its_own_dict_methods():
    item = MenuItem(
        id="M03",
        name="Nước cam",
        category="Đồ uống",
        price=18000,
        unit="ly",
        is_available=False,
        description="Cam tươi",
        prep_time=3,
        image="orange.png",
        color="#ff9900",
    )

    data = item.to_dict()

    assert data == {
        "id": "M03",
        "name": "Nước cam",
        "category": "Đồ uống",
        "price": 18000,
        "unit": "ly",
        "is_available": False,
        "description": "Cam tươi",
        "prep_time": 3,
        "image": "orange.png",
        "color": "#ff9900",
    }
    assert MenuItem.from_dict(data) == item


def test_menu_item_from_dict_supports_alias_keys():
    item = MenuItem.from_dict(
        {
            "item_id": "M04",
            "name": "Trà nóng",
            "item_type": "Đồ uống",
            "unit_price": "12000",
            "unit": "ly",
            "status": False,
        }
    )

    assert item.id == "M04"
    assert item.category == "Đồ uống"
    assert item.price == 12000
    assert item.is_available is False
    assert item.prep_time == 0


def test_menu_item_update_restores_state_after_invalid_data():
    item = MenuItem(
        id="M05",
        name="Bánh mì",
        category="Món chính",
        price=25000,
        unit="phần",
    )
    original = item.to_dict()

    with pytest.raises(ValueError, match="đã khôi phục"):
        item.update(name="Bánh mì mới", price=-1)

    assert item.to_dict() == original


def test_menu_catalog_crud_and_search():
    catalog = MenuCatalog()
    item1 = MenuItem(id="M01", name="Cà phê đen đá", category="Đồ uống", price=25000, unit="ly")
    item2 = MenuItem(id="M02", name="Trà đào cam sả", category="Đồ uống", price=35000, unit="ly", is_available=False)
    item3 = MenuItem(id="M05", name="Bánh mì chảo", category="Món chính", price=55000, unit="phần")

    # Thêm món
    assert catalog.add_item(item1) is True
    assert catalog.add_item(item2) is True
    assert catalog.add_item(item3) is True
    # Thêm trùng ID
    assert catalog.add_item(item1) is False

    # Lấy món theo ID
    assert catalog.get_item("M01") == item1
    assert catalog.get_item("M99") is None

    # Tìm kiếm
    found = catalog.search_items("cà phê")
    assert len(found) == 1
    assert found[0].id == "M01"

    # Lọc theo nhóm danh mục
    drinks = catalog.filter_by_category("Đồ uống")
    assert len(drinks) == 2

    # Lọc theo tình trạng còn món / hết món
    available_items = catalog.filter_by_availability(True)
    assert len(available_items) == 2
    unavailable_items = catalog.filter_by_availability(False)
    assert len(unavailable_items) == 1
    assert unavailable_items[0].id == "M02"

    # Cập nhật món
    assert catalog.update_item("M01", price=28000, is_available=False) is True
    assert catalog.get_item("M01").price == 28000
    assert catalog.get_item("M01").is_available is False

    # Xóa món
    assert catalog.remove_item("M01") is True
    assert catalog.get_item("M01") is None
    assert catalog.remove_item("M01") is False


def test_menu_catalog_autocomplete_matches_name_and_id_prefixes():
    catalog = MenuCatalog()
    items = [
        MenuItem(
            id=item_id,
            name=name,
            category="Đồ uống",
            price=10000,
            unit="ly",
        )
        for item_id, name in (
            ("DR01", "Trà đào"),
            ("DR02", "Trà sen"),
            ("CF01", "Cà phê"),
        )
    ]
    for item in items:
        catalog.add_item(item)

    res_tr = catalog.autocomplete_items("tr")
    assert len(res_tr) == 2
    assert sorted([i.id for i in res_tr]) == ["DR01", "DR02"]
    res_dr = catalog.autocomplete_items("dr")
    assert len(res_dr) == 2
    assert sorted([i.id for i in res_dr]) == ["DR01", "DR02"]
    assert catalog.autocomplete_items("TRÀ ĐÀO") == []
    assert catalog.autocomplete_items(" ") == []


def test_menu_catalog_autocomplete_limits_suggestions():
    catalog = MenuCatalog()
    items = [
        MenuItem(
            id=f"TR{index:02}",
            name=f"Trà số {index}",
            category="Đồ uống",
            price=10000,
            unit="ly",
        )
        for index in range(1, 8)
    ]
    for item in items:
        catalog.add_item(item)

    suggestions = catalog.autocomplete_items("tr", max_results=3)
    assert len(suggestions) == 3
    assert all(item in items for item in suggestions)
    assert catalog.autocomplete_items("tr", max_results=0) == []


def test_menu_catalog_loads_integer_priced_items_from_json():
    menu_path = Path(__file__).resolve().parent.parent / "data" / "menu.json"
    with menu_path.open(encoding="utf-8") as menu_file:
        menu_data = json.load(menu_file)

    catalog = MenuCatalog()
    catalog.load_from_dict(menu_data)

    items = catalog.get_all_items()
    assert len(items) == len(menu_data)
    assert all(type(item.price) is int for item in items)


def test_menu_catalog_uses_custom_hash_table():
    catalog = MenuCatalog()
    assert isinstance(catalog._items, HashTable)
    assert not isinstance(catalog._items, dict)


def test_custom_hash_table_operations():
    ht = HashTable(capacity=4)
    assert len(ht) == 0

    # put and get
    ht.put("k1", "v1")
    ht.put("k2", "v2")
    assert len(ht) == 2
    assert ht.get("k1") == "v1"
    assert ht.get("k2") == "v2"
    assert ht.get("k3", "default") == "default"

    # update existing key
    ht.put("k1", "v1_updated")
    assert len(ht) == 2
    assert ht.get("k1") == "v1_updated"

    # operator syntax __getitem__, __setitem__, __contains__
    ht["k3"] = "v3"
    assert "k3" in ht
    assert "k99" not in ht
    assert ht["k3"] == "v3"

    # test keys, values, items
    assert set(ht.keys()) == {"k1", "k2", "k3"}
    assert set(ht.values()) == {"v1_updated", "v2", "v3"}
    assert set(ht.items()) == {("k1", "v1_updated"), ("k2", "v2"), ("k3", "v3")}

    # pop
    popped = ht.pop("k2")
    assert popped == "v2"
    assert "k2" not in ht
    assert len(ht) == 2
    assert ht.pop("nonexistent", "fallback") == "fallback"

    # remove
    assert ht.remove("k1") is True
    assert ht.remove("k1") is False
    assert len(ht) == 1

    # __delitem__
    del ht["k3"]
    assert len(ht) == 0
    with pytest.raises(KeyError):
        del ht["nonexistent"]

    # clear
    ht.put("a", 1)
    ht.put("b", 2)
    assert len(ht) == 2
    ht.clear()
    assert len(ht) == 0
    assert ht.get("a") is None


def test_custom_hash_table_rehashing_and_collision():
    # Khởi tạo bảng với capacity rất nhỏ (2) để kích hoạt đụng độ và rehash liên tục
    ht = HashTable(capacity=2)
    for i in range(20):
        ht.put(f"item_{i}", i * 10)

    assert len(ht) == 20
    assert ht.capacity > 2  # Đã tự động resize

    # Toàn bộ dữ liệu vẫn nguyên vẹn sau khi rehash
    for i in range(20):
        assert ht.get(f"item_{i}") == i * 10

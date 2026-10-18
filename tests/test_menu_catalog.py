import pytest
from src.models.MenuItem import MenuItem
from src.models.MenuCatalog import MenuCatalog

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

def test_menu_item_validation_error():
    with pytest.raises(ValueError):
        MenuItem(
            id="M",  # Quá ngắn (< 2 ký tự)
            name="", # Trống
            category="Đồ uống",
            price=-5000, # Giá âm không hợp lệ
            unit="ly"
        )


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

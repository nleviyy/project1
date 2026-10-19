import pytest

from src.core.Cart import Cart
from src.models.MenuCatalog import MenuCatalog
from src.models.MenuItem import MenuItem


def make_item(*, available=True):
    return MenuItem(
        id="M01",
        name="Cà phê đen đá",
        category="Đồ uống",
        price=25000,
        unit="ly",
        is_available=available,
        prep_time=5,
    )


def test_cart_add_update_note_remove_and_undo_redo():
    cart = Cart()
    item = make_item()

    cart.add_item(item, quantity=2, note="ít đá")
    cart.update_quantity(item.id, 3)
    cart.set_note(item.id, "không đường")
    assert cart.get_order_items()[0]["quantity"] == 3
    assert cart.get_order_items()[0]["note"] == "không đường"
    assert cart.calculate_total() == 75000

    cart.undo()
    assert cart.get_order_items()[0]["note"] == "ít đá"
    cart.redo()
    assert cart.get_order_items()[0]["note"] == "không đường"

    cart.remove_item(item.id)
    assert cart.is_empty()
    cart.undo()
    assert cart.get_order_items()[0]["quantity"] == 3


def test_cart_rejects_unavailable_menu_item():
    cart = Cart()

    with pytest.raises(ValueError, match="đã hết"):
        cart.add_item(make_item(available=False))

    assert cart.is_empty()
    assert not cart.can_undo()

def test_cart_update_quantity_and_note_is_one_undo_action():
    cart = Cart()
    item = make_item()
    cart.add_item(item, quantity=2, note="regular")
    cart.update_item(item.id, quantity=4, note="extra")

    assert cart.undo()
    restored = cart.get_order_items()[0]
    assert restored["quantity"] == 2
    assert restored["note"] == "regular"


def test_menu_catalog_imports_one_menu_item_class():
    catalog = MenuCatalog()
    item = make_item()

    assert catalog.add_item(item)
    assert catalog.get_item(item.id) is item

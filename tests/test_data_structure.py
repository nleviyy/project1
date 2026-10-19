import unittest
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from KitchenManage import KitchenManager, Order, OrderStatus
from redo_undo import Cart, CartItem


# ====================== Hàng đợi bếp (FIFO) ======================
class TestKitchenQueue(unittest.TestCase):
    def setUp(self):
        self.kitchen = KitchenManager()

    def _cook_one(self):
        order = self.kitchen.start_next_order()
        self.kitchen.advance_status()            
        self.kitchen.finish_current_order()
        return order

    def test_fifo_order(self):
        for oid in ["A", "B", "C"]:
            self.kitchen.add_order(Order(oid))
        got = [self._cook_one().order_id for _ in range(3)]
        self.assertEqual(got, ["A", "B", "C"])

    def test_empty_queue(self):
        self.assertTrue(self.kitchen.is_empty())
        self.assertEqual(self.kitchen.count_waiting(), 0)
        self.assertIsNone(self.kitchen.start_next_order())
        self.assertIsNone(self.kitchen.peek_next_order())

    def test_queue_becomes_empty_after_all_done(self):
        self.kitchen.add_order(Order("A"))
        self._cook_one()
        self.assertTrue(self.kitchen.is_empty())

    def test_peek_does_not_remove(self):
        self.kitchen.add_order(Order("A"))
        self.kitchen.add_order(Order("B"))
        self.assertEqual(self.kitchen.peek_next_order().order_id, "A")
        self.assertEqual(self.kitchen.count_waiting(), 2)

    def test_duplicate_order_rejected(self):
        self.kitchen.add_order(Order("A"))
        with self.assertRaises(ValueError):
            self.kitchen.add_order(Order("A"))

    def test_cannot_start_when_busy(self):
        self.kitchen.add_order(Order("A"))
        self.kitchen.add_order(Order("B"))
        self.kitchen.start_next_order()
        with self.assertRaises(ValueError):
            self.kitchen.start_next_order()      

    def test_estimate_wait_time(self):
        a, b, c = Order("A", prep_time=5), Order("B", prep_time=7), Order("C", prep_time=3)
        for o in (a, b, c):
            self.kitchen.add_order(o)
        self.assertEqual(self.kitchen.estimate_wait_time(c), 5 + 7 + 3)
        self.kitchen.start_next_order()          # A đang làm
        self.assertEqual(self.kitchen.estimate_wait_time(a), 5)
        self.assertEqual(self.kitchen.estimate_wait_time(c), 5 + 7 + 3)


# ====================== Trạng thái đơn (8.2) ======================
class TestOrderStatus(unittest.TestCase):
    def setUp(self):
        self.kitchen = KitchenManager()
        self.order = Order("A")
        self.kitchen.add_order(self.order)

    def test_status_flow(self):
        self.assertEqual(self.kitchen.get_status("A"), OrderStatus.PENDING)
        self.kitchen.start_next_order()
        self.assertEqual(self.kitchen.get_status("A"), OrderStatus.PREPARING)
        self.kitchen.advance_status()
        self.assertEqual(self.kitchen.get_status("A"), OrderStatus.SERVED)
        self.assertEqual(self.kitchen.get_status_label("A"), "Đã lên món")

    def test_invalid_transition(self):
        self.kitchen.start_next_order()          
        with self.assertRaises(ValueError):
            self.kitchen.change_status("A", OrderStatus.COMPLETED)   

    def test_finish_before_served_rejected(self):
        self.kitchen.start_next_order()
        with self.assertRaises(ValueError):
            self.kitchen.finish_current_order()

    def test_cannot_advance_when_served(self):
        self.kitchen.start_next_order()
        self.kitchen.advance_status()
        with self.assertRaises(ValueError):
            self.kitchen.advance_status()

    def test_cancel_waiting_order(self):
        self.kitchen.cancel_order("A")
        self.assertEqual(self.order.status, OrderStatus.CANCELLED)
        self.assertEqual(self.kitchen.count_waiting(), 0)

    def test_cannot_cancel_current_order_while_preparing(self):
        self.kitchen.start_next_order()
        with self.assertRaises(ValueError):
            self.kitchen.cancel_order("A")
        self.assertEqual(self.order.status, OrderStatus.PREPARING)
        self.assertIs(self.kitchen.get_current_order(), self.order)

    def test_cannot_cancel_after_served(self):
        self.kitchen.start_next_order()
        self.kitchen.advance_status()
        with self.assertRaises(ValueError):
            self.kitchen.cancel_order("A")
        self.assertEqual(self.order.status, OrderStatus.SERVED)  

    def test_updated_at_is_valid_iso(self):
        self.kitchen.start_next_order()
        created = datetime.fromisoformat(self.order.created_at)
        updated = datetime.fromisoformat(self.order.updated_at)   
        self.assertGreaterEqual(updated, created)


# ====================== Undo / Redo giỏ hàng (8.3) ======================
PHO = {"id": "M01", "name": "Phở bò", "price": 50000, "is_available": True}
COM = {"id": "M02", "name": "Cơm tấm", "price": 45000, "is_available": True}
TRA = {"id": "M03", "name": "Trà đá", "price": 5000, "is_available": True}
HET = {"id": "M04", "name": "Bún bò", "price": 55000, "is_available": False}


def item_ids(cart):
    return [row["menu_item_id"] for row in cart.get_order_items()]


class TestCartBasic(unittest.TestCase):
    def setUp(self):
        self.cart = Cart()

    def test_add_and_merge_same_item(self):
        self.cart.add_item(PHO, 2)
        self.cart.add_item(PHO, 3)               
        self.assertEqual(self.cart.count_lines(), 1)
        self.assertEqual(self.cart.get_order_items()[0]["quantity"], 5)

    def test_calculate_total(self):
        self.cart.add_item(PHO, 2)               
        self.cart.add_item(TRA, 3)               
        self.assertEqual(self.cart.calculate_total(), 115000)

    def test_order_item_format_matches_spec(self):
        self.cart.add_item(PHO, 2, "ít hành")
        row = self.cart.get_order_items()[0]
        self.assertEqual(row, {
            "menu_item_id": "M01",
            "item_name": "Phở bò",
            "unit_price": 50000,
            "quantity": 2,
            "subtotal": 100000,
            "note": "ít hành",
        })

    def test_get_order_items_returns_copy(self):
        self.cart.add_item(PHO, 1)
        self.cart.get_order_items()[0]["quantity"] = 99   
        self.assertEqual(self.cart.get_order_items()[0]["quantity"], 1)

    def test_unavailable_item_rejected(self):
        with self.assertRaises(ValueError):
            self.cart.add_item(HET, 1)

    def test_invalid_quantity_rejected(self):
        with self.assertRaises(ValueError):
            self.cart.add_item(PHO, 0)
        with self.assertRaises(ValueError):
            self.cart.add_item(PHO, -2)

    def test_invalid_actions_do_not_change_history(self):
        for action in (lambda: self.cart.add_item(HET, 1),
                       lambda: self.cart.add_item(PHO, 0),
                       lambda: self.cart.remove_item("M99"),
                       lambda: self.cart.update_quantity("M99", 2),
                       lambda: self.cart.set_note("M99", "x")):
            with self.assertRaises(ValueError):
                action()
        self.assertEqual(self.cart.undo_stack, [])
        self.assertTrue(self.cart.is_empty())

    def test_remove_update_and_note(self):
        self.cart.add_item(PHO, 1)
        self.cart.add_item(COM, 1)
        self.cart.update_quantity("M01", 4)
        self.cart.set_note("M02", "không hành")
        self.cart.remove_item("M01")
        self.assertEqual(item_ids(self.cart), ["M02"])
        self.assertEqual(self.cart.get_order_items()[0]["note"], "không hành")

    def test_clear_resets_items_and_history(self):
        self.cart.add_item(PHO, 1)
        self.cart.add_item(COM, 1)
        self.cart.undo()
        self.cart.clear()
        self.assertTrue(self.cart.is_empty())
        self.assertFalse(self.cart.can_undo())
        self.assertFalse(self.cart.can_redo())

    def test_cart_item_dict_roundtrip(self):
        item = CartItem("M01", "Phở bò", 50000, 2, "ít hành")
        again = CartItem.from_dict(item.to_dict())
        self.assertEqual(again.to_dict(), item.to_dict())

    def test_cart_preserves_prep_time_for_kitchen_estimate(self):
        self.cart.add_item(
            {
                "id": "M01",
                "name": "Phở bò",
                "price": 50000,
                "prep_time": 7,
                "is_available": True,
            },
            quantity=3,
        )
        self.assertEqual(self.cart.get_order_items()[0]["prep_time"], 7)
        self.cart.undo()
        self.cart.redo()
        self.assertEqual(self.cart.get_order_items()[0]["prep_time"], 7)


class TestUndoRedo(unittest.TestCase):
    def setUp(self):
        self.cart = Cart()

    def test_undo_redo_multiple_steps(self):
        self.cart.add_item(PHO)
        self.cart.add_item(COM)
        self.cart.add_item(TRA)

        self.cart.undo()
        self.cart.undo()
        self.assertEqual(item_ids(self.cart), ["M01"])

        self.cart.redo()
        self.assertEqual(item_ids(self.cart), ["M01", "M02"])
        self.cart.redo()
        self.assertEqual(item_ids(self.cart), ["M01", "M02", "M03"])

    def test_undo_all_the_way_back(self):
        self.cart.add_item(PHO)
        self.cart.add_item(COM)
        self.cart.undo()
        self.cart.undo()
        self.assertTrue(self.cart.is_empty())
        self.assertFalse(self.cart.can_undo())

    def test_undo_redo_when_nothing_to_do(self):
        self.assertFalse(self.cart.undo())
        self.assertFalse(self.cart.redo())

    def test_new_action_after_undo_clears_redo(self):
        self.cart.add_item(PHO)
        self.cart.add_item(COM)
        self.cart.undo()
        self.assertTrue(self.cart.can_redo())
        self.assertEqual(len(self.cart.redo_stack), 1)

        self.cart.add_item(TRA)                  
        self.assertFalse(self.cart.can_redo())
        self.assertEqual(len(self.cart.redo_stack), 0)
        self.assertFalse(self.cart.redo())      
        self.assertEqual(item_ids(self.cart), ["M01", "M03"])

    def test_cart_data_after_restore(self):
        self.cart.add_item(PHO, 2, "ít hành")
        self.cart.update_quantity("M01", 5)
        self.cart.set_note("M01", "nhiều hành")
        self.assertEqual(self.cart.calculate_total(), 250000)

        self.cart.undo()                       
        row = self.cart.get_order_items()[0]
        self.assertEqual((row["quantity"], row["note"]), (5, "ít hành"))

        self.cart.undo()                         
        row = self.cart.get_order_items()[0]
        self.assertEqual(row["quantity"], 2)
        self.assertEqual(row["item_name"], "Phở bò")
        self.assertEqual(row["unit_price"], 50000)
        self.assertEqual(self.cart.calculate_total(), 100000)

        self.cart.redo()
        self.cart.redo()
        row = self.cart.get_order_items()[0]
        self.assertEqual((row["quantity"], row["note"]), (5, "nhiều hành"))
        self.assertEqual(self.cart.calculate_total(), 250000)

    def test_undo_remove_item(self):
        self.cart.add_item(PHO, 3)
        self.cart.remove_item("M01")
        self.assertTrue(self.cart.is_empty())
        self.cart.undo()
        self.assertEqual(self.cart.get_order_items()[0]["quantity"], 3)

    def test_snapshot_is_independent(self):
        self.cart.add_item(PHO, 2)
        self.cart.update_quantity("M01", 5)      
        self.cart._find("M01").quantity = 99    
        self.cart.undo()
        self.assertEqual(self.cart.get_order_items()[0]["quantity"], 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
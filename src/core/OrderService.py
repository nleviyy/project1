from datetime import datetime
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

CURRENT_DIR = Path(__file__).resolve().parent
SRC_DIR = CURRENT_DIR.parent
PROJECT_ROOT = SRC_DIR.parent

for path in [str(SRC_DIR), str(PROJECT_ROOT)]:
    if path not in sys.path:
        sys.path.append(path)

from src.models.Order import Order, OrderStatus
from src.models.OrderItem import OrderItem
from src.models.HashTable import HashTable
from src.core.JSONStorage import load_data, save_data
from src.core.paths import ORDERS_PATH, PAYMENTS_PATH
from src.core.sorting import merge_sort


class OrderService:
    """
    Service quản lý toàn bộ luồng nghiệp vụ liên quan đến Đơn hàng (Order).
    """

    def __init__(
        self,
        orders_file: Optional[Union[str, Path]] = None,
        payments_file: Optional[Union[str, Path]] = None,
        auto_load: bool = True,
        table_manager: Optional[Any] = None,
        kitchen_manager: Optional[Any] = None,
    ):
        self.orders_file: Path = Path(orders_file) if orders_file else ORDERS_PATH
        self.payments_file: Path = Path(payments_file) if payments_file else PAYMENTS_PATH
        self._orders: HashTable = HashTable()
        self.table_manager = table_manager
        self.kitchen_manager = kitchen_manager

        if auto_load:
            self.load_orders()

    def load_orders(self) -> bool:
        """Đọc danh sách đơn hàng từ file JSON vào bộ nhớ."""
        self._orders.clear()
        data = load_data(self.orders_file, default_data=[])
        if isinstance(data, list):
            for order_dict in data:
                if isinstance(order_dict, dict):
                    try:
                        order = Order.from_dict(order_dict)
                        self._orders.put(order.id, order)
                    except Exception as e:
                        print(f"[Cảnh báo OrderService] Bỏ qua đơn lỗi: {e}")
            return True
        return False

    def save_orders(self) -> bool:
        """Ghi toàn bộ đơn hàng hiện có ra file JSON nguyên tử."""
        data = [order.to_dict() for order in self._orders.values()]
        return save_data(self.orders_file, data)

    def generate_order_id(self, date_str: Optional[str] = None) -> str:
        """Sinh mã đơn hàng kế tiếp theo ngày: ORD-YYYYMMDD-XXX."""
        prefix_date = date_str or datetime.now().strftime("%Y%m%d")
        base_prefix = f"ORD-{prefix_date}-"

        max_seq = 0
        for order_id in self._orders.keys():
            if str(order_id).startswith(base_prefix):
                seq_str = str(order_id)[len(base_prefix):]
                if seq_str.isdigit():
                    val = int(seq_str)
                    if val > max_seq:
                        max_seq = val

        return f"{base_prefix}{max_seq + 1:03d}"

    def create_order(
        self,
        table_id: Union[int, str],
        items: Optional[List[Union[OrderItem, Dict[str, Any]]]] = None,
        notes: str = "",
        discount_amount: int = 0,
        custom_order_id: Optional[str] = None,
        check_existing_active: bool = False,
        table_manager: Optional[Any] = None,
    ) -> Order:
        """Tạo đơn hàng mới."""
        tm = table_manager or self.table_manager

        if check_existing_active and str(table_id).isdigit():
            active_order = self.get_active_order_by_table(table_id)
            if active_order:
                raise ValueError(
                    f"Bàn số {table_id} hiện đang có đơn hàng chưa hoàn thành ({active_order.id}). "
                    "Không thể tạo thêm đơn mới."
                )

        parsed_items: List[OrderItem] = []
        if items:
            for it in items:
                if isinstance(it, OrderItem):
                    parsed_items.append(it)
                elif isinstance(it, dict):
                    parsed_items.append(
                        OrderItem(
                            menu_item_id=it.get("menu_item_id", it.get("item_id", "M01")),
                            item_name=it.get("item_name", it.get("name", "Món")),
                            unit_price=int(it.get("unit_price", it.get("price", 0))),
                            quantity=int(it.get("quantity", it.get("sl", 1))),
                            note=it.get("note", ""),
                            prep_time=int(it.get("prep_time", 0) or 0),
                        )
                    )

        order_id = custom_order_id or self.generate_order_id()
        order = Order(
            id=order_id,
            table_id=table_id,
            status="PENDING",
            items=parsed_items,
            notes=notes,
            discount_amount=discount_amount,
        )

        self._orders.put(order.id, order)
        self.save_orders()

        if tm and not (isinstance(table_id, str) and table_id == "Mang về (Takeaway)"):
            try:
                t_id = int(table_id) if str(table_id).isdigit() else table_id
                tm.occupy_table(t_id, order.id)
            except Exception:
                pass

        return order

    def confirm_order(self, order_id: str, kitchen_manager: Optional[Any] = None) -> bool:
        """Xác nhận đơn hàng PENDING và chuyển vào bếp."""
        order = self.get_order_by_id(order_id)
        if not order:
            return False

        km = kitchen_manager or self.kitchen_manager
        if km:
            km.add_order(order)

        self.save_orders()
        return True

    def start_preparing_order(self, order_id: str) -> bool:
        """Bếp bắt đầu chế biến đơn: Chuyển trạng thái từ PENDING sang PREPARING."""
        order = self.get_order_by_id(order_id)
        if not order:
            raise KeyError(f"Không tìm thấy đơn hàng với mã: '{order_id}'")

        success = order.change_status(OrderStatus.PREPARING)
        if success:
            self.save_orders()
        return success

    def get_order_by_id(self, order_id: str) -> Optional[Order]:
        """Tìm đơn hàng theo mã đơn chính xác (O(1))."""
        if not order_id:
            return None
        return self._orders.get(str(order_id).strip())

    def get_order(self, order_id: str) -> Optional[Order]:
        """Bí danh cho get_order_by_id."""
        return self.get_order_by_id(order_id)

    def get_all_orders(self) -> List[Order]:
        """Lấy toàn bộ đơn hàng hiện có."""
        return list(self._orders.values())

    def get_orders_by_table(self, table_id: Union[int, str]) -> List[Order]:
        """Lấy tất cả các đơn hàng thuộc về một bàn."""
        t_str = str(table_id)
        return [order for order in self._orders.values() if str(order.table_id) == t_str]

    def get_active_order_by_table(self, table_id: Union[int, str]) -> Optional[Order]:
        """Tìm đơn đang hoạt động (PENDING, PREPARING, SERVED) của một bàn."""
        t_id_str = str(table_id)
        for order in self._orders.values():
            if str(order.table_id) == t_id_str and order.status in ("PENDING", "PREPARING", "SERVED"):
                return order
        return None

    def filter_orders_by_status(self, status: Union[str, OrderStatus]) -> List[Order]:
        """Lọc danh sách đơn hàng theo trạng thái."""
        target = status.value if isinstance(status, OrderStatus) else str(status).upper()
        return [order for order in self._orders.values() if order.status == target]

    def is_order_paid(self, order_id: str) -> bool:
        """
        Kiểm tra xem một đơn hàng đã được thanh toán hay chưa.
        1. Trạng thái của đơn hàng đã là 'COMPLETED'.
        2. Đã có bản ghi thanh toán thành công ('SUCCESS') trong file payments.json.
        """
        order = self.get_order_by_id(order_id)
        if order and order.status == OrderStatus.COMPLETED:
            return True

        payments_data = load_data(self.payments_file, default_data=[])
        if isinstance(payments_data, list):
            for pay in payments_data:
                if isinstance(pay, dict):
                    if pay.get("order_id") == order_id and pay.get("status") == "SUCCESS":
                        return True
        return False

    def can_checkout(self, order_id: str) -> Tuple[bool, str]:
        """
        Kiểm tra đơn hàng có đủ điều kiện thanh toán hay không.
        Chống thanh toán trùng lặp.
        """
        order = self.get_order_by_id(order_id)
        if not order:
            return False, f"Không tìm thấy đơn hàng mã '{order_id}'."

        if self.is_order_paid(order_id):
            return False, f"Đơn hàng '{order_id}' đã được thanh toán trước đó. Không thể thanh toán trùng!"

        if order.status == OrderStatus.CANCELLED:
            return False, f"Đơn hàng '{order_id}' đã bị hủy, không thể thanh toán."

        if len(order.items) == 0:
            return False, f"Đơn hàng '{order_id}' không có món ăn nào trong danh sách."

        if order.final_amount < 0:
            return False, f"Số tiền thanh toán ({order.final_amount} VNĐ) không hợp lệ."

        return True, "Đơn hàng hợp lệ, sẵn sàng để thanh toán."

    def cancel_order(
        self,
        order_id: str,
        reason: str = "",
        kitchen_manager: Optional[Any] = None,
        table_manager: Optional[Any] = None,
    ) -> bool:
        """Hủy đơn hàng và giải phóng bàn liên kết."""
        order = self.get_order_by_id(order_id)
        if not order:
            return False

        if order.status in ("COMPLETED", "CANCELLED"):
            raise ValueError(f"Không thể hủy đơn hàng đã ở trạng thái {order.status}.")

        order.status = "CANCELLED"
        order.updated_at = datetime.now().isoformat()
        if reason:
            order.notes = f"{order.notes} [Hủy: {reason}]".strip()

        km = kitchen_manager or self.kitchen_manager
        if km:
            try:
                km.cancel_order(order_id)
            except Exception:
                pass

        self.save_orders()

        tm = table_manager or self.table_manager
        if tm and order.table_id:
            try:
                t_id = int(order.table_id) if str(order.table_id).isdigit() else order.table_id
                tm.release_table(t_id, order_id=order.id)
            except Exception:
                pass

        return True

    def complete_order(self, order_id: str, force: bool = False) -> bool:
        """
        Đánh dấu đơn hàng là hoàn thành (COMPLETED) sau khi thanh toán thành công.
        """
        order = self.get_order_by_id(order_id)
        if not order:
            return False
        if order.status == OrderStatus.COMPLETED:
            return True

        if not force:
            payments_data = load_data(self.payments_file, default_data=[])
            has_successful_payment = isinstance(payments_data, list) and any(
                isinstance(payment, dict)
                and payment.get("order_id") == order_id
                and payment.get("status") == "SUCCESS"
                for payment in payments_data
            )
            if not has_successful_payment:
                raise ValueError(
                    f"Không thể hoàn thành đơn '{order_id}' khi chưa thanh toán SUCCESS."
                )
            if order.status != OrderStatus.SERVED:
                raise ValueError(
                    f"Chỉ có thể hoàn tất đơn '{order_id}' sau khi lên món (SERVED)."
                )

        order.status = "COMPLETED"
        order.updated_at = datetime.now().isoformat()
        self.save_orders()

        if self.table_manager and order.table_id:
            try:
                t_id = int(order.table_id) if str(order.table_id).isdigit() else order.table_id
                self.table_manager.release_table(t_id, order_id=order.id)
            except Exception:
                pass

        return True

    def set_kitchen_note(self, order_id: str, note: str) -> bool:
        """Cập nhật ghi chú của bếp cho đơn hàng."""
        order = self.get_order_by_id(order_id)
        if not order:
            return False
        order.kitchen_note = str(note)
        order.updated_at = datetime.now().isoformat()
        return self.save_orders()

    def prioritize_order(self, order_id: str, kitchen_manager: Optional[Any] = None) -> bool:
        """Đưa đơn hàng lên ưu tiên trong bếp."""
        order = self.get_order_by_id(order_id)
        if not order:
            return False
        order.priority_at = datetime.now().isoformat()
        order.updated_at = datetime.now().isoformat()

        km = kitchen_manager or self.kitchen_manager
        if km:
            km.prioritize_order(order_id)

        return self.save_orders()

    def _save_or_raise(self, order_id: str) -> None:
        if not self.save_orders():
            raise OSError(f"Không thể lưu trạng thái đơn hàng '{order_id}'.")

    def kitchen_start_next(self, kitchen_manager: Any) -> Optional[Order]:
        """Bắt đầu làm đơn kế tiếp trong bếp."""
        started = kitchen_manager.start_next_order()
        if started:
            oid = getattr(started, "id", None) or getattr(started, "order_id", None)
            order = self.get_order_by_id(oid)
            if order:
                order.status = "PREPARING"
                order.updated_at = datetime.now().isoformat()
            self._save_or_raise(str(oid))
        return started

    def kitchen_advance(self, kitchen_manager: Any) -> str:
        """Chuyển đơn đang chế biến sang bước kế tiếp (PREPARING -> SERVED) và lưu lại."""
        current = kitchen_manager.get_current_order()
        if current is None:
            raise ValueError("Bếp chưa làm đơn nào.")
        status = kitchen_manager.advance_status()
        oid = getattr(current, "id", None) or getattr(current, "order_id", None)
        order = self.get_order_by_id(oid)
        if order:
            order.status = status
            order.updated_at = datetime.now().isoformat()
        self._save_or_raise(str(oid))
        return status

    def kitchen_finish(self, kitchen_manager: Any) -> Order:
        """Kết thúc đơn đang chế biến sau khi đã lên món và lưu lại."""
        order = kitchen_manager.finish_current_order()
        oid = getattr(order, "id", None) or getattr(order, "order_id", None)
        o = self.get_order_by_id(oid)
        if o:
            o.status = getattr(order, "status", "SERVED")
            o.updated_at = datetime.now().isoformat()
        self._save_or_raise(str(oid))
        return order

    def sync_kitchen(self, kitchen_manager: Any) -> None:
        """Đồng bộ danh sách đơn hàng đang hoạt động vào bếp."""
        if kitchen_manager:
            kitchen_manager.restore_orders(self.get_all_orders())
            if not self.save_orders():
                raise OSError("Không thể lưu lại đơn hàng sau khi khôi phục bếp.")

    def add_item_to_order(self, order_id: str, item: OrderItem) -> bool:
        """Thêm món vào đơn hàng hiện có và tự động lưu."""
        order = self.get_order_by_id(order_id)
        if not order:
            raise KeyError(f"Không tìm thấy đơn hàng mã '{order_id}'.")

        order.add_item(item)
        return self.save_orders()

    def remove_item_from_order(self, order_id: str, menu_item_id: str) -> bool:
        """Xóa món khỏi đơn hàng hiện có và tự động lưu."""
        order = self.get_order_by_id(order_id)
        if not order:
            raise KeyError(f"Không tìm thấy đơn hàng mã '{order_id}'.")

        if order.remove_item(menu_item_id):
            return self.save_orders()
        return False

    def update_item_quantity_in_order(self, order_id: str, menu_item_id: str, quantity: int) -> bool:
        """Cập nhật số lượng món trong đơn và tự động lưu."""
        order = self.get_order_by_id(order_id)
        if not order:
            raise KeyError(f"Không tìm thấy đơn hàng mã '{order_id}'.")

        if order.update_item_quantity(menu_item_id, quantity):
            return self.save_orders()
        return False

    def place_order(
        self,
        table_id: Union[int, str],
        items: Union[List[OrderItem], List[Dict[str, Any]]],
        notes: str = "",
        *,
        table_manager: Optional[Any] = None,
        kitchen_manager: Optional[Any] = None,
    ) -> Order:
        """Luồng đặt món: kiểm tra bàn -> tạo đơn -> chiếm bàn -> đưa vào hàng đợi bếp.

        Nếu bước nào thất bại, đơn và bàn được hoàn lại để dữ liệu luôn nhất quán.
        """
        if not items:
            raise ValueError("Giỏ hàng trống, không thể tạo đơn.")
        tm = table_manager or self.table_manager
        dine_in = str(table_id).isdigit()
        if dine_in and tm is None:
            raise ValueError("Chưa kết nối quản lý bàn, không thể nhận bàn.")

        # 1. Kiểm tra bàn trước khi tạo đơn
        if dine_in:
            if not tm.is_table_available(int(table_id)):
                raise ValueError(f"Bàn số {table_id} hiện không còn trống.")
            if self.get_active_order_by_table(int(table_id)) is not None:
                raise ValueError(f"Bàn số {table_id} đang có đơn chưa hoàn thành.")

        # 2. Tạo đơn và chiếm bàn (create_order tự hoàn tác nếu lưu thất bại)
        order = self.create_order(
            table_id,
            items=items,
            notes=notes,
            check_existing_active=dine_in,
            table_manager=tm,
        )

        # 3. Đưa vào hàng đợi bếp; nếu thất bại thì hoàn tác đơn và bàn
        try:
            if not self.confirm_order(order.id, kitchen_manager=kitchen_manager):
                raise ValueError(f"Không thể xác nhận đơn hàng '{order.id}'.")
        except Exception:
            self._rollback_order(order, tm)
            raise
        return order

    def _rollback_order(self, order: Order, table_manager: Optional[Any]) -> None:
        """Hoàn tác đơn chưa được xác nhận và trả bàn về trống."""
        self._orders.pop(order.id, None)
        if table_manager is not None and str(order.table_id).isdigit():
            table_manager.release_table(int(order.table_id), order_id=order.id)
        self.save_orders()


from datetime import datetime, timedelta
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Đảm bảo import được cả khi chạy từ CLI, Streamlit hoặc Pytest
CURRENT_DIR = Path(__file__).resolve().parent
SRC_DIR = CURRENT_DIR.parent
PROJECT_ROOT = SRC_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"

for path in [str(SRC_DIR), str(PROJECT_ROOT)]:
    if path not in sys.path:
        sys.path.append(path)

try:
    from src.models.Order import Order, OrderStatus
    from src.models.OrderItem import OrderItem
    from src.models.JSONStorage import JSONStorage
    from src.models.HashTable import HashTable
except ImportError:
    try:
        from models.Order import Order, OrderStatus
        from models.OrderItem import OrderItem
        from models.JSONStorage import JSONStorage
        from models.HashTable import HashTable
    except ImportError:
        from ..models.Order import Order, OrderStatus
        from ..models.OrderItem import OrderItem
        from ..models.JSONStorage import JSONStorage
        from ..models.HashTable import HashTable


class OrderService:
    """
    Service quản lý toàn bộ luồng nghiệp vụ liên quan đến Đơn hàng (Order).
    Hiện thực hóa Sub Task 7.2:
    - Tạo đơn hàng mới (tự sinh mã chuẩn ORD-YYYYMMDD-XXX).
    - Xác nhận đơn (chuyển PENDING sang PREPARING).
    - Tìm kiếm đơn theo mã đơn / theo mã bàn (đơn đang hoạt động).
    - Kiểm tra đơn đã thanh toán để TRÁNH THANH TOÁN TRÙNG.
    - Quản lý trạng thái, tính tiền và đồng bộ dữ liệu với file data/orders.json.
    """

    def __init__(
        self,
        orders_file: Optional[str | Path] = None,
        payments_file: Optional[str | Path] = None,
        auto_load: bool = True,
        table_manager: Optional[Any] = None,
        kitchen_manager: Optional[Any] = None,
    ):
        self.orders_file: Path = Path(orders_file) if orders_file else (DATA_DIR / "orders.json")
        self.payments_file: Path = Path(payments_file) if payments_file else (DATA_DIR / "payments.json")
        self._orders: HashTable = HashTable()
        self.table_manager = table_manager
        self.kitchen_manager = kitchen_manager

        if auto_load:
            self.load_orders()

    # -------------------------------------------------------------
    # 1. Đọc và lưu trữ dữ liệu với JSONStorage
    # -------------------------------------------------------------
    def load_orders(self) -> bool:
        """Đọc danh sách đơn hàng từ file JSON vào bộ nhớ."""
        self._orders.clear()
        data = JSONStorage.load_data(str(self.orders_file), default_data=[])
        if isinstance(data, list):
            for order_dict in data:
                if isinstance(order_dict, dict):
                    try:
                        order = Order.from_dict(order_dict)
                        self._orders[order.id] = order
                    except Exception as e:
                        print(f"[Cảnh báo OrderService] Bỏ qua đơn lỗi: {e}")
            return True
        return False

    def save_orders(self) -> bool:
        """Ghi toàn bộ đơn hàng hiện có ra file JSON."""
        data = [order.to_dict() for order in self._orders.values()]
        return JSONStorage.save_data(str(self.orders_file), data)

    # -------------------------------------------------------------
    # 2. Sinh mã đơn hàng tự động (ORD-YYYYMMDD-XXX)
    # -------------------------------------------------------------
    def generate_order_id(self, date_str: Optional[str] = None) -> str:
        """
        Sinh mã đơn hàng kế tiếp theo ngày: ORD-YYYYMMDD-XXX (ví dụ: ORD-20261016-001).
        Đảm bảo tính duy nhất và không bị trùng lặp.
        """
        prefix_date = date_str or datetime.now().strftime("%Y%m%d")
        base_prefix = f"ORD-{prefix_date}-"

        # Tìm số thứ tự lớn nhất đã có trong ngày này
        max_seq = 0
        for order_id in self._orders.keys():
            if order_id.startswith(base_prefix):
                try:
                    seq_str = order_id[len(base_prefix):]
                    seq_num = int(seq_str)
                    if seq_num > max_seq:
                        max_seq = seq_num
                except ValueError:
                    continue

        new_seq = max_seq + 1
        return f"{base_prefix}{new_seq:03d}"

    # -------------------------------------------------------------
    # 3. Tạo đơn hàng (create_order)
    # -------------------------------------------------------------
    def create_order(
        self,
        table_id: int | str,
        items: Optional[List[OrderItem]] = None,
        notes: str = "",
        discount_amount: int = 0,
        custom_order_id: Optional[str] = None,
        check_existing_active: bool = False,
        table_manager: Optional[Any] = None,
    ) -> Order:
        """
        Tạo đơn hàng mới cho bàn ăn.
        :param table_id: Mã số bàn ăn
        :param items: Danh sách món ăn ban đầu (nếu có)
        :param notes: Ghi chú cho đơn hàng
        :param discount_amount: Số tiền chiết khấu / voucher ban đầu
        :param custom_order_id: Mã đơn chỉ định (nếu muốn đặt thủ công)
        :param check_existing_active: Nếu True, sẽ kiểm tra và không cho phép tạo thêm đơn nếu bàn đang có đơn chưa hoàn thành
        :return: Đối tượng Order vừa tạo
        """
        if check_existing_active and str(table_id).isdigit():
            active_order = self.get_active_order_by_table(table_id)
            if active_order:
                raise ValueError(
                    f"Bàn số {table_id} hiện đang có đơn hàng chưa hoàn thành ({active_order.id}). "
                    "Không thể tạo thêm đơn mới."
                )

        order_id = custom_order_id or self.generate_order_id()
        if order_id in self._orders:
            raise ValueError(f"Mã đơn hàng '{order_id}' đã tồn tại trong hệ thống.")

        now_iso = datetime.now().isoformat(timespec="seconds")
        order = Order(
            id=order_id,
            table_id=table_id,
            status=OrderStatus.PENDING,
            created_at=now_iso,
            updated_at=now_iso,
            items=items or [],
            discount_amount=discount_amount,
            notes=notes,
        )

        tm = table_manager or self.table_manager
        occupied_table = False
        if tm is not None and str(table_id).isdigit():
            if not tm.is_table_available(int(table_id)):
                raise ValueError(f"Bàn số {table_id} hiện không còn trống.")
            occupied_table = tm.occupy_table(int(table_id), order.id)
            if not occupied_table:
                raise ValueError(f"Không thể nhận bàn số {table_id}; vui lòng chọn bàn khác.")

        self._orders[order.id] = order
        if not self.save_orders():
            self._orders.pop(order.id, None)
            if occupied_table:
                tm.release_table(int(table_id))
            raise OSError(f"Không thể lưu đơn hàng '{order.id}'.")

        return order

    # -------------------------------------------------------------
    # 4. Xác nhận đơn (confirm_order) & Bắt đầu nấu (start_preparing_order)
    # -------------------------------------------------------------
    def confirm_order(
        self,
        order_id: str,
        kitchen_manager: Optional[Any] = None,
        auto_start_preparing: bool = False,
    ) -> bool:
        """
        Xác nhận đơn hàng: Đơn giữ trạng thái PENDING và được đưa vào hàng đợi bếp (Kitchen Queue).
        Theo chỉ đạo của Mentor: Khi xác nhận thành công, đơn giữ ở PENDING và đưa vào cuối Queue bếp;
        chỉ khi bếp lấy đơn ra chế biến thì mới chuyển sang PREPARING.
        :param order_id: Mã đơn hàng cần xác nhận.
        :param kitchen_manager: Quản lý bếp (tự động đẩy vào Queue).
        :param auto_start_preparing: Nếu True (cho phép chuyển thẳng sang PREPARING).
        :return: True nếu xác nhận thành công, False nếu thất bại.
        """
        order = self.get_order_by_id(order_id)
        if not order:
            raise KeyError(f"Không tìm thấy đơn hàng với mã: '{order_id}'")

        if order.status != OrderStatus.PENDING:
            return False

        if len(order.items) == 0:
            raise ValueError(f"Đơn hàng '{order_id}' chưa có món nào, không thể xác nhận.")

        km = kitchen_manager or self.kitchen_manager
        if km is not None:
            km.add_order(order)

        if auto_start_preparing:
            order.change_status(OrderStatus.PREPARING)

        if not self.save_orders():
            if km is not None:
                km.cancel_order(order_id)
            raise OSError(f"Không thể lưu trạng thái đơn hàng '{order_id}'.")
        return True

    def start_preparing_order(self, order_id: str) -> bool:
        """
        Bếp bắt đầu chế biến đơn: Chuyển trạng thái từ PENDING sang PREPARING.
        """
        order = self.get_order_by_id(order_id)
        if not order:
            raise KeyError(f"Không tìm thấy đơn hàng với mã: '{order_id}'")

        success = order.change_status(OrderStatus.PREPARING)
        if success:
            self.save_orders()
        return success

    # -------------------------------------------------------------
    # 5. Tìm kiếm đơn theo mã và theo bàn
    # -------------------------------------------------------------
    def get_order_by_id(self, order_id: str) -> Optional[Order]:
        """Tìm đơn hàng theo mã đơn chính xác."""
        if not order_id:
            return None
        return self._orders.get(str(order_id).strip())

    def get_orders_by_table(self, table_id: int) -> List[Order]:
        """Lấy tất cả các đơn hàng thuộc về một bàn (bao gồm cả đơn cũ và mới)."""
        return [order for order in self._orders.values() if order.table_id == int(table_id)]

    def get_active_order_by_table(self, table_id: int) -> Optional[Order]:
        """
        Tìm đơn hàng đang phục vụ tại bàn (trạng thái PENDING, PREPARING hoặc SERVED).
        Nếu có nhiều đơn, trả về đơn mới nhất.
        """
        latest: Optional[Order] = None
        for order in self._orders.values():
            if order.table_id == int(table_id) and order.is_active:
                if latest is None or str(order.created_at) > str(latest.created_at):
                    latest = order
        return latest

    def get_all_orders(self) -> List[Order]:
        """Lấy toàn bộ danh sách đơn hàng."""
        return list(self._orders.values())

    def filter_orders_by_status(self, status: str) -> List[Order]:
        """Lọc danh sách đơn hàng theo trạng thái."""
        target = status.upper().strip()
        return [order for order in self._orders.values() if order.status == target]

    # -------------------------------------------------------------
    # 6. Kiểm tra đơn đã thanh toán để tránh thanh toán trùng
    # -------------------------------------------------------------
    def is_order_paid(self, order_id: str) -> bool:
        """
        Kiểm tra xem một đơn hàng đã được thanh toán hay chưa.
        Nghiệp vụ kiểm tra kết hợp 2 nguồn để đảm bảo tuyệt đối an toàn:
        1. Trạng thái của đơn hàng đã là 'COMPLETED'.
        2. Đã có bản ghi thanh toán thành công ('SUCCESS') trong file data/payments.json.
        """
        order = self.get_order_by_id(order_id)
        if order and order.status == OrderStatus.COMPLETED:
            return True

        # Kiểm tra thêm trong nhật ký payments.json
        if self.payments_file.exists():
            payments_data = JSONStorage.load_data(str(self.payments_file), default_data=[])
            if isinstance(payments_data, list):
                for pay in payments_data:
                    if isinstance(pay, dict):
                        if pay.get("order_id") == order_id and pay.get("status") == "SUCCESS":
                            return True
        return False

    def can_checkout(self, order_id: str) -> Tuple[bool, str]:
        """
        Kiểm tra đơn hàng có đủ điều kiện thanh toán hay không.
        Giúp hệ thống TRÁNH THANH TOÁN TRÙNG và từ chối các đơn không hợp lệ.
        :return: (is_allowed: bool, reason_or_message: str)
        """
        order = self.get_order_by_id(order_id)
        if not order:
            return False, f"Không tìm thấy đơn hàng mã '{order_id}'."

        # Kiểm tra chống thanh toán trùng
        if self.is_order_paid(order_id):
            return False, f"Đơn hàng '{order_id}' đã được thanh toán trước đó. Không thể thanh toán trùng!"

        if order.status == OrderStatus.CANCELLED:
            return False, f"Đơn hàng '{order_id}' đã bị hủy, không thể thanh toán."

        if len(order.items) == 0:
            return False, f"Đơn hàng '{order_id}' không có món ăn nào trong danh sách."

        if order.final_amount < 0:
            return False, f"Số tiền thanh toán ({order.final_amount} VNĐ) không hợp lệ."

        return True, "Đơn hàng hợp lệ, sẵn sàng để thanh toán."

    # -------------------------------------------------------------
    # 7. Hoàn tất đơn hàng và các thao tác nghiệp vụ khác
    # -------------------------------------------------------------
    def complete_order(self, order_id: str, force: bool = False) -> bool:
        """
        Đánh dấu đơn hàng là hoàn thành (COMPLETED) sau khi thanh toán thành công.
        Có kiểm tra chống thanh toán trùng lặp.
        """
        order = self.get_order_by_id(order_id)
        if not order:
            return False
        if order.status == OrderStatus.COMPLETED:
            return True

        payments_data = JSONStorage.load_data(str(self.payments_file), default_data=[])
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

        # Chuyển trạng thái sang COMPLETED
        order.status = OrderStatus.COMPLETED
        order._touch()
        self.save_orders()

        # Giải phóng bàn nếu có TableManager
        if self.table_manager is not None:
            self.table_manager.release_table(order.table_id)

        return True

    def cancel_order(
        self,
        order_id: str,
        reason: str = "",
        kitchen_manager: Optional[Any] = None,
    ) -> bool:
        """
        Hủy một đơn hàng:
        Theo chỉ đạo của Mentor: Chỉ cho phép hủy đơn trước trạng thái SERVED.
        Nếu đơn đang chế biến trong bếp, cần xử lý việc hủy ở cả đơn hàng và hàng đợi bếp.
        """
        order = self.get_order_by_id(order_id)
        if not order:
            raise KeyError(f"Không tìm thấy đơn hàng mã '{order_id}'.")

        if order.status in (OrderStatus.SERVED, OrderStatus.COMPLETED):
            raise ValueError(
                f"Không thể hủy đơn hàng '{order_id}' vì đơn đang ở trạng thái {order.status} "
                "(theo quy tắc: chỉ được phép hủy trước khi lên món SERVED)."
            )

        if order.status == OrderStatus.CANCELLED:
            return True  # Đã hủy từ trước

        km = kitchen_manager or self.kitchen_manager
        if km is not None and hasattr(km, "cancel_order"):
            try:
                km.cancel_order(order_id)
            except Exception:
                pass

        if reason:
            order.notes = f"{order.notes} [Hủy: {reason}]".strip()

        order.status = OrderStatus.CANCELLED
        order._touch()
        self.save_orders()

        # Giải phóng bàn nếu có TableManager
        if self.table_manager is not None:
            self.table_manager.release_table(order.table_id)

        return True

    def prioritize_order(self, order_id: str, kitchen_manager: Optional[Any] = None) -> bool:
        """Bếp ưu tiên đơn đang chờ: đưa lên đầu hàng đợi và lưu thời điểm ưu tiên."""
        order = self.get_order_by_id(order_id)
        if not order:
            raise KeyError(f"Không tìm thấy đơn hàng mã '{order_id}'.")
        km = kitchen_manager or self.kitchen_manager
        if km is None:
            raise ValueError("Chưa kết nối bếp, không thể ưu tiên đơn.")
        km.prioritize_order(order_id)
        order.priority_at = datetime.now().isoformat()
        order._touch()
        if not self.save_orders():
            raise OSError(f"Không thể lưu ưu tiên của đơn '{order_id}'.")
        return True

    def set_kitchen_note(self, order_id: str, note: str) -> bool:
        """Lưu ghi chú của bếp cho đơn hàng."""
        order = self.get_order_by_id(order_id)
        if not order:
            raise KeyError(f"Không tìm thấy đơn hàng mã '{order_id}'.")
        clean = (note or "").strip()
        if len(clean) > 300:
            raise ValueError("Ghi chú bếp tối đa 300 ký tự.")
        order.kitchen_note = clean
        order._touch()
        if not self.save_orders():
            raise OSError(f"Không thể lưu ghi chú của đơn '{order_id}'.")
        return True

    def move_waiting_order(self, order_id: str, step: int, kitchen_manager: Optional[Any] = None) -> bool:
        """Đổi chỗ đơn đang chờ với đơn liền kề (step=-1 lên, +1 xuống) và lưu thứ tự mới."""
        if step not in (-1, 1):
            raise ValueError("Chỉ đổi chỗ 1 bậc mỗi lần.")
        km = kitchen_manager or self.kitchen_manager
        if km is None:
            raise ValueError("Chưa kết nối bếp, không thể chuyển thứ tự.")
        new_queue = km.move_waiting(order_id, step)
        base = datetime.now()
        total = len(new_queue)
        for index, order in enumerate(new_queue):
            order.priority_at = (base + timedelta(seconds=total - index)).isoformat()
        if not self.save_orders():
            raise OSError("Không thể lưu thứ tự hàng đợi.")
        return True

    def serve_order(self, order_id: str) -> bool:
        """Chuyển trạng thái đơn sang SERVED (đã phục vụ lên bàn)."""
        order = self.get_order_by_id(order_id)
        if not order:
            raise KeyError(f"Không tìm thấy đơn hàng mã '{order_id}'.")

        success = order.change_status(OrderStatus.SERVED)
        if success:
            self.save_orders()
        return success

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

    # -------------------------------------------------------------
    # 8. Đồng bộ với bếp: mọi thay đổi trạng thái bếp được lưu tại đây
    # -------------------------------------------------------------
    def place_order(
        self,
        table_id: int | str,
        items: List[OrderItem],
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
            table_manager.release_table(int(order.table_id))
        self.save_orders()

    def sync_kitchen(self, kitchen_manager: Any) -> None:
        """Dựng lại hàng đợi bếp từ đơn đã lưu. Gọi sau mỗi lần load_orders()."""
        kitchen_manager.restore_orders(self.get_all_orders())
        if not self.save_orders():
            raise OSError("Không thể lưu lại đơn hàng sau khi khôi phục bếp.")

    def _save_or_raise(self, order_id: str) -> None:
        if not self.save_orders():
            raise OSError(f"Không thể lưu trạng thái đơn hàng '{order_id}'.")

    def kitchen_start_next(self, kitchen_manager: Any) -> Optional[Order]:
        """Bếp lấy đơn đầu hàng đợi (PENDING -> PREPARING) và lưu lại."""
        order = kitchen_manager.start_next_order()
        if order is not None:
            self._save_or_raise(order.id)
        return order

    def kitchen_advance(self, kitchen_manager: Any) -> str:
        """Chuyển đơn đang chế biến sang bước kế tiếp (PREPARING -> SERVED) và lưu lại."""
        current = kitchen_manager.get_current_order()
        if current is None:
            raise ValueError("Bếp chưa làm đơn nào.")
        status = kitchen_manager.advance_status()
        self._save_or_raise(current.id)
        return status

    def kitchen_finish(self, kitchen_manager: Any) -> Order:
        """Kết thúc đơn đang chế biến sau khi đã lên món và lưu lại."""
        order = kitchen_manager.finish_current_order()
        self._save_or_raise(order.id)
        return order

    def update_item_quantity_in_order(self, order_id: str, menu_item_id: str, quantity: int) -> bool:
        """Cập nhật số lượng món trong đơn và tự động lưu."""
        order = self.get_order_by_id(order_id)
        if not order:
            raise KeyError(f"Không tìm thấy đơn hàng mã '{order_id}'.")

        if order.update_item_quantity(menu_item_id, quantity):
            return self.save_orders()
        return False
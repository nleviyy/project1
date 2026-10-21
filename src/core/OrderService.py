from datetime import datetime, timedelta
import os
from pathlib import Path
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

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
    from src.models.MenuCatalog import MenuCatalog
except ImportError:

    try:
        from models.Order import Order, OrderStatus
        from models.OrderItem import OrderItem
        from models.JSONStorage import JSONStorage
        from models.MenuCatalog import MenuCatalog
        from models.HashTable import HashTable
    except ImportError:
        from ..models.Order import Order, OrderStatus
        from ..models.OrderItem import OrderItem
        from ..models.JSONStorage import JSONStorage
        from ..models.MenuCatalog import MenuCatalog
        from ..models.HashTable import HashTable


class OrderService:
    """
    Service quản lý toàn bộ luồng nghiệp vụ liên quan đến Đơn hàng (Order).
    Hiện thực hóa Sub Task 7.2:
    - Tạo đơn hàng mới (tự sinh mã chuẩn ORD-YYYYMMDD-XXX).
    - Điều phối xác nhận đơn, chiếm bàn và xếp hàng bếp.
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
        if table_manager is None and orders_file is None:
            from src.core.TableManager import TableManager
            self.table_manager = TableManager()
        else:
            self.table_manager = table_manager

        if kitchen_manager is None and orders_file is None:
            from src.core.KitchenManager import KitchenManager
            self.kitchen_manager = KitchenManager()
        else:
            self.kitchen_manager = kitchen_manager

        if auto_load:
            self.load_orders()

    # -------------------------------------------------------------
    # 1. Đọc và lưu trữ dữ liệu với JSONStorage
    # -------------------------------------------------------------
    def load_orders(self) -> bool:
        """Đọc danh sách đơn hàng từ file JSON vào bộ nhớ."""
<<<<<<< Updated upstream
        data = JSONStorage.load_data(
            str(self.orders_file),
            default_data=[],
            strict=True,
=======
        data = JSONStorage.from_json_data(
            JSONStorage.load_data(
                str(self.orders_file),
                default_data=DoublyLinkedList(),
                strict=True,
            )
>>>>>>> Stashed changes
        )
        if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
            raise ValueError(f"Dữ liệu đơn hàng trong '{self.orders_file}' phải là danh sách object.")

        menu = MenuCatalog()
        menu_path = DATA_DIR / "menu.json"
        if menu_path.exists():
            menu_data = JSONStorage.load_data(
                str(menu_path),
                default_data=[],
                strict=True,
            )
<<<<<<< Updated upstream
            if not isinstance(menu_data, list):
                raise ValueError(f"Dữ liệu thực đơn trong '{menu_path}' phải là danh sách.")
            menu.load_from_dict(menu_data)
            if len(menu.get_all_items()) != len(menu_data):
                raise ValueError(
                    f"Thực đơn trong '{menu_path}' có món không hợp lệ hoặc mã bị trùng."
                )

        loaded_orders = {}
=======

        new_orders = HashTable()
        new_order_ids = DoublyLinkedList()
>>>>>>> Stashed changes
        for order_data in data:
            try:
                order = Order.from_dict(order_data)
<<<<<<< Updated upstream
            except ValueError as error:
                raise ValueError(
                    f"Dữ liệu đơn hàng '{order_data.get('id', 'không rõ mã')}' không hợp lệ."
                ) from error
            if order.id in loaded_orders:
                raise ValueError(f"Mã đơn '{order.id}' bị trùng trong '{self.orders_file}'.")
            for item in order.items:
                if not item.prep_time:
                    menu_item = menu.get_item(item.menu_item_id)
                    if menu_item is not None:
                        item.prep_time = menu_item.prep_time
            loaded_orders[order.id] = order
        self._orders = loaded_orders
=======
                for item in order.items:
                    if item.prep_time is None:
                        menu_item = menu.get_item(item.menu_item_id)
                        item.prep_time = (
                            menu_item.prep_time if menu_item is not None else 0
                        )
                if not new_orders.contains(order.id):
                    new_order_ids.add_last(order.id)
                new_orders.put(order.id, order)
            except (AttributeError, TypeError, ValueError) as error:
                print(f"[Cảnh báo OrderService] Bỏ qua đơn lỗi: {error}")

        self._orders = new_orders
        self._order_ids = new_order_ids
>>>>>>> Stashed changes
        return True


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
        items: Optional[List[Any]] = None,
        notes: str = "",
        discount_amount: int = 0,
        custom_order_id: Optional[str] = None,
        check_existing_active: bool = True,
        kitchen_manager: Optional[Any] = None,
        table_manager: Optional[Any] = None,
    ) -> Order:
        """
        Tạo, chiếm bàn và xếp đơn PENDING vào hàng đợi bếp qua nghiệp vụ điều phối chung (P0).

        Luồng xử lý:
        Chọn bàn → Chọn món → Xác nhận → Tạo Order → Chiếm bàn → Đưa vào Queue

        - Chỉ cho phép đặt món ở bàn AVAILABLE.
        - Không cho phép một bàn có hai đơn chưa hoàn thành (PENDING, PREPARING, SERVED).
        - Không tạo đơn nếu giỏ hàng rỗng hoặc có món không còn phục vụ.
        - Đơn sau khi xác nhận phải ở trạng thái PENDING (không chuyển sang PREPARING).
        - Nếu có bước thất bại, toàn bộ thao tác được rollback hoàn trả trạng thái ban đầu.
        """
        return self.place_order(
            table_id=table_id,
            items=items,
            notes=notes,
            discount_amount=discount_amount,
            custom_order_id=custom_order_id,
            kitchen_manager=kitchen_manager,
            table_manager=table_manager,
        )

    def place_order(
        self,
        table_id: int | str,
        items: Optional[List[Any]] = None,
        notes: str = "",
        discount_amount: int = 0,
        custom_order_id: Optional[str] = None,
        kitchen_manager: Optional[Any] = None,
        table_manager: Optional[Any] = None,
    ) -> Order:
        """Xác nhận đơn PENDING, chiếm bàn và đưa đơn vào Queue một cách nhất quán."""
        if not items:
            raise ValueError("Giỏ hàng đang trống, không thể tạo đơn hàng.")

        converted_items = []
        for item in items:
            if isinstance(item, dict):
                converted_items.append(OrderItem.from_dict(item))
            elif isinstance(item, OrderItem):
                converted_items.append(item)
            else:
                raise TypeError("Mỗi món đặt hàng phải là dict hoặc OrderItem.")
        items = converted_items

        table_id = int(table_id)
        is_takeaway = table_id == 0
        if not is_takeaway:
            if self.table_manager is None:
                raise RuntimeError("OrderService chưa được cấu hình TableManager.")
            if not self.table_manager.is_table_available(table_id):
                raise ValueError(
                    f"Bàn số {table_id} không ở trạng thái AVAILABLE hoặc không tồn tại."
                )
            active_order = self.get_active_order_by_table(table_id)
            if active_order:
                raise ValueError(
                    f"Bàn số {table_id} hiện có đơn chưa hoàn thành ({active_order.id})."
                )

        km = kitchen_manager or self.kitchen_manager
        if km is None:
            raise RuntimeError("OrderService chưa được cấu hình KitchenManager.")

        menu = MenuCatalog()
        menu_path = DATA_DIR / "menu.json"
        if menu_path.exists():
            menu_data = JSONStorage.load_data(
                str(menu_path),
                default_data=[],
                strict=True,
            )
            if not isinstance(menu_data, list):
                raise ValueError(f"Dữ liệu thực đơn trong '{menu_path}' phải là danh sách.")
            menu.load_from_dict(menu_data)
            if len(menu.get_all_items()) != len(menu_data):
                raise ValueError(f"Thực đơn trong '{menu_path}' có món không hợp lệ hoặc mã bị trùng.")

        for item in items:
            if not isinstance(item, OrderItem):
                raise TypeError("Mỗi món đặt hàng phải được chuyển thành OrderItem trước khi tạo đơn.")
            menu_item = menu.get_item(item.menu_item_id)
            if menu_item is None or not menu_item.is_available:
                raise ValueError(
                    f"Món '{item.item_name}' ({item.menu_item_id}) không còn phục vụ."
                )
            item.item_name = menu_item.name
            item.unit_price = menu_item.price
            item.subtotal = menu_item.price * item.quantity
            item.prep_time = menu_item.prep_time

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
            items=items,
            discount_amount=discount_amount,
            notes=notes,
        )

        tm = table_manager or self.table_manager
        if tm is not None:
            self.table_manager = tm
        table_occupied = False
        order_queued = False
        order_registered = False
        try:
            if not is_takeaway:
                if not self.table_manager.occupy_table(table_id, order.id):
                    raise ValueError(f"Không thể chiếm bàn số {table_id}; vui lòng chọn bàn khác.")
                table_occupied = True

            km.add_order(order)
            order_queued = True
            self._orders[order.id] = order
            order_registered = True
            if not self.save_orders():
                raise OSError("Không thể lưu đơn hàng.")
        except Exception as error:
            rollback_errors = []
            if order_queued:
                try:
                    km.cancel_order(order.id)
                except Exception as rollback_error:
                    rollback_errors.append(f"không thể gỡ đơn khỏi Queue: {rollback_error}")
            if order_registered:
                self._orders.pop(order.id, None)
            if table_occupied:
                try:
                    if not self.table_manager.release_table(table_id, order.id):
                        rollback_errors.append("không thể giải phóng bàn đã chiếm")
                except Exception as rollback_error:
                    rollback_errors.append(f"không thể giải phóng bàn: {rollback_error}")
            if rollback_errors:
                raise RuntimeError(
                    f"Tạo đơn thất bại ({error}); lỗi khi hoàn tác: "
                    + "; ".join(rollback_errors)
                ) from error
            raise

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
        Tương thích API cũ: xác minh đơn đã được place_order() xếp vào Queue.
        Việc tạo đơn, chiếm bàn và enqueue chỉ thực hiện qua place_order().
        :param order_id: Mã đơn hàng cần xác nhận.
        :param kitchen_manager: KitchenManager chứa đơn đã được xếp hàng.
        :param auto_start_preparing: Không còn hỗ trợ bắt đầu nấu khi xác nhận.
        :return: True nếu đơn vẫn đang PENDING và đã có trong Queue.
        """
        order = self.get_order_by_id(order_id)
        if not order:
            raise KeyError(f"Không tìm thấy đơn hàng với mã: '{order_id}'")

        if order.status != OrderStatus.PENDING:
            return False

        if len(order.items) == 0:
            raise ValueError(f"Đơn hàng '{order_id}' chưa có món nào, không thể xác nhận.")

        if auto_start_preparing:
            raise ValueError(
                "Xác nhận đơn không bắt đầu chế biến; bếp chỉ chuyển sang PREPARING "
                "khi nhận đơn từ Queue."
            )

        km = kitchen_manager or self.kitchen_manager
        if km is None:
            raise RuntimeError("OrderService chưa được cấu hình KitchenManager.")

        queued_orders = km.get_waiting_orders()
        current_order = km.get_current_order()
        if order not in queued_orders and current_order is not order:
            raise ValueError(
                f"Đơn '{order_id}' chưa được tạo qua luồng đặt món hoàn chỉnh."
            )
        return True

    def start_preparing_order(self, order_id: str) -> bool:
        """
        Bếp bắt đầu chế biến đơn: Chuyển trạng thái từ PENDING sang PREPARING.
        """
        order = self.get_order_by_id(order_id)
        if not order:
            raise KeyError(f"Không tìm thấy đơn hàng với mã: '{order_id}'")

        km = self.kitchen_manager
        if km is not None:
            current_order = km.get_current_order()
            if current_order is not None:
                if current_order.id != order.id:
                    return False
            else:
                waiting_orders = km.get_waiting_orders()
                if not waiting_orders or waiting_orders[0].id != order.id:
                    return False
                previous_updated_at = order.updated_at
                previous_started_at = order.preparing_started_at
                km.start_next_order()
                if self.save_orders():
                    return True
                if not km.restore_current_order_to_queue(order.id):
                    raise RuntimeError(
                        f"Không thể lưu trạng thái PREPARING hoặc khôi phục đơn "
                        f"'{order_id}' về Queue."
                    )
                order.updated_at = previous_updated_at
                order.preparing_started_at = previous_started_at
                raise OSError(
                    f"Không thể lưu trạng thái PREPARING cho đơn '{order_id}'."
                )

        success = order.change_status(OrderStatus.PREPARING)
        if success:
            if not self.save_orders():
                order.status = OrderStatus.PENDING
                order._touch()
                raise OSError(f"Không thể lưu trạng thái PREPARING cho đơn '{order_id}'.")
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
        Chỉ giao dịch SUCCESS được xem là bằng chứng thanh toán; trạng thái đơn
        hàng không thay thế cho bản ghi trong payments.json.
        """
        if self.payments_file.exists():
            payments_data = JSONStorage.load_data(
                str(self.payments_file),
                default_data=[],
                strict=True,
            )
            if not isinstance(payments_data, list) or any(
                not isinstance(payment, dict) for payment in payments_data
            ):
                raise ValueError(
                    f"Dữ liệu thanh toán trong '{self.payments_file}' không hợp lệ."
                )
            return any(
                payment.get("order_id") == order_id
                and payment.get("status") == "SUCCESS"
                for payment in payments_data
            )
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

        if order.status != OrderStatus.SERVED:
            return False, "Chỉ có thể thanh toán đơn ở trạng thái SERVED."

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

        payments_data = JSONStorage.load_data(
            str(self.payments_file),
            default_data=[],
            strict=True,
        )
        if not isinstance(payments_data, list) or any(
            not isinstance(payment, dict) for payment in payments_data
        ):
            raise ValueError(
                f"Dữ liệu thanh toán trong '{self.payments_file}' không hợp lệ."
            )
        has_successful_payment = any(
            isinstance(payment, dict)
            and payment.get("order_id") == order_id
            and payment.get("status") == "SUCCESS"
            for payment in payments_data
        )
        if not has_successful_payment:
            raise ValueError(
                f"Không thể hoàn thành đơn '{order_id}' khi chưa thanh toán SUCCESS."
            )
        if order.status == OrderStatus.COMPLETED:
            return True
        if order.status != OrderStatus.SERVED:
            raise ValueError(
                f"Chỉ có thể hoàn tất đơn '{order_id}' sau khi lên món (SERVED)."
            )

        # Chuyển trạng thái sang COMPLETED
        previous_updated_at = order.updated_at
        order.status = OrderStatus.COMPLETED
        order._touch()
        if not self.save_orders():
            order.status = OrderStatus.SERVED
            order.updated_at = previous_updated_at
            raise OSError(f"Không thể lưu trạng thái hoàn tất cho đơn '{order_id}'.")

        # Giải phóng bàn nếu có TableManager
        if (
            self.table_manager is not None
            and int(order.table_id) != 0
            and not self.table_manager.release_table(order.table_id, order.id)
        ):
            order.status = OrderStatus.SERVED
            order._touch()
            if not self.save_orders():
                raise RuntimeError(
                    f"Không thể giải phóng bàn hoặc khôi phục đơn '{order_id}' về SERVED."
                )
            raise OSError(
                f"Không thể giải phóng bàn cho đơn '{order_id}'; đơn vẫn ở trạng thái SERVED."
            )

        return True

    def cancel_order(
        self,
        order_id: str,
        reason: str = "",
        kitchen_manager: Optional[Any] = None,
    ) -> bool:
        """
        Hủy một đơn hàng:
        Chỉ cho phép hủy đơn đang PENDING; đơn đã bắt đầu chế biến không thể hủy.
        """
        order = self.get_order_by_id(order_id)
        if not order:
            raise KeyError(f"Không tìm thấy đơn hàng mã '{order_id}'.")

        if order.status != OrderStatus.PENDING:
            raise ValueError(
                f"Chỉ được hủy đơn ở trạng thái PENDING; đơn '{order_id}' "
                f"hiện ở trạng thái {order.status}."
            )

        km = kitchen_manager or self.kitchen_manager
        previous_notes = order.notes
        previous_updated_at = order.updated_at
        previous_started_at = order.preparing_started_at
        queue_position = None
        if km is not None:
            queue_position = next(
                (
                    index
                    for index, waiting_order in enumerate(km.get_waiting_orders())
                    if waiting_order.id == order_id
                ),
                None,
            )
            km.cancel_order(order_id)

        if reason:
            order.notes = f"{order.notes} [Hủy: {reason}]".strip()
        order.change_status(OrderStatus.CANCELLED)
        if not self.save_orders():
            order.status = OrderStatus.PENDING
            order.notes = previous_notes
            order.updated_at = previous_updated_at
            order.preparing_started_at = previous_started_at
            rollback_errors = []
            if km is not None:
                try:
                    if queue_position is None or not km.restore_order_to_queue(
                        order, queue_position
                    ):
                        rollback_errors.append("không thể khôi phục vị trí trong Queue")
                except Exception as rollback_error:
                    rollback_errors.append(f"không thể khôi phục Queue: {rollback_error}")
            if rollback_errors:
                raise RuntimeError(
                    "Không thể lưu thao tác hủy và lỗi khi hoàn tác: "
                    + "; ".join(rollback_errors)
                )
            raise OSError(f"Không thể lưu trạng thái hủy cho đơn '{order_id}'.")

        if self.table_manager is not None and int(order.table_id) != 0:
            if not self.table_manager.release_table(order.table_id, order.id):
                order.status = OrderStatus.PENDING
                order.notes = previous_notes
                order.updated_at = previous_updated_at
                order.preparing_started_at = previous_started_at
                rollback_errors = []
                if km is not None:
                    try:
                        if queue_position is None or not km.restore_order_to_queue(
                            order, queue_position
                        ):
                            rollback_errors.append("không thể khôi phục vị trí trong Queue")
                    except Exception as rollback_error:
                        rollback_errors.append(f"không thể khôi phục Queue: {rollback_error}")
                if not self.save_orders():
                    rollback_errors.append("không thể khôi phục đơn hàng đã lưu")
                if rollback_errors:
                    raise RuntimeError(
                        "Không thể giải phóng bàn và lỗi khi hoàn tác: "
                        + "; ".join(rollback_errors)
                    )
                raise OSError(
                    f"Không thể giải phóng bàn cho đơn '{order_id}'; đơn đã được khôi phục."
                )

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

        kitchen = self.kitchen_manager
        if kitchen is not None:
            if kitchen.get_current_order() is not order:
                raise ValueError("Chỉ có thể lên món cho đơn đang được bếp chế biến.")
            previous_started_at = order.preparing_started_at
            previous_updated_at = order.updated_at
            previous_status = order.status
            if order.status == OrderStatus.PREPARING:
                kitchen.advance_status()
            elif order.status != OrderStatus.SERVED:
                raise ValueError(
                    f"Không thể lên món khi đơn đang ở trạng thái '{order.status}'."
                )
            if not self.save_orders():
                order.status = previous_status
                order.preparing_started_at = previous_started_at
                order.updated_at = previous_updated_at
                raise OSError(f"Không thể lưu trạng thái SERVED cho đơn '{order_id}'.")
            kitchen.finish_current_order()
            return True

        previous_started_at = order.preparing_started_at
        previous_updated_at = order.updated_at
        previous_status = order.status
        success = order.change_status(OrderStatus.SERVED)
        if success:
            if not self.save_orders():
                order.status = previous_status
                order.preparing_started_at = previous_started_at
                order.updated_at = previous_updated_at
                raise OSError(f"Không thể lưu trạng thái SERVED cho đơn '{order_id}'.")
        return success

    def _save_order_mutation(
        self,
        order: Order,
        mutation: Callable[[], bool],
    ) -> bool:
        previous_order = order.model_copy(deep=True)
        try:
            if not mutation():
                return False
            if self.save_orders():
                return True
        except Exception:
            self._restore_order(order, previous_order)
            raise

        self._restore_order(order, previous_order)
        return False

    @staticmethod
    def _restore_order(order: Order, snapshot: Order) -> None:
        for field_name in type(snapshot).model_fields:
            setattr(order, field_name, getattr(snapshot, field_name))

    def add_item_to_order(self, order_id: str, item: OrderItem) -> bool:
        """Thêm món vào đơn hàng hiện có và tự động lưu."""
        order = self.get_order_by_id(order_id)
        if not order:
            raise KeyError(f"Không tìm thấy đơn hàng mã '{order_id}'.")

        return self._save_order_mutation(order, lambda: order.add_item(item))

    def remove_item_from_order(self, order_id: str, menu_item_id: str) -> bool:
        """Xóa món khỏi đơn hàng hiện có và tự động lưu."""
        order = self.get_order_by_id(order_id)
        if not order:
            raise KeyError(f"Không tìm thấy đơn hàng mã '{order_id}'.")

        return self._save_order_mutation(
            order,
            lambda: order.remove_item(menu_item_id),
        )

    # -------------------------------------------------------------
    # 8. Đồng bộ với bếp: mọi thay đổi trạng thái bếp được lưu tại đây
    # -------------------------------------------------------------

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

        return self._save_order_mutation(
            order,
            lambda: order.update_item_quantity(menu_item_id, quantity),
        )

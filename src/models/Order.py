from datetime import datetime
import os
import sys
from typing import Any, Dict, List, Optional, Set

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

try:
    from .OrderItem import OrderItem
except ImportError:
    from OrderItem import OrderItem


class OrderStatus:
    """Định nghĩa các hằng số trạng thái đơn hàng theo Data Contract."""
    PENDING = "PENDING"        # Chờ xác nhận / Chờ bếp
    PREPARING = "PREPARING"    # Đang chế biến
    SERVED = "SERVED"          # Đã lên món
    COMPLETED = "COMPLETED"    # Đã hoàn thành (đã thanh toán)
    CANCELLED = "CANCELLED"    # Đã hủy

    ALL = {PENDING, PREPARING, SERVED, COMPLETED, CANCELLED}
    TERMINAL = {COMPLETED, CANCELLED}

    LABELS = {
        PENDING: "Chờ xác nhận",
        PREPARING: "Đang chế biến",
        SERVED: "Đã lên món",
        COMPLETED: "Hoàn thành",
        CANCELLED: "Đã hủy",
    }

    VALID_NEXT = {
        PENDING: [PREPARING, CANCELLED],
        PREPARING: [SERVED, CANCELLED],
        SERVED: [COMPLETED],
        COMPLETED: [],
        CANCELLED: [],
    }

    @staticmethod
    def get_label(status: str) -> str:
        return OrderStatus.LABELS.get(status, str(status))


# Bảng quy tắc chuyển đổi trạng thái hợp lệ (Finite State Machine)
# Theo chỉ đạo của Mentor: Chỉ cho phép hủy đơn trước trạng thái SERVED
VALID_STATUS_TRANSITIONS: Dict[str, Set[str]] = {
    OrderStatus.PENDING: {OrderStatus.PREPARING, OrderStatus.CANCELLED},
    OrderStatus.PREPARING: {OrderStatus.SERVED, OrderStatus.CANCELLED},
    OrderStatus.SERVED: {OrderStatus.COMPLETED},  # Đã lên món thì không được hủy trực tiếp
    OrderStatus.COMPLETED: set(),  # Trạng thái kết thúc, không thể đổi tiếp
    OrderStatus.CANCELLED: set(),  # Đã hủy, không thể đổi tiếp
}


class Order:
    """
    Class quản lý thông tin và nghiệp vụ của một Đơn hàng (Order).
    Hiện thực hóa Sub Task 7.1 & kiến trúc thống nhất theo phản hồi Mentor:
    - Quản lý món trong đơn, thêm/xóa món, cập nhật số lượng, ghi chú.
    - Tính tổng tiền VNĐ (kiểu int).
    - Kiểm soát nghiêm ngặt luồng trạng thái (FSM): chỉ cho phép chỉnh sửa món khi ở PENDING.
    - Hỗ trợ đầy đủ interface cho KitchenManager (order_id, prep_time, set_status).
    """

    def __init__(
        self,
        id: Optional[str] = None,
        table_id: int = 1,
        status: str = OrderStatus.PENDING,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        items: Optional[List[OrderItem]] = None,
        discount_amount: int = 0,
        notes: str = "",
        prep_time: int = 0,
        order_id: Optional[str] = None,
    ):
        actual_id = str(id if id is not None else (order_id if order_id is not None else "")).strip()
        self.id: str = actual_id
        self.table_id: int = int(table_id)
        self.status: str = status.upper().strip() if status else OrderStatus.PENDING
        
        if self.status not in OrderStatus.ALL:
            raise ValueError(f"Trạng thái đơn hàng '{self.status}' không hợp lệ. Phải thuộc {OrderStatus.ALL}")

        now_str = datetime.now().isoformat(timespec="seconds")
        self.created_at: str = created_at or now_str
        self.updated_at: str = updated_at or self.created_at
        
        self.items: List[OrderItem] = items or []
        self.discount_amount: int = max(0, int(discount_amount))
        self.notes: str = (notes or "").strip()
        self._prep_time: int = max(0, int(prep_time))

        self.total_amount: int = 0
        self.final_amount: int = 0
        self.calculate_total()

    # -------------------------------------------------------------
    # Helper Properties & Aliases
    # -------------------------------------------------------------
    @property
    def order_id(self) -> str:
        """Alias cho id để tương thích đồng bộ với KitchenManager."""
        return self.id

    @order_id.setter
    def order_id(self, val: str) -> None:
        self.id = str(val).strip()

    @property
    def prep_time(self) -> int:
        return self._prep_time

    @prep_time.setter
    def prep_time(self, val: int) -> None:
        self._prep_time = max(0, int(val))

    def calculate_prep_time(self) -> int:
        """
        Tính thời gian chế biến ước tính (phút).
        Nếu có prep_time cấu hình riêng thì ưu tiên, nếu không tính theo số lượng món.
        """
        if self._prep_time > 0:
            return self._prep_time
        total_items = sum(item.quantity for item in self.items)
        return max(5, total_items * 3) if total_items > 0 else 0

    def set_status(self, new_status: str) -> None:
        """
        Chuyển trạng thái đơn với ngoại lệ ValueError nếu không hợp lệ
        (Đảm bảo interface tương thích chuẩn với KitchenManager).
        """
        target = new_status.upper().strip()
        if not self.can_transition_to(target):
            current_lbl = OrderStatus.get_label(self.status)
            target_lbl = OrderStatus.get_label(target)
            raise ValueError(f"Không thể chuyển từ '{current_lbl}' sang '{target_lbl}'")
        self.change_status(target)

    # -------------------------------------------------------------
    # Helper Properties kiểm tra trạng thái đơn
    # -------------------------------------------------------------
    @property
    def is_pending(self) -> bool:
        return self.status == OrderStatus.PENDING

    @property
    def is_preparing(self) -> bool:
        return self.status == OrderStatus.PREPARING

    @property
    def is_served(self) -> bool:
        return self.status == OrderStatus.SERVED

    @property
    def is_completed(self) -> bool:
        return self.status == OrderStatus.COMPLETED

    @property
    def is_cancelled(self) -> bool:
        return self.status == OrderStatus.CANCELLED

    @property
    def is_active(self) -> bool:
        """Đơn hàng đang hoạt động (chưa hoàn thành và chưa bị hủy)."""
        return self.status not in OrderStatus.TERMINAL

    @property
    def can_modify(self) -> bool:
        """
        Kiểm tra đơn hàng có được phép chỉnh sửa món hay không.
        Theo chỉ đạo của Mentor: Chỉ cho phép chỉnh sửa nội dung đơn khi còn ở PENDING.
        """
        return self.status == OrderStatus.PENDING

    # -------------------------------------------------------------
    # Quản lý món trong đơn (Thêm, Xóa, Cập nhật số lượng, Ghi chú)
    # -------------------------------------------------------------
    def add_item(self, item: OrderItem, merge_same_item: bool = True) -> OrderItem:
        """
        Thêm món vào đơn hàng.
        :param item: Đối tượng OrderItem cần thêm.
        :param merge_same_item: Nếu món đã tồn tại (cùng mã món và cùng ghi chú) thì cộng dồn số lượng.
        """
        if not self.can_modify:
            raise ValueError(f"Không thể thêm món vào đơn '{self.id}' vì đơn đang ở trạng thái {self.status}.")

        if not isinstance(item, OrderItem):
            raise TypeError("Đối tượng thêm vào phải thuộc lớp OrderItem.")

        if merge_same_item:
            for existing in self.items:
                if existing.menu_item_id == item.menu_item_id and existing.note == item.note:
                    existing.update_quantity(existing.quantity + item.quantity)
                    self._on_items_changed()
                    return existing

        self.items.append(item)
        self._on_items_changed()
        return item

    def remove_item(self, menu_item_id: str) -> bool:
        """
        Xóa món khỏi đơn hàng theo mã món (menu_item_id).
        Nếu có nhiều dòng cùng menu_item_id, xóa tất cả các dòng đó.
        """
        if not self.can_modify:
            raise ValueError(f"Không thể xóa món trong đơn '{self.id}' vì đơn đang ở trạng thái {self.status}.")

        initial_len = len(self.items)
        self.items = [item for item in self.items if item.menu_item_id != menu_item_id]
        
        if len(self.items) != initial_len:
            self._on_items_changed()
            return True
        return False

    def remove_item_at(self, index: int) -> bool:
        """
        Xóa món tại vị trí index cụ thể trong danh sách items.
        """
        if not self.can_modify:
            raise ValueError(f"Không thể xóa món trong đơn '{self.id}' vì đơn đang ở trạng thái {self.status}.")

        if 0 <= index < len(self.items):
            self.items.pop(index)
            self._on_items_changed()
            return True
        return False

    def update_item_quantity(self, menu_item_id: str, new_quantity: int) -> bool:
        """
        Cập nhật số lượng của món ăn trong đơn hàng.
        Nếu new_quantity <= 0 thì tự động xóa món.
        """
        if not self.can_modify:
            raise ValueError(f"Không thể cập nhật món trong đơn '{self.id}' vì đơn đang ở trạng thái {self.status}.")

        if new_quantity <= 0:
            return self.remove_item(menu_item_id)

        found = False
        for item in self.items:
            if item.menu_item_id == menu_item_id:
                item.update_quantity(new_quantity)
                found = True

        if found:
            self._on_items_changed()
            return True
        return False

    def update_item_note(self, menu_item_id: str, new_note: str) -> bool:
        """
        Cập nhật ghi chú riêng cho món trong đơn.
        """
        if not self.can_modify:
            raise ValueError(f"Không thể sửa ghi chú món trong đơn '{self.id}' vì đơn đang ở trạng thái {self.status}.")

        found = False
        for item in self.items:
            if item.menu_item_id == menu_item_id:
                item.update_note(new_note)
                found = True

        if found:
            self._touch()
            return True
        return False

    def set_notes(self, notes: str) -> None:
        """Cập nhật ghi chú chung của đơn hàng."""
        self.notes = (notes or "").strip()
        self._touch()

    def set_discount(self, discount_amount: int) -> None:
        """
        Áp dụng tiền giảm giá / voucher cho đơn hàng và tính lại final_amount.
        """
        if not self.can_modify:
            raise ValueError(f"Không thể áp dụng giảm giá cho đơn '{self.id}' vì đơn đang ở trạng thái {self.status}.")
        
        self.discount_amount = max(0, int(discount_amount))
        self.calculate_total()
        self._touch()

    # -------------------------------------------------------------
    # Tính toán tổng tiền
    # -------------------------------------------------------------
    def calculate_total(self) -> int:
        """
        Tính tổng tiền món (total_amount) và số tiền thực trả sau giảm giá (final_amount).
        :return: final_amount (VNĐ)
        """
        self.total_amount = sum(int(item.subtotal) for item in self.items)
        self.final_amount = max(0, self.total_amount - self.discount_amount)
        return self.final_amount

    def _on_items_changed(self) -> None:
        """Nghiệp vụ nội bộ: Gọi khi danh sách món thay đổi."""
        self.calculate_total()
        self._touch()

    def _touch(self) -> None:
        """Cập nhật thời gian updated_at thành thời điểm hiện tại."""
        self.updated_at = datetime.now().isoformat(timespec="seconds")

    # -------------------------------------------------------------
    # Kiểm tra và chuyển đổi trạng thái đơn
    # -------------------------------------------------------------
    def can_transition_to(self, new_status: str) -> bool:
        """
        Kiểm tra xem đơn hàng có thể chuyển sang trạng thái mới hay không.
        Tuân thủ luồng:
        - PENDING -> PREPARING, CANCELLED
        - PREPARING -> SERVED, CANCELLED
        - SERVED -> COMPLETED, CANCELLED
        """
        target = new_status.upper().strip()
        if target not in OrderStatus.ALL:
            return False
        
        allowed_next = VALID_STATUS_TRANSITIONS.get(self.status, set())
        return target in allowed_next

    def change_status(self, new_status: str, force: bool = False) -> bool:
        """
        Thực hiện chuyển đổi trạng thái đơn hàng.
        :param new_status: Trạng thái đích (PENDING, PREPARING, SERVED, COMPLETED, CANCELLED).
        :param force: Bỏ qua kiểm tra chuyển tiếp (dùng khi khôi phục dữ liệu đặc biệt).
        :return: True nếu chuyển đổi thành công, False nếu không hợp lệ.
        """
        target = new_status.upper().strip()
        if not force and not self.can_transition_to(target):
            return False

        self.status = target
        self._touch()
        return True

    # -------------------------------------------------------------
    # Serialization (to_dict / from_dict)
    # -------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        """
        Chuyển đổi đối tượng Order thành dictionary chuẩn hóa theo Data Contract JSON.
        """
        self.calculate_total()
        return {
            "id": self.id,
            "table_id": self.table_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status,
            "items": [item.to_dict() for item in self.items],
            "total_amount": int(self.total_amount),
            "discount_amount": int(self.discount_amount),
            "final_amount": int(self.final_amount),
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Order":
        """
        Khởi tạo đối tượng Order từ dictionary đọc từ file data/orders.json.
        """
        if not isinstance(data, dict):
            raise TypeError("Dữ liệu đầu vào phải là một dictionary.")

        raw_items = data.get("items", []) or []
        items_list = [OrderItem.from_dict(item_data) for item_data in raw_items if isinstance(item_data, dict)]

        order = cls(
            id=str(data.get("id", "")),
            table_id=int(data.get("table_id", 0)),
            status=str(data.get("status", OrderStatus.PENDING)),
            created_at=str(data.get("created_at", "")),
            updated_at=str(data.get("updated_at", "")),
            items=items_list,
            discount_amount=int(data.get("discount_amount", 0)),
            notes=str(data.get("notes", "") or ""),
        )
        return order

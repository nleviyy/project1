"""
TableManager: Quản lý danh sách bàn và điều phối trạng thái bàn ăn (P1).
- Quản lý trạng thái bàn ăn từ data/tables.json.
- Kiểm tra bàn trống trước khi nhận đơn.
- Chiếm bàn khi có đơn hoạt động và giải phóng bàn khi đơn hoàn thành hoặc bị hủy.
"""
from pathlib import Path
from typing import List, Optional, Union

from src.core.JSONStorage import save_data, load_data, CorruptDataError
from src.core.paths import TABLES_PATH
from src.models.HashTable import HashTable
from src.models.Table import Table


class TableDataError(Exception):
    """Ngoại lệ khi đọc hoặc nạp dữ liệu tables.json thất bại."""
    pass


class TableManager:
    def __init__(self, tables_file: Optional[Union[str, Path]] = None, auto_load: bool = True):
        self.tables_file = Path(tables_file) if tables_file else TABLES_PATH
        self._tables: HashTable = HashTable()
        self._load_failed: bool = False

        if auto_load:
            self.load_tables()

    def load_tables(self) -> None:
        """
        Đọc danh sách bàn từ file tables.json.
        - File không tồn tại: khởi tạo danh sách rỗng.
        - File tồn tại nhưng hỏng hoặc không phải list hợp lệ: ném TableDataError rõ ràng,
          KHÔNG gán dict rỗng, đánh dấu _load_failed = True.
        """
        if not self.tables_file.exists():
            self._tables = HashTable()
            self._load_failed = False
            return

        try:
            data = load_data(self.tables_file, default_data=None)
            if not isinstance(data, list):
                raise TableDataError(f"Dữ liệu trong {self.tables_file} phải là danh sách bàn (list).")

            new_tables = HashTable()
            for item in data:
                if not isinstance(item, dict) or "id" not in item:
                    raise TableDataError(f"Phần tử bàn không hợp lệ trong {self.tables_file}: {item}")
                table = Table.from_dict(item)
                new_tables.put(int(table.id), table)

            self._tables = new_tables
            self._load_failed = False
        except (CorruptDataError, TableDataError) as e:
            self._load_failed = True
            raise TableDataError(f"Không thể đọc file bàn ăn: {e}") from e
        except Exception as e:
            self._load_failed = True
            raise TableDataError(f"Lỗi không xác định khi nạp bàn ăn: {e}") from e

    def save_tables(self) -> None:
        """Lưu danh sách bàn vào file tables.json. Ném TableDataError nếu nạp thất bại."""
        if self._load_failed:
            raise TableDataError("Không thể lưu tables.json vì trạng thái nạp dữ liệu trước đó đã thất bại.")

        try:
            data = [table.to_dict() for table in self._tables.values()]
            save_data(self.tables_file, data)
        except OSError as e:
            raise OSError(f"Không thể lưu file tables.json: {e}") from e

    def get_all_tables(self) -> List[Table]:
        """Lấy toàn bộ danh sách bàn."""
        return list(self._tables.values())

    def get_table(self, table_id: int) -> Optional[Table]:
        """Tìm bàn theo mã bàn."""
        return self._tables.get(int(table_id))

    def get_available_tables(self) -> List[Table]:
        """Lấy danh sách các bàn đang trống sẵn sàng đón khách."""
        return [table for table in self._tables.values() if table.is_available]

    def is_table_available(self, table_id: int) -> bool:
        """Kiểm tra bàn có đang trống không."""
        table = self.get_table(table_id)
        return table.is_available if table else False

    def occupy_table(self, table_id: int, order_id: str) -> bool:
        """
        Chiếm bàn khi đơn hàng được tạo.
        Rollback trạng thái bộ nhớ nếu lưu file thất bại.
        """
        table = self.get_table(table_id)
        if not table:
            return False

        if not table.is_available and table.current_order_id != str(order_id):
            return False

        prev_status, prev_order_id = table.status, table.current_order_id
        table.occupy(order_id)
        try:
            self.save_tables()
        except OSError:
            table.status, table.current_order_id = prev_status, prev_order_id
            raise
        return True

    def release_table(self, table_id: int, order_id: Optional[str] = None) -> bool:
        """
        Giải phóng bàn khi đơn hàng thanh toán xong hoặc bị hủy.
        Nếu truyền order_id thì chỉ giải phóng khi current_order_id khớp; không khớp thì trả False.
        """
        table = self.get_table(table_id)
        if not table:
            return False

        if order_id is not None:
            if str(table.current_order_id) != str(order_id):
                return False

        prev_status, prev_order_id = table.status, table.current_order_id
        table.release()
        try:
            self.save_tables()
        except OSError:
            table.status, table.current_order_id = prev_status, prev_order_id
            raise
        return True

    def reserve_table(self, table_id: int) -> bool:
        """Đặt trước bàn (chuyển sang RESERVED). Rollback nếu lưu file thất bại."""
        table = self.get_table(table_id)
        if not table or not table.is_available:
            return False

        prev_status, prev_order_id = table.status, table.current_order_id
        table.reserve()
        try:
            self.save_tables()
        except OSError:
            table.status, table.current_order_id = prev_status, prev_order_id
            raise
        return True

    def vacate_table(self, table_id: int) -> bool:
        """Giải phóng bàn từ trạng thái RESERVED về AVAILABLE. Rollback nếu lưu thất bại."""
        table = self.get_table(table_id)
        if not table:
            return False

        prev_status, prev_order_id = table.status, table.current_order_id
        table.vacate()
        try:
            self.save_tables()
        except OSError:
            table.status, table.current_order_id = prev_status, prev_order_id
            raise
        return True

    def add_table(self, table: Table) -> bool:
        """Thêm bàn mới vào hệ thống và lưu vào tables.json. Rollback nếu lưu thất bại."""
        if not isinstance(table, Table):
            raise TypeError("Đối tượng thêm vào phải thuộc lớp Table.")
        t_id = int(table.id)
        if t_id in self._tables:
            return False

        self._tables.put(t_id, table)
        try:
            self.save_tables()
        except OSError:
            self._tables.remove(t_id)
            raise
        return True

    def remove_table(self, table_id: int) -> bool:
        """Xóa bàn khỏi hệ thống nếu bàn không bận (OCCUPIED). Rollback nếu lưu thất bại."""
        t_id = int(table_id)
        table = self.get_table(t_id)
        if not table or table.status == "OCCUPIED":
            return False

        self._tables.remove(t_id)
        try:
            self.save_tables()
        except OSError:
            self._tables.put(t_id, table)
            raise
        return True

    def update_table(
        self,
        table_id: int,
        name: Optional[str] = None,
        capacity: Optional[int] = None,
    ) -> bool:
        """
        Cập nhật tên và sức chứa của bàn ăn.
        Sức chứa không hợp lệ phải ném ValueError. Rollback nếu lưu thất bại.
        """
        table = self.get_table(table_id)
        if not table:
            return False

        if capacity is not None:
            try:
                cap_val = int(capacity)
            except (ValueError, TypeError) as err:
                raise ValueError(f"Sức chứa bàn không hợp lệ: {capacity}") from err
            if cap_val <= 0:
                raise ValueError("Sức chứa bàn phải lớn hơn 0.")
        else:
            cap_val = None

        prev_name = table.name
        prev_cap = table.capacity

        if name:
            clean_name = str(name).strip()
            if not clean_name:
                raise ValueError("Tên bàn ăn không được để trống.")
            table.name = clean_name
        if cap_val is not None:
            table.capacity = cap_val

        try:
            self.save_tables()
        except OSError:
            table.name = prev_name
            table.capacity = prev_cap
            raise
        return True

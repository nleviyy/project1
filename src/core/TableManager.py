"""
TableManager: Quản lý danh sách bàn và điều phối trạng thái bàn ăn (P1).
Hiện thực hóa yêu cầu của Mentor trong mục 2.2 và B:
- Quản lý trạng thái bàn ăn từ data/tables.json.
- Kiểm tra bàn trống trước khi nhận đơn.
- Chiếm bàn khi có đơn hoạt động và giải phóng bàn khi đơn hoàn thành hoặc bị hủy.
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from src.models.Table import Table, TableStatus


class TableManager:
    def __init__(self, tables_file: Optional[str] = None, auto_load: bool = True):
        if tables_file:
            self.tables_file = Path(tables_file)
        else:
            # Tìm đường dẫn mặc định tới data/tables.json
            current_dir = Path(__file__).resolve().parent
            project_root = current_dir.parent.parent
            self.tables_file = project_root / "data" / "tables.json"

        self._tables: Dict[int, Table] = {}
        if auto_load:
            self.load_tables()

    def load_tables(self) -> None:
        """Đọc danh sách bàn từ file tables.json."""
        if not self.tables_file.exists():
            self._tables = {}
            return

        try:
            with open(self.tables_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    self._tables = {
                        int(item["id"]): Table.from_dict(item)
                        for item in data
                        if isinstance(item, dict) and "id" in item
                    }
        except Exception as e:
            print(f"Lỗi khi đọc file tables.json: {e}")
            self._tables = {}

    def save_tables(self) -> None:
        """Lưu danh sách bàn vào file tables.json."""
        try:
            self.tables_file.parent.mkdir(parents=True, exist_ok=True)
            data = [table.to_dict() for table in self._tables.values()]
            with open(self.tables_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Lỗi khi lưu file tables.json: {e}")

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
        :param table_id: Mã bàn cần chiếm
        :param order_id: Mã đơn hàng liên kết
        :return: True nếu chiếm bàn thành công, False nếu bàn không tồn tại hoặc đã có khách
        """
        table = self.get_table(table_id)
        if not table:
            return False

        if not table.is_available and table.current_order_id != str(order_id):
            return False

        table.occupy(order_id)
        self.save_tables()
        return True

    def release_table(self, table_id: int) -> bool:
        """
        Giải phóng bàn khi đơn hàng thanh toán xong hoặc bị hủy.
        """
        table = self.get_table(table_id)
        if not table:
            return False

        table.release()
        self.save_tables()
        return True

import json
from pathlib import Path
from typing import Dict, List, Optional

from src.models.JSONStorage import JSONStorage
from src.models.Table import Table


class TableManager:
    def __init__(self, tables_file: Optional[str] = None, auto_load: bool = True):
        if tables_file:
            self.tables_file = Path(tables_file)
        else:
            current_dir = Path(__file__).resolve().parent
            project_root = current_dir.parent.parent
            self.tables_file = project_root / "data" / "tables.json"

        self._tables: Dict[int, Table] = {}
        if auto_load:
            self.load_tables()

    def load_tables(self) -> None:
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

    def save_tables(self) -> bool:
        data = [table.to_dict() for table in self._tables.values()]
        return JSONStorage.save_data(str(self.tables_file), data)

    def get_all_tables(self) -> List[Table]:
        return list(self._tables.values())

    def get_table(self, table_id: int) -> Optional[Table]:
        return self._tables.get(int(table_id))

    def get_available_tables(self) -> List[Table]:
        return [table for table in self._tables.values() if table.is_available]

    def is_table_available(self, table_id: int) -> bool:
        table = self.get_table(table_id)
        return table.is_available if table else False

    def occupy_table(self, table_id: int, order_id: str) -> bool:
        table = self.get_table(table_id)
        if not table:
            return False

        if not table.is_available:
            return False

        previous_status = table.status
        previous_order_id = table.current_order_id
        table.occupy(order_id)
        if not self.save_tables():
            table.status = previous_status
            table.current_order_id = previous_order_id
            return False
        return True

    def release_table(self, table_id: int, order_id: Optional[str] = None) -> bool:
        table = self.get_table(table_id)
        if not table:
            return False
        if order_id is not None and table.current_order_id != str(order_id):
            return False

        previous_status = table.status
        previous_order_id = table.current_order_id
        table.release()
        if not self.save_tables():
            table.status = previous_status
            table.current_order_id = previous_order_id
            return False
        return True

    def reserve_table(self, table_id: int) -> bool:
        table = self.get_table(table_id)
        if not table or not table.is_available:
            return False

        previous_status = table.status
        previous_order_id = table.current_order_id
        table.reserve()
        if not self.save_tables():
            table.status = previous_status
            table.current_order_id = previous_order_id
            return False
        return True

    def vacate_table(self, table_id: int) -> bool:
        table = self.get_table(table_id)
        if not table:
            return False

        previous_status = table.status
        previous_order_id = table.current_order_id
        table.vacate()
        if not self.save_tables():
            table.status = previous_status
            table.current_order_id = previous_order_id
            return False
        return True

    def add_table(self, table: Table) -> bool:
        """Thêm bàn mới vào hệ thống và lưu vào tables.json."""
        if not isinstance(table, Table):
            raise TypeError("Đối tượng thêm vào phải thuộc lớp Table.")
        if table.id in self._tables:
            return False
        self._tables[table.id] = table
        self.save_tables()
        return True

    def remove_table(self, table_id: int) -> bool:
        """Xóa bàn khỏi hệ thống nếu bàn không bận (OCCUPIED)."""
        table = self.get_table(table_id)
        if not table or table.status == "OCCUPIED":
            return False
        del self._tables[int(table_id)]
        self.save_tables()
        return True

    def update_table(
        self,
        table_id: int,
        name: Optional[str] = None,
        capacity: Optional[int] = None,
    ) -> bool:
        """Cập nhật tên và sức chứa của bàn ăn."""
        table = self.get_table(table_id)
        if not table:
            return False
        if name:
            table.name = str(name).strip()
        if capacity is not None and int(capacity) > 0:
            table.capacity = int(capacity)
        self.save_tables()
        return True


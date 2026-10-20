from pathlib import Path
from typing import Optional

from src.models.JSONStorage import JSONStorage
from src.models.Table import Table
from src.structures.hash_table import HashTable
from src.structures.linked_list import DoublyLinkedList


class TableManager:
    def __init__(self, tables_file: Optional[str] = None, auto_load: bool = True):
        if tables_file:
            self.tables_file = Path(tables_file)
        else:
            current_dir = Path(__file__).resolve().parent
            project_root = current_dir.parent.parent
            self.tables_file = project_root / "data" / "tables.json"

        self._tables = HashTable()
        self._table_ids = DoublyLinkedList()
        if auto_load:
            self.load_tables()

    def load_tables(self) -> None:
        self._tables.clear()
        self._table_ids.clear()
        if not self.tables_file.exists():
            return

        data = JSONStorage.from_json_data(
            JSONStorage.load_data(
                str(self.tables_file),
                default_data=DoublyLinkedList(),
            )
        )
        if not isinstance(data, DoublyLinkedList):
            print("Lỗi khi đọc file tables.json: dữ liệu phải là danh sách.")
            return

        for item in data:
            if not isinstance(item, HashTable):
                print("Cảnh báo khi đọc file tables.json: bỏ qua dữ liệu bàn không hợp lệ.")
                continue
            table_id = item.get("id")
            if table_id is None:
                print("Cảnh báo khi đọc file tables.json: bỏ qua bàn thiếu ID.")
                continue
            try:
                table = Table.from_dict(item)
                if not self._tables.contains(table.id):
                    self._table_ids.add_last(table.id)
                self._tables.put(table.id, table)
            except (TypeError, ValueError) as error:
                print("Cảnh báo khi đọc file tables.json: bỏ qua bàn lỗi: " + str(error))

    def save_tables(self) -> bool:
        data = DoublyLinkedList()
        for table_id in self._table_ids:
            table = self._tables.get(table_id)
            if table is not None:
                data.add_last(table.to_dict())
        return JSONStorage.save_data(str(self.tables_file), data)

    def get_all_tables(self) -> DoublyLinkedList:
        tables = DoublyLinkedList()
        for table_id in self._table_ids:
            table = self._tables.get(table_id)
            if table is not None:
                tables.add_last(table)
        return tables

    def get_table(self, table_id: int) -> Optional[Table]:
        return self._tables.get(int(table_id))

    def get_available_tables(self) -> DoublyLinkedList:
        tables = DoublyLinkedList()
        for table_id in self._table_ids:
            table = self._tables.get(table_id)
            if table is not None and table.is_available:
                tables.add_last(table)
        return tables

    def is_table_available(self, table_id: int) -> bool:
        table = self.get_table(table_id)
        return table.is_available if table else False

    def occupy_table(self, table_id: int, order_id: str) -> bool:
        table = self.get_table(table_id)
        if not table or not table.is_available:
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

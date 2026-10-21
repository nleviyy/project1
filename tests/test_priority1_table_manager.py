import json
import pytest
from pathlib import Path
from unittest.mock import patch

from src.core.TableManager import TableManager, TableDataError
from src.models.Table import Table, TableStatus


def test_table_manager_corrupted_file_raises_error_and_does_not_overwrite(tmp_path):
    """File tables.json bị hỏng -> load ném lỗi TableDataError và file không bị ghi đè rỗng."""
    tables_file = tmp_path / "tables.json"
    corrupt_content = "{ this is invalid json content !!"
    tables_file.write_text(corrupt_content, encoding="utf-8")

    # Load file hỏng phải ném TableDataError
    with pytest.raises(TableDataError):
        TableManager(tables_file=tables_file, auto_load=True)

    # Đảm bảo nội dung file tables.json vẫn giữ nguyên, không bị ghi đè thành []
    assert tables_file.read_text(encoding="utf-8") == corrupt_content

    # Khởi tạo không auto_load rồi load_tables cũng phải ném lỗi
    tm = TableManager(tables_file=tables_file, auto_load=False)
    with pytest.raises(TableDataError):
        tm.load_tables()

    # save_tables khi load thất bại cũng bị chặn ném TableDataError
    with pytest.raises(TableDataError, match="trước đó đã thất bại"):
        tm.save_tables()
    assert tables_file.read_text(encoding="utf-8") == corrupt_content


def test_table_manager_nonexistent_file_allows_empty_init(tmp_path):
    """File không tồn tại: được phép khởi tạo danh sách rỗng và không tạo file ngay."""
    nonexistent = tmp_path / "nonexistent_tables.json"
    tm = TableManager(tables_file=nonexistent, auto_load=True)
    assert len(tm.get_all_tables()) == 0
    assert not nonexistent.exists()


def test_table_manager_rollback_on_save_error(tmp_path):
    """
    Thêm rollback trạng thái trong bộ nhớ cho reserve_table, vacate_table,
    update_table, add_table, remove_table khi save_tables ném OSError.
    """
    tables_file = tmp_path / "tables.json"
    initial_tables = [
        {"id": 1, "name": "Bàn 01", "capacity": 4, "status": "AVAILABLE", "current_order_id": None},
        {"id": 2, "name": "Bàn 02", "capacity": 2, "status": "RESERVED", "current_order_id": None},
        {"id": 3, "name": "Bàn 03", "capacity": 6, "status": "AVAILABLE", "current_order_id": None},
    ]
    tables_file.write_text(json.dumps(initial_tables), encoding="utf-8")

    tm = TableManager(tables_file=tables_file, auto_load=True)

    with patch.object(tm, "save_tables", side_effect=OSError("Lỗi ổ đĩa mô phỏng")):
        # 1. Rollback reserve_table
        with pytest.raises(OSError):
            tm.reserve_table(1)
        assert tm.get_table(1).status == "AVAILABLE"

        # 2. Rollback vacate_table
        with pytest.raises(OSError):
            tm.vacate_table(2)
        assert tm.get_table(2).status == "RESERVED"

        # 3. Rollback update_table
        with pytest.raises(OSError):
            tm.update_table(3, name="Bàn VIP", capacity=10)
        assert tm.get_table(3).name == "Bàn 03"
        assert tm.get_table(3).capacity == 6

        # 4. Rollback add_table
        new_table = Table(id=4, name="Bàn 04", capacity=4)
        with pytest.raises(OSError):
            tm.add_table(new_table)
        assert tm.get_table(4) is None

        # 5. Rollback remove_table
        with pytest.raises(OSError):
            tm.remove_table(3)
        assert tm.get_table(3) is not None


def test_table_manager_release_table_with_order_id(tmp_path):
    """
    release_table(table_id, order_id=None): nếu truyền order_id thì chỉ giải phóng
    khi current_order_id khớp; không khớp thì trả False.
    """
    tables_file = tmp_path / "tables.json"
    initial_tables = [
        {"id": 1, "name": "Bàn 01", "capacity": 4, "status": "OCCUPIED", "current_order_id": "ORD-001"}
    ]
    tables_file.write_text(json.dumps(initial_tables), encoding="utf-8")

    tm = TableManager(tables_file=tables_file, auto_load=True)

    # Không khớp order_id -> trả False, trạng thái không đổi
    assert tm.release_table(1, order_id="ORD-WRONG") is False
    assert tm.get_table(1).status == "OCCUPIED"
    assert tm.get_table(1).current_order_id == "ORD-001"

    # Khớp order_id -> trả True, giải phóng thành AVAILABLE
    assert tm.release_table(1, order_id="ORD-001") is True
    assert tm.get_table(1).status == "AVAILABLE"
    assert tm.get_table(1).current_order_id is None


def test_table_manager_update_table_invalid_capacity_raises_value_error(tmp_path):
    """update_table: sức chứa không hợp lệ phải ném ValueError."""
    tables_file = tmp_path / "tables.json"
    tables_file.write_text(json.dumps([{"id": 1, "name": "Bàn 01", "capacity": 4}]), encoding="utf-8")

    tm = TableManager(tables_file=tables_file, auto_load=True)
    with pytest.raises(ValueError):
        tm.update_table(1, capacity=0)

    with pytest.raises(ValueError):
        tm.update_table(1, capacity=-5)

    with pytest.raises(ValueError):
        tm.update_table(1, capacity="invalid")


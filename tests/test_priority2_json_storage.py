import json
import pytest
from pathlib import Path

from src.core.JSONStorage import JSONStorage, CorruptDataError, load_data, save_data, write_json_updates


def test_json_storage_save_and_load(tmp_path):
    """Ghi rồi đọc lại nguyên tử."""
    file_path = tmp_path / "test_data.json"
    data = [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]

    save_data(file_path, data)
    assert file_path.exists()

    loaded = load_data(file_path)
    assert loaded == data


def test_json_storage_empty_list_and_dict_preserved(tmp_path):
    """File [] trả về [], file {} trả về {} (không bị nuốt nhầm sang default)."""
    file_list = tmp_path / "empty_list.json"
    file_dict = tmp_path / "empty_dict.json"

    save_data(file_list, [])
    save_data(file_dict, {})

    assert load_data(file_list, default_data="DEFAULT") == []
    assert load_data(file_dict, default_data="DEFAULT") == {}


def test_json_storage_corrupted_file_raises_corrupt_data_error(tmp_path):
    """JSON hỏng ném CorruptDataError kèm đường dẫn file, không trả default."""
    corrupt_file = tmp_path / "corrupt.json"
    corrupt_file.write_text("{ unclosed json: 123", encoding="utf-8")

    with pytest.raises(CorruptDataError) as exc_info:
        load_data(corrupt_file, default_data=[])
    assert str(corrupt_file) in str(exc_info.value)


def test_json_storage_nonexistent_file_does_not_create_file(tmp_path):
    """File không tồn tại thì trả default_data và KHÔNG tự ghi file."""
    nonexistent = tmp_path / "does_not_exist.json"
    result = load_data(nonexistent, default_data=[])
    assert result == []
    assert not nonexistent.exists()


def test_json_storage_zero_byte_file_returns_default(tmp_path):
    """File 0 byte rỗng thì trả default_data."""
    zero_byte = tmp_path / "zero.json"
    zero_byte.write_bytes(b"")
    assert load_data(zero_byte, default_data=["fallback"]) == ["fallback"]


def test_write_json_updates_atomic_and_rollback(tmp_path):
    """write_json_updates ghi đồng bộ nhiều file kèm rollback khi lỗi."""
    f1 = tmp_path / "f1.json"
    f2 = tmp_path / "f2.json"
    f1.write_text(json.dumps({"f1": "old"}), encoding="utf-8")
    f2.write_text(json.dumps({"f2": "old"}), encoding="utf-8")

    # Ghi thành công
    write_json_updates({f1: {"f1": "new"}, f2: {"f2": "new"}})
    assert json.loads(f1.read_text(encoding="utf-8")) == {"f1": "new"}
    assert json.loads(f2.read_text(encoding="utf-8")) == {"f2": "new"}


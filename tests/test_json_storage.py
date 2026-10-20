import json
from importlib import import_module

from src.core.TableManager import TableManager
from src.models.JSONStorage import JSONStorage


def test_json_storage_saves_and_reloads_data(tmp_path):
    path = tmp_path / "nested" / "data.json"
    payload = [{"id": "A", "prep_time": 5}]

    assert JSONStorage.save_data(str(path), payload)
    assert JSONStorage.load_data(str(path), default_data=[]) == payload


def test_json_storage_reports_write_failure_and_preserves_original(
    tmp_path, monkeypatch
):
    path = tmp_path / "data.json"
    original = [{"id": "original"}]
    path.write_text(json.dumps(original), encoding="utf-8")

    def fail_replace(source, destination):
        raise OSError("replace failed")

    storage_module = import_module("src.models.JSONStorage")
    monkeypatch.setattr(storage_module.os, "replace", fail_replace)

    assert not JSONStorage.save_data(str(path), [{"id": "updated"}])
    assert json.loads(path.read_text(encoding="utf-8")) == original
    assert list(tmp_path.iterdir()) == [path]


def test_table_manager_persists_and_reloads_table_state(tmp_path):
    path = tmp_path / "tables.json"
    path.write_text(
        json.dumps(
            [
                {
                    "id": 1,
                    "name": "Bàn 01",
                    "capacity": 2,
                    "status": "AVAILABLE",
                    "current_order_id": None,
                }
            ]
        ),
        encoding="utf-8",
    )

    manager = TableManager(tables_file=str(path))
    assert manager.occupy_table(1, "ORD-1")

    reloaded = TableManager(tables_file=str(path))
    table = reloaded.get_table(1)
    assert table is not None
    assert table.status == "OCCUPIED"
    assert table.current_order_id == "ORD-1"

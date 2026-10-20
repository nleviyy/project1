import json
from importlib import import_module

import pytest

from src.core.TableManager import TableManager
from src.models.JSONStorage import JSONStorage
from src.models.Table import Table


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


def test_strict_json_storage_does_not_hide_corrupt_json(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text("{invalid", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        JSONStorage.load_data(str(path), default_data=[], strict=True)


def test_table_mutations_roll_back_when_persistence_fails(tmp_path, monkeypatch):
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
    monkeypatch.setattr(manager, "save_tables", lambda: False)

    assert not manager.add_table(Table(id=2, name="Bàn 02", capacity=4))
    assert manager.get_table(2) is None
    assert not manager.update_table(1, name="Changed", capacity=6)
    assert manager.get_table(1).name == "Bàn 01"
    assert manager.get_table(1).capacity == 2
    assert not manager.remove_table(1)
    assert manager.get_table(1) is not None


def test_reserved_table_can_be_vacated_but_occupied_table_cannot(tmp_path):
    path = tmp_path / "tables.json"
    path.write_text(
        json.dumps(
            [
                {
                    "id": 1,
                    "name": "Bàn 01",
                    "capacity": 2,
                    "status": "OCCUPIED",
                    "current_order_id": "ORD-1",
                },
                {
                    "id": 2,
                    "name": "Bàn 02",
                    "capacity": 2,
                    "status": "RESERVED",
                    "current_order_id": None,
                },
            ]
        ),
        encoding="utf-8",
    )
    manager = TableManager(tables_file=str(path))

    assert not manager.vacate_table(1)
    assert manager.get_table(1).current_order_id == "ORD-1"
    assert manager.vacate_table(2)
    assert manager.get_table(2).status == "AVAILABLE"

import json
import os
import sys
import tempfile
from pathlib import Path

from src.structures.linked_list import DoublyLinkedList
from src.structures.hash_table import HashTable

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')


def _from_json(value):
    if isinstance(value, dict):
        table = HashTable()
        for key in value:
            table.put(key, _from_json(value[key]))
        return table
    if isinstance(value, list):
        linked = DoublyLinkedList()
        for element in value:
            linked.add_last(_from_json(element))
        return linked
    return value


def _to_json(value):
    """HashTable -> dict, DoublyLinkedList -> list (đổi đệ quy)."""
    if isinstance(value, dict):
        return {key: _to_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_json(item) for item in value]
    if isinstance(value, HashTable):
        result = {}
        node = value.keys().head
        while node is not None:
            result[node.data] = _to_json(value.get(node.data))
            node = node.next
        return result
    if isinstance(value, DoublyLinkedList):
        result = []
        node = value.head
        while node is not None:
            result.append(_to_json(node.data))
            node = node.next
        return result
    if hasattr(value, "to_dict"):
        return _to_json(value.to_dict())
    return value


def _is_empty(data):
    if isinstance(data, HashTable) or isinstance(data, DoublyLinkedList):
        return data.is_empty()
    return not data


class JSONStorage:
    @staticmethod
    def from_json_data(data):
        return _from_json(data)

    @staticmethod
    def to_json_data(data):
        return _to_json(data)

    @staticmethod
    def load_data(file_path, default_data):
        if not os.path.exists(file_path):
            print("Thông báo: File '" + file_path + "' không tồn tại. Đang tạo dữ liệu mặc định...")
            JSONStorage.save_data(file_path, default_data)
            return default_data

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if _is_empty(data):
                    print("Cảnh báo: File '" + file_path + "' trống. Sử dụng dữ liệu mặc định.")
                    return default_data
                return data
        except json.JSONDecodeError:
            print("Lỗi: Dữ liệu trong '" + file_path + "' bị hỏng (Invalid JSON). Sử dụng dữ liệu mặc định.")
            return default_data
        except Exception as e:
            print("Lỗi không xác định khi đọc '" + file_path + "': " + str(e))
            return default_data

    @staticmethod
    def save_data(file_path, data):
        temporary_path = None
        try:
            destination = Path(file_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            json_data = _to_json(data)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=destination.parent,
                delete=False,
                suffix=".tmp",
            ) as file:
                temporary_path = Path(file.name)
                json.dump(json_data, file, ensure_ascii=False, indent=4)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary_path, destination)
            return True
        except Exception as e:
            print("Lỗi khi lưu dữ liệu vào '" + file_path + "': " + str(e))
            return False
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()

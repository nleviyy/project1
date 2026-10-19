import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

class JSONStorage:
    @staticmethod
    def load_data(file_path: str, default_data: Any) -> Any:
        if not os.path.exists(file_path):
            print(f"Thông báo: File '{file_path}' không tồn tại. Đang tạo dữ liệu mặc định...")
            JSONStorage.save_data(file_path, default_data)
            return default_data

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if not data:
                    print(f"Cảnh báo: File '{file_path}' trống. Sử dụng dữ liệu mặc định.")
                    return default_data
                return data
        except json.JSONDecodeError:
            print(f"Lỗi: Dữ liệu trong '{file_path}' bị hỏng (Invalid JSON). Sử dụng dữ liệu mặc định.")
            return default_data
        except Exception as e:
            print(f"Lỗi không xác định khi đọc '{file_path}': {str(e)}")
            return default_data

    @staticmethod
    def save_data(file_path: str, data: Any) -> bool:
        temporary_path = None
        try:
            destination = Path(file_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=destination.parent,
                delete=False,
                suffix=".tmp",
            ) as file:
                temporary_path = Path(file.name)
                json.dump(data, file, ensure_ascii=False, indent=4)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary_path, destination)
            return True
        except Exception as e:
            print(f"Lỗi khi lưu dữ liệu vào '{file_path}': {str(e)}")
            return False
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()

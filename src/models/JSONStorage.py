import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any
from uuid import uuid4

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

class JSONStorage:
    @staticmethod
    def load_data(file_path: str, default_data: Any, *, strict: bool = False) -> Any:
        if not os.path.exists(file_path):
            if strict:
                return default_data
            print(f"Thông báo: File '{file_path}' không tồn tại. Đang tạo dữ liệu mặc định...")
            JSONStorage.save_data(file_path, default_data)
            return default_data

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if not data:
                    if strict:
                        return data
                    print(f"Cảnh báo: File '{file_path}' trống. Sử dụng dữ liệu mặc định.")
                    return default_data
                return data
        except json.JSONDecodeError:
            if strict:
                raise
            print(f"Lỗi: Dữ liệu trong '{file_path}' bị hỏng (Invalid JSON). Sử dụng dữ liệu mặc định.")
            return default_data
        except Exception as e:
            if strict:
                raise
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

    @staticmethod
    def save_many(updates: Dict[str | Path, Any]) -> None:
        staged: Dict[Path, Path] = {}
        originals: Dict[Path, bytes | None] = {}
        replaced: list[Path] = []
        try:
            for raw_target, data in updates.items():
                target = Path(raw_target)
                target.parent.mkdir(parents=True, exist_ok=True)
                originals[target] = target.read_bytes() if target.exists() else None
                temporary = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
                staged[target] = temporary
                with temporary.open("w", encoding="utf-8") as file:
                    json.dump(data, file, ensure_ascii=False, indent=2)
                    file.flush()
                    os.fsync(file.fileno())
            for target, temporary in staged.items():
                os.replace(temporary, target)
                replaced.append(target)
        except OSError as write_error:
            rollback_errors = []
            for target in reversed(replaced):
                try:
                    original = originals[target]
                    if original is None:
                        target.unlink(missing_ok=True)
                    else:
                        rollback = target.with_name(
                            f".{target.name}.{uuid4().hex}.rollback"
                        )
                        rollback.write_bytes(original)
                        os.replace(rollback, target)
                except OSError as rollback_error:
                    rollback_errors.append(f"{target}: {rollback_error}")
            if rollback_errors:
                raise RuntimeError(
                    f"Không thể ghi đồng bộ các file JSON ({write_error}); "
                    "lỗi khi khôi phục: " + "; ".join(rollback_errors)
                ) from write_error
            raise
        finally:
            for temporary in staged.values():
                temporary.unlink(missing_ok=True)

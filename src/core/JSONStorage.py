import json
import os
from pathlib import Path
from typing import Any, Dict, List, Union
from uuid import uuid4


class CorruptDataError(ValueError):
    """Ngoại lệ ném ra khi dữ liệu JSON bị hỏng hoặc không đúng định dạng."""

    def __init__(self, file_path: str, message: str = "Dữ liệu JSON bị hỏng"):
        self.file_path = file_path
        super().__init__(f"{message}: {file_path}")


def load_data(file_path: Union[str, Path], default_data: Any = None) -> Any:
    """
    Đọc dữ liệu từ file JSON.
    - File không tồn tại: trả về default_data và KHÔNG tự ghi file.
    - File có kích thước 0 byte (trống): coi là trống, trả về default_data.
    - File chứa [] hoặc {} hợp lệ: trả về đúng [] hoặc {}.
    - File chứa JSON hỏng: ném CorruptDataError kèm đường dẫn file.
    """
    path = Path(file_path)
    if not path.exists():
        return default_data

    # Kiểm tra kích thước file (0 byte)
    try:
        if path.stat().st_size == 0:
            return default_data
    except OSError:
        pass

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise CorruptDataError(str(path), f"Lỗi cú pháp JSON ({e.msg}) tại file") from e
    except Exception as e:
        raise CorruptDataError(str(path), f"Không thể đọc file ({e})") from e


def save_data(file_path: Union[str, Path], data: Any) -> bool:
    """
    Ghi dữ liệu JSON nguyên tử (atomic) bằng file tạm cùng thư mục rồi os.replace.
    Ném OSError khi có lỗi ghi file, không nuốt lỗi.
    """
    path = Path(file_path)
    parent_dir = path.parent
    if parent_dir:
        parent_dir.mkdir(parents=True, exist_ok=True)

    temp_path = parent_dir / f".{path.name}.{uuid4().hex}.tmp"
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(temp_path, path)
        return True
    except OSError as e:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        raise OSError(f"Lỗi khi lưu dữ liệu vào '{path}': {e}") from e


def write_json_updates(updates: Dict[Path, Any]) -> None:
    """
    Ghi đồng bộ nhiều file JSON nguyên tử kèm rollback nếu bất kỳ file nào gặp lỗi.
    Dùng chung cho toàn bộ hệ thống (PaymentService, TableManager, OrderService).
    """
    staged: Dict[Path, Path] = {}
    originals: Dict[Path, Union[bytes, None]] = {}
    replaced: List[Path] = []
    try:
        for target, data in updates.items():
            target_path = Path(target)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            originals[target_path] = target_path.read_bytes() if target_path.exists() else None
            temporary = target_path.with_name(f".{target_path.name}.{uuid4().hex}.tmp")
            staged[target_path] = temporary
            with open(temporary, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        for target_path, temporary in staged.items():
            os.replace(temporary, target_path)
            replaced.append(target_path)
    except OSError as e:
        for target_path in reversed(replaced):
            original = originals[target_path]
            if original is None:
                target_path.unlink(missing_ok=True)
            else:
                rollback = target_path.with_name(f".{target_path.name}.{uuid4().hex}.rollback")
                rollback.write_bytes(original)
                os.replace(rollback, target_path)
        raise OSError(f"Lỗi ghi nguyên tử đồng thời các file JSON: {e}") from e
    finally:
        for temporary in staged.values():
            if temporary.exists():
                temporary.unlink(missing_ok=True)


class JSONStorage:
    """Lớp bọc không trạng thái để tương thích với code cũ."""

    load_data = staticmethod(load_data)
    save_data = staticmethod(save_data)
    write_json_updates = staticmethod(write_json_updates)
    CorruptDataError = CorruptDataError


__all__ = [
    "JSONStorage",
    "CorruptDataError",
    "load_data",
    "save_data",
    "write_json_updates",
]

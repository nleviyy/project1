"""
Smoke test cơ bản để xác nhận môi trường pytest và cấu trúc project hoạt động chuẩn.
"""
from pathlib import Path
import json

def test_project_structure():
    """Kiểm tra sự tồn tại của các thư mục cốt lõi."""
    base_dir = Path(__file__).resolve().parent.parent
    assert (base_dir / "src").is_dir(), "Thư mục src/ phải tồn tại"
    assert (base_dir / "src" / "models").is_dir(), "Thư mục src/models/ phải tồn tại"
    assert (base_dir / "src" / "core").is_dir(), "Thư mục src/core/ phải tồn tại"
    assert (base_dir / "src" / "ui").is_dir(), "Thư mục src/ui/ phải tồn tại"
    assert (base_dir / "data").is_dir(), "Thư mục data/ phải tồn tại"
    assert (base_dir / "src" / "app.py").is_file(), "File src/app.py phải tồn tại"

def test_sample_data_format():
    """Kiểm tra tính hợp lệ của file JSON mẫu ban đầu."""
    base_dir = Path(__file__).resolve().parent.parent
    menu_file = base_dir / "data" / "sample_menu.json"
    tables_file = base_dir / "data" / "sample_tables.json"
    
    assert menu_file.is_file(), "File sample_menu.json phải tồn tại"
    with open(menu_file, "r", encoding="utf-8") as f:
        menu_items = json.load(f)
        assert isinstance(menu_items, list)
        assert len(menu_items) > 0

    assert tables_file.is_file(), "File sample_tables.json phải tồn tại"
    with open(tables_file, "r", encoding="utf-8") as f:
        tables = json.load(f)
        assert isinstance(tables, list)
        assert len(tables) > 0

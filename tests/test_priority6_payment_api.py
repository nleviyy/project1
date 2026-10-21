import json
import subprocess
import sys
import pytest
from pathlib import Path


def run_payment_api(payload_str: str) -> tuple[int, dict]:
    """Chạy module payment_api qua CLI subprocess và đọc stdout UTF-8."""
    cmd = [sys.executable, "-m", "src.core.payment_api"]
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = proc.communicate(input=payload_str.encode("utf-8"))
    exit_code = proc.returncode

    try:
        out_json = json.loads(stdout.decode("utf-8"))
    except Exception:
        out_json = {"raw": stdout.decode("utf-8", errors="ignore")}

    return exit_code, out_json


def test_payment_api_missing_fields_returns_400():
    """Request thiếu trường: trả JSON lỗi 400 và exit code != 0."""
    payload = json.dumps({"order_id": "ORD-001"})  # thiếu method, cashier_name
    exit_code, out_json = run_payment_api(payload)
    assert exit_code != 0
    assert out_json.get("status") == 400
    assert "error" in out_json


def test_payment_api_invalid_json_type_returns_400():
    """JSON không phải object (ví dụ: list hoặc string): trả JSON lỗi 400 và exit code != 0."""
    payload = json.dumps(["not", "an", "object"])
    exit_code, out_json = run_payment_api(payload)
    assert exit_code != 0
    assert out_json.get("status") == 400
    assert "JSON object" in out_json.get("error", "")


def test_payment_api_cash_without_cash_received_returns_400():
    """Thanh toán CASH thiếu cash_received: trả JSON lỗi 400 và exit code != 0."""
    payload = json.dumps({
        "order_id": "ORD-NONEXISTENT",
        "method": "CASH",
        "cashier_name": "Thu Ngân A",
        # thiếu cash_received
    })
    exit_code, out_json = run_payment_api(payload)
    assert exit_code != 0
    assert out_json.get("status") == 400
    assert "error" in out_json


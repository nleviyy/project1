import json
import sys
from typing import Optional
from pydantic import BaseModel, Field, ValidationError

from src.core.PaymentService import PaymentService
from src.models.Payment import PaymentMethod


class PaymentRequest(BaseModel):
    order_id: str = Field(..., description="Mã đơn hàng cần thanh toán")
    method: PaymentMethod = Field(..., description="Phương thức thanh toán (CASH, BANK_TRANSFER, CARD)")
    cashier_name: str = Field(..., description="Tên thu ngân")
    cash_received: Optional[int] = Field(default=None, description="Tiền mặt khách đưa")
    transaction_code: Optional[str] = Field(default=None, description="Mã giao dịch ngân hàng/thẻ")
    transaction_successful: Optional[bool] = Field(default=None, description="Kết quả giao dịch chuyển khoản/thẻ")


def _output_response(data: dict, status_code: int = 0) -> int:
    """Ghi output ra sys.stdout dưới dạng UTF-8 buffer."""
    encoded = json.dumps(data, ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()
    return status_code


def main() -> int:
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            return _output_response({"error": "Dữ liệu yêu cầu rỗng.", "status": 400}, status_code=1)

        try:
            req_json = json.loads(raw_input)
        except json.JSONDecodeError as err:
            return _output_response(
                {"error": f"JSON không hợp lệ: {err.msg}", "status": 400},
                status_code=1,
            )

        if not isinstance(req_json, dict):
            return _output_response(
                {"error": "Dữ liệu yêu cầu phải là một JSON object.", "status": 400},
                status_code=1,
            )

        try:
            req_model = PaymentRequest.model_validate(req_json)
        except ValidationError as err:
            return _output_response(
                {"error": str(err), "status": 400},
                status_code=1,
            )

        result = PaymentService().pay_order(
            order_id=req_model.order_id,
            method=req_model.method,
            cashier_name=req_model.cashier_name,
            cash_received=req_model.cash_received,
            transaction_code=req_model.transaction_code,
            transaction_successful=req_model.transaction_successful,
        )

        response = {
            "payment": result.payment.model_dump(mode="json"),
            "invoice": result.invoice.model_dump(mode="json") if result.invoice else None,
            "status": 200,
        }
        return _output_response(response, status_code=0)

    except ValueError as error:
        return _output_response({"error": str(error), "status": 400}, status_code=1)
    except Exception as error:
        return _output_response({"error": f"Lỗi hệ thống: {error}", "status": 500}, status_code=2)


if __name__ == "__main__":
    raise SystemExit(main())

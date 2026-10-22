import json
import sys

from src.core.PaymentService import PaymentService
from src.models.JSONStorage import JSONStorage


def main() -> int:
    try:
        request = json.load(sys.stdin)
        if not isinstance(request, dict):
            raise ValueError("Payment request must be a JSON object.")

        result = PaymentService().pay_order(
            order_id=request.get("order_id"),
            method=request.get("method"),
            cashier_name=request.get("cashier_name"),
            cash_received=request.get("cash_received"),
            transaction_code=request.get("transaction_code"),
            transaction_successful=request.get("transaction_successful"),
        )
        response = {
            "payment": JSONStorage.to_json_data(result.payment.to_dict()),
            "invoice": JSONStorage.to_json_data(result.invoice.to_dict()) if result.invoice else None,
        }
    except ValueError as error:
        response = {"error": str(error), "status": 400}
    except Exception as error:
        print(f"Payment API error: {error}", file=sys.stderr)
        return 1

    json.dump(response, sys.stdout, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

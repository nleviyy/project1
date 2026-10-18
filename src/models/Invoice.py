"""
Model Invoice: Quản lý thông tin hóa đơn của một đơn hàng sau khi thanh toán.
Hiện thực hóa yêu cầu của Mentor trong mục 2.2 và P1.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional


class Invoice:
    """
    Đại diện cho hóa đơn thanh toán xuất cho khách hàng.
    """

    def __init__(
        self,
        id: str,
        order_id: str,
        table_id: int,
        items: List[Dict[str, Any]],
        total_amount: int,
        discount_amount: int = 0,
        final_amount: int = 0,
        payment_id: Optional[str] = None,
        payment_method: str = "CASH",
        created_at: Optional[str] = None,
        cashier_name: str = "Vy",
    ):
        self.id: str = str(id).strip()
        self.order_id: str = str(order_id).strip()
        self.table_id: int = int(table_id)
        self.items: List[Dict[str, Any]] = items or []
        self.total_amount: int = int(total_amount)
        self.discount_amount: int = int(discount_amount)
        self.final_amount: int = int(final_amount) if final_amount else max(0, self.total_amount - self.discount_amount)
        self.payment_id: Optional[str] = str(payment_id).strip() if payment_id else None
        self.payment_method: str = str(payment_method).strip()
        self.created_at: str = created_at or datetime.now().isoformat(timespec="seconds")
        self.cashier_name: str = str(cashier_name).strip()

    def generate_text_receipt(self) -> str:
        """
        Tạo nội dung phiếu hóa đơn dạng text có thể in ra POS hoặc hiển thị trên giao diện.
        """
        lines = []
        lines.append("=" * 40)
        lines.append("          HÓA ĐƠN THANH TOÁN")
        lines.append(f" Mã hóa đơn: {self.id}")
        lines.append(f" Đơn hàng: {self.order_id} | Bàn: {self.table_id}")
        lines.append(f" Thời gian : {self.created_at}")
        lines.append(f" Thu ngân  : {self.cashier_name}")
        lines.append("-" * 40)
        lines.append(f"{'Tên món':<20}{'SL':>4}{'Thành tiền':>16}")
        lines.append("-" * 40)

        for item in self.items:
            name = item.get("item_name", item.get("name", "Món"))[:19]
            qty = item.get("quantity", 1)
            subtotal = item.get("subtotal", item.get("unit_price", 0) * qty)
            lines.append(f"{name:<20}{qty:>4}{subtotal:>14,d}đ")

        lines.append("-" * 40)
        lines.append(f"Tổng tiền món : {self.total_amount:>18,d} VNĐ")
        if self.discount_amount > 0:
            lines.append(f"Giảm giá      : -{self.discount_amount:>17,d} VNĐ")
        lines.append(f"THỰC THU      : {self.final_amount:>18,d} VNĐ")
        lines.append(f"Hình thức TT  : {self.payment_method}")
        lines.append("=" * 40)
        lines.append("    Cảm ơn quý khách và hẹn gặp lại!")
        lines.append("=" * 40)
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "table_id": self.table_id,
            "items": self.items,
            "total_amount": int(self.total_amount),
            "discount_amount": int(self.discount_amount),
            "final_amount": int(self.final_amount),
            "payment_id": self.payment_id,
            "payment_method": self.payment_method,
            "created_at": self.created_at,
            "cashier_name": self.cashier_name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Invoice":
        return cls(
            id=str(data.get("id", "")),
            order_id=str(data.get("order_id", "")),
            table_id=int(data.get("table_id", 0)),
            items=data.get("items", []),
            total_amount=int(data.get("total_amount", 0)),
            discount_amount=int(data.get("discount_amount", 0)),
            final_amount=int(data.get("final_amount", 0)),
            payment_id=data.get("payment_id"),
            payment_method=str(data.get("payment_method", "CASH")),
            created_at=data.get("created_at"),
            cashier_name=str(data.get("cashier_name", "Vy")),
        )

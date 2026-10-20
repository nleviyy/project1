from src.structures.hash_table import HashTable

def _to_int(value, error_message):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(error_message)


class OrderItem:
    def __init__(
        self,
        menu_item_id,
        item_name,
        unit_price,
        quantity,
        note="",
        prep_time=None,
        subtotal=None,
    ):
        if menu_item_id is None or str(menu_item_id).strip() == "":
            raise ValueError("Mã món ăn không được để trống.")
        if item_name is None:
            raise ValueError("Tên món ăn không được để trống.")

        unit_price = _to_int(unit_price, "Đơn giá phải là số nguyên.")
        if unit_price < 0:
            raise ValueError("Đơn giá không được âm.")

        quantity = _to_int(quantity, "Số lượng phải là số nguyên.")
        if quantity <= 0:
            raise ValueError("Số lượng phải lớn hơn 0.")

        if prep_time is not None:
            prep_time = _to_int(prep_time, "Thời gian chế biến phải là số nguyên.")
            if prep_time < 0:
                raise ValueError("Thời gian chế biến không được âm.")

        if subtotal is not None:
            subtotal = _to_int(subtotal, "Thành tiền phải là số nguyên.")
            if subtotal < 0:
                raise ValueError("Thành tiền không được âm.")

        self.menu_item_id = str(menu_item_id)
        self.item_name = str(item_name)
        self.unit_price = unit_price
        self.quantity = quantity
        self.note = note if note is not None else ""
        self.prep_time = prep_time

        # Chưa có hoặc bằng 0 thì tự tính: đơn giá * số lượng
        if subtotal is None or subtotal == 0:
            subtotal = unit_price * quantity
        self.subtotal = subtotal

    def update_quantity(self, quantity):
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Số lượng phải là số nguyên lớn hơn 0.")
        self.quantity = quantity
        self.subtotal = self.unit_price * quantity

    def update_note(self, note):
        self.note = note

    def to_dict(self):
        data = HashTable()
        data.put("menu_item_id", self.menu_item_id)
        data.put("item_name", self.item_name)
        data.put("unit_price", self.unit_price)
        data.put("quantity", self.quantity)
        data.put("subtotal", self.subtotal)
        data.put("note", self.note)
        if self.prep_time is not None:
            data.put("prep_time", self.prep_time)
        return data

    @classmethod
    def from_dict(cls, data):
        return cls(
            menu_item_id=data.get("menu_item_id"),
            item_name=data.get("item_name"),
            unit_price=data.get("unit_price"),
            quantity=data.get("quantity"),
            note=data.get("note"),
            prep_time=data.get("prep_time"),
            subtotal=data.get("subtotal"),
        )
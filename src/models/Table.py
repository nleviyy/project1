from src.structures.hash_table import HashTable


class TableStatus:
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    RESERVED = "RESERVED"

    @staticmethod
    def get_label(status):
        label = TABLE_STATUS_LABELS.get(str(status))
        if label is None:
            return str(status)
        return label

TABLE_STATUS_LABELS = HashTable()
TABLE_STATUS_LABELS.put("AVAILABLE", "Bàn trống")
TABLE_STATUS_LABELS.put("OCCUPIED", "Đang có khách")
TABLE_STATUS_LABELS.put("RESERVED", "Đã đặt trước")


class Table:
    def __init__(self, id, name, capacity, status="AVAILABLE", current_order_id=None):
        self.id = id
        self.name = name
        self.capacity = capacity
        self.status = status
        self.current_order_id = current_order_id
        self._validate()

    def _validate(self):

        try:
            self.id = int(self.id)
        except (ValueError, TypeError):
            raise ValueError("ID bàn ăn phải là số nguyên dương.")
        if self.id <= 0:
            raise ValueError("ID bàn ăn phải là số nguyên dương (> 0).")

        if not self.name or len(str(self.name).strip()) < 1:
            raise ValueError("Tên bàn ăn không được để trống.")
        self.name = str(self.name).strip()

        try:
            self.capacity = int(self.capacity)
        except (ValueError, TypeError):
            raise ValueError("Sức chứa của bàn phải là số nguyên dương.")
        if self.capacity <= 0:
            raise ValueError("Sức chứa của bàn phải lớn hơn 0.")

        self.status = str(self.status).upper().strip()
        if not TABLE_STATUS_LABELS.contains(self.status):
            raise ValueError(
                "Trạng thái bàn '" + self.status + "' không hợp lệ. "
                "Phải là AVAILABLE, OCCUPIED hoặc RESERVED."
            )

        if self.current_order_id is not None:
            self.current_order_id = str(self.current_order_id).strip()
            if not self.current_order_id:
                self.current_order_id = None

        if self.status == "AVAILABLE" and self.current_order_id is not None:
            raise ValueError("Bàn ở trạng thái AVAILABLE thì current_order_id bắt buộc là None.")

        if self.status == "OCCUPIED" and self.current_order_id is None:
            raise ValueError("Bàn ở trạng thái OCCUPIED thì bắt buộc phải có current_order_id.")

    # ---------- Trạng thái ----------

    @property
    def is_available(self):
        """Bàn thực sự trống: AVAILABLE và không có đơn hàng."""
        return self.status == "AVAILABLE" and self.current_order_id is None

    @property
    def is_occupied(self):
        return self.status == "OCCUPIED"

    def occupy(self, order_id):
        """Gắn đơn hàng vào bàn và đổi sang OCCUPIED."""
        if not order_id or not str(order_id).strip():
            raise ValueError("Mã đơn hàng gắn vào bàn không được để trống.")
        self.status = "OCCUPIED"
        self.current_order_id = str(order_id).strip()
        return True

    def vacate(self):
        """Giải phóng bàn về AVAILABLE."""
        self.status = "AVAILABLE"
        self.current_order_id = None
        return True

    def release(self):
        """Tên khác của vacate."""
        return self.vacate()

    def reserve(self):
        """Đặt trước bàn (RESERVED)."""
        self.status = "RESERVED"
        self.current_order_id = None
        return True

    def check_and_occupy(self, order_id):
        if not self.is_available:
            raise ValueError(
                "Lỗi: Bàn '" + self.name + "' (ID: " + str(self.id) + ") hiện đang ở trạng thái '"
                + self.status + "' hoặc đã có đơn hàng liên kết. Không thể đặt bàn này!"
            )
        return self.occupy(order_id)

    def update_status(self, new_status, order_id=None):

        target_status = str(new_status).upper().strip()
        target_order_id = str(order_id).strip() if order_id else None
        try:
            temp_table = Table(
                id=self.id,
                name=self.name,
                capacity=self.capacity,
                status=target_status,
                current_order_id=target_order_id,
            )
            self.status = temp_table.status
            self.current_order_id = temp_table.current_order_id
            return True
        except ValueError as e:
            print("[Lỗi cập nhật bàn " + str(self.id) + "] " + str(e))
            return False

    # ---------- Chuyển đổi dữ liệu ----------

    def to_dict(self):
        data = HashTable()
        data.put("id", self.id)
        data.put("name", self.name)
        data.put("capacity", self.capacity)
        data.put("status", self.status)
        data.put("current_order_id", self.current_order_id)
        return data

    def model_dump(self):
        return self.to_dict()

    def dict(self):
        return self.to_dict()

    @classmethod
    def from_dict(cls, data):
        name = data.get("name")
        if name is None:
            name = ""
        capacity = data.get("capacity")
        if capacity is None:
            capacity = 4
        status = data.get("status")
        if status is None:
            status = "AVAILABLE"
        return cls(
            id=data.get("id"),
            name=name,
            capacity=capacity,
            status=status,
            current_order_id=data.get("current_order_id"),
        )
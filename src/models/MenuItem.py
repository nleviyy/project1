from src.structures.hash_table import HashTable


class MenuItem:
    def __init__(
        self,
        id,
        name,
        category,
        price,
        unit,
        is_available=True,
        description="",
        prep_time=0,
        image="",
        color="#68452f",
    ):
        self.id = id
        self.name = name
        self.category = category
        self.price = price
        self.unit = unit
        self.is_available = is_available
        self.description = description
        self.prep_time = prep_time
        self.image = image
        self.color = color
        self._validate()

    def _validate(self):
        if not self.id or len(str(self.id).strip()) < 2:
            raise ValueError("ID món ăn phải có ít nhất 2 ký tự.")
        if not self.name or len(str(self.name).strip()) < 1:
            raise ValueError("Tên món không được để trống.")
        if not self.category or len(str(self.category).strip()) < 1:
            raise ValueError("Phân loại (category) không được để trống.")

        try:
            price = float(self.price)
        except (ValueError, TypeError):
            raise ValueError("Đơn giá phải là số hợp lệ.")
        if not price.is_integer():
            raise ValueError("Đơn giá phải là số nguyên (VNĐ).")
        if int(price) < 0:
            raise ValueError("Đơn giá phải lớn hơn hoặc bằng 0.")

        if not self.unit or len(str(self.unit).strip()) < 1:
            raise ValueError("Đơn vị tính không được để trống.")

        if self.prep_time is not None:
            try:
                self.prep_time = int(self.prep_time)
            except (ValueError, TypeError):
                raise ValueError("Thời gian chế biến phải là số nguyên.")
            if self.prep_time < 0:
                raise ValueError("Thời gian chế biến không được âm.")

        self.price = int(price)
        self.id = str(self.id).strip()
        self.name = str(self.name).strip()
        self.category = str(self.category).strip()
        self.unit = str(self.unit).strip()

    def copy(self):
        return MenuItem(
            self.id,
            self.name,
            self.category,
            self.price,
            self.unit,
            self.is_available,
            self.description,
            self.prep_time,
            self.image,
            self.color,
        )

    def update(
        self,
        name=None,
        category=None,
        price=None,
        unit=None,
        is_available=None,
        description=None,
        prep_time=None,
        image=None,
        color=None,
    ):

        old = self.copy()
        if name is not None:
            self.name = name
        if category is not None:
            self.category = category
        if price is not None:
            self.price = price
        if unit is not None:
            self.unit = unit
        if is_available is not None:
            self.is_available = is_available
        if description is not None:
            self.description = description
        if prep_time is not None:
            self.prep_time = prep_time
        if image is not None:
            self.image = image
        if color is not None:
            self.color = color

        try:
            self._validate()
        except (ValueError, TypeError) as e:
            self.name = old.name
            self.category = old.category
            self.price = old.price
            self.unit = old.unit
            self.is_available = old.is_available
            self.description = old.description
            self.prep_time = old.prep_time
            self.image = old.image
            self.color = old.color
            raise ValueError("Cập nhật thất bại, đã khôi phục dữ liệu ban đầu. Lỗi: " + str(e))

    def to_dict(self):
        data = HashTable()
        data.put("id", self.id)
        data.put("name", self.name)
        data.put("category", self.category)
        data.put("price", self.price)
        data.put("unit", self.unit)
        data.put("is_available", self.is_available)
        data.put("description", self.description)
        data.put("prep_time", self.prep_time)
        data.put("image", self.image)
        data.put("color", self.color)
        return data

    @staticmethod
    def _pick(data, key1, key2, key3, default):
        value = data.get(key1)
        if value is None:
            value = data.get(key2)
        if value is None:
            value = data.get(key3)
        if value is None:
            return default
        return value

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=str(cls._pick(data, "id", "item_id", "Item_id", "")),
            name=str(cls._pick(data, "name", "Name", "Name", "")),
            category=str(cls._pick(data, "category", "item_type", "Item_type", "Chưa phân loại")),
            price=cls._pick(data, "price", "unit_price", "Unit_price", 0),
            unit=str(cls._pick(data, "unit", "Unit", "Unit", "phần")),
            is_available=cls._pick(data, "is_available", "status", "Status_of_menuItem", True),
            description=cls._pick(data, "description", "Description", "Description", ""),
            prep_time=cls._pick(data, "prep_time", "Prep_time", "Prep_time", 0),
            image=cls._pick(data, "image", "image", "image", ""),
            color=cls._pick(data, "color", "color", "color", "#68452f"),
        )
from src.structures.linked_list import DoublyLinkedList

class HashNode:

    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.next = None


class HashTable:
    LOAD_FACTOR = 0.75

    def __init__(self, capacity=16):
        self.capacity = capacity if capacity >= 1 else 16
        self.buckets = [None] * self.capacity
        self.size = 0

    def _hash(self, key):
        result = 0
        for ch in str(key):
            result = (result * 31 + ord(ch)) % self.capacity
        return result

    def _find_node(self, key):
        node = self.buckets[self._hash(key)]
        while node is not None:
            if node.key == key:
                return node
            node = node.next
        return None

    def _resize(self):
        old_buckets = self.buckets
        self.capacity *= 2
        self.buckets = [None] * self.capacity
        for head in old_buckets:
            node = head
            while node is not None:
                following = node.next
                index = self._hash(node.key)
                node.next = self.buckets[index]
                self.buckets[index] = node
                node = following

    # ---------- Các thao tác chính ----------

    def put(self, key, value):
        """Thêm mới, hoặc cập nhật nếu key đã có. O(1) trung bình"""
        node = self._find_node(key)
        if node is not None:               # key đã có -> chỉ đổi value
            node.value = value
            return
        index = self._hash(key)
        new_node = HashNode(key, value)    # chưa có -> thêm vào đầu chuỗi
        new_node.next = self.buckets[index]
        self.buckets[index] = new_node
        self.size += 1
        if self.size / self.capacity >= self.LOAD_FACTOR:
            self._resize()


    def get(self, key, default=None):
        node = self._find_node(key)
        if node is None:
            return default
        return node.value

    def contains(self, key):
        return self._find_node(key) is not None

    def remove(self, key):
        index = self._hash(key)
        prev = None
        node = self.buckets[index]
        while node is not None:
            if node.key == key:
                if prev is None:           # nút nằm ở đầu chuỗi
                    self.buckets[index] = node.next
                else:
                    prev.next = node.next
                self.size -= 1
                return True
            prev = node
            node = node.next
        return False

    def pop(self, key, default=None):
        index = self._hash(key)
        prev = None
        node = self.buckets[index]
        while node is not None:
            if node.key == key:
                if prev is None:
                    self.buckets[index] = node.next
                else:
                    prev.next = node.next
                self.size -= 1
                return node.value
            prev = node
            node = node.next
        if default is not None:
            return default
        raise KeyError(key)

    def is_empty(self):
        return self.size == 0

    def clear(self):
        self.buckets = [None] * self.capacity
        self.size = 0

    def __len__(self):
        return self.size

    def __contains__(self, key):
        return self.contains(key)

    def __getitem__(self, key):
        node = self._find_node(key)
        if node is None:
            raise KeyError(key)
        return node.value

    def __setitem__(self, key, value):
        self.put(key, value)

    def __delitem__(self, key):
        if not self.remove(key):
            raise KeyError(key)

    def __iter__(self):
        node = self.keys().head
        while node is not None:
            yield node.data
            node = node.next


    def __eq__(self, other):
        if isinstance(other, HashTable):
            if self.size != other.size:
                return False
            for key in self:
                if not other.contains(key) or self.get(key) != other.get(key):
                    return False
            return True
        if isinstance(other, dict):
            if self.size != len(other):
                return False
            for key in self:
                if key not in other or self.get(key) != other[key]:
                    return False
            return True
        return NotImplemented


    def keys(self):
        result = DoublyLinkedList()
        for i in range(self.capacity):
            node = self.buckets[i]
            while node is not None:
                result.add_last(node.key)
                node = node.next
        return result

    def values(self):
        result = DoublyLinkedList()
        for i in range(self.capacity):
            node = self.buckets[i]
            while node is not None:
                result.add_last(node.value)
                node = node.next
        return result

    def items(self):
        result = DoublyLinkedList()
        for i in range(self.capacity):
            node = self.buckets[i]
            while node is not None:
                result.add_last((node.key, node.value))
                node = node.next
        return result
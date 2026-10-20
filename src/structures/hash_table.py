from src.structures.linked_list import DoublyLinkedList

class HashNode:

    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.next = None


class HashTable:
    def __init__(self, capacity=16):
        self.capacity = capacity
        self.buckets = [None] * capacity
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

    def get(self, key):
        node = self._find_node(key)
        if node is None:
            return None
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

    def is_empty(self):
        return self.size == 0


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
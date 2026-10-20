"""Bảng băm tự cài đặt: chaining cho xung đột, giữ thứ tự thêm vào bằng danh sách liên kết."""
from typing import Any, Iterator, Optional


class HashNode:
    """Một cặp key-value; nằm trong chuỗi của bucket và trong danh sách thứ tự."""

    def __init__(self, key: Any, value: Any):
        self.key = key
        self.value = value
        self.next: Optional["HashNode"] = None
        self.order_prev: Optional["HashNode"] = None
        self.order_next: Optional["HashNode"] = None


class HashTable:
    LOAD_FACTOR = 0.75

    def __init__(self, capacity: int = 32):
        self.capacity: int = capacity if capacity >= 1 else 32
        self.size: int = 0
        self._buckets: list = [None] * self.capacity  # mảng đầu chuỗi của từng bucket
        self._order_head: Optional[HashNode] = None
        self._order_tail: Optional[HashNode] = None

    def _hash(self, key: Any) -> int:
        hash_val = 0
        for char in str(key):
            hash_val = (hash_val * 31 + ord(char)) % self.capacity
        return hash_val

    def _find_node(self, key: Any) -> Optional[HashNode]:
        node = self._buckets[self._hash(key)]
        while node is not None:
            if node.key == key:
                return node
            node = node.next
        return None

    def _link_order(self, node: HashNode) -> None:
        node.order_prev = self._order_tail
        node.order_next = None
        if self._order_tail is None:
            self._order_head = node
        else:
            self._order_tail.order_next = node
        self._order_tail = node

    def _unlink_order(self, node: HashNode) -> None:
        if node.order_prev is None:
            self._order_head = node.order_next
        else:
            node.order_prev.order_next = node.order_next
        if node.order_next is None:
            self._order_tail = node.order_prev
        else:
            node.order_next.order_prev = node.order_prev
        node.order_prev = None
        node.order_next = None

    def _resize(self) -> None:
        old_buckets = self._buckets
        self.capacity *= 2
        self._buckets = [None] * self.capacity
        for head in old_buckets:
            node = head
            while node is not None:
                following = node.next
                index = self._hash(node.key)
                node.next = self._buckets[index]
                self._buckets[index] = node
                node = following

    def _remove_node(self, key: Any) -> Optional[HashNode]:
        index = self._hash(key)
        prev = None
        node = self._buckets[index]
        while node is not None:
            if node.key == key:
                if prev is None:
                    self._buckets[index] = node.next
                else:
                    prev.next = node.next
                self._unlink_order(node)
                self.size -= 1
                return node
            prev = node
            node = node.next
        return None

    def put(self, key: Any, value: Any) -> None:
        node = self._find_node(key)
        if node is not None:
            node.value = value
            return
        node = HashNode(key, value)
        index = self._hash(key)
        node.next = self._buckets[index]
        self._buckets[index] = node
        self._link_order(node)
        self.size += 1
        if self.size / self.capacity >= self.LOAD_FACTOR:
            self._resize()

    def get(self, key: Any, default: Any = None) -> Any:
        node = self._find_node(key)
        return default if node is None else node.value

    def pop(self, key: Any, default: Any = None) -> Any:
        node = self._remove_node(key)
        return default if node is None else node.value

    def remove(self, key: Any) -> bool:
        return self._remove_node(key) is not None

    def contains(self, key: Any) -> bool:
        return self._find_node(key) is not None

    def clear(self) -> None:
        self._buckets = [None] * self.capacity
        self.size = 0
        self._order_head = None
        self._order_tail = None

    def _iter_nodes(self) -> Iterator[HashNode]:
        node = self._order_head
        while node is not None:
            yield node
            node = node.order_next

    def keys(self) -> Iterator[Any]:
        for node in self._iter_nodes():
            yield node.key

    def values(self) -> Iterator[Any]:
        for node in self._iter_nodes():
            yield node.value

    def items(self) -> Iterator[tuple]:
        for node in self._iter_nodes():
            yield (node.key, node.value)

    def __len__(self) -> int:
        return self.size

    def __getitem__(self, key: Any) -> Any:
        node = self._find_node(key)
        if node is None:
            raise KeyError(key)
        return node.value

    def __setitem__(self, key: Any, value: Any) -> None:
        self.put(key, value)

    def __delitem__(self, key: Any) -> None:
        if not self.remove(key):
            raise KeyError(key)

    def __contains__(self, key: Any) -> bool:
        return self.contains(key)

    def __iter__(self) -> Iterator[Any]:
        return self.keys()
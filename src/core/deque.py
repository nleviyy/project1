from typing import Any, Callable, Iterator, Optional


class DequeNode:
    def __init__(self, data: Any):
        self.data: Any = data
        self.prev: Optional["DequeNode"] = None
        self.next: Optional["DequeNode"] = None


class Deque:
    """
    Hàng đợi hai đầu (Double-ended Queue) tự cài đặt trên danh sách liên kết đôi.
    Các thao tác append, append_left, pop, pop_left, add_last, add_first đều đạt O(1).
    Thao tác remove, pop_where đạt O(n).
    """

    def __init__(self):
        self.head: Optional[DequeNode] = None
        self.tail: Optional[DequeNode] = None
        self._size: int = 0

    def __len__(self) -> int:
        return self._size

    @property
    def size(self) -> int:
        return self._size

    def is_empty(self) -> bool:
        return self._size == 0

    def append(self, data: Any) -> None:
        """Thêm phần tử vào cuối hàng đợi (O(1))."""
        new_node = DequeNode(data)
        if self.tail is None:
            self.head = new_node
            self.tail = new_node
        else:
            new_node.prev = self.tail
            self.tail.next = new_node
            self.tail = new_node
        self._size += 1

    def add_last(self, data: Any) -> None:
        """Alias cho append (O(1))."""
        self.append(data)

    def append_left(self, data: Any) -> None:
        """Thêm phần tử vào đầu hàng đợi (O(1))."""
        new_node = DequeNode(data)
        if self.head is None:
            self.head = new_node
            self.tail = new_node
        else:
            new_node.next = self.head
            self.head.prev = new_node
            self.head = new_node
        self._size += 1

    def add_first(self, data: Any) -> None:
        """Alias cho append_left (O(1))."""
        self.append_left(data)

    def pop(self) -> Any:
        """Lấy và xóa phần tử ở cuối hàng đợi (O(1))."""
        if self.tail is None:
            raise IndexError("pop from empty deque")
        data = self.tail.data
        self.tail = self.tail.prev
        if self.tail is None:
            self.head = None
        else:
            self.tail.next = None
        self._size -= 1
        return data

    def pop_left(self) -> Any:
        """Lấy và xóa phần tử ở đầu hàng đợi (O(1))."""
        if self.head is None:
            raise IndexError("pop_left from empty deque")
        data = self.head.data
        self.head = self.head.next
        if self.head is None:
            self.tail = None
        else:
            self.head.prev = None
        self._size -= 1
        return data

    def pop_first(self) -> Any:
        """Alias cho pop_left."""
        return self.pop_left()

    def pop_last(self) -> Any:
        """Alias cho pop."""
        return self.pop()

    def remove_first(self) -> Optional[Any]:
        """Lấy và xóa phần tử đầu tiên, trả về None nếu rỗng."""
        if self.head is None:
            return None
        return self.pop_left()

    def remove(self, data: Any) -> bool:
        """Tìm và xóa phần tử đầu tiên khớp data khỏi Deque (O(n))."""
        curr = self.head
        while curr is not None:
            if curr.data == data:
                break
            curr = curr.next

        if curr is None:
            return False

        if curr.prev is None:
            self.head = curr.next
        else:
            curr.prev.next = curr.next

        if curr.next is None:
            self.tail = curr.prev
        else:
            curr.next.prev = curr.prev

        self._size -= 1
        return True

    def pop_where(self, predicate: Callable[[Any], bool]) -> Optional[Any]:
        """Tìm và xóa phần tử đầu tiên thỏa mãn predicate khỏi Deque (O(n))."""
        curr = self.head
        while curr is not None and not predicate(curr.data):
            curr = curr.next

        if curr is None:
            return None

        if curr.prev is None:
            self.head = curr.next
        else:
            curr.prev.next = curr.next

        if curr.next is None:
            self.tail = curr.prev
        else:
            curr.next.prev = curr.prev

        self._size -= 1
        return curr.data

    def peek_first(self) -> Any:
        if self.head is None:
            return None
        return self.head.data

    def peek_last(self) -> Any:
        if self.tail is None:
            return None
        return self.tail.data

    def clear(self) -> None:
        self.head = None
        self.tail = None
        self._size = 0

    def __iter__(self) -> Iterator[Any]:
        curr = self.head
        while curr is not None:
            yield curr.data
            curr = curr.next

    def to_list(self) -> list:
        return list(self)

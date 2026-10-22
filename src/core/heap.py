from typing import Any, Callable, List, Optional


class Heap:
    """
    Cài đặt Heap tổng quát (mặc định MaxHeap, truyền is_min=True để thành MinHeap) bằng mảng.
    Hỗ trợ push, pop, peek, sift_up, sift_down.
    Độ phức tạp: push O(log n), pop O(log n), peek O(1).
    """

    def __init__(self, key: Optional[Callable[[Any], Any]] = None, is_min: bool = False):
        self._data: List[Any] = []
        self._key = key
        self._is_min = is_min

    def _val(self, item: Any) -> Any:
        return self._key(item) if self._key else item

    def _is_higher_priority(self, a: Any, b: Any) -> bool:
        va, vb = self._val(a), self._val(b)
        return (va < vb) if self._is_min else (va > vb)

    def __len__(self) -> int:
        return len(self._data)

    def is_empty(self) -> bool:
        return len(self._data) == 0

    def peek(self) -> Any:
        if not self._data:
            raise IndexError("Heap rỗng")
        return self._data[0]

    def push(self, item: Any) -> None:
        self._data.append(item)
        self._sift_up(len(self._data) - 1)

    def pop(self) -> Any:
        if not self._data:
            raise IndexError("Heap rỗng")
        if len(self._data) == 1:
            return self._data.pop()

        root = self._data[0]
        self._data[0] = self._data.pop()
        self._sift_down(0)
        return root

    def _sift_up(self, idx: int) -> None:
        parent = (idx - 1) // 2
        while idx > 0 and self._is_higher_priority(self._data[idx], self._data[parent]):
            self._data[idx], self._data[parent] = self._data[parent], self._data[idx]
            idx = parent
            parent = (idx - 1) // 2

    def _sift_down(self, idx: int) -> None:
        n = len(self._data)
        while True:
            left = 2 * idx + 1
            right = 2 * idx + 2
            best = idx

            if left < n and self._is_higher_priority(self._data[left], self._data[best]):
                best = left
            if right < n and self._is_higher_priority(self._data[right], self._data[best]):
                best = right

            if best != idx:
                self._data[idx], self._data[best] = self._data[best], self._data[idx]
                idx = best
            else:
                break


class MaxHeap(Heap):
    """Alias mỏng cho MaxHeap (mặc định is_min=False)."""

    def __init__(self, key: Optional[Callable[[Any], Any]] = None):
        super().__init__(key=key, is_min=False)


class MinHeap(Heap):
    """Alias mỏng cho MinHeap (is_min=True)."""

    def __init__(self, key: Optional[Callable[[Any], Any]] = None):
        super().__init__(key=key, is_min=True)

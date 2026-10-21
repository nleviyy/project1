from typing import Any, Callable, List, Optional


class MaxHeap:
    def __init__(self, key: Optional[Callable[[Any], Any]] = None):
        self._data: List[Any] = []
        self._key = key

    def _val(self, item: Any) -> Any:
        return self._key(item) if self._key else item

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
        while idx > 0 and self._val(self._data[idx]) > self._val(self._data[parent]):
            self._data[idx], self._data[parent] = self._data[parent], self._data[idx]
            idx = parent
            parent = (idx - 1) // 2

    def _sift_down(self, idx: int) -> None:
        n = len(self._data)
        while True:
            left = 2 * idx + 1
            right = 2 * idx + 2
            largest = idx

            if left < n and self._val(self._data[left]) > self._val(self._data[largest]):
                largest = left
            if right < n and self._val(self._data[right]) > self._val(self._data[largest]):
                largest = right

            if largest != idx:
                self._data[idx], self._data[largest] = self._data[largest], self._data[idx]
                idx = largest
            else:
                break


class MinHeap:
    """
    Cài đặt MinHeap (hàng đợi ưu tiên min) bằng mảng.
    Hỗ trợ push, pop, peek, sift_up, sift_down.
    Độ phức tạp: push O(log n), pop O(log n), peek O(1).
    """

    def __init__(self, key: Optional[Callable[[Any], Any]] = None):
        self._data: List[Any] = []
        self._key = key

    def _val(self, item: Any) -> Any:
        return self._key(item) if self._key else item

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
        while idx > 0 and self._val(self._data[idx]) < self._val(self._data[parent]):
            self._data[idx], self._data[parent] = self._data[parent], self._data[idx]
            idx = parent
            parent = (idx - 1) // 2

    def _sift_down(self, idx: int) -> None:
        n = len(self._data)
        while True:
            left = 2 * idx + 1
            right = 2 * idx + 2
            smallest = idx

            if left < n and self._val(self._data[left]) < self._val(self._data[smallest]):
                smallest = left
            if right < n and self._val(self._data[right]) < self._val(self._data[smallest]):
                smallest = right

            if smallest != idx:
                self._data[idx], self._data[smallest] = self._data[smallest], self._data[idx]
                idx = smallest
            else:
                break

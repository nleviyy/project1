import pytest
from src.core.sorting import merge_sort, binary_search
from src.core.heap import MaxHeap, MinHeap
from src.core.deque import Deque
from src.models.HashTable import HashTable


# =====================================================================
# 1. KIỂM THỬ merge_sort
# =====================================================================
def test_merge_sort_empty_and_single():
    assert merge_sort([]) == []
    assert merge_sort([42]) == [42]


def test_merge_sort_duplicates_and_reverse():
    data = [5, 1, 9, 3, 5, 2, 8, 1]
    assert merge_sort(data) == sorted(data)
    assert merge_sort(data, reverse=True) == sorted(data, reverse=True)


def test_merge_sort_stability():
    """Kiểm tra tính ổn định: giữ nguyên thứ tự ban đầu của các phần tử có cùng key."""
    items = [("apple", 2), ("banana", 1), ("cherry", 2), ("date", 1)]
    sorted_items = merge_sort(items, key=lambda x: x[1])
    # ban đầu banana trước date (cùng 1), apple trước cherry (cùng 2)
    assert sorted_items == [("banana", 1), ("date", 1), ("apple", 2), ("cherry", 2)]


# =====================================================================
# 2. KIỂM THỬ binary_search
# =====================================================================
def test_binary_search_various_cases():
    arr = [10, 20, 30, 40, 50, 60]
    assert binary_search([], 10) == -1
    assert binary_search(arr, 10) == 0  # đầu
    assert binary_search(arr, 60) == 5  # cuối
    assert binary_search(arr, 30) == 2  # giữa
    assert binary_search(arr, 25) == -1  # không tồn tại
    assert binary_search(arr, 5) == -1
    assert binary_search(arr, 70) == -1


# =====================================================================
# 3. KIỂM THỬ MaxHeap (Top-k)
# =====================================================================
def test_max_heap_top_k():
    data = [15, 3, 27, 8, 42, 11, 65, 20]
    heap = MaxHeap()
    for x in data:
        heap.push(x)

    extracted = [heap.pop() for _ in range(len(data))]
    assert extracted == sorted(data, reverse=True)


# =====================================================================
# 4. KIỂM THỬ Deque
# =====================================================================
def test_deque_operations():
    d = Deque()
    assert len(d) == 0
    assert d.is_empty() is True

    d.append(2)
    d.append(3)
    d.append_left(1)
    assert list(d) == [1, 2, 3]
    assert len(d) == 3

    assert d.pop() == 3
    assert d.pop_left() == 1
    assert len(d) == 1
    assert d.pop() == 2
    assert d.is_empty() is True

    with pytest.raises(IndexError):
        d.pop()
    with pytest.raises(IndexError):
        d.pop_left()


# =====================================================================
# 5. KIỂM THỬ HashTable
# =====================================================================
def test_hash_table_extended_features():
    ht = HashTable(capacity=4)
    ht.put("k1", 100)
    ht.put("k2", 200)
    assert ht.get("k1") == 100
    assert "k1" in ht

    # Khóa trùng ghi đè giá trị
    ht.put("k1", 150)
    assert ht.get("k1") == 150
    assert len(ht) == 2

    # Remove
    assert ht.remove("k1") is True
    assert ht.remove("k1") is False
    assert "k1" not in ht

    # Resize tự động
    for i in range(50):
        ht.put(f"key_{i}", i)
    assert len(ht) == 51
    assert ht.get("key_25") == 25


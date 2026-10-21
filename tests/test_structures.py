import pytest
from src.structures.linked_list import DoublyLinkedList
from src.structures.hash_table import HashTable
from src.structures.stack import Stack


def test_doubly_linked_list_operations():
    dll = DoublyLinkedList()
    assert dll.is_empty()
    assert len(dll) == 0

    dll.add_last(1)
    dll.add_last(2)
    dll.add_first(0)
    assert len(dll) == 3
    assert list(dll) == [0, 1, 2]
    assert dll[0] == 0
    assert dll[1] == 1
    assert dll[2] == 2

    assert dll.peek_first() == 0
    assert dll.peek_last() == 2

    assert dll.remove_first() == 0
    assert dll.remove_last() == 2
    assert len(dll) == 1
    assert dll[0] == 1

    dll.add_last(3)
    assert dll.remove(3) is True
    assert dll.remove(99) is False

    dll.clear()
    assert dll.is_empty()
    assert len(dll) == 0


def test_hash_table_operations():
    ht = HashTable()
    assert ht.is_empty()
    assert len(ht) == 0

    ht.put("apple", 10)
    ht["banana"] = 20
    assert len(ht) == 2
    assert ht.get("apple") == 10
    assert ht["banana"] == 20
    assert "apple" in ht
    assert "cherry" not in ht

    assert ht.remove("apple") is True
    assert "apple" not in ht
    assert len(ht) == 1

    with pytest.raises(KeyError):
        _ = ht["apple"]

    ht.clear()
    assert ht.is_empty()
    assert len(ht) == 0


def test_stack_operations():
    s = Stack()
    assert s.is_empty()
    assert len(s) == 0

    s.push("a")
    s.push("b")
    assert s.peek() == "b"
    assert len(s) == 2

    assert s.pop() == "b"
    assert s.pop() == "a"
    assert s.pop() is None
    assert s.is_empty()

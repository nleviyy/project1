from src.structures.linked_list import DoublyLinkedList

class Stack:

    def __init__(self):
        self._items = DoublyLinkedList()

    def push(self, data):
        self._items.add_last(data)

    def pop(self):
        return self._items.remove_last()

    def peek(self):
        return self._items.peek_last()

    def is_empty(self):
        return self._items.is_empty()

    def size(self):
        return self._items.size

    def clear(self):
        self._items.clear()
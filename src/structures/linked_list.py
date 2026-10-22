class Node:

    def __init__(self, data):
        self.data = data
        self.prev = None
        self.next = None


class DoublyLinkedList:

    def __init__(self):
        self.head = None   # nút đầu
        self.tail = None   # nút cuối
        self.size = 0      # số phần tử

    def is_empty(self):
        return self.size == 0

    def __len__(self):
        return self.size

    def __iter__(self):
        node = self.head
        while node is not None:
            yield node.data
            node = node.next

    def __getitem__(self, index):
        if not isinstance(index, int):
            raise TypeError("Danh sách chỉ hỗ trợ chỉ số nguyên.")
        if index < 0:
            index += self.size
        if index < 0 or index >= self.size:
            raise IndexError("Chỉ số nằm ngoài phạm vi danh sách.")

        node = self.head
        for _ in range(index):
            node = node.next
        return node.data

    def __setitem__(self, index, data):
        if not isinstance(index, int):
            raise TypeError("Danh sách chỉ hỗ trợ chỉ số nguyên.")
        if index < 0:
            index += self.size
        if index < 0 or index >= self.size:
            raise IndexError("Chỉ số nằm ngoài phạm vi danh sách.")

        node = self.head
        for _ in range(index):
            node = node.next
        node.data = data

    def __eq__(self, other):
        if isinstance(other, (list, tuple)):
            if self.size != len(other):
                return False
            node = self.head
            index = 0
            while node is not None:
                if node.data != other[index]:
                    return False
                node = node.next
                index += 1
            return True
        if isinstance(other, DoublyLinkedList):
            if self.size != other.size:
                return False
            left = self.head
            right = other.head
            while left is not None:
                if left.data != right.data:
                    return False
                left = left.next
                right = right.next
            return True
        return NotImplemented

    # ---------- Thêm ----------

    def add_last(self, data):
        """Thêm vào cuối. O(1)"""
        new_node = Node(data)
        if self.tail is None:              # danh sách đang rỗng
            self.head = new_node
            self.tail = new_node
        else:
            new_node.prev = self.tail
            self.tail.next = new_node
            self.tail = new_node
        self.size += 1

    def add_first(self, data):
        """Thêm vào đầu. O(1)"""
        new_node = Node(data)
        if self.head is None:              # danh sách đang rỗng
            self.head = new_node
            self.tail = new_node
        else:
            new_node.next = self.head
            self.head.prev = new_node
            self.head = new_node
        self.size += 1


    def insert(self, index, data):
        """Chèn phần tử vào vị trí index."""
        if not isinstance(index, int):
            raise TypeError("Chỉ số phải là số nguyên.")
        if index <= 0:
            self.add_first(data)
            return
        if index >= self.size:
            self.add_last(data)
            return
        node = self.head
        for _ in range(index):
            node = node.next
        new_node = Node(data)
        new_node.prev = node.prev
        new_node.next = node
        node.prev.next = new_node
        node.prev = new_node
        self.size += 1



    def remove_first(self):
        if self.head is None:
            return None
        data = self.head.data
        self.head = self.head.next
        if self.head is None:              # vừa lấy phần tử cuối cùng
            self.tail = None
        else:
            self.head.prev = None
        self.size -= 1
        return data

    def remove_last(self):
        if self.tail is None:
            return None
        data = self.tail.data
        self.tail = self.tail.prev
        if self.tail is None:              # vừa lấy phần tử cuối cùng
            self.head = None
        else:
            self.tail.next = None
        self.size -= 1
        return data

    # ---------- Xem (không lấy ra) ----------

    def peek_first(self):
        if self.head is None:
            return None
        return self.head.data

    def peek_last(self):
        if self.tail is None:
            return None
        return self.tail.data

    # ---------- Xoá theo giá trị ----------

    def remove(self, data):

        node = self.head
        while node is not None:
            if node.data == data:
                break
            node = node.next

        if node is None:                   # không tìm thấy
            return False

        if node.prev is None:              # nút ở đầu
            self.head = node.next
        else:
            node.prev.next = node.next

        if node.next is None:              # nút ở cuối
            self.tail = node.prev
        else:
            node.next.prev = node.prev

        self.size -= 1
        return True

    def clear(self):
        self.head = None
        self.tail = None
        self.size = 0
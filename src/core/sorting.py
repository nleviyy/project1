from typing import Any, Callable, List, Optional


def merge_sort(
    items: List[Any],
    key: Optional[Callable[[Any], Any]] = None,
    reverse: bool = False,
) -> List[Any]:
    """
    Thuật toán sắp xếp trộn (Merge Sort) ổn định (stable), độ phức tạp O(n log n).
    Không sử dụng sorted() hay list.sort().
    """
    if len(items) <= 1:
        return list(items)

    def _merge(left: List[Any], right: List[Any]) -> List[Any]:
        result = []
        i = 0
        j = 0
        while i < len(left) and j < len(right):
            val_l = key(left[i]) if key else left[i]
            val_r = key(right[j]) if key else right[j]

            if not reverse:
                # Ổn định: phần tử bên trái <= phần tử bên phải thì lấy bên trái trước
                if val_l <= val_r:
                    result.append(left[i])
                    i += 1
                else:
                    result.append(right[j])
                    j += 1
            else:
                # reverse: phần tử bên trái >= phần tử bên phải thì lấy bên trái trước
                if val_l >= val_r:
                    result.append(left[i])
                    i += 1
                else:
                    result.append(right[j])
                    j += 1

        while i < len(left):
            result.append(left[i])
            i += 1
        while j < len(right):
            result.append(right[j])
            j += 1
        return result

    mid = len(items) // 2
    left_half = merge_sort(items[:mid], key=key, reverse=reverse)
    right_half = merge_sort(items[mid:], key=key, reverse=reverse)
    return _merge(left_half, right_half)


def binary_search(
    sorted_items: List[Any],
    target: Any,
    key: Optional[Callable[[Any], Any]] = None,
) -> int:
    """
    Tìm kiếm nhị phân trên danh sách đã sắp xếp tăng dần.
    Trả về chỉ số index nếu tìm thấy, ngược lại trả về -1.
    """
    low = 0
    high = len(sorted_items) - 1

    while low <= high:
        mid = (low + high) // 2
        val = key(sorted_items[mid]) if key else sorted_items[mid]
        if val == target:
            return mid
        elif val < target:
            low = mid + 1
        else:
            high = mid - 1

    return -1


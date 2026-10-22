"""Re-export HashTable từ src.structures.hash_table để đảm bảo đồng nhất một phiên bản duy nhất trong toàn hệ thống."""
from src.structures.hash_table import HashNode, HashTable

__all__ = ["HashNode", "HashTable"]
from enum import Enum

class SyncStatus(str, Enum):
    pending = "pending"
    success = "success"
    failed = "failed"
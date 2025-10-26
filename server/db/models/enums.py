from enum import Enum

class SyncStatus(str, Enum):
    pending = "pending"
    partial = "partial"
    synced = "synced"
    error = "error"
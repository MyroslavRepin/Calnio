from enum import Enum

class SyncStatus(str, Enum):
    """
    Synchronization status for tasks and events.
    
    Valid values:
        pending: Task is waiting to be synchronized
        success: Task was successfully synchronized  
        failed: Task synchronization failed
    """
    pending = "pending"
    success = "success"
    failed = "failed"
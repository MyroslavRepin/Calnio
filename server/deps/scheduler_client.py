from apscheduler.schedulers.asyncio import AsyncIOScheduler

_scheduler: AsyncIOScheduler | None = None

def get_scheduler() -> AsyncIOScheduler:
    """
    Retrieve or create a global instance of an AsyncIOScheduler.

    This function checks if a global AsyncIOScheduler instance exists.
    If it does, the same instance is returned. Otherwise, a new instance
    of AsyncIOScheduler is created and returned. This ensures that the
    scheduler is a singleton within the scope of its use.

    Returns:
        AsyncIOScheduler: The singleton instance of the AsyncIOScheduler.
    """
    global _scheduler

    if _scheduler is None:
        _scheduler = AsyncIOScheduler()

    return _scheduler


from apscheduler.schedulers.background import BlockingScheduler


def display():
    print("This is a scheduled task.")

scheduler = BlockingScheduler()
scheduler.add_job(display, 'interval', seconds=2)
scheduler.start()
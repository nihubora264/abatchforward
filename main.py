from bot import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from plugins.forwards.utils.background import handle_forward_queue
import datetime

if __name__ == '__main__':
    scheduler = AsyncIOScheduler()
    # start after 10 second
    scheduler.add_job(handle_forward_queue, 'date', run_date=datetime.datetime.now() + datetime.timedelta(seconds=10))
    scheduler.start()
    Bot().run()
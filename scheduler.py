from apscheduler.schedulers.blocking import BlockingScheduler

from database import init_db
from football_api import check_results


from config import DATABASE_URL

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Check your .env file."
    )
print("🚀 EdgeClass Scheduler Started")

init_db()

from database import debug_predictions

debug_predictions()
exit()

scheduler = BlockingScheduler()

scheduler.add_job(
    check_results,
    "interval",
    minutes=1
)

scheduler.start()
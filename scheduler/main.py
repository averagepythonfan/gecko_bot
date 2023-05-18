import schedule
import time
from tasks import PairTask, ModelTask, GeckoCoinAPIException


def pair_job():
    p = PairTask()
    try:
        p.update_data()
        PairTask.admin_notification('successfully')
    except GeckoCoinAPIException:
        PairTask.admin_notification('fail')


def model_job():
    m = ModelTask()
    m.do_runs()


schedule.every().day.at("10:00").do(model_job)
schedule.every(12).hours.at("10:00").do(pair_job)


while True:
    schedule.run_pending()
    time.sleep(1)

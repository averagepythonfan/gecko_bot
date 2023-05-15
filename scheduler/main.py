import schedule
import time
from tasks import PairTask, ModelTask

def pair_job():
    p = PairTask()
    p.update_data()

def model_job():
    m = ModelTask()
    m.do_runs()

schedule.every().day.at("10:00").do(model_job)
schedule.every(12).hours.at("10:00").do(pair_job)


while True:
    schedule.run_pending()
    time.sleep(1)

import requests
import rapidjson

from cogs.api.mongoApi import StatsApi
from pymongo import MongoClient

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger


client = MongoClient("mongodb://51.222.13.110:27017")
Api = StatsApi()
players_db = client.stats.players


def run():
    player_list = list(players_db.find().distinct('_id'))
    print(len(player_list))
    if len(player_list) > 100:
        for i in range(0, len(player_list), 100):
            Api.update_stats(player_list[i:i + n])
    else:
        Api.update_stats(player_list)


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(run, CronTrigger.from_crontab('0 10 * * *'))
    scheduler.add_job(run, CronTrigger.from_crontab('0 12 * * *'))
    print('Press Ctrl+{0} to exit'.format('C'))

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass

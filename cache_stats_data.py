import requests
import rapidjson

from cogs.api.mongoApi import StatsApi
from pymongo import MongoClient

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger


client = MongoClient("mongodb://51.222.13.110:27017")
Api = StatsApi()
players_db = client.stats.players


def run(realm):
    player_list = list(players_db.find({'realm': realm}).distinct('_id'))
    if len(player_list) == 0:
        print(f'No players on {realm}')
        return
    elif len(player_list) > 100:
        n = 100
        for i in range(0, len(player_list), n):
            Api.update_stats(player_list[i:i + n])
    else:
        Api.update_stats(player_list)


def refresh_wn8(realm):
    player_list = players_db.find({'realm': realm}).distinct('_id')
    Api.add_career_wn8(player_list)


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    # Refresh sessions
    scheduler.add_job(refresh_wn8, CronTrigger.from_crontab(
        '0 9 * * *'), args=['NA'])
    scheduler.add_job(refresh_wn8, CronTrigger.from_crontab(
        '0 1 * * *'), args=['EU'])
    scheduler.add_job(refresh_wn8, CronTrigger.from_crontab(
        '0 23 * * *'), args=['RU'])
    # Refresh WN8
    scheduler.add_job(refresh_wn8, CronTrigger.from_crontab(
        '10 9 * * *'), args=['NA'])
    scheduler.add_job(refresh_wn8, CronTrigger.from_crontab(
        '10 1 * * *'), args=['EU'])
    scheduler.add_job(refresh_wn8, CronTrigger.from_crontab(
        '10 23 * * *'), args=['RU'])

    print('Press Ctrl+{0} to exit'.format('C'))

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass

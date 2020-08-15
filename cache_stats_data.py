import requests
import rapidjson

from cogs.api.mongoApi import StatsApi
from pymongo import MongoClient
from pymongo import InsertOne, UpdateOne

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger


client = MongoClient("mongodb://51.222.13.110:27017")
Api = StatsApi()
players_db = client.stats.players
tankaverages = client.glossary.tankaverages


def run(realm):
    print(f'Working on {realm}')
    player_list = list(players_db.find({'realm': realm}).distinct('_id'))
    if len(player_list) == 0:
        print(f'No players on {realm}')
        return
    else:
        Api.update_stats(player_ids_long=player_list, hard=True)


def refresh_wn8(realm):
    player_list = players_db.find({'realm': realm}).distinct('_id')
    Api.add_career_wn8(player_list)


def refresh_tank_avg_cache():
    url = 'https://www.blitzstars.com/api/tankaverages.json'
    res = rapidjson.loads(requests.get(url).text)
    tanks_obj_list = []
    missing = 0
    for tank in res:
        tank.pop('_id')
        glossary_data = tankaverages.find_one({'tank_id': tank.get('tank_id')})
        if glossary_data:
            tank_name = glossary_data.get('name')
            tank_tier = glossary_data.get('tier')
            tank_nation = glossary_data.get('nation')

            tank.update({
                'name': tank_name,
                'tier': tank_tier,
                'nation': tank_nation
            })
            tanks_obj_list.append(
                UpdateOne(glossary_data, {'$set': tank}, upsert=True))
        else:
            missing += 1

    print(missing)
    result = tankaverages.bulk_write(
        tanks_obj_list, ordered=False)
    print(result.bulk_api_result)


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    # Refresh tank averages
    scheduler.add_job(refresh_tank_avg_cache, CronTrigger.from_crontab(
        '15 9 * * *'))
    # Refresh sessions
    scheduler.add_job(run, CronTrigger.from_crontab(
        '0 9 * * *'), args=['NA'])
    scheduler.add_job(run, CronTrigger.from_crontab(
        '0 1 * * *'), args=['EU'])
    scheduler.add_job(run, CronTrigger.from_crontab(
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

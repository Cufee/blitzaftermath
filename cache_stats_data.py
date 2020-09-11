import requests
import rapidjson

from cogs.api.stats_api import StatsApi
from pymongo import MongoClient
from pymongo import InsertOne, UpdateOne

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from datetime import datetime


client = MongoClient("mongodb://51.222.13.110:27017")
Api = StatsApi()
players_db = client.stats.players
tankaverages = client.glossary.tankaverages
db_tanks = client.glossary.tanks


def g_update():
    res = requests.get(
    'https://api.wotblitz.com/wotb/encyclopedia/vehicles/?application_id=add73e99679dd4b7d1ed7218fe0be448&fields=nation,is_premium,tier,tank_id,type,name,turrets,guns,suspensions,images')

    res_json = rapidjson.loads(res.text)

    for tank in res_json.get('data').values():
        db_tanks.update_one({"tank_id": tank.get('tank_id')},
                        {"$set": tank}, upsert=True)

def run(realm):
    print(f'[{datetime.utcnow()}] Working on {realm} sessions')
    player_list = list(players_db.find({'realm': realm}).distinct('_id'))
    if len(player_list) == 0:
        print(f'No players on {realm}')
        return
    else:
        Api.update_stats(player_ids_long=player_list, hard=False, realm=realm)
        Api.update_players(player_ids_long=player_list, realm=realm)


def refresh_wn8(realm):
    print(f'[{datetime.utcnow()}] Working on {realm} WN8')
    player_list = players_db.find({'realm': realm}).distinct('_id')
    Api.add_career_wn8(player_list, realm=realm)
    print(f"Done refreshing career WN8 {realm}")


def refresh_tank_avg_cache():
    print(f'[{datetime.utcnow()}] Working on tank acerages')
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

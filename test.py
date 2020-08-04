from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.blocking import BlockingScheduler
import requests
import rapidjson
from pymongo import MongoClient
from pymongo import InsertOne, UpdateOne
from pymongo.errors import BulkWriteError

from datetime import datetime

client = MongoClient("mongodb://51.222.13.110:27017")
db = client.summer2020contest
glossary = client.glossary
guilds_settings = client.guilds.guilds_settings

guilds = db.guilds
clans = db.clans
players = db.players
tanks = glossary.tanks
tankaverages = glossary.tankaverages
clan_marks = db.marksOfMastery

all_guilds = requests.get('http://127.0.0.1:5000/guilds')

data = rapidjson.loads(all_guilds.text)

for i in data:
    guilds_settings.insert_one(i)

    # wg_player_medals_api_url_base = 'http://api.wotblitz.com/wotb/tanks/achievements/?application_id=add73e99679dd4b7d1ed7218fe0be448&account_id='

    # url = 'https://www.blitzstars.com/api/tankaverages.json'

    # tiers = [5, 6, 7, 8, 9, 10]

    # for tier in tiers:
    #     all_avg = list(tankaverages.find({'tier': (tier), 'nation': 'usa'}).sort(
    #         'meanSd.dpbMean', 1).limit(5))

    #     if not all_avg:
    #         continue

    #     worst_list = []
    #     for tank in all_avg:
    #         name = tank.get('name')
    #         tank_id = tank.get('tank_id')
    #         avg_dmg = tank.get('meanSd').get('dpbMean')
    #         kpbMean = tank.get('meanSd').get('kpbMean')
    #         winrateMean = tank.get('meanSd').get('winrateMean')
    #         lastUpdate = tank.get('last_update')

    #         worst_list.append(
    #             f'{name} - WR:{winrateMean} Damage:{avg_dmg} Kills:{kpbMean} Updated:{dt_object}')
    #     tanks_str = "\n".join(worst_list)
    #     print(f'Tier:{tier} Tanks:\n{tanks_str}\n')

    # res = rapidjson.loads(requests.get(url).text)
    # tanks_obj_list = []
    # missing = 0
    # for tank in res:
    #     tank.pop('_id')
    #     glossary_data = tanks.find_one({'tank_id': tank.get('tank_id')})
    #     if glossary_data:
    #         missing += 1
    #         tank_name = glossary_data.get('name')
    #         tank_tier = glossary_data.get('tier')
    #         tank_nation = glossary_data.get('nation')

    #         tank.update({
    #             'name': tank_name,
    #             'tier': tank_tier,
    #             'nation': tank_nation
    #         })
    #     tanks_obj_list.append(InsertOne(tank))
    # print(missing)
    # result = tankaverages.bulk_write(
    #     tanks_obj_list, ordered=False)
    # print(result.bulk_api_result)

    # all_clans = list(clans.find())
    # print(len(all_clans))
    # for clan_ in all_clans:
    #     clans.update_one(
    #         clan_, {"$set": {'clan_aces_qr_usa_t5': clan_.get('clan_aces_usa_5')}})

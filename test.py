from cogs.stats.render import Render
from datetime import datetime, timedelta
from cogs.api.mongoApi import StatsApi
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.blocking import BlockingScheduler
import requests
import rapidjson
from pymongo import MongoClient
from pymongo import InsertOne, UpdateOne

client = MongoClient("mongodb://51.222.13.110:27017")
guilds_settings = client.guilds.guilds_settings

db = client.summer2020contest
glossary = client.glossary

guilds = db.guilds
clans = db.clans
players = db.players
tanks = glossary.tanks
tankaverages = glossary.tankaverages
clan_marks = db.marksOfMastery


statsApi = StatsApi()
Render(1013072123)

# statsApi.update_players(player_list)
# statsApi.update_stats(player_list)
# player_details, session_all, session_detailed = statsApi.get_session_stats(1013072123, session_duration=(
#     datetime.utcnow() - timedelta(hours=24)))

# print(rapidjson.dumps(session_all, indent=2))
# statsApi.add_premium_time(player_list[0], days_to_add=999)

# all_guilds = requests.get('http://127.0.0.1:5000/guilds')

# data = rapidjson.loads(all_guilds.text)

# for i in data:
#     guilds_settings.insert_one(i)

# wg_player_medals_api_url_base = 'http://api.wotblitz.com/wotb/tanks/achievements/?application_id=add73e99679dd4b7d1ed7218fe0be448&account_id='


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
#             f'{name} - WR:{winrateMean} Damage:{avg_dmg} Kills:{kpbMean}')
#     tanks_str = "\n".join(worst_list)
#     print(f'Tier:{tier} Tanks:\n{tanks_str}\n')

# url = 'https://www.blitzstars.com/api/tankaverages.json'
# res = rapidjson.loads(requests.get(url).text)
# tanks_obj_list = []
# missing = 0
# for tank in res:
#     tank.pop('_id')
#     glossary_data = tankaverages.find_one({'tank_id': tank.get('tank_id')})
#     if glossary_data:
#         tank_name = glossary_data.get('name')
#         tank_tier = glossary_data.get('tier')
#         tank_nation = glossary_data.get('nation')

#         tank.update({
#             'name': tank_name,
#             'tier': tank_tier,
#             'nation': tank_nation
#         })
#         tanks_obj_list.append(
#             UpdateOne(glossary_data, {'$set': tank}, upsert=True))
#     else:
#         missing += 1


# print(missing)
# result = tankaverages.bulk_write(
#     tanks_obj_list, ordered=False)
# print(result.bulk_api_result)

# all_players = list(players.find())
# print(len(all_players))
# for player_ in all_players:
#     players.update_one(
#         player_, {"$unset": {'aces_usa_5': ""}})

# list(tanks.find(
#     self.detailed_query))

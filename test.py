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
stats = client.stats

guilds = client.guilds.guilds_settings
clans = db.clans
players = db.players
players_stats = stats.players
tanks = glossary.tanks
tankaverages = glossary.tankaverages
clan_marks = db.marksOfMastery


# # Cache glossary
# res = requests.get(
#     'https://api.wotblitz.com/wotb/encyclopedia/vehicles/?application_id=add73e99679dd4b7d1ed7218fe0be448&fields=nation,is_premium,tier,tank_id,type,name,turrets,guns,suspensions,images')

# res_json = rapidjson.loads(res.text)

# for tank in res_json.get('data').values():
#     tanks.update_one({"tank_id": tank.get('tank_id')},
#                      {"$set": tank}, upsert=True)

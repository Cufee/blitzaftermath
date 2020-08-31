from datetime import datetime, timedelta
# from apscheduler.triggers.cron import CronTrigger
# from apscheduler.schedulers.blocking import BlockingScheduler
import requests
import rapidjson
from pymongo import MongoClient
from pymongo import InsertOne, UpdateOne

from cogs.api.guild_settings_api import API_v2

# from cogs.api.mongoApi import StatsApi
# from cogs.stats.render import Render

client = MongoClient("mongodb://51.222.13.110:27017")
guilds_settings = client.guilds.guilds_settings

db = client.summer2020contest
glossary = client.glossary
stats = client.stats

guilds = client.guilds.guilds_settings
clans = db.clans
players = db.players
players_stats = stats.players
db_tanks = glossary.tanks
tankaverages = glossary.tankaverages
clan_marks = db.marksOfMastery


# # Cache glossary
# res = requests.get(
#     'https://api.wotblitz.com/wotb/encyclopedia/vehicles/?application_id=add73e99679dd4b7d1ed7218fe0be448&fields=nation,is_premium,tier,tank_id,type,name,turrets,guns,suspensions,images')

# res_json = rapidjson.loads(res.text)

# for tank in res_json.get('data').values():
#     tanks.update_one({"tank_id": tank.get('tank_id')},
#                      {"$set": tank}, upsert=True)

# Migrate DB
Guilds_API = API_v2()
all_guild_raw = requests.get("http://127.0.0.1:5000/guilds")
all_guilds = rapidjson.loads(all_guild_raw.text)
for guild_settings in all_guilds:
    guild_id = str(guild_settings.get("guild_id"))
    guild_name = str(guild_settings.get("guild_name"))
    replay_channels_raw = str(guild_settings.get("guild_channels_replays"))
    Guilds_API.add_new_guild(guild_id, guild_name)

    if ";" in replay_channels_raw:
        replay_channels = replay_channels_raw.split(";")
    else:
        replay_channels = [replay_channels_raw]

    new_settings = {
        "guild_channels_replays": replay_channels
    }

    Guilds_API.update_guild(guild_id, settings=new_settings)
    print(f"Migrated {guild_name}")
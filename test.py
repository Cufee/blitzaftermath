from datetime import datetime, timedelta
import time
# from apscheduler.triggers.cron import CronTrigger
# from apscheduler.schedulers.blocking import BlockingScheduler
import requests
import rapidjson
from pymongo import MongoClient
from pymongo import InsertOne, UpdateOne

from cogs.api.guild_settings_api import API_v2

from cogs.api.stats_api import StatsApi
# from cogs.stats.render import Render

client = MongoClient("mongodb://51.222.13.110:27017")
guilds_settings = client.guilds.guilds_settings

db = client.summer2020contest
glossary = client.glossary
stats = client.stats

# guilds = client.guilds.guilds_settings
# clans = db.clans
# players = db.players
# players_stats = stats.players
# db_tanks = glossary.tanks
# tankaverages = glossary.tankaverages
# clan_marks = db.marksOfMastery
users = stats.users


# Cache glossary
# res = requests.get(
#     'https://api.wotblitz.com/wotb/encyclopedia/vehicles/?application_id=add73e99679dd4b7d1ed7218fe0be448&fields=nation,is_premium,tier,tank_id,type,name,turrets,guns,suspensions,images')

# res_json = rapidjson.loads(res.text)

# for tank in res_json.get('data').values():
#     db_tanks.update_one({"tank_id": tank.get('tank_id')},
#                      {"$set": tank}, upsert=True)

# from cogs.api.clan_rating_api import ClansRating

# cr = ClansRating()
# sa = StatsApi()

# # cr.add_clan(realm="NA", clan_tag="-MM")

# details = cr.get_clan_details(realm="NA", clan_tag="-MM")

# members = details.get("members_ids")

# time_start = time.time()
# duration = datetime.now() - timedelta(days=8)
# for m in members:
#     try:
#         _ = sa.get_session_stats(m, session_duration=duration)
#     except:
#         continue
# time_end = time.time()
# print(time_end - time_start)

# Need to write async mongo api using Motor
# https://towardsdatascience.com/fast-and-async-in-python-accelerate-your-requests-using-asyncio-62dafca83c33
# https://docs.python.org/3/library/asyncio-sync.html#asyncio.Semaphore

# from cogs.clan_activity.service.async_mongo_api import AsyncClanActivityAPI

# API = AsyncClanActivityAPI()

# API.enable_for_clan(("NA", "RUS_"))

# Migration script
# from cogs.pay_to_win.stats_module import CustomBackground
# from cogs.api.discord_users_api import DiscordUsersApi

# du = DiscordUsersApi()
# bg = CustomBackground()

# for u in users.find():
#     u_id = u.get("_id")
#     u_id_str = str(u_id)
#     res = bg.get(u_id_str)
#     if res:
#         continue
#     else:
#         raw_url = f"https://res.cloudinary.com/vkodev/image/upload/v1599849089/Aftermath/{u_id}.jpg"
#         try:
#             err, link = bg.put(u_id_str, raw_url)
#             if err:
#                 continue
#             print("ok")
#         except:
#             continue
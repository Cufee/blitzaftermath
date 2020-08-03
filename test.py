from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.blocking import BlockingScheduler
import requests
import rapidjson
from pymongo import MongoClient
from pymongo import InsertOne, UpdateOne
from pymongo.errors import BulkWriteError

client = MongoClient("mongodb://51.222.13.110:27017")
db = client.summer2020contest
glossary = client.summer2020contest

guilds = db.guilds
clans = db.clans
players = db.players
tanks = glossary.tanks
clan_marks = db.marksOfMastery

wg_player_medals_api_url_base = 'http://api.wotblitz.com/wotb/tanks/achievements/?application_id=add73e99679dd4b7d1ed7218fe0be448&account_id='


# def test1():
#     print('test 1')


# def test2():
#     print('test 2')


# if __name__ == "__main__":
#     scheduler = BlockingScheduler()
#     scheduler.add_job(test1, 'interval', seconds=1)
#     scheduler.add_job(test2, 'interval', seconds=3)

#     print('Press Ctrl+{0} to exit'.format('C'))

#     try:
#         scheduler.start()
#     except (KeyboardInterrupt, SystemExit):
#         pass
# url = 'https://api.wotblitz.com/wotb/account/info/?application_id=add73e99679dd4b7d1ed7218fe0be448&account_id='


# def divide_chunks(l, n):
#     # looping till length l
#     for i in range(0, len(l), n):
#         yield l[i:i + n]


# player_ids = players.find().distinct('player_id')
# requst_list = list(divide_chunks(player_ids, 90))

# for list_ in requst_list:
#     req_url = url + ','.join(str(p) for p in list_)
#     res = requests.get(req_url)

#     for player_ in list_:
#         player_name_ = players.find_one({'player_id': player_})
#         if player_name_ and player_name_ != 'Unknown':
#             print('skipped')
#             continue
#         res_j = rapidjson.loads(res.text)
#         data = res_j.get(
#             'data', {})
#         player_data = data.get(str(player_), {})

#         if not player_data:
#             continue
#         player_name = player_data.get(
#             'nickname', 'Unknown')

#         players.update_one({'player_id': player_}, {
#                            "$set": {'player_name': player_name}})
#         print(player_name)

# for player_ in all_players:
#     player_.update_one(player_, {'$set': {'aces': player_.get('aces_usa_5')}})

all_clans = list(clans.find())

print(len(all_clans))

for clan_ in all_clans:
    clans.update_one(
        clan_, {"$set": {'clan_aces_qr_usa_t5': clan_.get('clan_aces_usa_5')}})

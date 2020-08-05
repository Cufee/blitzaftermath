import requests
import rapidjson
from datetime import datetime
from time import sleep

from pymongo import MongoClient
from pymongo import InsertOne, UpdateOne
from pymongo.errors import BulkWriteError

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

client = MongoClient("mongodb://51.222.13.110:27017")
db = client.summer2020contest
glossary = client.glossary

guilds = db.guilds
clans = db.clans
players = db.players
tanks = glossary.tanks

wg_api_url_base = '/wotb/clans/info/?application_id=add73e99679dd4b7d1ed7218fe0be448&clan_id='
wg_player_api_url_base = '/wotb/account/achievements/?application_id=add73e99679dd4b7d1ed7218fe0be448&account_id='
wg_player_info_api_url_base = '/wotb/account/info/?application_id=add73e99679dd4b7d1ed7218fe0be448&account_id='
wg_clan_api_url_base = '/wotb/clans/list/?application_id=add73e99679dd4b7d1ed7218fe0be448&search='
wg_clan_info_api_url_base = '/wotb/clans/info/?application_id=add73e99679dd4b7d1ed7218fe0be448&clan_id='
wg_player_medals_api_url_base = '/wotb/tanks/achievements/?application_id=add73e99679dd4b7d1ed7218fe0be448&account_id='


class UpdateCache():
    def __init__(self, realm: str = 'NA', nation: str = None, starting_tier: int = 1, fake=False):
        self.nation: str = nation
        self.realm: str = realm
        self.starting_tier: int = starting_tier

        self.detailed_query = {}
        self.detailed_query_name = 'aces_qr'
        if nation:
            self.detailed_query.update({'nation': self.nation})
            self.detailed_query_name += f'_{self.nation}'
        if starting_tier:
            self.detailed_query.update(
                {'tier': {'$gt': (self.starting_tier - 1)}})
            self.detailed_query_name += f'_t{self.starting_tier}'

        detailed_tanks_list = tanks.find(
            self.detailed_query).distinct('tank_id')
        if len(detailed_tanks_list) > 99:
            raise Exception(
                f'Tank list is {len(detailed_tanks_list)}, WG API limit is 100. There is no code to handle list splitting atm')

        print(len(detailed_tanks_list))

        self.detailed_tanks_list_str = ','.join(
            str(t) for t in detailed_tanks_list)

        self.update()

    def get_wg_api_domain(self, realm):
        # Detect realm
        realm = realm.upper()
        if realm == 'RU':
            player_realm = 'ru'
            api_domain = 'http://api.wotblitz.ru'

        elif realm == 'EU':
            player_realm = 'eu'
            api_domain = 'http://api.wotblitz.eu'

        elif realm == 'NA':
            player_realm = 'na'
            api_domain = 'http://api.wotblitz.com'

        elif realm == 'ASIA':
            player_realm = 'asia'
            api_domain = 'http://api.wotblitz.asia'
        else:
            player_realm = 'None'
            api_domain = None
        return api_domain

    def update(self):
        self.api_domain: str = self.get_wg_api_domain(self.realm)
        clans_update_obj = []
        players_update_obj = []

        all_clans = clans.find({'clan_realm': self.realm})
        all_clans_ids = clans.find(
            {'clan_realm': self.realm}).distinct('clan_id')
        all_clans_str = ','.join(str(c) for c in all_clans_ids)
        clans_url = self.api_domain + wg_clan_info_api_url_base + all_clans_str
        clan_res = requests.get(clans_url)
        if clan_res.status_code != 200:
            raise Exception(
                f'Unable to access WG clan API usin {clan_id}. [{clan_res.status_code}]')

        requests_cnt = 0
        player_name_check = []
        for clan in all_clans:
            clan_id = clan.get('clan_id')
            clan_name = clan.get('clan_name')
            print(f'Working on {clan_name}')
            if self.nation or self.starting_tier:
                clan_aces_str = f'clan_{self.detailed_query_name}'
                last_aces = clan.get(clan_aces_str)
            else:
                clan_aces_str = f'clan_aces'
                last_aces = clan.get(clan_aces_str)

            clan_data: dict = rapidjson.loads(clan_res.text).get(
                'data', None)
            current_members: list = clan_data.get(
                str(clan_id), {}).get('members_ids')
            last_members = clan.get('members', [])

            current_members_str = ','.join(str(m) for m in current_members)
            players_url = self.api_domain + wg_player_api_url_base + current_members_str
            requests_cnt += 1
            players_res = requests.get(players_url)
            if players_res.status_code != 200:
                print(
                    f'Unable to fetch player data for {clan_name}. [{players_res.status_code}]')
                continue

            players_res_data: dict = rapidjson.loads(
                players_res.text).get('data', None)

            clan_aces_gained = 0

            for player_id in current_members:
                if requests_cnt % 20 == 0:
                    print('Sleep')
                    sleep(5)
                    if requests_cnt % 200 == 0:
                        print(requests_cnt)
                        sleep(15)

                if last_members != [] and player_id not in last_members:
                    print(
                        f'Skipping and resetting {player_id} due to clan change.')
                    player_update = {
                        f'aces_gained': 0,
                        'timestamp': datetime.utcnow(),
                    }
                    players_update_obj.append(
                        UpdateOne({'player_id': player_id},  {'$set': player_update}, upsert=True))
                    continue

                player_data: dict = players_res_data.get(str(player_id), None)
                current_player_aces = player_data.get(
                    'achievements', {}).get('markOfMastery', 0)
                last_player_data = players.find_one(
                    {'player_id': player_id})

                if not last_player_data:
                    insert_obj = InsertOne({
                        'player_id': player_id,
                        'aces': current_player_aces,
                        'timestamp': datetime.utcnow()
                    })
                    players_update_obj.append(insert_obj)
                    player_name_check.append(player_id)
                    continue

                player_name = last_player_data.get('player_name', None)
                if not player_name:
                    player_name_check.append(player_id)

                last_player_aces: int = last_player_data.get(
                    'aces', current_player_aces)
                last_player_aces_gained: int = last_player_data.get(
                    'aces_gained', 0)
                aces_gained: int = current_player_aces - last_player_aces

                if aces_gained == None:
                    player_update = {
                        f'aces': current_player_aces,
                        'timestamp': datetime.utcnow(),
                    }
                    players_update_obj.append(
                        UpdateOne({'player_id': player_id},  {'$set': player_update}, upsert=True))
                    continue
                elif aces_gained == 0:
                    player_update = {
                        'timestamp': datetime.utcnow(),
                    }
                    players_update_obj.append(
                        UpdateOne({'player_id': player_id},  {'$set': player_update}, upsert=True))
                    continue
                else:
                    player_update = {}

                if self.nation or self.starting_tier:
                    detailed_url = self.api_domain + wg_player_medals_api_url_base + \
                        str(player_id) + '&tank_id=' + \
                        self.detailed_tanks_list_str
                    requests_cnt += 1
                    detailed_res = requests.get(detailed_url)

                    if detailed_res.status_code != 200:
                        print(
                            f'[{player_id}] WG Tanks API responded with {detailed_res.status_code}')
                        continue

                    else:
                        ace_query_data = rapidjson.loads(
                            detailed_res.text).get('data', {}).get(str(player_id), [])
                        if not ace_query_data:
                            print(f'No ace query data for {player_id}')
                            continue

                        current_player_query_aces = 0
                        for tank in ace_query_data:
                            tank_aces = tank.get('achievements', {}).get(
                                'markOfMastery', 0)
                            tank_id = tank.get('tank_id')
                            current_player_query_aces += tank_aces

                        last_player_query_aces: int = last_player_data.get(
                            self.detailed_query_name, current_player_query_aces)

                        if current_player_query_aces == 0:
                            current_player_query_aces = last_player_query_aces

                    if last_player_query_aces <= current_player_query_aces:
                        aces_gained_adjusted = current_player_query_aces - last_player_query_aces
                    else:
                        last_player_query_aces = current_player_query_aces
                        aces_gained_adjusted = 0

                    player_update.update(
                        {f'aces_gained': (last_player_aces_gained + aces_gained_adjusted), self.detailed_query_name: current_player_query_aces})

                else:
                    aces_gained_adjusted = aces_gained
                    player_update.update(
                        {f'aces_gained': (last_player_aces_gained + aces_gained_adjusted), self.detailed_query_name: current_player_query_aces})

                player_update.update(
                    {f'aces': current_player_aces, 'timestamp': datetime.utcnow()})
                players_update_obj.append(UpdateOne({'player_id': player_id},  {
                                          '$set': player_update}, upsert=True))

                clan_aces_gained += aces_gained_adjusted

            if clan_aces_gained == 0:
                clan_update = {
                    'members': current_members,
                    'timestamp': datetime.utcnow()
                }
                clans_update_obj.append(
                    UpdateOne({'clan_id': clan_id},  {'$set': clan_update}, upsert=True))
                continue

            clan_update = {
                clan_aces_str: (last_aces + clan_aces_gained),
                'members': current_members,
                'timestamp': datetime.utcnow()
            }
            clans_update_obj.append(
                UpdateOne({'clan_id': clan_id},  {'$set': clan_update}, upsert=True))

            print(
                f"""
Clan Update:
Last Aces:    {last_aces}
Gained:       {clan_aces_gained}
New Aces:     {(last_aces + clan_aces_gained)}""")

            # Update players without nicknames
            requst_list = list(self.divide_chunks(player_name_check, 99))
            for list_ in requst_list:
                req_url = self.api_domain + wg_player_info_api_url_base + \
                    ','.join(str(p) for p in list_)
                res = requests.get(req_url)
                for player_ in list_:
                    res_j = rapidjson.loads(res.text)
                    if res.status_code != 200:
                        print(
                            f'WG API player info responded with [{res_j.status_code}]')
                        break
                    data = res_j.get(
                        'data', {})

                    player_data = data.get(str(player_), {})
                    if not player_data:
                        continue
                    player_name = player_data.get(
                        'nickname', None)
                    if not player_name:
                        print(f'Failed to fetch name for {player_}')
                        continue

                    player_update = UpdateOne({'player_id': player_}, {'$set': {
                        'player_name': player_name
                    }}, upsert=False)
                    players_update_obj.append(player_update)

            print(
                f'{clan_name} gained {clan_aces_gained} Aces\n')

        try:
            if not fake:
                if clans_update_obj:
                    result_clans = clans.bulk_write(
                        clans_update_obj, ordered=False)
                if players_update_obj:
                    result_players = players.bulk_write(
                        players_update_obj, ordered=False)
                print(
                    f'Requests sent: {requests_cnt}\nClans:\n{result_clans.bulk_api_result}\n\nPlayers:\n{result_players.bulk_api_result}')
            else:
                print(
                    f'THIS WAS A FAKE RUN\nRequests sent: {requests_cnt}\n')

        except Exception as e:
            if e == BulkWriteError:
                print(bwe.details)
                pass
            else:
                print(e)
                pass

    def divide_chunks(self, l, n):
        # looping till length l
        for i in range(0, len(l), n):
            yield l[i:i + n]


def run():
    print('Starting update')
    update = UpdateCache('NA', 'usa', 5)
    print(f'Update complete {datetime.utcnow()}')


def fakerun():
    print('Starting update')
    update = UpdateCache('NA', 'usa', 5, fake=True)
    print(f'Update complete {datetime.utcnow()}')


def reset_gained_aces():
    print('Resetting player Aces')

    players_all = list(players.find())
    player_updates = []

    for player_ in players_all:
        player_update = UpdateOne(player_, {'$set': {
            f'aces_gained': 0,
            'timestamp': datetime.utcnow(),
        }}, upsert=True)
        player_updates.append(player_update)

    result_clans = players.bulk_write(
        player_updates, ordered=False)

    print('Done resetting player Aces')


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(run, CronTrigger.from_crontab('*/30 * * * *'))
    scheduler.add_job(reset_gained_aces,
                      CronTrigger.from_crontab('0 10 * * *'))
    print('Press Ctrl+{0} to exit'.format('C'))

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass

    # run()

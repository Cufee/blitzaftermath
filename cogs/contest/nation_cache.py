import requests
import rapidjson
from datetime import datetime

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
wg_clan_api_url_base = '/wotb/clans/list/?application_id=add73e99679dd4b7d1ed7218fe0be448&search='
wg_clan_info_api_url_base = '/wotb/clans/info/?application_id=add73e99679dd4b7d1ed7218fe0be448&clan_id='
wg_player_medals_api_url_base = '/wotb/tanks/achievements/?application_id=add73e99679dd4b7d1ed7218fe0be448&account_id='


class UpdateCache():
    def __init__(self, realm: str, nation: str, starting_tier: int = 1):
        self.nation: str = nation
        self.realm: str = realm
        self.starting_tier: int = starting_tier

        top_clans_cnt = 10
        top_clans_list = list(clans.find({'clan_realm': realm}).sort(
            'clan_aces', -1))
        self.top_clans = []
        index = 0
        while index <= len(top_clans_list) and index < top_clans_cnt:
            self.top_clans.append(top_clans_list[index].get('clan_id'))
            index += 1

        detailed_tanks_list = tanks.find(
            {'nation': self.nation, 'tier': {'$gt': (self.starting_tier - 1)}}).distinct('tank_id')

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

        for clan in all_clans:
            clan_id = clan.get('clan_id')
            clan_name = clan.get('clan_name')
            print(f'Working on {clan_name}')
            last_aces = clan.get('clan_aces')
            last_query_aces = clan.get(
                f'clan_aces_{self.nation}_{self.starting_tier}')

            clan_data: dict = rapidjson.loads(clan_res.text).get(
                'data', None)
            current_members: list = clan_data.get(
                str(clan_id), {}).get('members_ids')
            last_members = clan.get('members', current_members)

            current_members_str = ','.join(str(m) for m in current_members)
            players_url = self.api_domain + wg_player_api_url_base + current_members_str
            players_res = requests.get(players_url)
            if players_res.status_code != 200:
                print(
                    f'Unable to fetch player data for {clan_name}. [{players_res.status_code}]')
                continue
            players_res_data: dict = rapidjson.loads(
                players_res.text).get('data', None)

            clan_aces_gained = 0
            clan_query_aces_gained = 0
            for player_id in current_members:
                if player_id not in last_members:
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
                        f'aces_{self.nation}_{self.starting_tier}': current_player_aces,
                        'timestamp': datetime.utcnow()
                    })
                    players_update_obj.append(insert_obj)
                    continue

                last_player_aces: int = last_player_data.get(
                    'aces', current_player_aces)
                last_player_query_aces: int = last_player_data.get(
                    f'aces_{self.nation}_{self.starting_tier}', 0)
                aces_gained: int = current_player_aces - last_player_aces

                if aces_gained == 0:
                    continue

                if aces_gained != 0 and clan_id in self.top_clans:
                    detailed_url = self.api_domain + wg_player_medals_api_url_base + \
                        str(player_id) + '&tank_id=' + \
                        self.detailed_tanks_list_str
                    detailed_res = requests.get(detailed_url)

                    if detailed_res.status_code != 200:
                        print(
                            f'[{player_id}] WG Tanks API responded with {detailed_res.status_code}')
                        continue

                    else:
                        ace_query_data = rapidjson.loads(
                            detailed_res.text).get('data', {}).get(str(player_id), [])

                        current_player_query_aces = 0
                        for tank in ace_query_data:
                            tank_aces = tank.get('achievements', {}).get(
                                'markOfMastery', 0)
                            tank_id = tank.get('tank_id')

                            tank_name = tanks.find(
                                {'tank_id': tank_id}).distinct('name')

                            current_player_query_aces += tank_aces
                else:
                    current_player_query_aces = last_player_query_aces

                aces_gained_adjusted = aces_gained
                if last_player_query_aces < current_player_query_aces and last_player_query_aces != 0 and clan_id in self.top_clans:
                    aces_gained_adjusted = current_player_query_aces - last_player_query_aces
                elif last_player_query_aces < current_player_query_aces and last_player_query_aces == 0 and clan_id in self.top_clans:
                    aces_gained_adjusted = 0

                player_update = UpdateOne({'player_id': player_id}, {'$set': {
                    f'aces': current_player_aces,
                    f'aces_gained': aces_gained_adjusted,
                    f'aces_{self.nation}_{self.starting_tier}': current_player_query_aces,
                    'timestamp': datetime.utcnow(),
                }}, upsert=True)
                print(
                    f'---\nPlayer {player_id}\nQuery Aces: {current_player_query_aces}, was {last_player_query_aces}\nRegular Aces: {current_player_aces}, was {last_player_aces}\nGained: {aces_gained_adjusted}')
                players_update_obj.append(player_update)

                clan_aces_gained += aces_gained
                if current_player_query_aces < last_player_query_aces:
                    continue
                elif last_player_query_aces == 0:
                    clan_query_aces_gained = 0
                else:
                    clan_query_aces_gained += (current_player_query_aces -
                                               last_player_query_aces)

            if clan_aces_gained == last_aces:
                continue

            clan_update = UpdateOne({'clan_id': clan_id}, {'$set': {
                'clan_aces': (last_aces + clan_aces_gained),
                f'clan_aces_{self.nation}_{self.starting_tier}': (last_query_aces + clan_query_aces_gained),
                'members': current_members,
                'timestamp': datetime.utcnow()
            }}, upsert=True)
            print(
                f'-----{clan_name} gained {clan_query_aces_gained} Aces, {clan_aces_gained} regular Aces\n')
            clans_update_obj.append(clan_update)

        try:
            if clans_update_obj:
                result_clans = clans.bulk_write(
                    clans_update_obj, ordered=False)
            if players_update_obj:
                result_players = players.bulk_write(
                    players_update_obj, ordered=False)
            print(
                f'Updated {len(clans_update_obj)} clans and {len(players_update_obj)} players')

        except Exception as e:
            if e == BulkWriteError:
                print(bwe.details)
                pass
            else:
                print(e)
                pass


def run():
    print('Starting update')
    update = UpdateCache('NA', 'usa', 5)
    print('Update complete')


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(run, CronTrigger.from_crontab('0 * * * *'))
    print('Press Ctrl+{0} to exit'.format('C'))

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass

    # run()

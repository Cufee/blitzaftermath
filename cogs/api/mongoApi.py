from pymongo import MongoClient
from pymongo import InsertOne, UpdateOne
from pymongo.errors import BulkWriteError
import rapidjson
import requests

from datetime import datetime, timedelta
from time import sleep


def get_wg_api_domain(realm=None, player_id=None):
    # Detect realm
    id_length = len(str(player_id))
    if realm:
        realm = realm.upper()

    if realm == 'RU' or id_length == 8:
        player_realm = 'RU'
        api_domain = 'http://api.wotblitz.ru'

    elif realm == 'EU' or id_length == 9:
        player_realm = 'EU'
        api_domain = 'http://api.wotblitz.eu'

    elif realm == 'NA' or id_length == 10:
        player_realm = 'NA'
        api_domain = 'http://api.wotblitz.com'
    else:
        raise Exception(
            'Unable to find this player on RU, EU or NA. ASIA server queries are not supported by WG.')
    return api_domain, player_realm


def divide_chunks(list, n=99):
    # Split long list into chunks of N size
    for i in range(0, len(list), n):
        yield list[i:i + n]


class GuildApi():
    def __init__(self):
        client = MongoClient("mongodb://51.222.13.110:27017")
        self.guilds_collection = client.guilds
        self.features = client.guilds.features
        self.guilds_settings = client.guilds.guilds_settings

    def get_guild(self, guild_id: int):
        guild_id = long(guild_id)

    def add_guild(self, guild_dict: dict):
        pass

    def check_one_param(self, guild_id: int, key):
        pass

    def check_guild_replays_channel(self, guild_id: int):
        pass

    def check_guild_stats_channel(self, guild_id: int, channel_id: int):
        pass


class StatsApi():
    def __init__(self):
        client = MongoClient("mongodb://51.222.13.110:27017")
        self.stats_collection = client.stats
        self.players = client.stats.players
        self.sessions = client.stats.sessions
        self.clans = client.stats.clans
        self.glossary = client.glossary.tanks

        # WG Stats API URLs
        self.wg_api_personal_data = '/wotb/account/info/?application_id=add73e99679dd4b7d1ed7218fe0be448&account_id='
        self.wg_api_clan_info = '/wotb/clans/accountinfo/?application_id=add73e99679dd4b7d1ed7218fe0be448&extra=clan&account_id='
        self.wg_api_achievements = '/wotb/account/achievements/?application_id=add73e99679dd4b7d1ed7218fe0be448&account_id='
        self.wg_api_statistics_all = '/wotb/account/info/?application_id=add73e99679dd4b7d1ed7218fe0be448&extra=statistics.rating&fields=statistics.rating,statistics.all,updated_at,last_battle_time&account_id='
        self.wg_api_vehicle_statistics = '/wotb/tanks/stats/?application_id=add73e99679dd4b7d1ed7218fe0be448&account_id='
        self.wg_api_vehicle_achievements = '/wotb/tanks/achievements/?application_id=add73e99679dd4b7d1ed7218fe0be448&account_id='

    def update_players(self, player_ids_long: list, realm=None):
        """Takes in a list of player ids and realm (optional). Adds/Updates all players to the database with default settings.\nDoes not cache any stats."""
        if len(player_ids_long) > 100:
            raise Exception(
                'Player IDs list is longer than 100. There is no code to handle this atm.')
        else:
            player_ids = player_ids_long

        # Get API domain through passed realm or first player_id on the list
        if realm:
            api_domain, _ = get_wg_api_domain(realm=realm)
        else:
            api_domain, realm = get_wg_api_domain(player_id=player_ids[0])

        # Count requests send to avoid spam / Not implemented
        requests_ctn = 0
        # Create a string from player IDs
        player_list_str = ','.join(str(p) for p in player_ids)
        url_players = api_domain + self.wg_api_personal_data + player_list_str
        url_player_clans = api_domain + self.wg_api_clan_info + player_list_str
        res_players = requests.get(url_players)
        res_player_clans = requests.get(url_player_clans)
        requests_ctn += 2

        res_player_data_raw = rapidjson.loads(res_players.text)
        res_player_clans_raw = rapidjson.loads(res_player_clans.text)
        if res_players.status_code != 200 or res_player_clans.status_code != 200:
            raise Exception(
                f'WG API returned:\nPlayer data:{res_players.status_code}\nClan data:{res_player_clans.status_code}')
        elif not res_player_data_raw or not res_player_clans_raw:
            raise Exception(f'WG API did not return any data')

        res_player_data = res_player_data_raw.get('data')
        res_player_clans_data = res_player_clans_raw.get('data')

        new_players_list = []
        for player_id in player_ids:
            # Get player details and premium status
            player_details = self.players.find_one({'_id': player_id})
            update_premium = True
            if player_details:
                update_premium = False

            player_data = res_player_data.get(str(player_id))
            player_clan_data = res_player_clans_data.get(str(player_id))

            # Player info
            nickname = player_data.get('nickname')
            last_battle_time = datetime.utcfromtimestamp(
                player_data.get('last_battle_time'))
            updated_at = datetime.utcfromtimestamp(
                player_data.get('updated_at'))

            # Basic clan info
            clan_id = player_clan_data.get('clan_id')
            clan_role = player_clan_data.get('role')
            clan_joined_at = datetime.utcfromtimestamp(
                player_clan_data.get('joined_at'))

            # Detailed clan info
            clan_data = player_clan_data.get('clan')
            clan_name = clan_data.get('name')
            clan_tag = clan_data.get('tag')
            clan_emblem_id = clan_data.get('emblem_set_id')

            new_player = {
                'nickname': nickname,
                'realm': realm,
                'last_battle_time': last_battle_time,
                'clan_id': clan_id,
                'clan_name': clan_name,
                'clan_tag': clan_tag,
                'clan_role': clan_role,
                'clan_joined_at': clan_joined_at,
            }

            if update_premium:
                new_player.update(
                    {'am_premium_expiration': datetime.utcnow()})

            new_players_list.append(UpdateOne({'_id': player_id}, {
                                    '$set': new_player}, upsert=True))

        try:
            if new_players_list:
                result_players = self.players.bulk_write(
                    new_players_list, ordered=False)
                print(f'{datetime.utcnow()}\n{result_players.bulk_api_result}')
            else:
                print(f'{datetime.utcnow()}\nNo valid objects to insert.')
            return ('Done')
        except Exception as e:
            if e == BulkWriteError:
                print(e.details)
            else:
                print(e)
            return ('Something Failed.')

    def update_stats(self, player_ids_long: list, realm=None):
        """Takes in a list of player ids and realm (optional). Updates stats for each player"""
        if len(player_ids_long) > 100:
            raise Exception(
                'Player IDs list is longer than 100. There is no code to handle this atm.')
        else:
            player_ids = player_ids_long

        # Get API domain through passed realm or first player_id on the list
        if realm:
            api_domain, _ = get_wg_api_domain(realm=realm)
        else:
            api_domain, _ = get_wg_api_domain(player_id=player_ids[0])

        # Count requests send to avoid spam / Not implemented
        requests_ctn = 0
        # Create a string from player IDs
        player_list_str = ','.join(str(p) for p in player_ids)
        url_stats_all = api_domain + self.wg_api_statistics_all + player_list_str
        res_stats_all = requests.get(url_stats_all)
        requests_ctn += 1

        res_stats_all_raw = rapidjson.loads(res_stats_all.text)
        if res_stats_all.status_code != 200:
            raise Exception(
                f'WG API returned {res_stats_all.status_code}')
        elif not res_stats_all_raw:
            raise Exception(f'WG API did not return any data')
        res_stats_all_data = res_stats_all_raw.get('data')

        # Time calculation for long sessions
        delata_30_day = (datetime.utcnow() - timedelta(days=30, minutes=1))
        delata_60_day = (datetime.utcnow() - timedelta(days=60, minutes=1))
        delata_90_day = (datetime.utcnow() - timedelta(days=90, minutes=1))

        sessions_list = []
        for player_id in player_ids:
            # Get player details and premium status
            player_details = self.players.find_one({'_id': player_id})
            am_premium_expiration = player_details.get(
                'am_premium_expiration') or datetime.utcnow()
            player_is_premium = False
            if datetime.utcnow() < am_premium_expiration:
                player_is_premium = True

            # Get last player data and sessions
            last_session_list = list(self.sessions.find(
                {'player_id': player_id}).sort('timestamp', -1).limit(1))
            if last_session_list:
                last_session = last_session_list[0]

                # Past sessions long / Not sure how to implement best, safe to remove completely.
                # past_sessions_list = []
                # past_session_30_day = list(self.sessions.find(
                #     {'player_id': player_id}, {'timestamp': {'$gt': delata_30_day}}).sort('timestamp', 1)).limit(1)[0]
                # past_sessions_list.append(past_session_30_day)
                # past_session_60_day = list(self.sessions.find(
                #     {'player_id': player_id}, {'timestamp': {'$gt': delata_30_day}}).sort('timestamp', 1)).limit(1)[0]
                # past_sessions_list.append(past_session_60_day)
                # past_session_90_day = list(self.sessions.find(
                #     {'player_id': player_id}, {'timestamp': {'$gt': delata_30_day}}).sort('timestamp', 1)).limit(1)[0]
                # past_sessions_list.append(past_session_90_day)
            else:
                last_session = {}
                past_sessions_list = []

            last_battles_random = last_session.get('battles_random', 0)
            last_battles_rating = last_session.get('battles_rating', 0)
            last_battles_total = last_battles_random + last_battles_rating

            player_data = res_stats_all_data.get(str(player_id))
            stats_random = player_data.get('statistics', {}).get('all', {})
            battles_random = player_data.get(
                'statistics', {}).get('all', {}).get('battles', 0)
            stats_rating = player_data.get('statistics', {}).get('rating', {})
            battles_rating = player_data.get('statistics', {}).get(
                'rating', {}).get('battles', 0)
            last_battle_time = datetime.utcfromtimestamp(
                player_data.get('last_battle_time'))
            battles_total = battles_random + battles_rating

            if last_battles_total == battles_total and battles_total != 0:
                print(f'Player {player_id} played 0 battles')
                continue

            if player_is_premium:
                # Gather per vehicle stats
                vehicle_stats_url = api_domain + \
                    self.wg_api_vehicle_statistics + str(player_id)
                vehicles_stats_res = requests.get(vehicle_stats_url)
                requests_ctn += 1
                vehicles_stats_raw = rapidjson.loads(vehicles_stats_res.text)
                if vehicles_stats_res.status_code != 200 or not vehicles_stats_raw:
                    raise Exception(
                        f'Failed to get data from WG API, status code {vehicles_stats_res.status_code}')
                vehicles_stats_data = vehicles_stats_raw.get(
                    'data').get(str(player_id))
                vehicles_stats = {}
                for tank_stats in vehicles_stats_data:
                    tank_id = tank_stats.get('tank_id')
                    vehicles_stats.update({str(tank_id): tank_stats})
            else:
                vehicles_stats = None

            player_stats = {
                'player_id': player_id,
                'timestamp': datetime.utcnow(),
                'stats_random': stats_random,
                'battles_random': battles_random,
                'stats_rating': stats_rating,
                'battles_rating': battles_rating,
                'last_battle_time': last_battle_time,
                'archive': False,
                'vehicles': vehicles_stats
            }
            sessions_list.append(InsertOne(player_stats))

            if requests_ctn % 100 == 0:
                sleep(5)

        try:
            if sessions_list:
                result = self.sessions.bulk_write(
                    sessions_list, ordered=False)
                print(f'{datetime.utcnow()}\n{result.bulk_api_result}')
            else:
                print(f'{datetime.utcnow()}\nNo valid objects to insert.')
            return ('Done')
        except Exception as e:
            if e == BulkWriteError:
                print(e.details)
            else:
                print(e)
            return ('Something Failed.')

    def add_premium_time(self, player_id: int, days_to_add=None):
        player_details = self.players.find_one({'_id': player_id})
        if not player_details or not days_to_add:
            raise Exception(
                f'Player with ID {player_id} not found or days_to_add is 0')

        current_expiration = player_details.get(
            'am_premium_expiration') or datetime.utcnow()
        new_expiration = current_expiration + timedelta(days=days_to_add)
        player_update = {
            'am_premium_expiration': new_expiration
        }
        self.players.update_one(player_details, {'$set': player_update})

    def get_session_stats(self, player_id: int, session_duration: datetime = None):
        """Get a dict of the session specified. Where session_duration is a datetime obj (timedelta), will default to last session vs current stats."""
        player_details = self.players.find_one({'_id': player_id})
        if not player_details:
            raise Exception(f'Player with ID {player_id} not found')

        # Check if a player has premium status
        am_premium_expiration = player_details.get(
            'am_premium_expiration') or datetime.utcnow()
        player_is_premium = False
        if datetime.utcnow() < am_premium_expiration:
            player_is_premium = True

        # Request and check basic stats
        api_domain, _ = get_wg_api_domain(player_id=player_id)
        stats_all_url = api_domain + \
            self.wg_api_statistics_all + str(player_id)

        stats_all_res = requests.get(stats_all_url)
        stata_all_res_raw = rapidjson.loads(stats_all_res.text)
        if stats_all_res.status_code != 200 or not stata_all_res_raw:
            raise Exception(
                f'Failed to get player stats, WG responded with {stats_all_res.status_code}')
        if player_is_premium:
            # Request and check detailed stats
            stats_detailed_url = api_domain + \
                self.wg_api_vehicle_statistics + str(player_id)
            stats_detailed_res = requests.get(stats_detailed_url)
            stats_detailed_res_raw = rapidjson.loads(stats_detailed_res.text)

            if stats_detailed_res.status_code != 200 or not stats_detailed_res_raw:
                print(
                    f'Failed to get detailed player stats, WG responded with {stats_detailed_res.status_code}')
                session_detailed = {}
            else:
                # Get current detailed stats
                stats_detailed_tanks = stats_detailed_res_raw.get(
                    'data').get(str(player_id))
                stats_detailed_data = {}
                for tank_stats in stats_detailed_tanks:
                    tank_id = tank_stats.get('tank_id')
                    tank_stats_all = tank_stats
                    stats_detailed_data.update({str(tank_id): tank_stats_all})

                # Get last session object
                if session_duration:
                    last_detailed_stats_list = list(self.sessions.find(
                        {'player_id': player_id, 'vehicles': {'$exists': True, '$ne': stats_detailed_data}, 'timestamp': {'$gt': session_duration}}).sort('timestamp', 1).limit(1))
                    if last_detailed_stats_list:
                        last_detailed_stats_data = last_detailed_stats_list[0].get(
                            'vehicles') or {}
                    else:
                        last_detailed_stats_data = None
                else:
                    last_detailed_stats_list = list(self.sessions.find(
                        {'player_id': player_id, 'vehicles': {'$exists': True, '$ne': stats_detailed_data}}).sort('timestamp', -1).limit(1))

                    if last_detailed_stats_list:
                        last_detailed_stats_data = last_detailed_stats_list[0].get(
                            'vehicles') or {}
                    else:
                        last_detailed_stats_data = None

                if not last_detailed_stats_data:
                    print('Last detailed session not available.')
                    session_detailed = {}
                else:
                    # Compare two dicts using sets
                    set_last_detailed_stats_data = set(
                        last_detailed_stats_data)
                    set_stats_detailed_data = set(stats_detailed_data)
                    session_detailed_diff = (
                        set_stats_detailed_data - set_last_detailed_stats_data)

                    session_detailed = {}
                    for tank in stats_detailed_data.keys():
                        session_old = last_detailed_stats_data.get(
                            tank).get('all') or {}
                        session_current = stats_detailed_data.get(
                            tank).get('all') or {}

                        diff = {key: (session_current.get(key) - session_old.get(
                            key)) for key in session_current.keys()}

                        if diff.get('battles') != 0:
                            tank_name = self.glossary.find_one(
                                {'tank_id': int(tank)}).get('name') or 'Unknown'
                            diff.update({'tank_name': tank_name})
                            session_detailed.update({tank: diff})

        # Check Basic stats
        player_data = stata_all_res_raw.get('data').get(str(player_id))
        stats_random = player_data.get('statistics', {}).get('all', {})
        stats_rating = player_data.get('statistics', {}).get('rating', {})

        if session_duration:
            last_stats_list = list(self.sessions.find({'player_id': player_id, '$or': [{'stats_random': {'$exists': True, '$ne': stats_random}}, {
                                   'stats_rating': {'$exists': True, '$ne': stats_rating}}], 'timestamp': {'$gt': session_duration}}).sort('timestamp', 1).limit(1))
            if not last_stats_list:
                last_stats_list = None
            else:
                last_stats = last_stats_list[0]
        else:
            last_stats_list = list(self.sessions.find({'player_id': player_id, '$or': [{'stats_random': {'$exists': True, '$ne': stats_random}}, {
                                   'stats_rating': {'$exists': True, '$ne': stats_rating}}]}).sort('timestamp', -1).limit(1))
            if not last_stats_list:
                last_stats = None
            else:
                last_stats = last_stats_list[0]

        # Compare stats
        if last_stats:
            session_all_random = {}
            session_all_rating = {}
            random_diff = {key: (stats_random.get(key, 0) - last_stats.get('stats_random').get(
                key, 0)) for key in stats_random.keys()}
            rating_diff = {key: (stats_rating.get(key, 0) - last_stats.get('stats_rating').get(
                key, 0)) for key in stats_rating.keys()}

            session_all = {
                'stats_random': random_diff,
                'stats_rating': rating_diff
            }
        else:
            session_all = {
                'stats_random': None,
                'stats_rating': None
            }

        return player_details, session_all, session_detailed

    def get_vehicle_stats(self, player_id: int, tank_id: int):
        api_domain, realm = get_wg_api_domain(player_id=player_id)
        pass

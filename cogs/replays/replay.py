import requests
import rapidjson


class Replay:
    def __init__(self, replay_urls):
        self.wg_app_token = 'add73e99679dd4b7d1ed7218fe0be448'
        self.wg_api_url_end = f'/wotb/account/info/?&application_id={self.wg_app_token}&account_id='
        self.wg_tanks_api_url_end = f'/wotb/encyclopedia/vehicles/?&application_id={self.wg_app_token}&fields=tier,is_premium,type,name,nation&tank_id='
        self.wg_tank_stats_api_url_end = f'/wotb/tanks/stats/?&application_id={self.wg_app_token}&fields=all&account_id='

        self.base_view_url = 'https://replays.wotinspector.com/en/view/'
        self.base_api_url = 'https://wotinspector.com/api/replay/upload/?details=full&url='

        self.replay_urls = replay_urls
        self.api_urls = []

        for url in replay_urls:
            self.api_urls.append(self.base_api_url + url)

        self.replays = {}

    def process_replays(self):
        for url in self.api_urls:
            replay_data = rapidjson.loads(requests.get(url).text)
            replay_id = replay_data.get('data').get(
                'view_url').replace(self.base_view_url, '')

            battle_summary = self.gather_battle_summary(replay_data)

            protagonist_id = replay_data.get(
                'data').get('summary').get('protagonist')
            players = self.gather_players(
                replay_data.get('data').get('summary'))

            download_url = replay_data.get('data').get('download_url')

            replay = {
                'download_url': download_url,
                'battle_summary': battle_summary,
                'players': players
            }
            self.replays[replay_id] = replay

        return self.replays

    def gather_battle_summary(self, data):

        replay_data = data.get('data')
        winner_team = replay_data.get('summary').get('winner_team')
        battle_type = replay_data.get('summary').get('battle_type')
        battle_duration = replay_data.get('summary').get('battle_duration')
        battle_result = replay_data.get('summary').get('battle_result')
        battle_start_time = replay_data.get(
            'summary').get('battle_start_timestamp')
        map_name = replay_data.get('summary').get('map_name')
        room_type = replay_data.get('summary').get('room_type')
        protagonist = replay_data.get('summary').get('protagonist')

        battle_summary = {
            "protagonist": protagonist,
            "winner_team": winner_team,
            "battle_result": battle_result,
            "battle_type": battle_type,
            "battle_duration": battle_duration,
            "battle_start_timestamp": battle_start_time,
            "map_name": map_name,
            "room_type": room_type
        }

        return battle_summary

    def gather_players(self, replay_summary):
        players = {}
        protagonist_id = replay_summary.get('protagonist')
        players_all = replay_summary.get('details')

        enemies = replay_summary.get('enemies')
        allies = replay_summary.get('allies')

        # Get stats for each player from WG API
        player_ids_all = replay_summary.get(
            'allies') + replay_summary.get('enemies')
        player_ids_all_str = ','.join((str(player)
                                       for player in player_ids_all))
        wg_api_domain, player_realm = self.get_wg_api_domain(protagonist_id)

        players_stats = rapidjson.loads(requests.get(
            wg_api_domain + self.wg_api_url_end + player_ids_all_str).text).get('data')

        # Get all vehicle data from WG API
        vehicles_all = []
        for player in players_all:
            vehicle = player.get('vehicle_descr')
            if vehicle not in vehicles_all:
                vehicles_all.append(vehicle)
        vehicles_all_str = ','.join((str(vehicle)
                                     for vehicle in vehicles_all))
        vehicles_all_data = rapidjson.loads(requests.get(
            wg_api_domain + self.wg_tanks_api_url_end + vehicles_all_str).text).get('data')

        for player in players_all:
            player_id = str(player.get('dbid'))
            clan_tag = player.get('clan_tag')
            nickname = players_stats.get(player_id).get('nickname')
            stats = players_stats.get(player_id).get('statistics').get('all')

            vehicle = vehicles_all_data.get(str(
                player.get('vehicle_descr')))
            vehicle_id = player.get('vehicle_descr')

            try:
                vehicle_stats = rapidjson.loads(requests.get(
                    wg_api_domain + self.wg_tank_stats_api_url_end + player_id + f'&tank_id={vehicle_id}').text).get('data').get(player_id)[0].get('all')
            except:
                vehicle_stats = None

            if int(player_id) in enemies:
                team = 2
            else:
                team = 1

            player_data = {
                player_id: {
                    'nickname': nickname,
                    'clan_tag': clan_tag,
                    'team': team,
                    'vehicle': vehicle,
                    'vehicle_stats': vehicle_stats,
                    'performance': player,
                    'stats': stats
                }
            }

            players.update(player_data)
        return players

    def get_wg_api_domain(self, player_id):
        # Detect realm
        if len(str(player_id)) == 8:
            player_realm = 'ru'
            api_domain = 'http://api.wotblitz.ru'

        if len(str(player_id)) == 9:
            player_realm = 'eu'
            api_domain = 'http://api.wotblitz.eu'

        if len(str(player_id)) == 10:
            player_realm = 'na'
            api_domain = 'http://api.wotblitz.com'

        else:
            player_realm = 'asia'
            api_domain = 'http://api.wotblitz.asia'
        return api_domain, player_realm

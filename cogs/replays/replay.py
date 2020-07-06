import requests
import rapidjson

class Replay:
    def __init__(self, replay_urls):
      self.wg_app_token = 'add73e99679dd4b7d1ed7218fe0be448'
      self.wg_api_url_end = f'/wotb/account/info/?&application_id={self.wg_app_token}&account_id='

      self.base_view_url = 'https://replays.wotinspector.com/en/view/'
      self.base_api_url = 'https://wotinspector.com/api/replay/upload/?url='

      self.replay_urls = replay_urls
      self.api_urls = []

      for url in replay_urls:
        self.api_urls.append(self.base_api_url + url)
      
      self.replays = []
    
    def gather_all(self):
      for url in self.api_urls:
        protagonist_id, replay_id, replay_summary = self.gather_summary(url)

        self.get_wg_api_url(protagonist_id)

        players = self.gather_players(replay_summary)

        replay = {
          'id': replay_id,
          'protagonist': protagonist_id,
          'summary': replay_summary,
          'players': players,
        }
        self.replays.append(replay)
      
      return self.replays

    def gather_summary(self, url):
      res = requests.get(url)
      res_json = rapidjson.loads(res.text)

      protagonist_id = res_json.get('data').get('summary').get('protagonist')
      replay_id = res_json.get('data').get('view_url').replace(self.base_view_url, '')
      replay_summary = res_json.get('data').get('summary')

      return protagonist_id, replay_id, replay_summary

    def gather_players(self, replay_summary):
      players = []

      protagonist_id = int(replay_summary.get('protagonist'))
      allies_string = ','.join(str(player_id) for player_id in replay_summary.get('allies'))
      enemies_string = ','.join(str(player_id) for player_id in replay_summary.get('enemies'))

      wg_api_url_final, player_realm = self.get_wg_api_url(protagonist_id)
      allies_stats = rapidjson.loads(requests.get(wg_api_url_final + allies_string).text)
      enemies_stats = rapidjson.loads(requests.get(wg_api_url_final + enemies_string).text)

      for player_id in allies_stats.get('data'):
        player = {
          'player_id': player_id,
          'relm': player_realm,
          'team': 'allies',
          'data': {
            'all': allies_stats.get('data').get(player_id),
            '30-day': {},
            '60-day': {},
            '90-day': {},
          }
        }
        players.append(player)

      for player_id in enemies_stats.get('data'):
        player = {
          'player_id': player_id,
          'relm': player_realm,
          'team': 'enemies',
          'data': {
            'all': enemies_stats.get('data').get(player_id),
            '30-day': {},
            '60-day': {},
            '90-day': {},
          }
        }
        players.append(player)

      return players

    def get_wg_api_url(self, player_id):
      # Detect realm
      if player_id < 500000000:
        player_realm = 'ru'
        api_domain = 'http://wotblitz.ru'

      if player_id < 1000000000:
        player_realm = 'eu'
        api_domain = 'http://api.wotblitz.eu'

      if player_id < 2000000000:
        player_realm = 'na'
        api_domain = 'http://api.wotblitz.com'

      else:
        player_realm = 'asia'
        api_domain = 'http://api.wotblitz.asia'

      return api_domain + self.wg_api_url_end, player_realm

      

        
import rapidjson
import requests


class Api():
    def __init__(self):
        self.API_URL_BASE = 'http://127.0.0.1:5000'

    def guild_get(self, guild_id, guild_name):
        url = self.API_URL_BASE + '/guild/' + guild_id
        res = requests.get(url)
        enabled_channels = []
        stats = []

        # If guild is not found, add it
        if res.status_code == 404:
            url = self.API_URL_BASE + '/guild'
            guild = {
                'guild_id': guild_id,
                'guild_name': guild_name
            }
            new_res = requests.post(url, json=guild)
        elif res.status_code == 200:
            new_res = res
        else:
            new_res = res
            return {"status_code": new_res.status_code}

        if new_res.status_code == 200:
            res_dict = rapidjson.loads(new_res.text)
            enabled_channels_res = res_dict.get('guild_channels_replays')
            guild_is_premium = res_dict.get('guild_is_premium')
            guild_name_cache = res_dict.get('guild_name')
            stats_res = res_dict.get('guild_render_fields')

            if enabled_channels_res:
                if ';' in enabled_channels_res:
                    enabled_channels = enabled_channels_res.split(';')
                else:
                    enabled_channels = [enabled_channels_res]
            if stats_res:
                if ';' in stats_res:
                    stats = stats_res.split(';')
                else:
                    stats = [stats_res]

            # Update guild name cache
            if guild_name_cache != guild_name:
                url = self.API_URL_BASE + '/guild/' + guild_id
                guild = {
                    'guild_name': guild_name
                }
                res = requests.put(url, json=guild)

            new_guild_obj = {
                "status_code": res.status_code,
                "enabled_channels": enabled_channels,
                "guild_is_premium": guild_is_premium,
                "stats": stats
            }

            return new_guild_obj

        else:
            return {"status_code": res.status_code}

    def guild_put(self, guild_id, dict):
        url = self.API_URL_BASE + '/guild/' + guild_id
        res = requests.get(url)
        if res.status_code != 200:
            return {"status_code": res.status_code}
        current_settings = rapidjson.loads(res.text)
        new_settings = {}
        dict_keys = dict.keys()
        for key in dict_keys:
            values = dict.get(key)
            if isinstance(values, list):
                values = ';'.join(values)
            new_settings[key] = values

        put_res = requests.put(url, json=new_settings)
        if put_res.status_code == 200:
            return True
        else:
            return {"status_code": put_res.status_code}

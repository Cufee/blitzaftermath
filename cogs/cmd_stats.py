from discord.ext import commands, tasks
import discord
import requests
import rapidjson

from cogs.replays.replay import Replay
from cogs.replays.rating import Rating
from cogs.replays.render import Render


API_URL_BASE = 'http://127.0.0.1:5000'
debug = False


def get_guild_settings(guild_id, guild_name):
    url = API_URL_BASE + '/guild/' + guild_id
    res = requests.get(url)
    enabled_channels = []
    stats = []

    # If guild is not found, add it
    if res.status_code == 404:
        url = API_URL_BASE + '/guild'
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
        enabled_channels_res = res_dict.get('guild_channels')
        guild_is_premium = res_dict.get('guild_is_premium')
        guild_name_cache = res_dict.get('guild_name')
        stats_res = res_dict.get('guild_render_fields')

        if enabled_channels_res:
            if ';' in enabled_channels_res:
                enabled_channels = enabled_channels_res.split(';')
            else:
                enabled_channels = [enabled_channels_res, ]
        if stats_res:
            if ';' in stats_res:
                stats = stats_res.split(';')
            else:
                stats = [stats_res, ]

        # Update guild name cache
        if guild_name_cache != guild_name:
            url = 'http://127.0.0.1:5000/guild/' + guild_id
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


def update_guild_settins(guild_id, dict):
    url = API_URL_BASE + '/guild/' + guild_id
    res = requests.get(url)
    if res.status_code != 200:
        return {"status_code": res.status_code}
    current_settings = rapidjson.loads(res.text)
    new_settings = {}
    dict_keys = dict.keys()
    for key in dict_keys:
        value = dict.get(key)
        new_settings[key] = value

    put_res = requests.put(url, json=new_settings)
    if put_res.status_code == 200:
        return True
    else:
        return {"status_code": put_res.status_code}


class blitz_aftermath_stats(commands.Cog):

    def __init__(self, client):
        self.client = client

    # Events
    # @commands.Cog.listener()
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'[Beta] Aftermath Stats cog is ready.')

    # Commands
    @commands.command(aliases=['wr', 'session'])
    async def stats(self, message):
        if message.author == self.client.user:
            return

        guild_id = str(message.guild.id)
        guild_name = str(message.guild.name)

        guild_settings = get_guild_settings(guild_id, guild_name)
        if guild_settings.get('status_code') != 200:
            return

        enabled_channels = guild_settings.get('enabled_channels')
        stats = guild_settings.get('stats')
        guild_is_premium = guild_settings.get('guild_is_premium')

        # Verify channel
        if str(message.channel.id) not in enabled_channels:
            return

    # Commands
    # @commands.command(aliases=[''])


def setup(client):
    client.add_cog(blitz_aftermath_stats(client))

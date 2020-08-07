from datetime import datetime, timedelta
from discord.ext import commands, tasks
import discord
import requests
import rapidjson

from cogs.replays.replay import Replay
from cogs.replays.rating import Rating
from cogs.replays.render import Render
from cogs.api.mongoApi import StatsApi, MongoClient

client = MongoClient("mongodb://51.222.13.110:27017")
players = client.stats.players

debug = False
API = StatsApi()


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
    async def stats(self, message, player_name_str):
        if message.author == self.client.user:
            return
        try:
            # if True:
            if '@' in player_name_str:
                player_name_str = player_name_str
                player_name_str_list = player_name_str.split('@')
                player_name = player_name_str_list[0]
                player_realm = player_name_str_list[1].upper()
                player_details = players.find_one(
                    {'nickname': player_name, 'realm': player_realm})
                if not player_details:
                    raise Exception(
                        'Player not found. This feature is only enabled for a limited number of users during the testing period.')
                player_id = player_details.get('_id')
                player_details, last_stats, session_all, session_detailed = API.get_session_stats(
                    player_id, session_duration=(datetime.utcnow() - timedelta(hours=24)))
                await message.channel.send(f'```{rapidjson.dumps(session_all, indent=2)}```')

        except Exception as e:
            await message.channel.send(f'```{e}```')

    # Commands
    # @commands.command(aliases=[''])


def setup(client):
    client.add_cog(blitz_aftermath_stats(client))

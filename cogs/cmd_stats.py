from datetime import datetime, timedelta
from discord.ext import commands, tasks
import discord
import requests
import rapidjson
import traceback

from cogs.stats.render import Render
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
                        'Player not found. This feature is only enabled for a limited number of users during the testing period. Please reach out to Vovko#0851 if you would like to enable this feature.')
                player_id = player_details.get('_id')

                image = Render(player_id=player_id).render_image()
                await message.channel.send(file=image)

        except Exception as e:
            print(traceback.format_exc())
            await message.channel.send(f'```{e}```')

    # Commands
    # @commands.command(aliases=[''])


def setup(client):
    client.add_cog(blitz_aftermath_stats(client))

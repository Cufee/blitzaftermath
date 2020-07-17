from discord.ext import commands, tasks
import discord
import requests
import rapidjson

from cogs.replays.replay import Replay
from cogs.replays.rating import Rating
from cogs.replays.render import Render
from cogs.api.api import Api

debug = False
Api = Api()


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
        enabled_cahnnels = []
        print('stats')

    # Commands
    # @commands.command(aliases=[''])


def setup(client):
    client.add_cog(blitz_aftermath_stats(client))

from discord.ext import commands, tasks
import discord
import requests
import rapidjson

from cogs.replays.replay import Replay
from cogs.replays.rating import Rating
from cogs.replays.render import Render
from api.api import Api

debug = False
Api = Api()


class maintenance(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.client.remove_command("help")

    # Events
    # @commands.Cog.listener()
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'[Beta] Aftermath Stats cog is ready.')

    # Commands
    # @commands.command(aliases=[''])

    @commands.command(aliases=['help'])
    async def _help(self, ctx):
        guild_id = ctx.guild.id

        help_str = (f"""
Use `v-check TAG@SERVER` to check the current Ace Tanker count of a clan. Individual player contributions are reset every 24 hours.
You can also check the current top 5 clans by Ace Tanker medals using `v-top`.
To analyze a WoT Blitz replay, just send a file and I will do the rest.
        """)

        await ctx.send(help_str)


def setup(client):
    client.add_cog(maintenance(client))

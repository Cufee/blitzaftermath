from datetime import datetime, timedelta
from discord.ext import commands, tasks
import discord
import requests
import rapidjson
import traceback
import re

from cogs.stats.zap_render import Render
from cogs.api.stats_api import StatsApi, MongoClient, get_wg_api_domain
from cogs.api.discord_users_api import DiscordUsersApi

from cogs.pay_to_win.stats_module import CustomBackground

import time

client = MongoClient("mongodb://51.222.13.110:27017")
players = client.stats.players

debug = False
API = StatsApi()
UsersApi = DiscordUsersApi()
bgAPI = CustomBackground()

def zap_render(player_id: int, realm: str, days: int, bg_url: str):
    start = time.time()
    request_dict = {        
        "player_id": player_id,
        "realm": realm,
        "days": days
    }
    player_data = rapidjson.loads(requests.get("http://localhost:6969/player", json=request_dict).text)
    print(f'Zap fetch took {round((time.time() - start), 2)} seconds')
    if player_data.get('error', None):
        raise Exception("Zap failed to fetch data.")

    return Render(player_id=player_id , realm=realm, bg_url=bg_url, data=player_data).render_image()

class blitz_aftermath_zap_stats(commands.Cog):

    def __init__(self, client):
        self.client = client

    # Events
    # @commands.Cog.listener()
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'[Beta] Aftermath Zap-Stats cog is ready.')


    # Commands
    @commands.command(aliases=['z'])
    async def zap(self, message, days_str=0):
        if message.author == self.client.user:
            return

        start = time.time()
        try:
            days = int(days_str)
        except:
            days = 0

        player_id = UsersApi.get_default_player_id(
            discord_user_id=(message.author.id))

        if player_id:
            bg_url = UsersApi.get_custom_bg(message.author.id)
            player_realm = players.find_one(
                {'_id': player_id}).get("realm")
            
            image = zap_render(player_id, player_realm, days, bg_url)

            await message.channel.send(f"Zap took {round((time.time() - start), 2)} seconds.", file=image)
            print(f"Zap took {round((time.time() - start), 2)} seconds.")
            return None
        else:
            await message.channel.send(f'You do not have a default WoT Blitz account set.\nUse `{self.client.command_prefix[0]}iam Username@Server` to set a default account for me to look up.')
            return None

def setup(client):
    client.add_cog(blitz_aftermath_zap_stats(client))

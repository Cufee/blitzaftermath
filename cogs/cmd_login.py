from discord.ext import commands, tasks
import discord
import requests
import rapidjson

from cogs.api.discord_users_api import DiscordUsersApi
from cogs.api.stats_api import StatsApi

users_api = DiscordUsersApi()
stats_api = StatsApi()

class login(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.client.remove_command("help")

    # Events
    # @commands.Cog.listener()
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'[Beta] Aftermath login cog is ready.')

    @commands.command()
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def login(self, ctx, realm=None):
        if realm:
            realm = realm.upper()
        else:
            player_id = users_api.get_default_player_id(ctx.author.id)
            player_details = stats_api.players.find_one({'_id': player_id})
            if player_details:
                realm = player_details.get("realm")

        valid_realms = ["NA", "EU", "RU", "ASIA"]
        if realm not in valid_realms:
            await ctx.send("{realm} is not a valid server.\n*Example: `v-login EU`*")
            return

        user_id = ctx.author.id
        new_login = {
            "realm": realm,
            "discord_user_id": user_id
        }

        try:
            res = requests.get("http://158.69.62.236/newlogin", json=new_login)
        except:
            await ctx.send("It looks like Aftermath login service is under maintenance, please try again later.")
            return

        intent_id = rapidjson.loads(res.text).get('intent_id')
        await ctx.send(f"Here is your login link!\nhttp://158.69.62.236/login/{intent_id}")
        return




def setup(client):
    client.add_cog(login(client))

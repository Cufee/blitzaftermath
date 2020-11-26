from discord.ext import commands
import requests
import rapidjson

from cogs.api.discord_users_api import DiscordUsersApiV2
from cogs.api.stats_api import StatsApi

users_api = DiscordUsersApiV2()
stats_api = StatsApi()

class login(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.client.remove_command("help")
        self.api_domain = "https://api.aftermath.link"


    # Events
    # @commands.Cog.listener()
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'[Beta] Aftermath login cog is ready.')


    @commands.command()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def login(self, ctx, realm=None):
        try:
            dm_channel = await ctx.author.create_dm()
        except:
            await ctx.send('Hey {ctx.author.mention}! You need to allow DMs for this command to work.')
            return

        if realm:
            realm = realm.upper()
            player_id = None
        else:
            try:
                player_id = users_api.get_user_default_pid(ctx.author.id)
            except Exception as e:
                if e == "This user does not have a default WoT Blitz account set.":
                    await ctx.send("Please specify the server you would like to login at.\n*For example: `v-login EU`*")
                    return
                await ctx.send("It looks like Aftermath login service is under maintenance, please try again later.")
                return

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
            res = requests.get(f"{self.api_domain}/newlogin", json=new_login)
        except:
            await ctx.send("It looks like Aftermath login service is under maintenance, please try again later.")
            return

        if res.status_code == 200:
            intent_id = rapidjson.loads(res.text).get('intent_id')
            existing_id = rapidjson.loads(res.text).get('existing_id', 0)
            message = ""
            if existing_id > 0:
                # Lookup nickname
                player_name = stats_api.players.find_one({'_id': player_id}).get("nickname")
                message = f"It looks like you are currently logged in as {player_name}.\n\n"

            await dm_channel.send(f"{message}Here is your new login link for {realm}! It will expire in 5 minutes.\n{self.api_domain}/login/{intent_id}\n**Please keep it safe.**")
        elif res.status_code == 409:
            username = rapidjson.loads(res.text).get('nickname')
            await dm_channel.send(f"It looks like you are logged in as {username} already.")
        else:
            await dm_channel.send(f"Something did not work.")
        return


def setup(client):
    client.add_cog(login(client))

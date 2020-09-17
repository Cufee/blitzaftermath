from datetime import datetime, timedelta
from discord.ext import commands, tasks
import discord
import requests
import rapidjson
import traceback
import re
from io import BytesIO

from cogs.api.stats_api import StatsApi, MongoClient, get_wg_api_domain
from cogs.api.discord_users_api import DiscordUsersApi
from cogs.pay_to_win.stats_module import CustomBackground
from cogs.api.message_cache_api import MessageCacheAPI

import time

db_client = MongoClient("mongodb://51.222.13.110:27017")
players = db_client.stats.players

debug = False
API = StatsApi()
CacheAPI = MessageCacheAPI()
UsersApi = DiscordUsersApi()
bgAPI = CustomBackground()

def zap_render(player_id: int, realm: str, days: int, bg_url: str, sort_key: str = ""):
        request_dict = {        
            "player_id": player_id,
            "realm": realm,
            "days": days,
            "sort_key": sort_key,
            "detailed_limit": 0,
            "bg_url": bg_url
        }
        try:
            res = requests.get("http://localhost:6969/player", json=request_dict)
        except requests.exceptions.ConnectionError:
            raise Exception("It looks like Aftermath stats is currently down for maintenance.")
        if res.status_code == 200:
            image = discord.File(filename="result.png", fp=BytesIO(res.content))
            return image, request_dict
        else:
            res_json = rapidjson.loads(res.text)
            print(res_json.get('error'))
            if res_json.get('error') == "mongo: no documents in result":
                raise Exception("Not enough data to render your session.")
            else:
                raise Exception("Zap failed to render your session.")


class blitz_aftermath_stats(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.sort_battles = self.client.get_emoji(
            756207071304876123)
        self.sort_winrate = self.client.get_emoji(
            756207071027789886)
        self.sort_rating = self.client.get_emoji(
            756207070956748891)

    # Events
    # @commands.Cog.listener()
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'[Beta] Aftermath Stats cog is ready.')


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not payload.guild_id:
            return
            
        guild = discord.utils.find(
            lambda g: g.id == payload.guild_id, self.client.guilds)
        member = discord.utils.find(
            lambda m: m.id == payload.user_id, guild.members)
        if member == self.client.user:
            return

        channel = discord.utils.find(
            lambda m: m.id == payload.channel_id, guild.channels)

        message = await channel.fetch_message(payload.message_id)
        message_details = CacheAPI.get_message_details(payload.message_id, payload.guild_id)
        if not message_details:
            return

        if ((datetime.utcnow() - timedelta(seconds=15)) < message_details.get('timestamp')):
            dm_channel = await member.create_dm()
            await dm_channel.send("You will need to wait 15 seconds before using sort.")
            return
        
        player_id = message_details.get('request').get('player_id')
        player_realm = message_details.get('request').get('realm')
        days = message_details.get('request').get('days')
        bg_url = message_details.get('request').get('bg_url')
        old_key = message_details.get('request').get('sort_key')
        
        if payload.emoji == self.sort_battles:
            new_key = "-battles"
            if old_key == "-battles":
                new_key = "+battles"

        if payload.emoji == self.sort_rating:
            new_key = "-wn8"
            if old_key == "-wn8":
                new_key = "+wn8"

        if payload.emoji == self.sort_winrate:
            new_key = "-winrate"
            if old_key == "-winrate":
                new_key = "+winrate"

        image, request = zap_render(player_id, player_realm, days, bg_url, sort_key=new_key)

        new_message = await message.channel.send(file=image)
        CacheAPI.cache_message(new_message.id, message.guild.id, request)
        await new_message.add_reaction(self.sort_battles)
        await new_message.add_reaction(self.sort_rating)
        await new_message.add_reaction(self.sort_winrate)

        return
        


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user or isinstance(message.channel, discord.channel.DMChannel):
            return

        # Blitzbot Member object
        blitzbot = self.client.get_user(173628074846453761)
        if not blitzbot or not message.mentions or message.mentions[0] != blitzbot or "wr" not in message.content:
            return

        player_id = UsersApi.get_default_player_id(
                    discord_user_id=(message.author.id))
        if player_id:
            bg_url = UsersApi.get_custom_bg(message.author.id)
            player_realm = players.find_one(
                {'_id': player_id}).get("realm")

            days = 0
            image, _ = zap_render(player_id, player_realm, days, bg_url)

            await message.channel.send("Don't worry, I got your back! This even looks **a lot** better :)\n*Use v-help to learn more about Aftermath.*", file=image)
        else:
            await message.channel.send("Pssst, you can get the same information with Aftermath, it will just look *a lot* better :)\n\n*Use v-help to learn more about Aftermath.*")
    

    # Commands
    @commands.command(aliases=['wr', 'session', 'Stats', 'Wr'])
    async def stats(self, message, *args):
        if message.author == self.client.user or isinstance(message.channel, discord.channel.DMChannel):
            return

        # Convert session hours into int
        if args and  len(args[-1]) < 3:
            try:
                session_days = int(args[-1])
                args = args[:-1]
            except:
                session_days = None
        else:
            session_days = None

        player_name_str = "".join(args).strip()

        try:
            # Used later to check if a default account should be set
            trydefault = False

            if not player_name_str:
                player_id = UsersApi.get_default_player_id(
                    discord_user_id=(message.author.id))

                if player_id:
                    bg_url = UsersApi.get_custom_bg(message.author.id)
                    player_realm = players.find_one(
                        {'_id': player_id}).get("realm")

                    days = 0
                    if session_days:
                        days = session_days

                    image, request = zap_render(player_id, player_realm, days, bg_url)

                    new_message = await message.channel.send(file=image)
                    CacheAPI.cache_message(new_message.id, message.guild.id, request)
                    await new_message.add_reaction(self.sort_battles)
                    await new_message.add_reaction(self.sort_rating)
                    await new_message.add_reaction(self.sort_winrate)
                    return None
                else:
                    await message.channel.send(f'You do not have a default WoT Blitz account set.\nUse `{self.client.command_prefix[0]}iam Username@Server` to set a default account for me to look up.')
                    return None

            elif '@' in player_name_str:
                player_name_str = player_name_str
                player_name_str_list = player_name_str.split('@')
                player_name = player_name_str_list[0]
                if len(player_name) < 3:
                    raise Exception(
                        'Player name needs to be at least 3 characters long')
                player_realm = player_name_str_list[1].upper()
                player_details = players.find_one(
                    {'nickname': re.compile(player_name, re.IGNORECASE), 'realm': player_realm})
                if not player_details:
                    # Check if username is valid
                    api_domain, _ = get_wg_api_domain(realm=player_realm)
                    api_url = api_domain + \
                        '/wotb/account/list/?application_id=add73e99679dd4b7d1ed7218fe0be448&search=' + player_name
                    res = requests.get(api_url)
                    res_data_raw = rapidjson.loads(res.text)
                    if res.status_code != 200 or not res_data_raw:
                        raise Exception(
                            f'WG API responded with {res.status_code}')

                    res_data = res_data_raw.get('data')

                    # Check other servers
                    if not res_data:
                        other_domains = ["NA", "EU", "ASIA", "RU"]
                        other_domains.remove(player_realm)
                        res_data = None
                        other_realm = None
                        for r in other_domains:
                            api_domain, _ = get_wg_api_domain(realm=r)
                            api_url = api_domain + \
                                '/wotb/account/list/?application_id=add73e99679dd4b7d1ed7218fe0be448&search=' + player_name
                            res = requests.get(api_url)
                            res_data_raw = rapidjson.loads(res.text)
                            if res.status_code != 200 or not res_data_raw:
                                print(f"WG API responded with {res.status_code}")
                                continue
                            res_data = res_data_raw.get('data')
                            if res_data:
                                other_realm = r
                                break
                        if not res_data:
                            raise Exception(
                                f'WG: Player not found. I also checked {",".join(other_domains)} servers. Is the username spelled correctly?')
                        else:
                            await message.channel.send(f"I was not able to find {player_name} on {player_realm}. But there is an account with this name on {other_realm}.\n*Use `{self.client.command_prefix[0]}stats {player_name_str_list[0]}@{other_realm}` to check it.*")
                            return

                    # Get player id and enable tracking
                    player_data_1 = res_data[0]
                    print(player_data_1)
                    player_id = player_data_1.get('account_id')
                    player_name_fixed = player_data_1.get('nickname')

                    API.update_players([player_id], realm=player_realm)
                    msg_str = f'Enabling for {player_name_fixed} on {player_realm}. You will need to **play at least one regular battle** to start tracking.'
                    await message.channel.send(msg_str)
                    
                    # Set a default player_id  if it is not set already
                    default_player_id = UsersApi.get_default_player_id(
                        discord_user_id=(message.author.id))
                    if not default_player_id:
                        UsersApi.link_to_player(
                            discord_user_id=(message.author.id), player_id=player_id)
                    
                    API.update_stats([player_id], realm=player_realm)
                    API.add_career_wn8([player_id], realm=player_realm)
                    return

                else:
                    player_id = player_details.get('_id')
                    player_realm = player_details.get('realm')
                
                bg_url = UsersApi.get_custom_bg(message.author.id)

                days = 0
                if session_days:
                    days = session_days


                image, request = zap_render(player_id, player_realm, days, bg_url)

                new_message = await message.channel.send(file=image)
                CacheAPI.cache_message(new_message.id, message.guild.id, request)
                await new_message.add_reaction(self.sort_battles)
                await new_message.add_reaction(self.sort_rating)
                await new_message.add_reaction(self.sort_winrate)

                # Try to set a new default account for new users
                trydefault = True

            else:
                player_name = player_name_str
                players_list = list(players.find(
                    {'nickname': re.compile(player_name, re.IGNORECASE)}))
                

                if len(players_list) > 1:
                    await message.channel.send(
                        f'Multiple players found with this username. Please specify the server you would like to check.\n*For example: {player_name}@eu*', delete_after=30)
                elif len(players_list) == 1:
                    player_id = players_list[0].get("_id")
                    player_realm = players_list[0].get("realm")
                    bg_url = UsersApi.get_custom_bg(message.author.id)

                    days = 0
                    if session_days:
                        days = session_days

                    image, request = zap_render(player_id, player_realm, days, bg_url)

                    new_message = await message.channel.send(file=image)
                    CacheAPI.cache_message(new_message.id, message.guild.id, request)
                    await new_message.add_reaction(self.sort_battles)
                    await new_message.add_reaction(self.sort_rating)
                    await new_message.add_reaction(self.sort_winrate)
                    # Try to set a new default account for new users
                    trydefault = True

                else:
                    await message.channel.send(
                        f'Player {player_name} not found. Please specify the server you would like to check.\n*For example: {player_name}@eu*', delete_after=30)

            if trydefault and player_id:
                # Set a default player_id  if it is not set already
                default_player_id = UsersApi.get_default_player_id(
                    discord_user_id=(message.author.id))
                if not default_player_id:
                    UsersApi.link_to_player(
                        discord_user_id=(message.author.id), player_id=player_id)
                    print(f"Set a new default for {message.author.nick}")


        except Exception as e:
            print(traceback.format_exc())
            if e == ConnectionError:
                await message.channel.send(f'Something did not work as planned :confused:\n```Failed to establish a connection to Wargaming API. Please try again in a few seconds.```')
            else:
                await message.channel.send(f'Something did not work as planned :confused:\n```{e}```')

    @commands.command(aliases=['Iam', 'IAM'])
    async def iam(self, message, player_name_str):
        if message.author == self.client.user or isinstance(message.channel, discord.channel.DMChannel):
            return

        try:
            # Split player string, check validity, find player ID
            if '@' in player_name_str:
                player_name_str = player_name_str
                player_name_str_list = player_name_str.split('@')
                player_name = player_name_str_list[0]
                if len(player_name) < 3:
                    raise Exception(
                        'Player name needs to be at least 3 characters long')
                player_realm = player_name_str_list[1].upper()
                player_details = players.find_one(
                    {'nickname': re.compile(player_name, re.IGNORECASE), 'realm': player_realm})
                if not player_details:
                    # Check if username is valid
                    api_domain, _ = get_wg_api_domain(realm=player_realm)
                    api_url = api_domain + \
                        '/wotb/account/list/?application_id=add73e99679dd4b7d1ed7218fe0be448&search=' + player_name
                    res = requests.get(api_url)
                    res_data_raw = rapidjson.loads(res.text)
                    if res.status_code != 200 or not res_data_raw:
                        raise Exception(
                            f'WG API responded with {res.status_code}')

                    res_data = res_data_raw.get('data')
                    if not res_data:
                        print(api_url)
                        print(res_data)
                        raise Exception(
                            f'WG: Player not found. Is the username spelled correctly?')

                    # Get player id and enable tracking
                    player_data_1 = res_data[0]
                    player_id = player_data_1.get('account_id')

                    late_update = True

                else:
                    late_update = False
                    player_id = player_details.get('_id')
                    player_realm = player_details.get('realm')

                # Get Discord user ID
                user_id = message.author.id
                UsersApi.link_to_player(
                    discord_user_id=user_id, player_id=player_id)
                if late_update:
                    message_text = f'Awesome! You will be able to check your stats with `{self.client.command_prefix[0]}stats` **once you play one more regular battle**.'
                else:
                    message_text = f'Awesome! You can now check your stats with `{self.client.command_prefix[0]}stats`.'

                await message.channel.send(message_text)

                if late_update:
                    API.update_players([player_id], realm=player_realm)
                    API.update_stats([player_id], realm=player_realm)
                    API.add_career_wn8([player_id], realm=player_realm)
                return None

            else:
                await message.channel.send(
                    f'There is no `@` in your message. Please use this symbol to separate the username and server.\n*For example: {self.client.command_prefix[0]}iam Vovko@na*', delete_after=30)
                return None

        # Handle exceptions
        except Exception as e:
            print(traceback.format_exc())
            await message.channel.send(f'Something did not work as planned :confused:\n```{e}```')

    @commands.command(aliases=['bg'])
    async def fancy(self, ctx, url=None):
        if ctx.author == self.client.user or isinstance(ctx.channel, discord.channel.DMChannel):
            return

        # Fix url
        try:
            url = url.strip()
        except:
            url = None
        print(url)
        try:
            # Set image url
            if url:
                img_url = url
            else:
                img_url = None

            attachments = ctx.message.attachments
            # Check attachments for jpeg images
            for att in attachments:
                if att.url:
                    img_url = att.url
                    break

            # Image url found
            if img_url:
                err, secure_url = bgAPI.put(user_id=str(ctx.author.id), image_url=img_url)
                if not err:
                    UsersApi.add_custom_bg(ctx.author.id, secure_url)
                    await ctx.send("Awesome! Your stats will now shine bright :)")
                    return
                else:
                    raise Exception(err)
            # No valid url
            else:
                raise Exception('There is no link to a valid image in your message.\nUsage example:\nv-fancy https://i.imgflip.com/1ovalo.jpg')

        # Handle exceptions
        except Exception as e:
            print(traceback.format_exc())
            await ctx.channel.send(f'Something did not work as planned :confused:\n```{e}```')

    @commands.command(aliases=['nobg'])
    async def notfancy(self, ctx):
        if ctx.author == self.client.user or isinstance(ctx.channel, discord.channel.DMChannel):
            return

        try:
            UsersApi.remove_custom_bg(ctx.author.id)
            err = bgAPI.delete(str(ctx.author.id))
            if err:
                raise Exception(err)
            await ctx.send("Removed your custom background for stats.")

        # Handle exceptions
        except Exception as e:
            print(traceback.format_exc())
            await ctx.channel.send(f'Something did not work as planned :confused:\n```{e}```')


def setup(client):
    client.add_cog(blitz_aftermath_stats(client))

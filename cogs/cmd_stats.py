from datetime import datetime, timedelta
from discord.ext import commands, tasks
import discord
import requests
import rapidjson
import traceback
import re

from cogs.stats.render import Render
from cogs.api.mongoApi import StatsApi, MongoClient, get_wg_api_domain, DiscordUsersApi

client = MongoClient("mongodb://51.222.13.110:27017")
players = client.stats.players

debug = False
API = StatsApi()
UsersApi = DiscordUsersApi()


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
    async def stats(self, message, player_name_str=None, hours=None):
        if message.author == self.client.user:
            return
        # Convert session hours into int
        try:
            session_hours = int(hours)
        except:
            session_hours = None
        try:
            if not player_name_str and not hours:
                player_id = UsersApi.get_default_player_id(
                    discord_user_id=(message.author.id))
                if player_id:
                    image = Render(player_id=player_id,
                                   hours=session_hours).render_image()
                    await message.channel.send(file=image)
                    return None
                else:
                    await message.channel.send(f'You do not have a default WoT Blitz account set.\nUse `{self.client.command_prefix[0]}iam Username@Server` to set a default account for me to look up.\nOr use `{self.client.command_prefix[0]}stats Username@Server` to check your stats.', delete_after=30)
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
                    if not res_data:
                        print(api_url)
                        print(res_data)
                        raise Exception(
                            f'WG: Player not found. Are the username and server spelled correctly?')

                    # Get player id and enable tracking
                    player_data_1 = res_data[0]
                    print(player_data_1)
                    player_id = player_data_1.get('account_id')
                    player_name_fixed = player_data_1.get('nickname')

                    API.update_players([player_id])
                    await message.channel.send(f'Enabling for {player_name_fixed} on {player_realm}. You will need to play at least one battle to start tracking.')
                    API.update_stats([player_id])
                    API.add_career_wn8([player_id])
                    return

                else:
                    player_id = player_details.get('_id')

                image = Render(player_id=player_id,
                               hours=session_hours).render_image()
                await message.channel.send(file=image)
                # Doing a forced session reset every 24 hours
                # API.update_stats([player_id])
            else:
                player_name = player_name_str
                player_id_list = players.find(
                    {'nickname': re.compile(player_name, re.IGNORECASE)}).distinct('_id')
                if len(player_id_list) > 1:
                    await message.channel.send(
                        'Multiple players found with this username. Please specify the server you would like to check.\n*For example: {player_name}@eu*', delete_after=30)
                elif len(player_id_list) == 1:
                    player_id = player_id_list[0]
                    image = Render(player_id=player_id,
                                   hours=session_hours).render_image()
                    await message.channel.send(file=image)
                else:
                    await message.channel.send(
                        f'Player {player_name} not found. Please specify the server you would like to check.\n*For example: {player_name}@eu*', delete_after=30)

        except Exception as e:
            print(traceback.format_exc())
            await message.channel.send(f'Something did not work as planned :confused:\n```{e}```')

    @commands.command(aliases=['Iam', 'IAM'])
    async def iam(self, message, player_name_str):
        if message.author == self.client.user:
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
                            f'WG: Player not found. Are the username and server spelled correctly?')

                    # Get player id and enable tracking
                    player_data_1 = res_data[0]
                    print(player_data_1)
                    player_id = player_data_1.get('account_id')
                    player_name_fixed = player_data_1.get('nickname')

                    late_update = True

                else:
                    late_update = False
                    player_id = player_details.get('_id')

                # Get Discord user ID
                user_id = message.author.id
                UsersApi.link_to_player(
                    discord_user_id=user_id, player_id=player_id)
                await message.channel.send(f'Awesome! You can now check your stats with `{self.client.command_prefix[0]}stats`.')

                if late_update:
                    API.update_players([player_id])
                    API.update_stats([player_id])
                    API.add_career_wn8([player_id])
                return None

            else:
                await message.channel.send(
                    f'There is no `@` in your message. Please use this symbol to separate the username and server.\n*For example: {self.client.command_prefix[0]}iam Vovko@na*', delete_after=30)
                return None

        # Handle exceptions
        except Exception as e:
            print(traceback.format_exc())
            await message.channel.send(f'Something did not work as planned :confused:\n```{e}```')


def setup(client):
    client.add_cog(blitz_aftermath_stats(client))

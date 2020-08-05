from discord.ext import commands, tasks
import discord
import asyncio
import requests
import rapidjson
import traceback

from datetime import datetime, timedelta, timezone
from pymongo import MongoClient
from pymongo import InsertOne, UpdateOne
from pymongo.errors import BulkWriteError

from cogs.contest.render import Render

client = MongoClient("mongodb://51.222.13.110:27017")
db = client.summer2020contest

guilds = db.guilds
clans = db.clans
players = db.players
clan_marks = db.marksOfMastery

wg_api_url_base = '/wotb/clans/info/?application_id=add73e99679dd4b7d1ed7218fe0be448&clan_id='
wg_player_api_url_base = '/wotb/account/achievements/?application_id=add73e99679dd4b7d1ed7218fe0be448&account_id='
wg_clan_api_url_base = '/wotb/clans/list/?application_id=add73e99679dd4b7d1ed7218fe0be448&search='
wg_clan_info_api_url_base = '/wotb/clans/info/?application_id=add73e99679dd4b7d1ed7218fe0be448&clan_id='


def get_wg_api_domain(realm):
    # Detect realm
    realm = realm.upper()
    if realm == 'RU':
        player_realm = 'ru'
        api_domain = 'http://api.wotblitz.ru'

    elif realm == 'EU':
        player_realm = 'eu'
        api_domain = 'http://api.wotblitz.eu'

    elif realm == 'NA':
        player_realm = 'na'
        api_domain = 'http://api.wotblitz.com'

    elif realm == 'ASIA':
        player_realm = 'asia'
        api_domain = 'http://api.wotblitz.asia'

    else:
        api_domain = None
    return api_domain


def get_clan_marks(clan_id):
    if not clan_id:
        raise Exception('No clan ID specified')
    clan_data = clans.find_one({'clan_id': clan_id})
    clan_aces = clan_data.get('clan_aces')
    return clan_aces


class blitz_aftermath_contest(commands.Cog):

    def __init__(self, client):
        self.client = client

    # Events
    # @commands.Cog.listener()
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'[Beta] Aftermath Contest cog is ready.')

    # Commands
    @commands.command(aliases=['c'])
    async def check(self, message, clan_id_str=None):
        if message.author == self.client.user:
            return
        guild_id = message.guild.id
        if clan_id_str:
            clan_id_str = clan_id_str.upper()
        try:
            if clan_id_str:
                if '@' in clan_id_str:
                    clan_list = (clan_id_str).split('@')
                    clan_tag = clan_list[0]
                    clan_realm = clan_list[1]
                    clan_data = clans.find_one(
                        {'clan_tag': clan_tag, 'clan_realm': clan_realm})
                    if not clan_data:
                        await self.addclan(message, clan_id_str)
                        raise Exception(
                            f'Nothing found matching {clan_tag} on {clan_realm}')

                    clan_id = clans.find_one(
                        {'clan_tag': clan_tag, 'clan_realm': clan_realm}).get('clan_id')
                else:
                    clan_ids = clans.find(
                        {'clan_tag': clan_id_str}).distinct('clan_id')
                    if len(clan_ids) == 1:
                        clan_id = clan_ids[0]
                    else:
                        raise Exception(
                            f'Please specify a server for {clan_id_str.upper()}.\n*`v-check TAG@SERVER`*')
            else:
                guild_settings = guilds.find_one({'guild_id': guild_id})
                if not guild_settings:
                    raise Exception(
                        'This server does not have a default clan set. Please specify the clan tag and server you want to check.')

                clan_id = guild_settings.get('default_clan_id')
                clan_data = clan_data = clans.find_one(
                    {'clan_id': clan_id})
                clan_tag = clan_data.get('clan_tag')

            image = Render(top_players=3, clan_id=clan_id,
                           nation='usa', starting_tier=5).render_image()
            await message.channel.send(file=image)

        except Exception as e:
            print(str(traceback.format_exc()))
            await message.channel.send(f'Something did not work.\n```{e}```', delete_after=30)

    @commands.command(aliases=['c-init'])
    # @commands.is_owner()
    async def c_init(self, message):
        if message.author == self.client.user:
            return
        guild_id = int(message.guild.id)
        guild_name = str(message.guild.name)
        channel_id = str(message.channel.id)
        channel = message.channel
        guild_settings = guilds.find_one({'guild_id': guild_id})
        if not guild_settings:
            new_guild_settings = {
                'guild_id': guild_id,
                'guild_name': guild_name,
                'enabled': True,
                'channel': channel_id,
                'default_clan_id': 0,
            }
            response = guilds.insert_one(new_guild_settings)
            await channel.send(f'Enabled in {guild_name}\n```{response}```', delete_after=10)
        else:
            await channel.send(f'Already enabled in {guild_name}', delete_after=10)

    @commands.command(aliases=['c-add'])
    @commands.is_owner()
    async def addclan(self, message, clan_id_str):
        if message.author == self.client.user:
            return

        channel = message.channel
        clan_id = None
        status_code = None
        try:
            clan_id_list = (clan_id_str.upper()).split('@')
            clan_tag = clan_id_list[0]
            clan_realm = clan_id_list[1] or None

            api_domain = get_wg_api_domain(clan_realm)
            if not api_domain:
                raise Exception(f'{clan_realm} is not valid realm')
            url = api_domain + wg_clan_api_url_base + clan_tag
            res = requests.get(url)
            status_code = res.status_code
            res_json = rapidjson.loads(res.text)
            clan_id = res_json.get('data')[0].get('clan_id') or None
        except Exception as e:
            await message.channel.send(f'I was not able to find anything matching {clan_tag} on {clan_realm} [{status_code}]', delete_after=30)
            pass

        if clan_id:
            clan = clans.find_one({'clan_id': clan_id})
            if not clan:
                new_clan = {
                    'clan_id': clan_id,
                    'clan_tag': clan_tag,
                    'clan_realm': clan_realm,
                    'clan_name': clan_tag,
                    'timestamp': datetime.utcnow()
                }
                response = clans.insert_one(new_clan)
                await channel.send(f'Enabled for {clan_tag}', delete_after=10)
            else:
                await channel.send(f'Already enabled for {clan_tag}', delete_after=10)

    @commands.command()
    @commands.is_owner()
    async def defclan(self, message, clan_str):
        if message.author == self.client.user:
            return
        # await message.delete()
        guild_id = message.guild.id
        guild_settings = guilds.find_one({'guild_id': guild_id})

        clan_list = (clan_str.upper()).split('@')
        clan_tag = clan_list[0]
        clan_realm = clan_list[1]
        api_domain = get_wg_api_domain(clan_realm)
        if not api_domain:
            raise Exception(f'{clan_realm} is not valid server')
        url = api_domain + wg_clan_api_url_base + clan_tag
        res = requests.get(url)
        if res.status_code != 200:
            await message.channel.send(f'Unable to find a clan named {clan_tag} on {clan_realm}')
            return
        else:
            res_json = rapidjson.loads(res.text)
            clan_id = res_json.get('data')[0].get('clan_id') or None
            new_clan_tag = res_json.get('data')[0].get('tag') or None
            guilds.update_one(
                guild_settings, {"$set": {"default_clan_id": clan_id}})

            new_default_clan_id = clan_id

            await message.channel.send(f'Updated the default clan for {message.guild.name} to {new_clan_tag}', delete_after=30)

    @commands.command()
    async def top(self, message):
        if message.author == self.client.user:
            return
        image = Render(nation='usa', starting_tier=5).render_image()
        await message.channel.send(file=image)

    @commands.command()
    @commands.is_owner()
    async def set(self, message, clan_str, aces):
        if message.author == self.client.user:
            return
        guild_id = message.guild.id

        clan_list = (clan_str.upper()).split('@')
        clan_tag = clan_list[0]
        clan_realm = clan_list[1]

        clan_data = clans.find_one(
            {'clan_tag': clan_tag, 'clan_realm': clan_realm})
        if not clan_data:
            await message.channel.send(f'Did not find {clan_tag} on {clan_realm}')
            return

        clan_id = clan_data.get('clan_id')
        aces = int(aces)
        clans.update_one(clan_data, {"$set": {"clan_aces_usa_5": aces}})
        await create_queue(clan_id=clan_id)
        clan_aces = get_clan_marks(clan_id=clan_id)
        await message.channel.send(f'Players in [{clan_tag}] earned {clan_aces} Ace Tankers.\n*This data is collected every hour and may be incomplete for some clans*.')


def setup(client):
    client.add_cog(blitz_aftermath_contest(client))

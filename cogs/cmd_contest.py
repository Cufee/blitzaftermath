from discord.ext import commands, tasks
import discord
import requests
import rapidjson

from datetime import datetime, timedelta, timezone
from pymongo import MongoClient
from pymongo import InsertOne, UpdateOne
from pymongo.errors import BulkWriteError

import traceback

client = MongoClient(
    "mongodb+srv://vko:XwufAAtwZh2JxR3E@cluster0-ouwv6.mongodb.net/<dbname>?retryWrites=true&w=majority")
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


async def update_clan_marks(clan_id=None, channel=None, force=False):

    clan_ids = {
        'NA': [],
        'RU': [],
        'EU': [],
        'ASIA': [],
    }
    if clan_id:
        clan_realm = clans.find_one({'clan_id': clan_id}).get('clan_realm')
        clan_ids.update({clan_realm: [clan_id]})
    else:
        all_clans = clans.find()
        for clan_data in all_clans:
            clan_realm = clan_data.get('clan_realm')
            clan_id = clan_data.get('clan_id')
            if not clan_id or not clan_realm:
                print(f'Skipping {clan_id} on {clan_realm}')
                continue

            current_list = clan_ids.get(clan_realm)
            current_list.append(clan_id)
            clan_ids.update({clan_realm: current_list})

    clan_update_obj_list = []
    player_update_obj_list = []
    for realm in clan_ids.keys():
        api_domain = get_wg_api_domain(realm)
        all_clans_str = ','.join(str(id) for id in (clan_ids.get(realm)))
        if not all_clans_str:
            continue
        api_url = api_domain + wg_clan_info_api_url_base + all_clans_str
        res = requests.get(api_url)
        if res.status_code != 200:
            raise Exception(f'WG API responded with {res.status_code}')

        res_data = rapidjson.loads(res.text).get('data') or None
        if not res_data:
            print(rapidjson.dumps(rapidjson.loads(res.text), indent=2))
            raise Exception('Incomplete data received from WG API')
            continue

        for clan_id in clan_ids.get(realm):
            clan_db_data = clans.find_one({'clan_id': clan_id})
            clan_data = res_data.get(str(clan_id))
            clan_name = clan_data.get('name')
            clan_tag = clan_data.get('tag')

            current_members = clan_data.get('members_ids')
            last_members = clan_db_data.get('members', current_members)
            current_members_str = ','.join(str(m) for m in current_members)
            api_url = api_domain + wg_player_api_url_base + current_members_str
            res = requests.get(api_url)
            if res.status_code != 200:
                raise Exception(f'WG API responded with {res.status_code}')

            player_res_data = rapidjson.loads(res.text).get('data')
            clan_aces_gained = 0
            for player_id in current_members:
                player_data = player_res_data.get(
                    str(player_id), {})

                if not player_data:
                    print(
                        f'Skipping player {player_id}, no data recieved from WG API')
                    continue

                current_player_aces = player_data.get(
                    'achievements', {}).get('markOfMastery', 0)
                last_player_data = players.find_one(
                    {'player_id': player_id})

                if not last_player_data:
                    insert_obj = InsertOne({
                        'player_id': player_id,
                        'aces': None,
                        'timestamp': datetime.utcnow()
                    })
                    player_update_obj_list.append(insert_obj)
                    continue

                last_aces = last_player_data.get('aces')
                if not last_aces:
                    last_aces = current_player_aces

                if current_player_aces == last_aces and force == False:
                    continue

                aces_gained = current_player_aces - last_aces
                if player_id in last_members and player_id in current_members:
                    clan_aces_gained += aces_gained

                # Update player record
                player_update = {
                    'aces': current_player_aces,
                    'timestamp': datetime.utcnow()
                }
                player_update_obj = UpdateOne({'player_id': player_id}, {
                                              '$set': player_update}, upsert=True)
                player_update_obj_list.append(player_update_obj)

            # Update clan record
            last_clan_aces = clan_db_data.get('clan_aces') or 0
            if last_clan_aces == (last_clan_aces + clan_aces_gained) and force == False:
                continue

            clan_update = {
                'members': current_members,
                'clan_aces': (last_clan_aces + clan_aces_gained),
                'timestamp': datetime.utcnow()
            }
            if clan_db_data.get('clan_name') != clan_name:
                clan_update['clan_name'] = clan_name
            if clan_db_data.get('clan_tag') != clan_tag:
                clan_update['clan_tag'] = clan_tag

            clan_update_obj = UpdateOne(
                {'clan_id': clan_id}, {'$set': clan_update}, upsert=True)
            clan_update_obj_list.append(clan_update_obj)

    try:
        result_clans = clans.bulk_write(clan_update_obj_list)
        result_players = players.bulk_write(player_update_obj_list)
        return result_clans.bulk_api_result, result_players.bulk_api_result
    except BulkWriteError as bwe:
        print(bwe.with_traceback)
        pass


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

    @tasks.loop(hours=1)
    async def printer(self):
        await update_clan_marks()
        print('Updated clan data')

    # Commands
    @commands.command()
    async def update(self, message, clan_id_str=None):
        if message.author == self.client.user:
            return
        # await message.delete()
        guild_id = message.guild.id

        if clan_id_str and clan_id_str != 'force':
            clan_list = (clan_id_str.upper()).split('@')
            clan_tag = clan_list[0]
            clan_realm = clan_list[1]
            lan_data = clans.find_one(
                {'clan_tag': clan_tag, 'clan_realm': clan_realm})
            if not clan_data:
                await message.channel.send('Not found')
                return
            clan_id = clan_data.get('clan_id', 0)
            result_clans, result_players = await update_clan_marks(clan_id=clan_id)
        elif clan_id_str == 'force':
            result_clans, result_players = await update_clan_marks(force=True)
        else:
            result_clans, result_players = await update_clan_marks()

        await message.channel.send(f'Update complete\n```{result_clans}```\n```{result_players}```')

    # Commands
    @commands.command(aliases=['c'])
    async def check(self, message, clan_id_str=None):
        if message.author == self.client.user:
            return
        guild_id = message.guild.id
        try:
            if clan_id_str:
                clan_list = (clan_id_str.upper()).split('@')
                clan_tag = clan_list[0]
                clan_realm = clan_list[1]
                clan_data = clans.find_one(
                    {'clan_tag': clan_tag, 'clan_realm': clan_realm})
                clan_id = clan_data.get('clan_id')
            else:
                guild_settings = guilds.find_one({'guild_id': guild_id})
                if not guild_settings:
                    raise Exception(
                        'This server does not have a default clan set. Please specify the clan tag and realm you want to check.')

                clan_id = guild_settings.get('default_clan_id')
                clan_data = clan_data = clans.find_one(
                    {'clan_id': clan_id})
                clan_tag = clan_data.get('clan_tag')
            try:
                await update_clan_marks(clan_id=clan_id)
            except:
                pass
            clan_aces = get_clan_marks(clan_id=clan_id)
            await message.channel.send(f'Players in [{clan_tag}] earned {clan_aces} Ace Tankers.\n*This data is collected every hour and may be incomplete for some clans*.')
        except Exception as e:
            print(str(traceback.format_exc()))
            await message.channel.send(f'Something did not work.\n```{e}```')

    # Commands
    @ commands.command(aliases=['c-init'])
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
                'default_clan_id': None,
            }
            response = guilds.insert_one(new_guild_settings)
            await channel.send(f'Enabled in {guild_name}\n```{response}```', delete_after=10)
        else:
            await channel.send(f'Already enabled in {guild_name}', delete_after=10)

    # Commands
    @ commands.command(aliases=['c-add'])
    async def addclan(self, message, clan_id):
        if message.author == self.client.user:
            return

        channel = message.channel
        clan_id = None
        status_code = None
        try:
            clan_id_list = (clan_id.upper()).split('@')
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
            await message.channel.send(f'I was not able to find anything matching {clan_tag} on {clan_realm} [{status_code}]\n```{e}```', delete_after=30)
            return

        if clan_id:
            clan = clans.find_one({'clan_id': clan_id})
            if not clan:
                new_clan = {
                    'clan_id': clan_id,
                    'clan_tag': clan_tag,
                    'clan_realm': clan_realm,
                }
                response = clans.insert_one(new_clan)
                await channel.send(f'Enabled for {clan_tag}\n```{response}```', delete_after=10)
            else:
                await channel.send(f'Already enabled for {clan_tag}', delete_after=10)

    # Commands
    @ commands.command()
    async def myclan(self, message, clan_str):
        if message.author == self.client.user:
            return
        await message.delete()
        guild_id = message.guild.id
        guild_settings = guilds.find_one({'guild_id': guild_id})

        clan_list = (clan_str.upper()).split('@')
        clan_tag = clan_list[0]
        clan_realm = clan_list[1]
        api_domain = get_wg_api_domain(clan_realm)
        if not api_domain:
            raise Exception(f'{clan_realm} is not valid realm')
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


def setup(client):
    client.add_cog(blitz_aftermath_contest(client))

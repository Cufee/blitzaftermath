from discord.ext import commands, tasks
import discord
import requests
import rapidjson

from datetime import datetime, timedelta, timezone
from pymongo import MongoClient

import traceback

client = MongoClient(
    "mongodb+srv://vko:XwufAAtwZh2JxR3E@cluster0-ouwv6.mongodb.net/<dbname>?retryWrites=true&w=majority")
db = client.summer2020contest

guilds = db.guilds
clans = db.clans
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

    else:
        player_realm = 'asia'
        api_domain = 'http://api.wotblitz.asia'

    return api_domain


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


async def update_clan_marks(clan_id=None, clan_realm=None, channel=None):
    clan_ids = {}

    if clan_id and clan_realm:
        clan_ids[clan_realm] = [clan_id]
    else:
        for clan in clans.find():
            clan_realm = clan.get('clan_realm')
            clan_ids_list = clan_ids.get(clan_realm, [])
            clan_ids_list.append(clan.get('clan_id'))
            clan_ids[clan_realm] = (clan_ids_list)

    if not clan_ids:
        raise Exception('No clanIds provided.')

    clan_entries = []
    for realm in clan_ids.keys():
        api_domain = get_wg_api_domain(realm)
        all_clan_ids = clan_ids.get(realm, [])
        if not all_clan_ids:
            continue

        all_clan_ids_str = ','.join(str(i) for i in all_clan_ids)

        url = api_domain + wg_clan_info_api_url_base + all_clan_ids_str
        res = requests.get(url)
        clans_res_json = rapidjson.loads(res.text)
        # print(rapidjson.dumps(res_json, indent=2))
        if res.status_code != 200 or not clans_res_json:
            raise Exception(
                f'WG api responded with {res["status_code"]}\n{res.status}')

        for clan_id in all_clan_ids:
            badges_total = 0
            res_data = clans_res_json.get('data')
            clan_data = res_data.get(str(clan_id))
            if not clan_data:
                print(f'Failed to update for {clan_id}')
                continue

            members = res_data.get(
                str(clan_id)).get('members_ids') or []
            members_str = ','.join(str(m) for m in members)

            url = api_domain + wg_player_api_url_base + members_str
            res = requests.get(url)
            if res.status_code != 200:
                raise Exception(
                    f'WG api responded with {res.status_code}\n{res.status}')

            res_json = rapidjson.loads(res.text)
            for member in members:
                mastery_marks = res_json.get('data').get(
                    str(member)).get('achievements').get('markOfMastery') or 0
                badges_total += mastery_marks

            clan_entry = {
                'clan_id': clan_id,
                'badges_total': badges_total,
                'timestamp': datetime.utcnow(),
            }
            clan_entries.append(clan_entry)

        result = clan_marks.insert_many(clan_entries)
    if channel:
        await channel.send(f'Updated Mastery marks for {len(clan_entries)} clans.')
    print(f'Updated {len(clan_entries)} clans.')
    return result


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

    # Commands
    @commands.command(aliases=['contest', 'm'])
    async def mastery(self, message):
        if message.author == self.client.user:
            return
        guild_id = message.guild.id

    # Commands
    @commands.command(aliases=['c-init'])
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
    @commands.command(aliases=['c-add'])
    async def addclan(self, message, clan_id):
        if message.author == self.client.user:
            return

        channel = message.channel
        status_code = 0
        try:
            clan_id_list = clan_id.split('@')
            clan_name = clan_id_list[0]
            clan_realm = clan_id_list[1].upper() or None

            api_domain = get_wg_api_domain(clan_realm)
            url = api_domain + wg_clan_api_url_base + clan_name
            res = requests.get(url)
            status_code = res.status_code
            res_json = rapidjson.loads(res.text)
            clan_id = res_json.get('data')[0].get('clan_id') or None
        except Exception as e:
            await message.channel.send(f'I was not able to find anything matching {clan_name} on {clan_realm} [{status_code}]\n```{e}```', delete_after=30)

        if clan_id:
            clan = clans.find_one({'clan_id': clan_id})
            if not clan:
                new_clan = {
                    'clan_id': clan_id,
                    'clan_name': clan_name,
                    'clan_realm': clan_realm,
                }
                response = clans.insert_one(new_clan)
                await channel.send(f'Enabled for {clan_name}\n```{response}```', delete_after=10)
            else:
                await channel.send(f'Already enabled for {clan_name}', delete_after=10)

    # Commands
    @commands.command(aliases=['c-upd'])
    async def update(self, message):
        if message.author == self.client.user:
            return

        await update_clan_marks(channel=message.channel)
        return

    # Commands
    @commands.command()
    async def check(self, message, clan_str=None):
        if message.author == self.client.user:
            return

        if not clan_str:
            guild_id = message.guild.id
            guild_settings = guilds.find_one({'guild_id': guild_id})
            clan_id = guild_settings.get('default_clan_id') or None
            clan = clans.find_one({'clan_id': clan_id})
            clan_name = clan.get('clan_name') or None
            clan_realm = clan.get('clan_realm') or None
        else:
            clan_str_list = clan_str.split('@')
            clan_name = clan_str_list[0]
            clan_realm = clan_str_list[1].upper()

            try:
                clan = clans.find_one({"$and": [{"clan_name": clan_name},
                                                {"clan_realm": clan_realm}]})
                clan_id = clan.get('clan_id', None)
            except:
                api_domain = get_wg_api_domain(clan_realm)
                url = api_domain + wg_clan_api_url_base + clan_name
                res = requests.get(url)
                if res.status_code != 200:
                    await message.channel.send(f'Unable to find a clan named {clan_name} on {clan_realm}')
                    return
                else:
                    res_json = rapidjson.loads(res.text)
                    clan_id = res_json.get('data')[0].get('clan_id') or None

        if not clan_id:
            await message.channel.send(f'Unable to find {clan_name} on {clan_realm}')
            return
        else:
            try:
                try:
                    current_marks = list(clan_marks.find(
                        {'clan_id': clan_id, 'timestamp': {"$gt": datetime.utcnow() - timedelta(hours=24)}}).sort('timestamp', -1).limit(1))[0].get('badges_total') or None
                except:
                    new_clan = {
                        'clan_id': clan_id,
                        'clan_name': clan_name,
                        'clan_realm': clan_realm,
                    }
                    response = clans.insert_one(new_clan)
                    await update_clan_marks(clan_id=clan_id, clan_realm=clan_realm)
                    await message.channel.send(f'Enabled for {clan_name}. Tracking will start in 1 hour.', delete_after=30)
                    return
                finally:
                    current_marks = list(clan_marks.find(
                        {'clan_id': clan_id, 'timestamp': {"$gt": datetime.utcnow() - timedelta(hours=24)}}).sort('timestamp', -1).limit(1))[0].get('badges_total') or None
                    if not current_marks:
                        raise Exception(f'Failed to pull data for {clan_name}')
                    last_marks_dict = list(clan_marks.find(
                        {'clan_id': clan_id, 'timestamp': {"$gt": datetime.utcnow() - timedelta(hours=24)}}).sort('timestamp', 1).limit(1))[0]
                    last_marks = last_marks_dict.get('badges_total')
                    last_marks_time = last_marks_dict.get('timestamp')
                    time_delta = datetime.utcnow() - last_marks_time

                    await message.channel.send(f'Players in {clan_name} earned {current_marks - last_marks} Marks of Mastery over the past {(time_delta.seconds // 3600)} hours')

            except Exception as e:
                print(e, str(traceback.format_exc()))
                await message.channel.send(f'Oh no, something did not work!\n```{e}```', delete_after=15)

        return

    # Commands
    @ commands.command()
    async def myclan(self, message, clan_str):
        if message.author == self.client.user:
            return
        await message.delete()
        guild_id = message.guild.id
        guild_settings = guilds.find_one({'guild_id': guild_id})

        clan_list = clan_str.split('@')
        clan_name = clan_list[0]
        clan_realm = clan_list[1]
        api_domain = get_wg_api_domain(clan_realm)
        url = api_domain + wg_clan_api_url_base + clan_name
        res = requests.get(url)
        if res.status_code != 200:
            await message.channel.send(f'Unable to find a clan named {clan_name} on {clan_realm}')
            return
        else:
            res_json = rapidjson.loads(res.text)
            clan_id = res_json.get('data')[0].get('clan_id') or None
            new_clan_name = res_json.get('data')[0].get('tag') or None
            guilds.update_one(
                guild_settings, {"$set": {"default_clan_id": clan_id}})

            new_default_clan_id = clan_id

            await message.channel.send(f'Updated the default clan for {message.guild.name} to {new_clan_name}', delete_after=30)


def setup(client):
    client.add_cog(blitz_aftermath_contest(client))

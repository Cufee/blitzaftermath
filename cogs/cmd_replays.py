from discord.ext import commands, tasks
import discord
import requests
import rapidjson

from cogs.replays.replay import Replay
from cogs.replays.rating import Rating
from cogs.replays.render import Render


API_URL_BASE = 'http://127.0.0.1:5000'
debug = False


def get_image(urls, rating=None, stats=None, stats_bottom=None, bg=1, brand=1, darken=1, mapname=1):
    # Send replay to WoTInspector
    replays_list_data = Replay(urls).process_replays()
    replay_data = replays_list_data.get(
        list(replays_list_data.keys())[0])
    replay_id = list(replays_list_data.keys())[0]
    replay_link = replay_data.get('download_url')
    replay_data = Rating(
        replay_data).get_brt()

    image_file = Render(
        replay_data, replay_id, stats=stats, stats_bottom=stats_bottom).image(bg=bg, brand=brand, darken=darken, mapname=mapname)

    return image_file, replay_id, replay_link


def get_guild_settings(guild_id, guild_name):
    url = API_URL_BASE + '/guild/' + guild_id
    res = requests.get(url)
    enabled_channels = []
    stats = []

    # If guild is not found, add it
    if res.status_code == 404:
        url = API_URL_BASE + '/guild'
        guild = {
            'guild_id': guild_id,
            'guild_name': guild_name
        }
        new_res = requests.post(url, json=guild)
    elif res.status_code == 200:
        new_res = res
    else:
        new_res = res
        return {"status_code": new_res.status_code}

    if new_res.status_code == 200:
        res_dict = rapidjson.loads(new_res.text)
        enabled_channels_res = res_dict.get('guild_channels')
        guild_is_premium = res_dict.get('guild_is_premium')
        guild_name_cache = res_dict.get('guild_name')
        stats_res = res_dict.get('guild_render_fields')

        if enabled_channels_res:
            if ';' in enabled_channels_res:
                enabled_channels = enabled_channels_res.split(';')
            else:
                enabled_channels = [enabled_channels_res, ]
        if stats_res:
            if ';' in stats_res:
                stats = stats_res.split(';')
            else:
                stats = [stats_res, ]

        # Update guild name cache
        if guild_name_cache != guild_name:
            url = 'http://127.0.0.1:5000/guild/' + guild_id
            guild = {
                'guild_name': guild_name
            }
            res = requests.put(url, json=guild)

        new_guild_obj = {
            "status_code": res.status_code,
            "enabled_channels": enabled_channels,
            "guild_is_premium": guild_is_premium,
            "stats": stats
        }

        return new_guild_obj

    else:
        return {"status_code": res.status_code}


def update_guild_settins(guild_id, dict):
    url = API_URL_BASE + '/guild/' + guild_id
    res = requests.get(url)
    if res.status_code != 200:
        return {"status_code": res.status_code}
    current_settings = rapidjson.loads(res.text)
    new_settings = {}
    dict_keys = dict.keys()
    for key in dict_keys:
        value = dict.get(key)
        new_settings[key] = value

    put_res = requests.put(url, json=new_settings)
    if put_res.status_code == 200:
        return True
    else:
        return {"status_code": put_res.status_code}


class blitz_aftermath_replays(commands.Cog):

    def __init__(self, client):
        self.client = client

    # Events
    # @commands.Cog.listener()
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'[Beta] Aftermath Replays cog is ready.')

    # Events
    # @commands.Cog.listener()
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user:
            return
        attachments = message.attachments
        guild_id = str(message.guild.id)
        guild_name = str(message.guild.name)

        guild_settings = get_guild_settings(guild_id, guild_name)
        if guild_settings.get('status_code') != 200:
            return

        enabled_channels = guild_settings.get('enabled_channels')
        stats = guild_settings.get('stats')
        guild_is_premium = guild_settings.get('guild_is_premium')

        # Verify channel
        if str(message.channel.id) not in enabled_channels:
            return

        replays = []
        if attachments:
            print('valid message')

            for attachment in attachments:
                if attachment.url.endswith('.wotbreplay'):
                    replays.append(attachment.url)

            if replays:
                rating = 'mBRT1_1A'
                stats_bot = None

                embed_desc = (
                    'React with 👀 for a transparent picture\nReact with 📈 for more detailed performance results')

                if debug == False:
                    try:
                        image_file, replay_id, replay_link = get_image(
                            replays, stats=stats, rating=rating)
                        embed = discord.Embed(
                            title='Download replay', url=replay_link, description=embed_desc)
                        embed.set_footer(text=f"MD5: {replay_id}")

                    except:
                        image_file = None
                        embed = discord.Embed()
                        embed.set_author(name='Aftermath')
                        embed.add_field(
                            name="Something failed...", value="I ran into an issue processing this replay, please let @Vovko know :)", inline=False)

                    # Send final message
                    await message.channel.send(embed=embed, file=image_file)

                else:
                    image_file, replay_id, replay_link = get_image(
                        replays, stats=stats, rating=rating)
                    embed = discord.Embed(
                        title='Download replay', url=replay_link, description=embed_desc)
                    embed.set_footer(text=f"MD5: {replay_id}")
                    await message.channel.send(embed=embed, file=image_file)
                    return

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        guild = discord.utils.find(
            lambda g: g.id == payload.guild_id, self.client.guilds)
        guild_id = str(guild.id)
        guild_name = str(guild.name)
        channel = self.client.get_channel(payload.channel_id)

        guild_settings = get_guild_settings(guild_id, guild_name)
        if guild_settings.get('status_code') != 200:
            await channel.send(f'Hmmm... Something did not go as planned, please try again in a few seconds. {guild_settings.get("status_code")}', delete_after=30)
            return

        enabled_channels = guild_settings.get('enabled_channels')
        stats = guild_settings.get('stats')
        guild_is_premium = guild_settings.get('guild_is_premium')

        if payload.channel_id not in enabled_channels:
            return
        else:
            message = await channel.fetch_message(payload.message_id)

            guild = discord.utils.find(
                lambda g: g.id == payload.guild_id, self.client.guilds)
            member = discord.utils.find(
                lambda m: m.id == payload.user_id, guild.members)

            if payload.emoji.name == '📈':
                replays = []

                stats = ['damage_rating', 'kill_rating',
                         'shot_rating', 'spotting_rating', 'track_rating', 'blocked_rating']

                replays.append(message.embeds[0].url)
                image_file, replay_id, replay_link = get_image(
                    replays, rating='mBRT1_1', stats=stats)

                embed = discord.Embed(
                    title='Download replay', url=replay_link)
                embed.set_footer(text=f"MD5: {replay_id}")

                await channel.send(embed=embed, file=image_file)
                try:
                    await message.remove_reaction(payload.emoji, member)
                except:
                    pass
                return

            elif payload.emoji.name == '👀':
                print('Sending DM')
                replays = []
                replays.append(message.embeds[0].url)
                image_file, replay_id, replay_link = get_image(
                    replays, bg=0, brand=0, darken=0, mapname=0)

                embed = discord.Embed(
                    title='Download replay', url=replay_link)
                embed.set_footer(text=f"MD5: {replay_id}")

                dm_channel = await member.create_dm()
                await dm_channel.send(embed=embed, file=image_file)
                try:
                    await message.remove_reaction(payload.emoji, member)
                except:
                    pass
                return
            else:
                return

    # Commands
    # @commands.command(aliases=[''])

    @commands.command()
    async def WatchHere(self, ctx):
        if ctx.author.bot or ctx.author == self.client.user:
            return

        await ctx.message.delete()

        guild_id = str(ctx.guild.id)
        guild_name = str(ctx.guild.name)
        channel_id = str(ctx.channel.id)
        channel_name = str(ctx.channel.name)
        user_id = str(ctx.author.id)
        user = ctx.author

        guild_settings = get_guild_settings(guild_id, guild_name)
        if guild_settings.get('status_code') != 200:
            await ctx.send(f'Hmmm... Something did not go as planned, please try again in a few seconds. {guild_settings.get("status_code")}', delete_after=30)
            return

        enabled_channels = guild_settings.get('enabled_channels')

        if channel_id in enabled_channels:
            await ctx.send(f'It looks like you already have me watching #{channel_name}.', delete_after=30)
            return

        guild_is_premium = guild_settings.get('guild_is_premium')

        if len(enabled_channels) >= 1 and not guild_is_premium:
            currently_enabled_channels = []
            for channel in enabled_channels:
                currently_enabled_channels.append(
                    f'#{discord.utils.get(ctx.guild.channels, id=int(channel))}')

            currently_enabled_channels = ', '.join(currently_enabled_channels)

            await ctx.send(f'It looks like you already have me watching {currently_enabled_channels}. You will need to be a premium member to enable more channels. You can also override those channels by using `{self.client.command_prefix}WatchHereOnly`', delete_after=30)
            return
        else:
            new_enabled_channels = enabled_channels.copy()
            new_enabled_channels.append(channel_id)
            enabled_channels_str = ';'.join(new_enabled_channels)
            new_settings = {'guild_channels': enabled_channels_str}
            res = update_guild_settins(guild_id, new_settings)
            if res:
                await ctx.send(f'Roger that! I am now watching #{channel_name} for WoT Blitz replays.', delete_after=30)
                return
            else:
                await ctx.send(f'Hmmm... Something did not go as planned, please try again in a few seconds. {res.get("status_code")}', delete_after=30)
                return

    @commands.command()
    async def LookAway(self, ctx):
        if ctx.author.bot or ctx.author == self.client.user:
            return

        await ctx.message.delete()

        guild_id = str(ctx.guild.id)
        guild_name = str(ctx.guild.name)
        channel_id = str(ctx.channel.id)
        channel_name = str(ctx.channel.name)
        user_id = str(ctx.author.id)
        user = ctx.author

        guild_settings = get_guild_settings(guild_id, guild_name)
        if guild_settings.get('status_code') != 200:
            await ctx.send(f'Hmmm... Something did not go as planned, please try again in a few seconds. {guild_settings.get("status_code")}', delete_after=30)
            return

        enabled_channels = guild_settings.get('enabled_channels')

        if channel_id in enabled_channels:
            new_enabled_channels = enabled_channels.copy()
            channel_index = new_enabled_channels.index(channel_id)
            new_enabled_channels = new_enabled_channels.pop(channel_index)
            enabled_channels_str = ';'.join(new_enabled_channels)
            new_settings = {'guild_channels': enabled_channels_str}
            res = update_guild_settins(guild_id, new_settings)
            if res:
                await ctx.send(f'Roger that! I am not watching #{channel_name} anymore.', delete_after=30)
                return
            else:
                await ctx.send(f'Hmmm... Something did not go as planned, please try again in a few seconds. {res.get("status_code")}', delete_after=30)
                return
        else:
            await ctx.send(f'I am not watching #{channel_name} right now. You can add this channel by typing `{self.client.command_prefix}WatchHere`', delete_after=30)

    @commands.command()
    async def WatchHereOnly(self, ctx):
        if ctx.author.bot or ctx.author == self.client.user:
            return

        await ctx.message.delete()

        guild_id = str(ctx.guild.id)
        guild_name = str(ctx.guild.name)
        channel_id = str(ctx.channel.id)
        channel_name = str(ctx.channel.name)
        user_id = str(ctx.author.id)
        user = ctx.author

        guild_settings = get_guild_settings(guild_id, guild_name)
        if guild_settings.get('status_code') != 200:
            await ctx.send(f'Hmmm... Something did not go as planned, please try again in a few seconds. {guild_settings.get("status_code")}', delete_after=30)
            return

        new_settings = {'guild_channels': channel_id}
        res = update_guild_settins(guild_id, new_settings)
        if res:
            await ctx.send(f'Roger that! I am now watching #{channel_name} for WoT Blitz replays and nothing else!', delete_after=30)
            return
        else:
            await ctx.send(f'Hmmm... Something did not go as planned, please try again in a few seconds. {res.get("status_code")}', delete_after=30)
            return


def setup(client):
    client.add_cog(blitz_aftermath_replays(client))

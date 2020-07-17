from discord.ext import commands, tasks
import discord
import requests
import rapidjson

from cogs.replays.replay import Replay
from cogs.replays.rating import Rating
from cogs.replays.render import Render
from cogs.api.api import Api

debug = True
Api = Api()


def get_image(urls, rating=None, stats=None, stats_bottom=None, bg=1, brand=1, darken=1, mapname=0):
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


class blitz_aftermath_replays(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.emoji_01 = self.client.get_emoji(
            733729140611612722)
        self.emoji_02 = self.client.get_emoji(
            733730453084700693)
        self.emoji_10 = self.client.get_emoji(
            733729140234256436)

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
        replays = []
        if attachments:
            guild_id = str(message.guild.id)
            guild_name = str(message.guild.name)

            guild_settings = Api.guild_get(guild_id, guild_name)
            if guild_settings.get('status_code') != 200:
                return

            enabled_channels = guild_settings.get('enabled_channels')
            stats = guild_settings.get('stats')
            guild_is_premium = guild_settings.get('guild_is_premium')

            # Verify channel
            if str(message.channel.id) in enabled_channels:
                print('valid message')

                for attachment in attachments:
                    if attachment.url.endswith('.wotbreplay'):
                        replays.append(attachment.url)

                if replays:
                    rating = 'mBRT1_1A'
                    stats_bot = None

                    embed_desc = (
                        f'React with {self.emoji_02} for a transparent picture\n\
                        React with {self.emoji_01} for more detailed performance results\n\
                        ')

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
                        image_message = await message.channel.send(embed=embed, file=image_file)
                        await image_message.add_reaction(self.emoji_02)
                        await image_message.add_reaction(self.emoji_01)

                    else:
                        image_file, replay_id, replay_link = get_image(
                            replays, stats=stats, rating=rating)
                        embed = discord.Embed(
                            title='Download replay', url=replay_link, description=embed_desc)
                        embed.set_footer(text=f"MD5: {replay_id}")
                        await message.channel.send(embed=embed, file=image_file)
                        return
            else:
                return

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        guild = discord.utils.find(
            lambda g: g.id == payload.guild_id, self.client.guilds)
        member = discord.utils.find(
            lambda m: m.id == payload.user_id, guild.members)

        if member == self.client.user:
            return

        guild_id = str(guild.id)
        guild_name = str(guild.name)
        channel = self.client.get_channel(payload.channel_id)
        guild_settings = Api.guild_get(guild_id, guild_name)
        if guild_settings.get('status_code') != 200:
            await channel.send(f'Hmmm... Something did not go as planned, please try again in a few seconds. {guild_settings.get("status_code")}', delete_after=30)
            return

        enabled_channels = guild_settings.get('enabled_channels')
        stats = guild_settings.get('stats')
        guild_is_premium = guild_settings.get('guild_is_premium')

        if str(payload.channel_id) in enabled_channels:
            message = await channel.fetch_message(payload.message_id)
            if payload.emoji == self.emoji_01:
                replays = []

                stats = ['damage_rating', 'kill_rating',
                         'shot_rating', 'spotting_rating', 'track_rating', 'blocked_rating']

                replays.append(message.embeds[0].url)
                image_file, replay_id, replay_link = get_image(
                    replays, rating='mBRT1_1', stats=stats)

                stats_message = await channel.send(file=image_file)
                return

            elif payload.emoji == self.emoji_02:
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
                return
            else:
                return
        else:
            return

    # Commands
    # @commands.command(aliases=[''])

    @commands.command(aliases=['lh', 'lookhere'])
    async def LookHere(self, ctx):
        if ctx.author.bot or ctx.author == self.client.user:
            return

        await ctx.message.delete()

        guild_id = str(ctx.guild.id)
        guild_name = str(ctx.guild.name)
        channel_id = str(ctx.channel.id)
        channel_name = str(ctx.channel.name)
        user_id = str(ctx.author.id)
        user = ctx.author

        guild_settings = Api.guild_get(guild_id, guild_name)
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
            new_settings = {'guild_channels_replays': new_enabled_channels}
            res = Api.guild_put(guild_id, new_settings)
            if res:
                await ctx.send(f'Roger that! I am now watching #{channel_name} for WoT Blitz replays.', delete_after=30)
                return
            else:
                await ctx.send(f'Hmmm... Something did not go as planned, please try again in a few seconds. {res.get("status_code")}', delete_after=30)
                return

    @commands.command(aliases=['la', 'lookaway'])
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

        guild_settings = Api.guild_get(guild_id, guild_name)
        if guild_settings.get('status_code') != 200:
            await ctx.send(f'Hmmm... Something did not go as planned, please try again in a few seconds. {guild_settings.get("status_code")}', delete_after=30)
            return

        enabled_channels = guild_settings.get('enabled_channels')

        if channel_id in enabled_channels:
            new_enabled_channels = enabled_channels.copy()
            new_enabled_channels.remove(channel_id)
            new_settings = {'guild_channels_replays': new_enabled_channels}
            res = Api.guild_put(guild_id, new_settings)
            if res:
                await ctx.send(f'Roger that! I am not watching #{channel_name} anymore.', delete_after=30)
                return
            else:
                await ctx.send(f'Hmmm... Something did not go as planned, please try again in a few seconds. {res.get("status_code")}', delete_after=30)
                return
        else:
            await ctx.send(f'I am not watching #{channel_name} right now. You can add this channel by typing `{self.client.command_prefix}WatchHere`', delete_after=30)

    @commands.command(aliases=['olh', 'LookOnlyHere', 'onlylookhere', 'lookonlyhere'])
    async def OnlyLookHere(self, ctx):
        if ctx.author.bot or ctx.author == self.client.user:
            return

        await ctx.message.delete()

        guild_id = str(ctx.guild.id)
        guild_name = str(ctx.guild.name)
        channel_id = str(ctx.channel.id)
        channel_name = str(ctx.channel.name)
        user_id = str(ctx.author.id)
        user = ctx.author

        guild_settings = Api.guild_get(guild_id, guild_name)
        if guild_settings.get('status_code') != 200:
            await ctx.send(f'Hmmm... Something did not go as planned, please try again in a few seconds. {guild_settings.get("status_code")}', delete_after=30)
            return

        new_settings = {'guild_channels_replays': [channel_id]}
        res = Api.guild_put(guild_id, new_settings)
        if res:
            await ctx.send(f'Roger that! I am now watching #{channel_name} for WoT Blitz replays and nothing else!', delete_after=30)
            return
        else:
            await ctx.send(f'Hmmm... Something did not go as planned, please try again in a few seconds. {res.get("status_code")}', delete_after=30)
            return


def setup(client):
    client.add_cog(blitz_aftermath_replays(client))

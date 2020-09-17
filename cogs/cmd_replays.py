from discord.ext import commands, tasks
import discord
import requests
import rapidjson
import traceback

from cogs.replays.replay import Replay
from cogs.replays.rating import Rating
from cogs.replays.render import Render
from cogs.api.guild_settings_api import API_v2

Guilds_API = API_v2()


def get_image(urls, rating=None, stats=None, stats_bottom=None, bg=1, brand=1, darken=1, mapname=0, raw=0):
    # Send replay to WoTInspector
    replays_list_data = Replay(urls).process_replays()
    replay_data = replays_list_data.get(
        list(replays_list_data.keys())[0])
    replay_id = list(replays_list_data.keys())[0]
    replay_link = replay_data.get('download_url')
    replay_data = Rating(
        replay_data).get_brt()

    room_type = replay_data.get(
        'battle_summary').get('room_type')
    room_type_mod = 0
    special_room_types = replay_data.get(
        'battle_summary').get(
        'special_room_types', [])
    if room_type in special_room_types and raw == 0:
        stats = ['rating', 'time_alive', 'damage_blocked',
                 'damage_made', 'accuracy']
        stats_bottom = []
        room_type_mod = 1

    image_file = Render(
        replay_data, replay_id, stats=stats, stats_bottom=stats_bottom).make_image(bg=bg, brand=brand, darken=darken, mapname=mapname)

    return image_file, replay_id, replay_link, room_type_mod


class blitz_aftermath_replays(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.emoji_01 = self.client.get_emoji(
            733729140611612722)
        self.emoji_02 = self.client.get_emoji(
            733730453084700693)
        self.emoji_03 = self.client.get_emoji(
            737794899721846804)
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
        if message.author == self.client.user or isinstance(message.channel, discord.channel.DMChannel):
            return
        attachments = message.attachments
        replays = []
        if attachments:
            guild_id = str(message.guild.id)
            enabled_channels, status_code = Guilds_API.get_one_guild_setting(guild_id=guild_id, key="guild_channels_replays")
            if status_code != 200:
                return

            # Verify channel
            if str(message.channel.id) in enabled_channels:
                for attachment in attachments:
                    if attachment.url.endswith('.wotbreplay'):
                        replays.append(attachment.url)

                if replays:
                    print(f'valid message - {message.guild.name}')
                    rating = 'mBRT1_1A'
                    try:
                        image_file, replay_id, replay_link, room_type_mod = get_image(
                            replays, rating=rating)

                        embed_desc = f'React with {self.emoji_02} for a transparent picture'
                        embed_desc += f'\nReact with {self.emoji_03} for a detailed performance breakdown of each player'
                        if room_type_mod == 0:
                            embed_desc += f'\nReact with {self.emoji_01} for a detailed Rating breakdown\n'
                        embed_desc += f'\nReact with {self.emoji_10} to learn more about Aftermath Rating'

                        embed = discord.Embed(
                            title='Download replay', url=replay_link, description=embed_desc)
                        embed.set_footer(text=f"MD5: {replay_id}")

                        # Send final message
                        image_message = await message.channel.send(embed=embed, file=image_file)

                        await image_message.add_reaction(self.emoji_02)
                        await image_message.add_reaction(self.emoji_03)
                        if room_type_mod == 0:
                            await image_message.add_reaction(self.emoji_01)
                        await image_message.add_reaction(self.emoji_10)

                    except Exception as e:
                        image_file = None
                        embed = discord.Embed()
                        embed.set_author(name='Aftermath')
                        embed.add_field(
                            name="Something failed...", value="This may occur when a replay file is incomplete or Wargaming API is not accessible, please try again in a few minutes.", inline=False)
                        embed.set_footer(
                            text=f"I ran into an issue processing this replay, this will be reported automatically.")
                        embed.set_footer(
                            text=f"{e}\nThis was reported automatically.")
                        await message.channel.send(embed=embed, file=image_file, delete_after=60)

                        # Report the error
                        channel_invite = await message.channel.create_invite(max_age=300)
                        owner_member = self.client.get_user(202905960405139456)
                        dm_channel = await owner_member.create_dm()
                        await dm_channel.send(f'An error occured in {guild_id} ({message.channel})\n```{replays[0]}```\n```{str(traceback.format_exc())}```\n{channel_invite}')
            else:
                return

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

        guild_id = str(guild.id)
        channel = self.client.get_channel(payload.channel_id)
        enabled_channels, status_code = Guilds_API.get_one_guild_setting(guild_id=guild_id, key="guild_channels_replays")
        if status_code != 200:
            await channel.send(f'Hmmm... Something did not go as planned, please try again in a few seconds. {status_code}', delete_after=30)
            return

        # guild_is_premium = guild_settings.get('guild_is_premium')     # Not used

        if str(payload.channel_id) in enabled_channels:
            message = await channel.fetch_message(payload.message_id)

            # Detailed Rating reaction
            if payload.emoji == self.emoji_01:
                for reaction in message.reactions:
                    if reaction.emoji == self.emoji_01:
                        await reaction.clear()

                replays = []
                stats = ['damage_rating', 'kill_rating', 'travel_rating',
                         'shot_rating', 'spotting_rating', 'assist_rating', 'blocked_rating']

                replays.append(message.embeds[0].url)
                image_file, replay_id, replay_link, _ = get_image(
                    replays, rating='mBRT1_1', stats=stats)

                await channel.send('Here is a Rating breakdown for this battle:', file=image_file)
                return

            # Detailed performance reaction
            if payload.emoji == self.emoji_03:
                for reaction in message.reactions:
                    if reaction.emoji == self.emoji_03:
                        await reaction.clear()

                replays = []
                stats = ['player_wr', 'damage_made', 'kills', 'damage_blocked', 'damage_assisted',
                         'enemies_spotted', 'distance_travelled', 'time_alive']

                replays.append(message.embeds[0].url)
                image_file, replay_id, replay_link, _ = get_image(
                    replays, rating='mBRT1_1', stats=stats, raw=1)

                await channel.send('Here is a detailed performance breakdown for each player:', file=image_file)
                return

            # Transparent picture reaction
            elif payload.emoji == self.emoji_02:
                print('Sending DM')
                replays = []
                replays.append(message.embeds[0].url)
                image_file, replay_id, replay_link, _ = get_image(
                    replays, bg=0, brand=1, darken=0, mapname=0)

                embed = discord.Embed(
                    title='Download replay', url=replay_link)
                embed.set_footer(text=f"MD5: {replay_id}")

                dm_channel = await member.create_dm()
                try:
                    await dm_channel.send(embed=embed, file=image_file)
                except:
                    print('DM failed')
                    await channel.send(f"Oh no! I can't send DMs to you {member.mention}. Please adjust your settings.", delete_after=30)
                return

            elif payload.emoji == self.emoji_10:
                embed = discord.Embed()
                embed.add_field(
                    name="Aftermath Rating", value=f"Our Rating is calculated based on the performance of each individual player, comparing them to the battle average.\n\nWhile we take many factors into account, your Damage, Accuracy, Spotting and Blocked Damage will give you the most points.\n\nYou can see a detailed rating breakdown by reacting with {self.emoji_01} to the original message.", inline=False)

                dm_channel = await member.create_dm()
                try:
                    await dm_channel.send(embed=embed)
                except:
                    print('DM failed')
                    await channel.send(f"Oh no! I can't send DMs to you {member.mention}. Please adjust your settings.", delete_after=30)
                return
            else:
                return
        else:
            return

    # Commands
    # @commands.command(aliases=[''])

    @commands.command(aliases=['lh', 'lookhere'])
    @commands.has_permissions(manage_messages=True)
    async def LookHere(self, ctx):
        if ctx.author.bot or ctx.author == self.client.user:
            return

        try:
            await ctx.message.delete()
        except:
            await ctx.send("It looks like I do not have `Manage Messages` permissions in this channel, this may affect my functionality.")

        guild_id = str(ctx.guild.id)
        guild_name = str(ctx.guild.name)
        channel_id = str(ctx.channel.id)
        channel_name = str(ctx.channel.name)

        enabled_channels, status_code = Guilds_API.get_one_guild_setting(guild_id=guild_id, key="guild_channels_replays")
        if status_code == 404:
            Guilds_API.add_new_guild(guild_id=guild_id, guild_name=guild_name)
            enabled_channels = []
        elif status_code != 200:
            await ctx.send(f'Hmmm... Something did not go as planned, please try again in a few seconds. {status_code}', delete_after=30)
            return


        if channel_id in enabled_channels:
            await ctx.send(f'It looks like you already have me watching #{channel_name}.', delete_after=30)
            return

        guild_is_premium, _ = Guilds_API.get_one_guild_setting(guild_id=guild_id, key="guild_is_premium")
        if enabled_channels:
            new_enabled_channels = enabled_channels.append(channel_id)
        else:
            new_enabled_channels = [channel_id]

        if len(new_enabled_channels) > 2 and not guild_is_premium:
            channel_names = []
            for channel in enabled_channels:
                channel_names.append(self.client.get_channel(channel).name)
            try:
                await ctx.send(f"It looks like you already have me watching {channel_names[0]} and {channel_names[1]}. You will need to be a premium member to enable more channels.")
            except:
                 await ctx.send(f"It looks like you already have me watching multiple channels. You will need to be a premium member to enable more channels.")

        else:
            new_settings = {"guild_channels_replays": new_enabled_channels}
            _, status_code = Guilds_API.update_guild(guild_id=guild_id, settings=new_settings)
            if status_code == 200:
                await ctx.send(f"I am now watching #{channel_name} for replays!")
            else:
                await ctx.send(f"I was not able to add this channel. `{status_code}`")

    @commands.command(aliases=['la', 'lookaway'])
    @commands.has_permissions(manage_messages=True)
    async def LookAway(self, ctx):
        if ctx.author.bot or ctx.author == self.client.user:
            return

        try:
            await ctx.message.delete()
        except:
            await ctx.send("It looks like I do not have `Manage Messages` permissions in this channel, this may affect my functionality.")

        guild_id = str(ctx.guild.id)
        channel_id = str(ctx.channel.id)
        channel_name = str(ctx.channel.name)

        enabled_channels, status_code = Guilds_API.get_one_guild_setting(guild_id=guild_id, key="guild_channels_replays")
        if status_code != 200:
            await ctx.send(f'Hmmm... Something did not go as planned, please try again in a few seconds. {status_code}', delete_after=30)
            return

        if channel_id in enabled_channels:
            new_enabled_channels = enabled_channels.copy()
            new_enabled_channels.remove(channel_id)
            new_settings = {'guild_channels_replays': new_enabled_channels}
            _, status_code = Guilds_API.update_guild(guild_id=guild_id, settings=new_settings)
            if status_code == 200:
                await ctx.send(f'Roger that! I am not watching #{channel_name} anymore.', delete_after=30)
                return
            else:
                await ctx.send(f'Hmmm... Something did not go as planned, please try again in a few seconds. {status_code}', delete_after=30)
                return
        else:
            await ctx.send(f'I am not watching #{channel_name} right now. You can add this channel by typing `{self.client.command_prefix[0]}LookHere`', delete_after=30)

    @commands.command(aliases=['olh', 'LookOnlyHere', 'onlylookhere', 'lookonlyhere'])
    @commands.has_permissions(manage_messages=True)
    async def OnlyLookHere(self, ctx):
        if ctx.author.bot or ctx.author == self.client.user:
            return

        try:
            await ctx.message.delete()
        except:
            await ctx.send("It looks like I do not have `Manage Messages` permissions in this channel, this may affect my functionality.")


        guild_id = str(ctx.guild.id)
        channel_id = str(ctx.channel.id)
        channel_name = str(ctx.channel.name)

        _, status_code = Guilds_API.get_one_guild_setting(guild_id=guild_id, key="guild_channels_replays")
        if status_code != 200:
            await ctx.send(f'Hmmm... Something did not go as planned, please try again in a few seconds. {status_code}', delete_after=30)
            return

        new_settings = {'guild_channels_replays': [channel_id]}
        _, status_code = Guilds_API.update_guild(guild_id=guild_id, settings=new_settings)
        if status_code == 200:
            await ctx.send(f'Roger that! I am now watching #{channel_name} for WoT Blitz replays and nothing else!', delete_after=30)
            return
        else:
            await ctx.send(f'Hmmm... Something did not go as planned, please try again in a few seconds. {status_code}', delete_after=30)
            return


def setup(client):
    client.add_cog(blitz_aftermath_replays(client))

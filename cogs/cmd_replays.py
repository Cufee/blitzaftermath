from discord.ext import commands, tasks
import discord

from cogs.replays.replay import Replay
from cogs.replays.rating import Rating
from cogs.replays.render import Render

enabled_channels = [719831153162321981, 719875141047418962]
debug = False


def get_image(urls, rating='sBRT1_0', stats=None, stats_bottom=None, bg=1, brand=1, darken=1, mapname=1):
    # Send replay to WoTInspector
    replays_list_data = Replay(urls).process_replays()
    replay_data = replays_list_data.get(
        list(replays_list_data.keys())[0])
    replay_id = list(replays_list_data.keys())[0]
    replay_link = replay_data.get('download_url')
    replay_data = Rating(
        replay_data).calculate_rating(rating)

    image_file = Render(
        replay_data, replay_id, stats=stats, stats_bottom=stats_bottom).image(bg=bg, brand=brand, darken=darken, mapname=mapname)

    return image_file, replay_id, replay_link


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
        channel_name = message.channel.name
        attachments = message.attachments

        # Verify channel
        if message.channel.id not in enabled_channels:
            return

        replays = []
        if attachments:
            print('valid message')

            for attachment in attachments:
                if attachment.url.endswith('.wotbreplay'):
                    replays.append(attachment.url)

            if replays:
                stats = ['kills', 'damage', 'player_wr', 'rating']
                stats_bot = None

                embed_desc = (
                    'React with 👀 for a transparent picture\nReact with 📈 for more detailed performance results')

                if debug == False:
                    try:
                        image_file, replay_id, replay_link = get_image(
                            replays, stats=stats)
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
                        replays, stats=stats)
                    embed = discord.Embed(
                        title='Download replay', url=replay_link, description=embed_desc)
                    embed.set_footer(text=f"MD5: {replay_id}")
                    await message.channel.send(embed=embed, file=image_file)
                    return

    # Events
    # @commands.Cog.listener()
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        print('reaction')
        if payload.channel_id not in enabled_channels:
            return
            print('error')
        else:
            channel = self.client.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)

            guild = discord.utils.find(
                lambda g: g.id == payload.guild_id, self.client.guilds)
            member = discord.utils.find(
                lambda m: m.id == payload.user_id, guild.members)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.channel_id not in enabled_channels:
            return
        else:
            channel = self.client.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)

            guild = discord.utils.find(
                lambda g: g.id == payload.guild_id, self.client.guilds)
            member = discord.utils.find(
                lambda m: m.id == payload.user_id, guild.members)

            if payload.emoji.name == '📈':
                replays = []

                stats = ['kill_efficiency', 'damage_efficiency',
                         'shot_efficiency', 'spotting_efficiency']

                replays.append(message.embeds[0].url)
                image_file, replay_id, replay_link = get_image(
                    replays, rating='mBRT1_0', stats=stats)

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


def setup(client):
    client.add_cog(blitz_aftermath_replays(client))

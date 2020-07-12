from discord.ext import commands, tasks
import discord

from cogs.replays.replay import Replay
from cogs.replays.rating import Rating
from cogs.replays.render import Render


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
        # if message.channel.id != 719875141047418962:
        if message.channel.id != 719831153162321981 and message.channel.id != 719875141047418962:
            return

        replays = []
        if attachments:
            print('valid message')

            for attachment in attachments:
                if attachment.url.endswith('.wotbreplay'):
                    replays.append(attachment.url)

            # Send replay to WoTInspector
            replays_list_data = Replay(replays).process_replays()

            replay_data = replays_list_data.get(
                list(replays_list_data.keys())[0])
            replay_id = list(replays_list_data.keys())[0]

            replay_data = Rating(replay_data).calculate_rating('mBRT1_0')

            # Send message
            try:
                image_file = Render(replay_data, replay_id).image()
                await message.channel.send(f"```MD5: {replay_id}```", file=image_file)
            except:
                embed = Render(replay_data, replay_id).embed()
                await message.channel.send(embed=embed)
            return


def setup(client):
    client.add_cog(blitz_aftermath_replays(client))

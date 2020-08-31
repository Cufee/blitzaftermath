from discord.ext import commands, tasks
import discord
import requests
import rapidjson
import sys
import traceback
from datetime import datetime

from cogs.replays.replay import Replay
from cogs.replays.rating import Rating
from cogs.replays.render import Render
from cogs.api.guild_settings_api import API_v2

debug = False
Guilds_API = API_v2()


class maintenance(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.client.remove_command("help")

    # Events
    # @commands.Cog.listener()
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'[Beta] Aftermath Stats cog is ready.')

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        guild_id = str(guild.id)
        guild_name = str(guild.id)
        _, status_code = Guilds_API.add_new_guild(guild_id, guild_name)

        owner_member = self.client.get_user(202905960405139456)
        dm_channel = await owner_member.create_dm()
        await dm_channel.send(f"Aftermath joined {guild_name}. Setup complete with `{status_code}`.")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        guild_id = str(guild.id)
        guild_name = str(guild.id)
        new_settings = {"kicked_on": datetime.utcnow()}
        _, status_code = Guilds_API.update_guild(guild_id, new_settings, safe=False)

        owner_member = self.client.get_user(202905960405139456)
        dm_channel = await owner_member.create_dm()
        await dm_channel.send(f"Aftermath was removed from {guild_name}. Edit complete with `{status_code}`.")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, 'on_error'):
            return
        # This prevents any cogs with an overwritten cog_command_error being handled here.
        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        ignored = ()
        # ignored = (commands.CommandNotFound, )

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, 'original', error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            return

        if isinstance(error, commands.DisabledCommand):
            await ctx.send(f'{ctx.command} has been disabled.')

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.send(f'{ctx.command} can not be used in Private Messages.')
            except discord.HTTPException:
                pass

        # Command not found or is disabled
        elif isinstance(error, commands.CommandNotFound):
            try:
                await ctx.author.send(f'This is not a valid command. You can use `v-help` to check all available commands.')
            except discord.HTTPException:
                pass

        # For this error example we check to see where it came from...
        elif isinstance(error, commands.BadArgument):
            if ctx.command.qualified_name == 'tag list':  # Check if the command being invoked is 'tag list'
                await ctx.send('I could not find that member. Please try again.')

        else:
            # All other Errors not returned come here. And we can just print the default TraceBack.
            print('Ignoring exception in command {}:'.format(
                ctx.command), file=sys.stderr)
            traceback.print_exception(
                type(error), error, error.__traceback__, file=sys.stderr)

    @commands.command(aliases=['help'])
    async def _help(self, ctx):
        help_str = (f"""
**AfterMath**:
To analyze a WoT Blitz replay, just send a file and I will do the rest.

**AfterStats**:
Command: `v-stats`
Aliases: `v-wr`, `v-session`

Use `v-stats PlayerName` to check the last session of a player.
*For example: `v-stats Vovko`*

*All sessions are reset at 02:00 daily, based on server timezone.
Newly added players will need to play at least one battle before Aftermath starts tracking their session.*

You can also check a specific session with `v-stats PlayerName hours`.
*For example:* `v-stats Vovko@na 48`
        """)

# **DISABLED**
# **AfterContest**:
# Use `v-check TAG@SERVER` to check the current Ace Tanker count of a clan. Individual player contributions are reset every 24 hours.
# You can also check the current top 5 clans by Ace Tanker medals using `v-top`.



        await ctx.send(help_str)


    @commands.command()
    @commands.is_owner()
    async def broadcast(self, ctx):
        all_guilds, status_code = Guilds_API.get_all_guilds()
        if status_code != 200:
            ctx.send(f"Error `{status_code}`")
            return

        brk_message = ctx.message.content[(len(f"{ctx.prefix}{ctx.command} ")):]
        if not brk_message:
            return
        
        message_failed_guilds = []
        for guild_data in all_guilds:
            default_replay_channels = guild_data.get("guild_channels_replays")
            if not default_replay_channels:
                guild_name = guild_data.get("guild_name")
                message_failed_guilds.append(guild_name)
                continue
            
            channel = self.client.get_channel(int(default_replay_channels[0]))
            if channel:
                await channel.send(brk_message)


def setup(client):
    client.add_cog(maintenance(client))

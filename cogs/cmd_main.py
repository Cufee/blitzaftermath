from discord.ext import commands
import discord
import sys
import traceback
from datetime import datetime

from cogs.api.guild_settings_api import API_v2
from cogs.api.discord_users_api import DiscordUsersApiV2
from cogs.api.message_cache_api import MessageCacheAPI
from cogs.api.bans_api import BansAPI
from cogs.api.stats_api import MongoClient, StatsApi, get_wg_api_domain
import re

from random import random

import requests
import rapidjson

command_cooldown = 5

db_client = MongoClient("mongodb://51.222.13.110:27017")
players = db_client.stats.players

debug = False
Guilds_API = API_v2()
Ban_API = BansAPI()
UsersApiV2 = DiscordUsersApiV2()
CacheAPI = MessageCacheAPI()
API = StatsApi()

api_domain = "https://api.aftermath.link"
stats_domain = "https://stats.aftermath.link"

# Strings
# Help
help_str = (f"""
**Replays**:
```To analyze a WoT Blitz replay, just send a file and I will do the rest.```
**Stats**:
- *All sessions are reset at 02:00 daily, based on server timezone.*
- *Newly added players will need to play at least one battle before Aftermath starts tracking their session.*

`v-stats`
```
Aliases: v-wr, v-session

Use v-stats PlayerName to check the last session of a player.
- For example: v-stats Vovko

You can also check a specific session with v-stats PlayerName days.
- For example: v-stats Vovko-na 3
```
`v-iam`
```
To change the default account Aftermath looks up for you, use v-iam NewName.
```
`v-fancy`
```
Aliases: v-bg

Sets a new background for your stats.
- For example: v-fancy https://link-to-an-image.jpg

- You can also just attach an image to this message instead of using a link.
```
**Other**:
`v-login`
```
Use this command to verify your account and get a checkmark next to your name.

- This is a required step for setting up a background image or buying Aftermath Premium for the first time.
```
`v-premium`
```
Use this command to get your Aftermath Premium membership.
```
""")
# Permissions
perms_text = """Here is a full list of permissions Aftermath needs to function correctly:
```
Basic permissions:
- Read Messages
- Read Message History
- Send Messages
- Manage Messages
- Embed Links
- Attach Files
- Add Reaction
- Use External Reactions
- Connect (voice)
- Speak   (voice)

Other permissions:
- Create Instant Invites
    This is used to invite the developer to the server in case an error has occured and was automatically reported.
- Change Nickname
    Just to make sure Aftermath name can be adjusted across all servers.```"""


class maintenance(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.client.remove_command("help")
        self.api_domain = "https://api.aftermath.link"

    async def report_to_owner(self, message):
        owner_member = self.client.get_user(202905960405139456)
        dm_channel = await owner_member.create_dm()
        await dm_channel.send(message)
        return

    async def global_message(self, message, embed):
        reached = 0
        channels = 0
        failed = 0
        for guild in self.client.guilds:
            # Try to message last used channels
            try:
                last_chan_ids = CacheAPI.get_last_used_channels(guild.id) or []
                sent = 0
                for id in last_chan_ids:
                    try:
                        channel = self.client.get_channel(int(id))
                        await channel.send(message, embed=embed)
                        channels += 1
                        sent += 1
                    except:
                        continue

                if sent == 0:
                    raise Exception("did no reach any channels")
                reached += 1

            # Try messaging replays channel
            except Exception as e:
                print(e)
                try:
                    channl_id, _ = Guilds_API.get_one_guild_setting(str(guild.id), "guild_channels_replays")
                    channel = self.client.get_channel(int(channl_id[0]))
                    await channel.send(message, embed=embed)
                    channels += 1
                    reached += 1
                except Exception as e:
                    print(e)
                    failed += 1
                continue
        
        return f"Reached {channels} channels on {reached} servers, {failed} servers failed"

    # Events
    # @commands.Cog.listener()
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'[Beta] Aftermath maintenance cog is ready.')


    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        guild_id = str(guild.id)
        guild_name = str(guild.name)
        _, status_code = Guilds_API.add_new_guild(guild_id, guild_name)

        await self.report_to_owner(f"Aftermath joined {guild_name}. Setup complete with `{status_code}`.")
        return


    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        guild_id = str(guild.id)
        guild_name = str(guild.name)
        new_settings = {"kicked_on": datetime.utcnow()}
        _, status_code = Guilds_API.update_guild(guild_id, new_settings, safe=False)

        await self.report_to_owner(f"Aftermath was removed from {guild_name}. Edit complete with `{status_code}`.")
    

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def perms(self, ctx):
        perms = ctx.channel.permissions_for(ctx.guild.me).value
        await ctx.send(f"{perms_text}*Your perms code is {perms}*")


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

        ignored = (commands.CommandNotFound, )

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, 'original', error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            return

        elif isinstance(error, commands.DisabledCommand):
            await ctx.send(f'{ctx.command} has been disabled.', delete_after=15)

        elif isinstance(error, commands.errors.CommandOnCooldown):
            try:
                await ctx.author.send(error)
            except discord.HTTPException:
                pass

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.send(f'This command can not be used in Private Messages.')
            except discord.HTTPException:
                pass

        # Check if command missing arguments
        elif isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send(f'You will need to give me more context to use this command. Check v-help if you are not sure what arguments a given command requires.', delete_after=15)

        elif isinstance(error, commands.CheckFailure):
            await ctx.send(f'You do not have the required permissions to use this command.', delete_after=15)

        else:
            # All other Errors not returned come here. And we can just print the default TraceBack.
            print('Ignoring exception in command {}:'.format(
                ctx.command), file=sys.stderr)
            traceback.print_exception(
                type(error), error, error.__traceback__, file=sys.stderr)


    @commands.command()
    @commands.is_owner()
    async def ban(self, ctx, _, hours, *args):
        await ctx.message.delete()

        # Check for a mention
        if not ctx.message.mentions:
            await ctx.send("You need to mention somebody in this message.", delete_after=15)
            return

        # Compile reason and get user
        reason = " ".join(args)
        user = ctx.message.mentions[0]

        # Ban
        try:
            Ban_API.ban_user(user.id, reason, False, min=1, hrs=int(hours))
        except Exception as e:
            print(e)
            await ctx.send("An error occured. Check logs.", delete_after=15)
            return
    
        await ctx.send(f"{user.name} has been banned for {hours} hours.", delete_after=15)
        return
        

def setup(client):
    client.add_cog(maintenance(client))

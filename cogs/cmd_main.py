from discord.ext import commands
import discord
import sys
import traceback
from datetime import datetime

from cogs.api.guild_settings_api import API_v2
from cogs.api.discord_users_api import DiscordUsersApiV2
from cogs.api.message_cache_api import MessageCacheAPI
from cogs.pay_to_win.stats_module import CustomBackground
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
bgAPI = CustomBackground()
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
                last_chan_ids = CacheAPI.get_last_used_channels(guild.id)
                for id in last_chan_ids:
                    channel = self.client.get_channel(int(id))
                    await channel.send(message, embed=embed)
                    channels += 1
                reached += 1

            # Try messaging replays channel
            except:
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
    @commands.guild_only()
    async def on_message(self, message):
        ctx = await self.client.get_context(message)
        if not ctx.command or ctx.prefix not in self.client.command_prefix or message.author == self.client or isinstance(ctx.channel, discord.channel.DMChannel):
            return

        perms = message.channel.permissions_for(ctx.guild.me).value
        if perms < 70642753:
            flag = random()
            if flag > 0.5:
                await ctx.send(f"*Aftermath does not have proper permissions on this server. Please check `v-perms` if you are an administrator.*")
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

        ignored = ()
        # ignored = (commands.CommandNotFound, )

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

        # # Command not found or is disabled
        # elif isinstance(error, commands.CommandNotFound):
        #     try:
        #         await ctx.author.send(help_str)
        #     except discord.HTTPException:
        #         pass

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
    async def broadcast(self, ctx):
        brc_message = ctx.message.content[(len(f"{ctx.prefix}{ctx.command} ")):]
        if not brc_message:
            await ctx.send("Message is empty")
            return

        embed=discord.Embed(color=0xff0000)
        embed.add_field(name="Service Annoucement", value=brc_message, inline=False)
        embed.set_footer(text=f"- {ctx.author.name}#{ctx.author.discriminator}")
        
        result = await self.global_message(None, embed)
        await ctx.send(result)


    @commands.command()
    @commands.is_owner()
    async def spoms(self, ctx):
        brc_message = ctx.message.content[(len(f"{ctx.prefix}{ctx.command} ")):]
        if not brc_message:
            await ctx.send("Message is empty")
            return

        embed=discord.Embed(color=0x0aff00)
        embed.add_field(name="Sponsored Message", value=brc_message, inline=False)
        
        result = await self.global_message(None, embed)
        await ctx.send(result)


    @commands.command()
    async def invite(self, ctx):
        if ctx.guild:
            try:
                await ctx.message.delete()
            except:
                print(f"Failed to delete a message in {ctx.guild.name}")

        dm_channel = await ctx.author.create_dm()
        await dm_channel.send("You can invite me to your server by following this link:\nhttps://byvko.dev/")


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

    @commands.command()
    async def premium(self, ctx):
        premium_message = "Aftermath Premium is a monthly subscription that supports bot development and pays for server costs.\n\nHere are some perks you will get:\n- Advanced sorting using the reactions below your session stats.\n- Custom background for stats.\n- 30 day sessions."

        # Get user data
        try:
            _ = UsersApiV2.get_user_data(ctx.author.id)
        except:
            await ctx.send("Something did not work as planned. Try using v-login first.")
            return
        
        res_raw = requests.get(f"{self.api_domain}/payments/new/{ctx.author.id}")
        if not res_raw:
            await ctx.send("It looks like Aftermath is partially down for maintenance, please try again later.", delete_after=30)
            return

        res_data = rapidjson.loads(res_raw.text)
        error = res_data.get("error")
        payment_link = res_data.get("payment_link")

        if error == "already subscribed":
            await ctx.send("You already have a subscription to Aftermath Premium, thanks!", delete_after=30)
            return

        if payment_link and not error:
            try:
                dm_channel = await ctx.author.create_dm()
                await dm_channel.send(f"{premium_message}\n\nYour PayPal payment link:\n{payment_link}\n\n*It may take up to an hour to process your payment, if you do not see your membership after that hour has passed, please use `v-report message` to report this issue.*")
                return
            except:
                await ctx.send(f"Hey {ctx.author.mention}! I am not able to DM you, please make sure you have DMs open.", delete_after=30)
                return

        await ctx.send(f"Something went wrong :confused:\n```{error}```")
        await self.report_to_owner(f"Failed to get a payment link in {ctx.guild.name} ({ctx.guild.name})\nUserID: {ctx.author.id}\nError: {error}")
        return

    @commands.command()
    async def oldreport(self, ctx, *args):
        await ctx.message.delete()

        if len(args) < 5:
            await ctx.send('Please describe the issue you are having in more detail.\n*For example: v-report Does not show my stats, giving me error "Zap render failed"*.')
            return

        try:
            user_data = UsersApiV2.get_user_data(ctx.author.id)
        except:
            await ctx.send(f"Hey {ctx.author.mention}! Please use v-login to enable error reporting for your account.", delete_after=30)
            return

        if user_data.get("banned", False):
            return
    
        message = " ".join(args)
        await self.report_to_owner(f"Error report from {ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})\nGuild: {ctx.guild.id}\n```{message}```")
        await ctx.send("Thank you for reporting an issue! Please make sure your DMs are open in case we need to contact you through Discord.", delete_after=30)
        return

    @commands.command()
    @commands.is_owner()
    async def padd(self, ctx, _, days):
        await ctx.message.delete()

        # Check for a mention
        if not ctx.message.mentions:
            await ctx.send("You need to mention somebody in this message.", delete_after=15)
            return

        try:
            days = int(days)
        except:
            await ctx.send("Unable to parse days(int) from passed argument.", delete_after=15)
            return

        # Create intent
        res_data = {}
        try:
            req = {
                "user_id": ctx.message.mentions[0].id,
                "premium_days": int(days)
            }
            res = requests.get(f"{self.api_domain}/premium/add", json=req)
            res_data = rapidjson.loads(res.text)
        except:
            await ctx.send(f"Failed to reach the API.", delete_after=15)
            return
        
        if res_data.get("error"):
            await ctx.send(res_data.get("error"), delete_after=30)
            return

        # Commit intent
        intent_id = res_data.get("intent_id")
        if not intent_id:
            await ctx.send("Got bad intent_id", delete_after=15)
            return

        com_res_data = {}
        try:
            res = requests.get(f"{self.api_domain}/premium/redirect/" + intent_id)
            com_res_data = rapidjson.loads(res.text)
        except:
            await ctx.send(f"Failed to reach the API while commiting.", delete_after=15)
            return
        
        if com_res_data.get("error"):
            await ctx.send(com_res_data.get("error"), delete_after=30)
            return

        await ctx.send(f"Added {days} days of Aftermath Premium for {ctx.message.mentions[0].name} - {com_res_data.get('status')}", delete_after=30)
        return


    @commands.command(aliases=['bg'])
    @commands.cooldown(1, command_cooldown, commands.BucketType.user)
    @commands.guild_only()
    async def fancy(self, ctx, url=None):
        if ctx.author == self.client.user or isinstance(ctx.channel, discord.channel.DMChannel):
            return

        try:
            res = requests.get(f'{api_domain}/users/{ctx.author.id}')
            premium = rapidjson.loads(res.text).get('premium', False)
            verified = rapidjson.loads(res.text).get('verified', False)
            if not verified:
                await ctx.send("You need to verify your account with `v-login` before setting up a background image.")
                return
            elif not premium:
                await ctx.send("You will need to have Aftermath Premium to change the background.")
                return
            
        except:
            await ctx.send("It looks like Aftermath is partially down for maintenance. Try again later.")
            return

        # Fix url
        try:
            url = url.strip()
        except:
            url = None

        try:
            # Set image url
            if url:
                img_url = url
            else:
                img_url = None

            attachments = ctx.message.attachments
            # Check attachments for jpeg images
            for att in attachments:
                if att.url:
                    img_url = att.url
                    break

            # Image url found
            if img_url:
                err = bgAPI.put(user_id=str(ctx.author.id), image_url=img_url)
                if not err:
                    await ctx.send("Awesome! Your stats will now shine bright :)")
                    return
                else:
                    raise Exception(err)
            # No valid url
            else:
                raise Exception('There is no link to a valid image in your message.\nUsage example:\nv-fancy https://i.imgflip.com/1ovalo.jpg')

        # Handle exceptions
        except Exception as e:
            print(traceback.format_exc())
            await ctx.channel.send(f'Something did not work as planned :confused:\n```{e}```')


    @commands.command(aliases=['nobg'])
    @commands.cooldown(1, command_cooldown, commands.BucketType.user)
    @commands.guild_only()
    async def notfancy(self, ctx):
        if ctx.author == self.client.user or isinstance(ctx.channel, discord.channel.DMChannel):
            return

        try:
            err = bgAPI.delete(str(ctx.author.id))
            if err:
                raise Exception(err)
            await ctx.send("Removed your custom background for stats.")

        # Handle exceptions
        except Exception as e:
            print(traceback.format_exc())
            await ctx.channel.send(f'Something did not work as planned :confused:\n```{e}```')


    @commands.command(aliases=['Iam', 'IAM'])
    @commands.cooldown(1, command_cooldown, commands.BucketType.user)
    @commands.guild_only()
    async def iam(self, message, player_name_str):
        try:
            # Split player string, check validity, find player ID
            if '@' in player_name_str:
                await message.channel.send("Please use `-` instead of `@` to separate the username and server.")
                return

            elif '-' in player_name_str:
                player_name_str = player_name_str
                player_name_str_list = player_name_str.split('-')
                player_name = player_name_str_list[0]
                if len(player_name) < 3:
                    raise Exception(
                        'Player name needs to be at least 3 characters long')
                player_realm = player_name_str_list[1].upper()
                player_details = players.find_one(
                    {'nickname': re.compile(player_name, re.IGNORECASE), 'realm': player_realm})
                if not player_details:
                    # Check if username is valid
                    api_domain, _ = get_wg_api_domain(realm=player_realm)
                    api_url = api_domain + \
                        '/wotb/account/list/?application_id=add73e99679dd4b7d1ed7218fe0be448&search=' + player_name
                    res = requests.get(api_url)
                    res_data_raw = rapidjson.loads(res.text)
                    if res.status_code != 200 or not res_data_raw:
                        raise Exception(
                            f'WG API responded with {res.status_code}')

                    res_data = res_data_raw.get('data')
                    if not res_data:
                        print(api_url)
                        print(res_data)
                        raise Exception(
                            f'WG: Player not found. Is the username spelled correctly?')

                    # Get player id and enable tracking
                    player_data_1 = res_data[0]
                    player_id = player_data_1.get('account_id')

                    late_update = True

                else:
                    late_update = False
                    player_id = player_details.get('_id')
                    player_realm = player_details.get('realm')

                # Get Discord user ID
                user_id = message.author.id
                try:
                    UsersApiV2.set_user_player_id(
                        discord_user_id=user_id, player_id=player_id)
                except Exception as e:
                    print(traceback.format_exc())
                    await message.channel.send(f'Something did not work as planned :confused:\n```{e}```')
                    return

                if late_update:
                    message_text = f'Awesome! You will be able to check your stats with `{self.client.command_prefix[0]}stats` **once you play one more regular battle**.'
                else:
                    message_text = f'Awesome! You can now check your stats with `{self.client.command_prefix[0]}stats`.'

                await message.channel.send(message_text)

                if late_update:
                    API.update_players([player_id], realm=player_realm)
                    API.update_stats([player_id], realm=player_realm)
                    API.add_career_wn8([player_id], realm=player_realm)
                return None

            else:
                await message.channel.send(
                    f'There is no `-` in your message. Please use this symbol to separate the username and server.\n*For example: {self.client.command_prefix[0]}iam Vovko-na*', delete_after=30)
                return None

        # Handle exceptions
        except Exception as e:
            print(traceback.format_exc())
            await message.channel.send(f'Something did not work as planned :confused:\n```{e}```')

def setup(client):
    client.add_cog(maintenance(client))

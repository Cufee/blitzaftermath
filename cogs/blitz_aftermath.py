from discord.ext import commands, tasks
import discord

import rapidjson
import requests
import re

# Nononets setup
nano_url = 'https://app.nanonets.com/api/v2/OCR/Model/81ef3ac1-fa8f-49fc-9e02-bfc8218c7d8c/LabelUrls/'
nano_headers = {
    'accept': 'application/x-www-form-urlencoded'
}

# WG API setup
wg_application_id = 'application_id=add73e99679dd4b7d1ed7218fe0be448'
wg_api_base_url = 'https://api.wotblitz.com/wotb/account/'
wg_api_addon_list = 'list/?'
wg_api_addon_info = 'info/?'
wg_api_realm_na = 'r_realm=na'

class blitz_aftermath(commands.Cog):

    def __init__(self, client):
        self.client = client

    # Events
    # @commands.Cog.listener()
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'[Beta] help cog is ready.')

    # Events
    # @commands.Cog.listener()
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user: return
        channel = message.channel.name
        attachments = message.attachments

        # Verify channel
        if message.channel.id != 719875141047418962:
            return

        nano_data = { 'urls': []}
        if attachments:
            print('valid message')

            for attachment in attachments:
                nano_data.get('urls').append(attachment.url)

            # Send image to Nanonet
            response = requests.request('POST', nano_url, headers=nano_headers, auth=requests.auth.HTTPBasicAuth('7LqEDWQPGBQjhCp8G2jBJSgJuVzAqNLR', ''), data=nano_data)
            all_predictions = rapidjson.loads(response.text).get('result')[0].get('prediction')

            # Check if image was valid
            if len(all_predictions) < 10:
                await message.channel.send('Failed to find at least 10 usernames', delete_after=30)
                return

            # Separate into allies and enemies
            min_x = 1000
            max_x = 0
            longest_name = 0
            allies = []
            enemies = []
            error = []
            for prediction in all_predictions:
                prd_max_x = prediction.get('xmax')
                prd_min_x = prediction.get('xmin')

                name_length = prd_max_x - prd_min_x
                if name_length > longest_name:
                    longest_name = name_length

                if prd_max_x > max_x:
                    max_x = prd_max_x
                if prd_min_x < min_x:
                    min_x = prd_min_x
            
            middle_line = longest_name*1.5 + min_x

            for prediction in all_predictions:
                prd_min_x = prediction.get('xmax')

                if prd_min_x < middle_line:
                    allies.append(prediction.get('ocr_text'))
                if prd_min_x > middle_line:
                    enemies.append(prediction.get('ocr_text'))

            # Get winrate from WG api
            allies, ally_wr = add_winrate(allies)
            enemies, enemy_wr = add_winrate(enemies)
            
            all_wr = ally_wr + enemy_wr

            if len(all_wr) > 10:
                ally_team_wr = round(sum(ally_wr) / len(ally_wr), 1)
                enemy_team_wr = round(sum(enemy_wr) / len(enemy_wr), 1)
                embed_stats_text = f'Your team had {ally_team_wr}% winrate\nEnemy team had {enemy_team_wr}% winrate'

            if len(all_wr) < 10:
                embed_stats_text = f"Please try a higher resolution image.\n*Not enough valid data to calculate team win rates.*"

            # Defining Embed
            embed_allies = ('\n'.join(allies))
            embed_enemies = ('\n'.join(enemies))
            embed_stats = embed_stats_text
            embed_footer = "This bot is made and maintained by @Vovko #0851. Let me know if something breaks :)" + f'\n{min_x}, {max_x}, {middle_line}, {len(all_predictions)}'

            # Constructing Embed
            embed=discord.Embed(title="Support Blitz Aftermath", url="https://www.paypal.me/vovko", description="If you would like to support me, click the link above.")
            embed.add_field(name="Allies", value=f'```{embed_allies}```', inline=False)
            embed.add_field(name="Enemies", value=f'```{embed_enemies}```', inline=False)
            embed.add_field(name="Stats", value=f'```{embed_stats}```', inline=False)
            embed.set_footer(text=embed_footer)

            # Send message
            await message.channel.send(embed=embed)
            return


def add_winrate(raw_list):
    win_rates = []
    # Gathering player stats from WG API
    for username in raw_list:
        username_index = raw_list.index(username)
        username_raw = username.strip()
        if '(' in username_raw or '[' in username_raw or '.' in username_raw:
            print(username_raw)
            if username_raw.startswith('(') or username_raw.startswith('['):
                raw_list.remove(username_raw)
                continue
            username_raw = re.split('\(|\[\.', username_raw)
            username_raw = username_raw[0]
        # Find closest matching player by name
        list_request_url = f'{wg_api_base_url}{wg_api_addon_list}{wg_application_id}&{wg_api_realm_na}&search={username_raw}'
        request = requests.get(list_request_url)
        raw_user_response = rapidjson.loads(request.text)

        # Check for bad request
        if raw_user_response.get('status') != 'ok':
            user_winrate = '0.0%'
            raw_list[username_index] = f'[{user_winrate}] {username}'
            continue

        # Get account ID from username
        if not raw_user_response.get('data'):
            user_winrate = '0.0%'
            raw_list[username_index] = f'[{user_winrate}] {username}'
            continue
        raw_user_data = raw_user_response.get('data')[0]
        username_fixed = raw_user_data.get('nickname')
        account_id = raw_user_data.get('account_id')
        info_request_url = f'{wg_api_base_url}{wg_api_addon_info}{wg_application_id}&{wg_api_realm_na}&account_id={account_id}'
        request = requests.get(info_request_url)

        # Check for bad request
        if raw_user_response.get('status') != 'ok':
            user_winrate = '0.0%'
            raw_list[username_index] = f'[{user_winrate}] {username_fixed}'
            continue
                
        user_stats_raw = rapidjson.loads(request.text)
        user_stats_all = user_stats_raw.get('data').get(str(account_id)).get('statistics').get('all')

        user_battles_won = user_stats_all.get('wins')
        user_battles_lost = user_stats_all.get('losses')
        user_battles_total = int(user_stats_all.get('battles')) + 1 # Adding one in case it's a 0

        user_winrate = int(user_battles_won) / int(user_battles_total) * 100
        if user_winrate > 30.0 and user_winrate < 80.0:
            win_rates.append(user_winrate)
        user_winrate = f'{str(round(user_winrate, 1))}%'

        raw_list[username_index] = f'[{user_winrate}] {username_fixed}'
    return raw_list, win_rates

def setup(client):
    client.add_cog(blitz_aftermath(client))
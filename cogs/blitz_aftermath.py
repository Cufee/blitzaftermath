from discord.ext import commands, tasks
import discord

import rapidjson
import requests

# Nononets setup
nano_url = 'https://app.nanonets.com/api/v2/OCR/Model/81ef3ac1-fa8f-49fc-9e02-bfc8218c7d8c/LabelUrls/'
nano_headers = {
    'accept': 'application/x-www-form-urlencoded'
}


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

        if message.channel.id != 719875141047418962 or message.channel.id != 719831153162321981:
            return

        nano_data = { 'urls': []}
        if attachments:
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


            # Defining Embed
            embed_allies = ('\n'.join(allies))
            embed_enemies = ('\n'.join(enemies))
            embed_stats = 'Coming soon ;)'
            embed_footer = "This bot is made and maintained by @Vovko #0851. Let me know if something breaks :)" + f'\n{min_x}, {max_x}, {middle_line}'

            # Constructing Embed
            embed=discord.Embed(title="Support Blitz Aftermath", url="https://www.paypal.me/vovko", description="If you would like to support me, click the link above.")
            embed.add_field(name="Allies", value=f'```{embed_allies}```', inline=False)
            embed.add_field(name="Enemies", value=f'```{embed_enemies}```', inline=False)
            embed.add_field(name="Stats", value=f'```{embed_stats}```', inline=False)
            embed.set_footer(text=embed_footer)

            # Send message
            await message.channel.send(embed=embed)
            return


def setup(client):
    client.add_cog(blitz_aftermath(client))

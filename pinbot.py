# This example requires the 'message_content' intent.

import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
import re
import requests 
import datetime

# Load environment variables
load_dotenv()
bot_token = os.environ.get("TOKEN")
command_prefix = os.environ.get("PREFIX")

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix=command_prefix, intents=intents)
servers = {}

class server:
    def __init__(self, server):
        self.server = server
        self.pin_cache = {} # id:list
        self.last_updated = None
        self.channels = server.text_channels
        self.watched_channels = []
        print(self.channels)

    async def build_cache(self):
        for channel in self.channels: # For each text channel get all its pins as a list
            if channel in self.watched_channels:
                await self.build_channel_cache(channel)
            
    async def build_channel_cache(self, channel):
        try:
            print(f"Channel {channel.name} added")
            self.last_updated = datetime.datetime.now()
            self.pin_cache[channel.id] = await channel.pins()
            
        except:
            pass

    def pin_count(self, channel_id):
        return len(self.pin_cache[channel_id])

    def get_pins(self, channel_id):
        return self.pin_cache[channel_id]

    def get_channel_id(self, channel_name):
        return discord.utils.get(self.channels, name=channel_name).id
    
    def pins_full(self, channel_id):
        return len(self.pin_cache[channel_id]) == 49

    def watch_channels(self, watched):
        self.watched_channels = watched

    def new_watched_channel(self, new_channel):
        self.watched_channels.append(new_channel)

        
def createembed(message, content, link, image_url=None):
    author_name = message.author.name  # Get the author name from the context
    textString = f'[{content}]({link})' if content else link  # If content exists, use it; otherwise, just use the link
    embed = discord.Embed(
        title=None,
        description=textString,
        timestamp=message.created_at,
        color=discord.Color.blue()
    ).set_author(name=author_name, icon_url=message.author.avatar.url)
    
    # If the message contains an image or a GIF, add it to the embed
    if image_url:
        embed.set_image(url=image_url)

    return embed

async def send_embed_message(message):
    channel = message.channel
    try:
        # Construct the message link (format: https://discord.com/channels/{guild_id}/{channel_id}/{message_id})
        message_link = f"https://discord.com/channels/{message.guild.id}/{channel.id}/{message.id}"

        image_url = None
        embed_content = message.content

        # Case 1: Check if the message has an attachment (image or GIF)
        if message.attachments:
            for attachment in message.attachments:
                if attachment.url:  # Use the attachment URL directly, no need to parse
                    image_url = attachment.url
                    break
        
        # Case 2: If the message contains embeds (like a GIF from Tenor), use the embed image
        elif message.embeds:
            for embed in message.embeds:
                if embed.image:  # This checks for an embedded image
                    image_url = embed.image.url
                    break

        # Case 3: Check if the message content contains a direct GIF link (like Tenor or other GIF services)
        if not image_url and message.content and ("tenor.com/view" in message.content or message.content.endswith('.gif')):
            # First, use the direct link if it exists (previous working logic)
            image_url = message.content.strip()

            # If it's a Tenor page link, attempt to extract the direct GIF link
            if "tenor.com/view" in message.content:
                tenor_direct_gif_url = get_tenor_direct_gif_url(message.content.strip())
                if tenor_direct_gif_url:
                    image_url = tenor_direct_gif_url

            embed_content = None
        
        # Create an embed using the message content, message link, and image URL (if any)
        embed = createembed(message, embed_content, message_link, image_url)
        
        # Send the embed to the current channel
        await channel.send(embed=embed)
        return
            
    except Exception as e:
        await channel.send(f"An error occurred: {e}")

def get_tenor_direct_gif_url(tenor_url):
    print(tenor_url)

        # Make a request to Tenor's page to retrieve the GIF metadata
    if re.findall(r'https?://tenor.com/view\S+', tenor_url):
      tenor_http = requests.get(tenor_url)
      direct_link_list = re.findall(r"https?://media1.tenor.com/m\S+.gif", tenor_http.text)
      direct_link = direct_link_list[0]
      return direct_link
    else:
      print("Not a tenor link")



@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    
    for guild in client.guilds: # Create a server class object for every server
        new_server = server(guild)
        servers[guild.id] = new_server
        print(guild.name + "added")
        
        await new_server.build_cache() # Build the pin cache for all text channels 


@client.command()
async def countpins(ctx, channel_name: str):
    server = servers[ctx.guild.id]
    channel_id = server.get_channel_id(channel_name)
    pins = server.pin_count(channel_id)
    print(server.get_pins(channel_id))

    await ctx.send(f"There are {pins} in the channel")


@client.command()
async def sendembed(ctx):
    # Find the channel by name
    channel = ctx.channel
    
    if not channel:
        await ctx.send(f"Channel '{channel.name}' not found.")
        return

    async for message in channel.history(limit=2): 
        if message.id != ctx.message.id:
            await send_embed_message(message)

    # Fetch the most recent message


        
@client.event
async def on_guild_channel_pins_update(channel, last_pin):
    # Update the cache for the specific channel when pins change
    guild_id = channel.guild.id

    if guild_id in servers:
        server = servers[guild_id]
        await server.build_channel_cache(channel) # Update the local cache of pinned message

        if last_pin.replace(tzinfo=None) > server.last_updated : # If a pin was added
            if not server.pins_full(channel.id): # Check if pin limit has been reached (capped at 49 to maintain usability of pins)
                await send_embed_message(server.pin_cache[channel.id][0])

            else:
                pass



        elif last_pin.replace(tzinfo=None) < server.last_updated: # If a pin was removed
            pass



       
    
          # Rebuild the pin cache for the channel when pins are updated





client.run(bot_token)

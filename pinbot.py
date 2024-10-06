# This example requires the 'message_content' intent.

import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
import re
import requests 
import datetime
from collections import deque

# Load environment variables
load_dotenv()
bot_token = os.environ.get("TOKEN")
command_prefix = os.environ.get("PREFIX")

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix=command_prefix, intents=intents)
servers = {}

class Pin:

    def __init__(self, message):
        self.message = message
        self.embed = None
        self.modified_by = None
        self.modified = False

    def add_embed(self, embed):
        self.embed = embed

    def get_embed(self):
        return self.embed
    
    def modify(self, user):
        self.modified = True
        self.modified_by = user


class server:
    def __init__(self, server):
        self.server = server
        self.pin_cache = {} # channel_id:list
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
            
            channel_pins = await channel.pins()
            self.pin_cache[channel.id] = deque([])

            for pin in channel_pins:
                self.pin_cache[channel.id].append(Pin(pin))
            
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

    def print_pins(self, pin_list):
        print("Pins:\n")
        for pin in pin_list:
            print(pin.message.content, end='\n')
    
    async def update_channel_cache(self, channel):
        print(f"Channel {channel.name} updated")
        self.last_updated = datetime.datetime.now()
        
        channel_pins = await channel.pins()
        pin_objects = []

        for pin in channel_pins:
                pin_objects.append(Pin(pin))

        if len(pin_objects) > len(self.pin_cache[channel.id]): # If a pin was added
            changed = get_changed_messages(pin_objects, self.pin_cache[channel.id])
            for item in reversed(changed):
                self.pin_cache[channel.id].appendleft(item)
            
            print("New Pin Added")
            self.print_pins(self.pin_cache[channel.id])
            return changed, False
        
        else: # If a pin was removed
            changed = get_changed_messages(self.pin_cache[channel.id], pin_objects) # Get list of pins that were removed

            for item in reversed(changed):
                self.pin_cache[channel.id].remove(item)

            print("Pin removed")
            self.print_pins(self.pin_cache[channel.id])
            return changed, True # return the pin(s) that were removed


def get_changed_messages(list1, list2):
# Create sets of message IDs from both lists
    list1_ids = {pin.message.id for pin in list1}
    list2_ids = {pin.message.id for pin in list2}
    

    # Find IDs that are in list1 but not in list2
    removed_ids = list1_ids - list2_ids

    # Return the Pin objects from list1 that were removed
    removed_pins = [pin for pin in list1 if pin.message.id in removed_ids]
    
    return removed_pins


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

async def send_embed_message(pin_obj):
    message = pin_obj.message
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
        embed_message = await channel.send(embed=embed)
        pin_obj.add_embed(embed_message)

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
        new_server.new_watched_channel(discord.utils.get(guild.channels, name="pins"))
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
        changed_pins, change = await server.update_channel_cache(channel)


        if not change: # If no pins were removed (a pin was added)
                for new_pin in changed_pins:
                    if not server.pins_full(channel.id):  # Check if the pin limit has been reached (capped at 49)
                        await send_embed_message(new_pin)  # Send the most recent pinned message
                        #print(server.get_pins(channel.id)[0].get_embed())
        else:
            for new_pin in changed_pins:
                try:
                    embed = new_pin.get_embed()                
                    if embed:
                        await embed.delete()

                except:
                    continue


client.run(bot_token)

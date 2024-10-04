# This example requires the 'message_content' intent.

import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
import re

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
        self.channels = server.text_channels
        print(self.channels)

    async def build_cache(self):
        for channel in self.channels: # For each text channel get all its pins as a list
            await self.build_channel_cache(channel)
            
    async def build_channel_cache(self, channel):
        try:
            print(f"Channel {channel.name} added")
            self.pin_cache[channel.id] = await channel.pins()
            
        except:
            pass

    def pin_count(self, channel_id):
        return len(self.pin_cache[channel_id])

    def get_pins(self, channel_id):
        return self.pin_cache[channel_id]

    def get_channel_id(self, channel_name):
        return discord.utils.get(self.channels, name=channel_name).id

def createembed(ctx, content, link, image_url=None):
    author_name = ctx.author.name  # Get the author name from the context
    textString = f'[{content}]({link})' if content else link  # If content exists, use it; otherwise, just use the link
    embed = discord.Embed(
        title=f"Message by {author_name}",
        description=textString,
        color=discord.Color.blue()
    )
    
    # If the message contains an image or a GIF, add it to the embed
    if image_url:
        embed.set_image(url=image_url)

    return embed

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

    # Fetch the most recent message
    try:
        async for last_message in channel.history(limit=10):  # Fetch the most recent 10 messages
            # Skip the command message itself (triggered by the bot or the user)
            if last_message.id != ctx.message.id:
                # Construct the message link (format: https://discord.com/channels/{guild_id}/{channel_id}/{message_id})
                message_link = f"https://discord.com/channels/{ctx.guild.id}/{channel.id}/{last_message.id}"

                image_url = None
                
                # Case 1: Check if the message has an attachment (image or GIF)
                if last_message.attachments:
                    for attachment in last_message.attachments:
                        if attachment.url:  # Use the attachment URL directly, no need to parse
                            image_url = attachment.url
                            break
                
                # Case 2: If the message contains embeds (like a GIF from Tenor), use the embed image
                elif last_message.embeds:
                    for embed in last_message.embeds:
                        if embed.image:  # This checks for an embedded image
                            image_url = embed.image.url
                            break

                # Case 3: Check if the message content contains a direct GIF link (like Tenor or other GIF services)
                if not image_url and last_message.content and ("tenor.com/view" in last_message.content or last_message.content.endswith('.gif')):
                    image_url = last_message.content.strip()

                # Create an embed using the message content, message link, and image URL (if any)
                embed = createembed(ctx, last_message.content or "[Media]", message_link, image_url)
                
                # Send the embed to the current channel
                await ctx.send(embed=embed)
                return
            
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

        
@client.event
async def on_guild_channel_pins_update(channel, last_pin):
    # Update the cache for the specific channel when pins change
    guild_id = channel.guild.id
    if guild_id in servers:
        server = servers[guild_id]
        await server.build_channel_cache(channel)  # Rebuild the pin cache for the channel when pins are updated





client.run(bot_token)

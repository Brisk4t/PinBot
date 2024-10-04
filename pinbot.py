# This example requires the 'message_content' intent.

import discord
import os
from dotenv import load_dotenv
from discord.ext import commands

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
        self.pin_cache = {} # String:list
        self.channels = server.text_channels
        print(self.channels)

    async def build_cache(self):
        for channel in self.channels: # For each text channel get all its pins as a list
            channel_name = channel.name
            print("Awaiting all pins")
            try:
                self.pin_cache[channel.name] = await channel.pins()
                print(f"Channel {channel_name} added")

            except:
                continue

    def pin_count(self, channel_name):
        return len(self.pin_cache[channel_name])




def createembed(ctx, content, link):
    author = None
    textString = '[' + content + '](' + link + ')'
    embed = discord.Embed(
        title = author,
        description=textString,
        color=discord.Color.blue()
    )


    return embed

@client.command()
async def countpins(ctx, channel_name: str):
    server = servers[ctx.guild.name]
    pins = server.pin_count(channel_name)
    await ctx.send(f"There are {pins} in the channel")

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    
    for guild in client.guilds:
        new_server = server(guild)
        servers[guild.name] = new_server
        print("server added")
        await new_server.build_cache()
        
@client.event
async def on_guild_channel_pins_udpate(channel, last_pin):
    pass




client.run(bot_token)

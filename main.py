import os

import discord
from discord.ext import commands

import re
from image_getter import get_images

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


@bot.event
async def on_ready():
    print(f"{bot.user} が起動しました！")


@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")


bot.run(TOKEN)

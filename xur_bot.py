import os
import random

import discord
from discord.ext import commands
from dotenv import load_dotenv
from better_profanity import profanity
import discord_response

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

client = commands.Bot(command_prefix="!")


@client.command()
async def inv(ctx):
    await client.wait_until_ready()
    message = discord_response.message()
    if discord_response.embedded:
        await ctx.send(embed=message)
    else:
        await ctx.send(message)


@client.event
async def on_ready():
    print(f'{client.user.name} has connected to Discord!')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    xur_quotes = [
        '*I am an Agent of the Nine.*',
        '*I am only an Agent. The Nine rule beyond the Jovians*',
        '*I am merely a trash collector for the Nine.*'
    ]

    xur_badword = [
        '**Guardian!**',
        '**You must stop eating salted popcorn**'
    ]

    xur_nine = [
        ('*I cannot explain what the Nine are. They are... very large.* '
         '*I cannot explain. The fault is mine, not yours.*'),
    ]

    if (
            (message.content.lower() == 'who is xur') |
            (message.content.lower() == 'what is xur')
    ):
        response = random.choice(xur_quotes)
        await message.channel.send(response)

    elif (
            (profanity.contains_profanity(message.content)) |
            (message.content.lower() == 'i\'m salty') |
            (message.content.lower() == 'im salty') |
            (message.content.lower() == 'i am salty')
    ):
        response = random.choice(xur_badword)
        await message.channel.send(response)

    elif (
            (message.content.lower() == 'who are the nine') |
            (message.content.lower() == 'what are the nine') |
            (message.content.lower() == 'who is the nine') |
            (message.content.lower() == 'what is the nine')
    ):
        response = random.choice(xur_nine)
        await message.channel.send(response)

    elif (
            message.content == 'raise-exception'
    ):
        raise discord.DiscordException

    await client.process_commands(message)


@client.event
async def on_error(event, *args, **kwargs):
    with open('err.log', 'a') as f:
        if event == 'on_message':
            f.write(f'Unhandled message: {args[0]}\n')
        else:
            raise


client.run(TOKEN)

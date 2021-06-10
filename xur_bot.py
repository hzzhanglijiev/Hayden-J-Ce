import os
import random
from datetime import datetime
import better_profanity
from discord.ext import commands
from dotenv import load_dotenv
from Vendor import Vendor
from VendorDictionary import VendorDictionary
from xur_quotes import who_is_xur, who_are_the_nine, bad_word, bad_word_at_xur
from helpers import Emoji

regular_profanity = better_profanity.Profanity()
hate_speech_check = better_profanity.Profanity()
hate_speech_check.load_censor_words_from_file('hate_speech.txt')

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
Xur = Vendor(name='Xur')
Vendor_Dictionary = VendorDictionary()
client = commands.Bot(command_prefix="!")


@client.command()
async def xur(ctx):
    # Sends an embedded message containing Xur's current inventory, or if he
    # is not currently present, returns a message telling the user when he'll arrive next
    await client.wait_until_ready()
    message = Xur.message()
    if Xur.embedded:
        await ctx.send(embed=message)
    else:
        await ctx.send(message)


@client.command()
async def bounties(ctx, name: str):  # Currently still being tested
    # Sends an embedded message containing the requested vendor's bounties. If they
    # are not currently present or the user requests a unidentifiable vendor, sends a informational message
    try:
        vendor = Vendor_Dictionary.search(name=name)
        await client.wait_until_ready()
        await ctx.send(embed=vendor.message())
    except (RuntimeError, AttributeError):
        await client.wait_until_ready()
        await ctx.send("That vendor does not exist in my files or doesn't sell bounties")


@client.event
async def on_ready():  # Confirmation in the terminal to let you know the bot has activated successfully
    print(f'{client.user.name} has connected to Discord!')


@client.event
async def on_message(message):
    # if the message is from xur_bot, ignore it
    if message.author == client.user:
        return
    # Check what kind of message it is
    if (
            ('who is xur' in message.content.lower()) |
            ('what is xur' in message.content.lower())
    ):
        response = random.choice(who_is_xur)
        await message.channel.send(response)
    elif hate_speech_check.contains_profanity(message.content):
        await message.channel.purge(limit=1)

    elif (
            (regular_profanity.contains_profanity(message.content)) |
            ('i\'m salty' in message.content.lower()) |
            ('im salty' in message.content.lower()) |
            ('i am salty' in message.content.lower())
    ):
        if 'xur' in message.content.lower():
            await message.add_reaction(emoji=Emoji.ULDREN_THUMBS_DOWN.value)
            response = random.choice(bad_word_at_xur)
        else:
            response = random.choice(bad_word)
        await message.channel.send(response)

    elif (
            ('who are the nine' in message.content.lower()) |
            ('what are the nine' in message.content.lower()) |
            ('who is the nine' in message.content.lower()) |
            ('what is the nine' in message.content.lower())
    ):
        response = random.choice(who_are_the_nine)
        await message.channel.send(response)

    await client.process_commands(message)


@client.event
async def on_error(event, *args, **kwargs):
    with open('err.log', 'a') as f:
        if event == 'on_message':
            message = args[0]
            f.write(
                f'\nERROR on {datetime.now().strftime("%m/%d/%Y at %H:%M:%S")}\nServer: {message.guild}\nChannel: {message.channel}\nUser: {message.author}\nUnhandled message: {message.content}\n')
        else:
            raise


client.run(TOKEN)

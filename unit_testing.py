import datetime
import discord
import random
from dateutil import rrule, relativedelta

def print_embed(embed: discord.Embed):
    print(embed.to_dict())

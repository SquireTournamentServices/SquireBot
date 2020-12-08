# bot.py
import os
import random

from discord.ext import commands
from dotenv import load_dotenv

from tournament.match import match
from tournament.deck import deck
from tournament.player import player
from tournament.tournament import tournament

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')

players = {}

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


@bot.command(name='register')
async def addPlayer( ctx ):
    players[ctx.message.author.name] = player( ctx.message.author.name, ctx.message.author.display_name )
    print( "New player added!\n\tName: " + players[ctx.message.author.name].playerName +"\n\tDisplay: " + players[ctx.message.author.name].displayName )


@bot.command(name='deck')
async def getDecklist( ctx, arg ):
    if not ctx.message.author.name in players:
        await ctx.send( ctx.message.author.mention +", you need to register before you can submit a decklist. Please you the register command to do so." )
    else:
        players[ctx.message.author.name].addDeck( arg )
        print( players[ctx.message.author.name].decks[-1].cards )
        print( players[ctx.message.author.name].decks[-1].deckHash )

bot.run(TOKEN)

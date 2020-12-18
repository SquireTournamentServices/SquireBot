# bot.py
import os
import shutil
import random

from discord.ext import commands
from dotenv import load_dotenv

from tournament.match import match
from tournament.deck import deck
from tournament.player import player
from tournament.tournament import tournament
from tournament.tournamentUtils import *


from baseBot import *
from adminCommands import *
from userCommands import *



savedTournaments = [ f'currentTournaments/{d}' for d in os.listdir( "currentTournaments" ) if os.path.isdir( f'currentTournaments/{d}' ) ]

for tourn in savedTournaments:
    newTourn = tournament( "", "" )
    newTourn.loadTournament( tourn )
    if newTourn.tournName != "":
        currentTournaments[newTourn.tournName] = newTourn

newLine = "\n\t- "
print( f'These are the saved tournaments:{newLine}{newLine.join(savedTournaments)}' )
print( f'These are the loaded current tournaments:{newLine}{newLine.join(currentTournaments)}' )


bot.run(TOKEN)

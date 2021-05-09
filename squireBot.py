# bot.py
import os
import shutil
import random

from discord.ext import commands
from dotenv import load_dotenv

from Tournament import *

from baseBot import *
from adminCommands import *
from playerCommands import *
from judgeCommands import *




newLine = "\n\t- "
print( f'These are the saved tournaments:{newLine}{newLine.join(savedTournaments)}' )
print( f'These are the loaded current tournaments:{newLine}{newLine.join(tournaments)}' )


bot.run(TOKEN)

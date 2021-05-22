# bot.py
import os
import shutil
import random
import re

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

TOKEN = os.getenv( "TESTING_TOKEN" )

reCommand = re.compile( "^!" )


@bot.event
async def on_message( msg ):
    if msg.author == bot.user:
        return
    content = re.sub( "\s+", " ", msg.content.strip() ).split( " " )
    if not reCommand.search( content[0] ):
        return
    # The command name is the string between the starting "!" and the first space
    command = content[0][1:]
    # The args are everything after the command name
    args = content[1:]
    ctx = await bot.get_context( msg )
    if command in bot.all_commands:
        await bot.all_commands[command]( ctx, *args )


bot.run(TOKEN)

import os

import discord
import random
import re
from random import getrandbits
from discord import Activity, ActivityType
from discord.ext import commands
from dotenv import load_dotenv


load_dotenv()
TOKEN = os.getenv('TESTER_TOKEN')
SquireBotID = int(os.getenv('SquireBotID'))
PrototypeBotID = int(os.getenv('PrototypeBotID'))
botIDs = [ SquireBotID, PrototypeBotID ]

testFiles = [ f'testCases/{f}' for f in os.listdir( "testCases" ) if os.path.isfile( f'testCases/{f}' ) ]
tests = [ ]
for testFile in testFiles:
    with open( testFile ) as testData:
        tests.append( [ f'!{cmd.strip()}' for cmd in testData.read().strip().split("!")[1:] ] )

position = [ 0, 0 ]
status = [False, False]

async def sendCommand( msg ) -> None:
    if status[1] or not status[0]:
        return None
    await msg.channel.send( content=tests[position[1]][position[0]] )
    position[0] += 1
    if position[0] == len(tests[position[1]]):
        await msg.channel.send( "Moving on to the next test" )
        position[0] = 0
        position[1] += 1
        if position[1] == len(tests):
            await msg.channel.send( "Last test command sent" )
            status[1] = True

bot = commands.Bot(command_prefix='!')


@bot.event
async def on_ready( ):
    print( f'Ready to run {len(tests)} test{"" if len(tests) == 1 else "s"}' )

@bot.event
async def on_message( msg ):
    if msg.author == bot.user:
        return
    if msg.content.strip() == "!run-tests":
        print( "Starting tests..." )
        status[0] = True
        await sendCommand( msg )
    elif msg.author.id in botIDs:
        await sendCommand( msg )


bot.run(TOKEN)


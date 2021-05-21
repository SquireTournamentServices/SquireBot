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

testFiles = [ f'tests/{f}' for f in os.listdir( "tests" ) if os.path.isfile( f'tests/{f}' ) ]
tests = [ ]
for testFile in testFiles:
    with open( testFile ) as testData:
        tests.append( testData.strip().split("\n") )

currentTest    = 0
currentCommand = 0

finished = False

async def sendCommand( ctx ) -> None:
    if finished:
        return None
    ctx.send( content=tests[currentTest][currentCommand] )
    currentCommand += 1
    if currentCommand == len(tests[currentTest]):
        currentCommand = 0
        currentTest += 1
        if currentTest == len(tests):
            finished = True
    

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_message():
    if message.author.id in botIDs:
        sendCommand( ctx )
        

bot.remove_command( "run-tests" )
@bot.command(name='run-tests')
async def printHelp( ctx ):
    sendCommand( ctx )
    return


bot.run(TOKEN)


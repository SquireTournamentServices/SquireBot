import os

import discord
import random
import re


from random import getrandbits
from typing import List

from discord import Activity, ActivityType
from discord.ext import commands
from dotenv import load_dotenv


# A very simple class to handle data management for unit test cases
class commandTest:
    def __init__( self, name: str,  cmds: List[str] ):
        self.name: str = name
        self.commands: list = cmds
        self.index: int = 0

        self.started: bool = False
        self.finished: bool = False
    
    # Returns the next command for a test then changes the started/finished
    # propties of the test so it can be externally monitored
    def getNextCommand( self ) -> str:
        if self.finished:
            return None
        if not self.started:
            self.started = True
        self.index += 1
        if self.index == len(self.commands):
            self.finished = True
        return self.commands[self.index - 1]
    
    # Allows the test to be start over
    def reset( self ) -> None:
        self.index = 0
        self.started = False
        self.finished = False


load_dotenv()
TOKEN = os.getenv('TESTER_TOKEN')

SquireBotID = int(os.getenv('SquireBotID'))
PrototypeBotID = int(os.getenv('PrototypeBotID'))
botIDs = [ SquireBotID, PrototypeBotID ]

bot = commands.Bot( command_prefix="!" )
reCommand = re.compile( "^!" )

testFiles = [ f'testCases/{f}' for f in os.listdir( "testCases" ) if os.path.isfile( f'testCases/{f}' ) ]
tests: dict = { }
queue: list = [ ]
for testFile in testFiles:
    with open( testFile ) as testData:
        name = re.sub( ".txt", "", testFile.split("/")[-1] )
        cmds = [ f'!{cmd.strip()}' for cmd in testData.read().strip().split("!")[1:] ]
        tests[name] = commandTest( name, cmds ) 


async def sendCommand( msg ) -> None:
    if queue[0].finished:
        return
    if not queue[0].started:
        await msg.channel.send( content = f'Starting test "{queue[0].name}".' )
    await msg.channel.send( content=queue[0].getNextCommand() )
    if queue[0].finished:
        await msg.channel.send( content = f'Test "{queue[0].name}" is finished.' )
        del( queue[0] )
    if len(queue) == 0:
        await msg.channel.send( content = f'All queued tests are finished.' )


@bot.event
async def on_ready( ):
    print( f'Ready to run {len(tests)} test{"" if len(tests) == 1 else "s"}' )


@bot.event
async def on_message( msg ):
    if msg.author == bot.user:
        return
    content = re.sub( "\s+", " ", msg.content.strip() ).split( " " )
    # If the message is from the SquireBot or the Testing bot, send the next command
    if msg.author.id in botIDs:
        if len(queue) > 0:
            await sendCommand( msg )
        return
    # If the message isn't from either bot and isn't a command, do nothing
    if not reCommand.search( content[0] ):
        return
    command = content[0][1:]
    args = content[1:]
    # If the command is a defined command, run that command
    # Otherwise, do nothing
    if command in bot.all_commands:
        await bot.all_commands[command]( msg, *args )


@bot.command( name = "run-tests" )
async def runTests( msg, *args ):
    print( "Starting test(s)" )
    if len(args) == 0:
        args = list(tests.keys())
    for test in args:
        if test in tests:
            tests[test].reset( )
            queue.append( tests[test] )
    await sendCommand( msg )



bot.run(TOKEN)


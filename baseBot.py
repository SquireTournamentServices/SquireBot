import os
import traceback

import discord
import random
import re
from random import getrandbits
from discord import Activity, ActivityType
from discord.ext import commands
from dotenv import load_dotenv

from Tournament import *


# ---------------- Help Message Methods ---------------- 

LINK_TO_PLAYER_CMD_DOC   = "https://gitlab.com/monarch3/SquireBot/-/tree/development/docs/UserCommands.md"
LINK_TO_JUDGE_CMD_DOC    = "https://gitlab.com/monarch3/SquireBot/-/tree/development/docs/JudgeCommands.md" 
LINK_TO_ADMIN_CMD_DOC    = "https://gitlab.com/monarch3/SquireBot/-/tree/development/docs/AdminCommands.md" 
LINK_TO_CRASH_COURSE_DOC = "https://gitlab.com/monarch3/SquireBot/-/tree/development/docs/CrashCourse.md" 

commandSnippets = { } 
commandCategories = { "registration": [ ], "playing": [ ], "misc": [ ],
                      "admin-registration": [ ], "admin-playing": [ ], "admin-misc": [ ],
                      "management": [ ], "properties": [ ], "day-of": [ ] }

async def sendAdminHelpMessage( ctx ) -> None:
    embed = discord.Embed( )
    
    embed.add_field( name="\u200b", value="**__User Commands__**", inline = False )

    embed.add_field( name="**Registration**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["registration"] ]), inline=False )
    embed.add_field( name="**Match**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["playing"] ]), inline=False )
    embed.add_field( name="**Miscellaneous**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["misc"] ]),inline=False )
    
    embed.add_field( name="\u200b", value="**__Judge Commands__**", inline = False )

    embed.add_field( name="**Registration**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["admin-registration"] ]), inline=False )
    embed.add_field( name="**Match**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["admin-playing"] ]), inline=False )
    embed.add_field( name="**Miscellaneous**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["admin-misc"] ]),inline=False )
    
    embed.add_field( name="\u200b", value="**__Admin Commands__**", inline = False )

    embed.add_field( name="**Manage Tournament**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["management"] ]), inline=False )
    embed.add_field( name="**Properties**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["properties"] ]), inline=False )
    embed.add_field( name="**Day-Of**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["day-of"] ]),inline=False )
    
    embed.add_field( name="**__Additional Information__**", value=f'The full documentation for the judge commands can be found [here]({LINK_TO_JUDGE_CMD_DOC}) and admin commands [here]({LINK_TO_ADMIN_CMD_DOC}). The user commands are [here]({LINK_TO_PLAYER_CMD_DOC}), and the crash course is [here]({LINK_TO_PLAYER_CMD_DOC}). If you have ideas about how to improve this bot, [let us know](https://forms.gle/jt9Hpaz3ZcVNfeiRA)!',inline=False )
    
    await ctx.send( embed=embed )
    return

async def sendJudgeHelpMessage( ctx ) -> None:
    embed = discord.Embed( )
    
    embed.add_field( name="\u200b", value="**__User Commands__**", inline = False )

    embed.add_field( name="**Registration**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["registration"] ]), inline=False )
    embed.add_field( name="**Match**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["playing"] ]), inline=False )
    embed.add_field( name="**Miscellaneous**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["misc"] ]),inline=False )
    
    embed.add_field( name="\u200b", value="**__Judge Commands__**", inline = False )

    embed.add_field( name="**Registration**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["admin-registration"] ]), inline=False )
    embed.add_field( name="**Match**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["admin-playing"] ]), inline=False )
    embed.add_field( name="**Miscellaneous**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["admin-misc"] ]),inline=False )
    
    embed.add_field( name="**__Additional Information__**", value=f'The full documentation for the judge commands can be found [here]({LINK_TO_JUDGE_CMD_DOC}). The user commands are [here]({LINK_TO_PLAYER_CMD_DOC}), and the crash course is [here]({LINK_TO_CRASH_COURSE_DOC}). If you have ideas about how to improve this bot, [let us know](https://forms.gle/jt9Hpaz3ZcVNfeiRA)!',inline=False )
    
    await ctx.send( embed=embed )
    return

async def sendUserHelpMessage( ctx ) -> None:
    embed = discord.Embed( )
    
    embed.add_field( name="**__Registration Commands__**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["registration"] ]), inline=False )
    embed.add_field( name="**__Match Commands__**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["playing"] ]), inline=False )
    embed.add_field( name="**__Miscellaneous Commands__**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["misc"] ]),inline=False )

    embed.add_field( name="**__Additional Information__**", value=f'Additional information about each command can be found [here]({LINK_TO_PLAYER_CMD_DOC}). There is also a [crash course]({LINK_TO_CRASH_COURSE_DOC}) for new users. If you have ideas about how to improve this bot, [let us know](https://forms.gle/jt9Hpaz3ZcVNfeiRA)!',inline=False )
    
    await ctx.send( embed=embed )
    return

# ---------------- Command Util Methods ---------------- 

# Looks through all guilds, finds the guilds where the user is a member, and
# gets the tournaments they are registered for
def getTournamentsByPlayer( user: discord.Member ) -> List:
    digest: list = [ ]
    for gld in guildSettingsObjects:
        if not guildSettingsObjects[gld].isMember( user ):
            continue
        digest += guildSettingsObjects[gld].getPlayerTournaments( user )
    return digest

async def isPrivateMessage( ctx, send: bool = True ) -> bool:
    digest = (str(ctx.message.channel.type) == 'private')
    if digest and send:
        await ctx.send( f'You are not allowed to send most commands via DM. To see what commands you can send via DM, use the !squirebot-help command.' )
    return digest

async def isAdmin( ctx, send: bool = True ) -> bool:
    digest = False
    judgeMention = getJudgeMention( ctx.guild )
    adminMention = getTournamentAdminMention( ctx.guild )
    for role in ctx.author.roles:
        digest |= str(role).lower() == "tournament admin"
        digest |= str(role).lower() == "judge"
    if not digest and send:
        await ctx.send( f'{ctx.author.mention}, invalid permissions: You are not tournament staff. Please do not use this command again or {adminMention} or {judgeMention} may intervene.' )
    return digest

async def isTournamentAdmin( ctx, send: bool = True ) -> bool:
    digest = False
    
    adminMention = getTournamentAdminMention( ctx.message.guild )
    for role in ctx.author.roles:
        digest |= str(role).lower() == "tournament admin"
    if not digest and send:
        await ctx.send( f'{ctx.author.mention}, invalid permissions: You are not tournament staff. Please do not use this command again or {adminMention} may intervene.' )
    return digest

async def isTournDead( tourn, ctx, send: bool = True ) -> bool:
    digest = tourn.isDead( )
    if digest and send:
        await ctx.send( f'{ctx.author.mention}, {tourn} has ended or been cancelled. Contact {tourn.tournAdminRole} if you think this is an error.' )
    return digest

async def isTournRunning( tourn, ctx, send: bool = True ) -> bool:
    digest = tourn.isActive() and not await isTournDead( tourn, ctx, False )
    if not digest and send:
        await ctx.send( f'{ctx.author.mention}, {tourn.name} has not started yet.' )
    return digest

async def isRegOpen( tourn, ctx, send: bool = True ) -> bool:
    digest = tourn.regOpen
    if send and not digest:
        await ctx.send( f'{ctx.author.mention}, registration for {tourn} is closed. Please contact tournament staff if you think this is an error.' )
    return digest

async def hasRegistered( tourn, plyr, ctx, send: bool = True ) -> bool:
    digest = plyr in tourn.players
    if send and not digest:
        await ctx.send( f'{ctx.author.mention}, you are not registered for {tourn.name}. Please register before trying to access the tournament.' )
    return digest
        
async def isActivePlayer( tourn, plyr, ctx, send: bool = True ) -> bool:
    digest = tourn.players[plyr].isActive( )
    if send and not digest:
        await ctx.send( f'{ctx.author.mention}, you registered for {tourn.name} but have been dropped. Contact tournament staff if you think this is an error.' )
    return digest
    
async def hasOpenMatch( tourn, plyr, ctx, send: bool = True ) -> bool:
    digest = tourn.players[plyr].hasOpenMatch( )
    if send and not digest:
        await ctx.send( f'{ctx.author.mention}, you are not an active player in a match. You do not need to do anything.' )
    return digest

async def hasCommandWaiting( ctx, user: int, send: bool = True ) -> bool:
    digest = user in commandsToConfirm
    if send and digest:
        await ctx.send( f'{ctx.author.mention}, you have a command waiting for your confirmation. That confirmation request is being overwriten by this one.' )
    return digest

async def createMisfortune( ctx ) -> None:
    playerMatch = None
    tourns = guildSettingsObjects[ctx.guild.id].getPlayerTournaments( ctx.author )
    for tourn in tourns.values():
        if tourn.players[ctx.author.id].hasOpenMatch():
            playerMatch = tourn.players[ctx.author.id].findOpenMatch()
            break
    if playerMatch is None:
        await ctx.send( f'{ctx.author.mention}, you are not in an open match, so you can not create any misfortune.' )
        return
    
    await ctx.send( f'{ctx.author.mention}, you have created misfortune for {playerMatch.getMention()}. How will you all respond? (send via DM)' )
    for plyr in playerMatch.activePlayers:
        await tourn.players[plyr].discordUser.send( content=f'Misfortune has been created in your match. Tell me how you will respond (with "!misfortune [number]")!' )
    
    listOfMisfortunes.append( (ctx, playerMatch) )

async def recordMisfortune( ctx, misfortune, num: int ) -> bool:
    misfortune[1].misfortunes[ctx.author.id] = num
    await ctx.send( f'{ctx.author.mention}, your response to this misfortune has been recorded!' )
    if len( misfortune[1].misfortunes ) == len( misfortune[1].activePlayers ):
        tourns = currentGuildTournaments( misfortune[0].message.guild.name )
        for tourn in tourns.values():
            if not ctx.author.id in tourn.players:
                continue
            if tourn.players[ctx.author.id].hasOpenMatch():
                break
        newLine = "\n\t"
        printout = newLine.join( [ f'{tourn.players[plyr].discordUser.mention}: {misfortune[1].misfortunes[plyr]}' for plyr in misfortune[1].misfortunes ] )
        await misfortune[0].send( f'{misfortune[1].role.mention}, the results of your misfortune are in!{newLine}{printout}' )
        misfortune[1].misfortunes = { }
        return True
    return False
     

def getJudgeMention( a_guild ) -> str:
    digest = ""
    for role in a_guild.roles:
        if str(role).lower() == "judge":
            digest = role.mention
            break
    return digest

def getTournamentAdminMention( a_guild ) -> str:
    adminMention = ""
    for role in a_guild.roles:
        if str(role).lower() == "tournament admin":
            adminMention = role.mention
            break
    return adminMention

def splitMessage( msg: str, limit: int = 2000, delim: str = "\n" ) -> List[str]:
    if len(msg) <= limit:
        return [ msg ]
    msg = msg.split( delim )
    digest = [ "" ]
    for submsg in msg:
        if len(digest[-1]) + len(submsg) <= limit:
            digest[-1] += delim + submsg
        else:
            digest.append( submsg )
    return digest
    

# ---------------- The Bot Base ---------------- 

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
MAX_COIN_FLIPS = int( os.getenv('MAX_COIN_FLIPS') )

DEV_SERVER_ID: int = None
if not os.getenv('DEV_SERVER_ID') is None:
    DEV_SERVER_ID = int( os.getenv('DEV_SERVER_ID') )  

ERROR_LOG_CHANNEL_ID: int = None
if not os.getenv('ERROR_LOG_CHANNEL_ID') is None:
    ERROR_LOG_CHANNEL_ID = int( os.getenv('ERROR_LOG_CHANNEL_ID') )

random.seed( )

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

guildSettingsObjects = { }

# A dictionary indexed by user idents and consisting of creation time, duration, and a coro to be awaited
commandsToConfirm = { }

# A list of matches that we currently resolving Wheel of Misfortune
listOfMisfortunes = [ ]

savedGuildSettings = [ f'guilds/{d}' for d in os.listdir( "guilds" ) if os.path.isdir( f'guilds/{d}' ) ]


# When ready, the bot needs to looks at each pre-loaded tournament and add a discord user to each player.
@bot.event
async def on_ready():
    await bot.wait_until_ready( )
    print(f'{bot.user.name} has connected to Discord!\n')
    for guild in bot.guilds:
        print( f'This bot is connected to {guild.name} which has {len(guild.members)}!' ) 
        try:
            guildSettingsObjects[guild.id] = guildSettings( guild )
            if os.path.isdir( f'guilds/{guild.id}' ):
                await guildSettingsObjects[guild.id].load( f'guilds/{guild.id}/' )
            else:
                guildSettingsObjects[guild.id].save( f'guilds/{guild.id}/' )
            guildSettingsObjects[guild.id].setEventLoop( bot.loop )
            for tourn in guildSettingsObjects[guild.id].tournaments:
                await tourn.updateInfoMessage()
        except Exception as ex:
            print(f'Error loading settings for {guild.name}')
            print(ex)
            traceback.print_exception(type(ex), ex, ex.__traceback__)
    print( "" )

# When the bot is added to a new guild, a settings object needs to be added for that guild
@bot.event
async def on_guild_join( guild ):
    if not (guild.id in guildSettingsObjects):
        guildSettingsObjects[guild.id] = guildSettings( guild )
        guildSettingsObjects[guild.id].save( f'guilds/{guild.id}/' )


# When an uncaught error occurs, the tracebot of the error needs to be printed
# to stderr, logged, and sent to the development server's error log channel
@bot.event
async def on_command_error( ctx: discord.ext.commands.Context, error: Exception ):
    error = getattr(error, 'original', error)
    traceback.print_exception( type(error), error, error.__traceback__ )
    
    mention = ctx.message.author.mention
    if isinstance( error, discord.ext.commands.CommandNotFound ):
        return
    elif isinstance(error, DeckRetrievalError ):
        await ctx.send( f'{mention}, your decklist can not be retrieved. Check that your URL is correct.' )
        return
    elif isinstance(error, CodFileError ):
        await ctx.send( f'{mention}, there is an error in your .cod file. Check that the file was not changed after you saved it.' )
        return
    elif isinstance(error, DecklistError ):
        await ctx.send( f'{mention}, there is an error in your decklist. Check that you entered it correctly.' )
        return
    else:
        await ctx.send( f'{mention}, there was an error while processing your command.' )

    message: str = f'{getTime()}: An error has occured on the server {ctx.guild.name}. Below is the context of the error and traceback.\n\n'
    message     += f'{ctx.message.content}\n'
    
    with open( "squireBotError.log", "a" ) as errorFile:
        errorFile.write( message + "".join(traceback.format_exception( type(error), error, error.__traceback__ )) )
    
    devServer = bot.get_guild( DEV_SERVER_ID )
    if devServer is None:
        return
    errorChannel = devServer.get_channel( ERROR_LOG_CHANNEL_ID )
    if isinstance( errorChannel, discord.TextChannel ):
        await errorChannel.send( message + f'```{"".join(traceback.format_exception( type(error), error, error.__traceback__ ))}```' )
    
    return
    

bot.remove_command( "help" )
@bot.command(name='help')
async def printHelp( ctx ):
    await ctx.send( f'{ctx.author.mention}, use the command "!squirebot-help" to see the list of my commands.' )


@bot.command(name='squirebot-help')
async def printHelp( ctx ):
    if await isPrivateMessage( ctx, send=False ):
        await sendUserHelpMessage( ctx )
        return
    if await isTournamentAdmin( ctx, send=False ):
        await sendAdminHelpMessage( ctx )
    elif await isAdmin( ctx, send=False ):
        await sendJudgeHelpMessage( ctx )
    else:
        await sendUserHelpMessage( ctx )


@bot.command(name='yes')
async def confirmCommand( ctx ):
    if not ctx.author.id in commandsToConfirm:
        await ctx.send( f'{ctx.author.mention}, there are no commands needing your confirmation.' )
        return
    
    if commandsToConfirm[ctx.author.id][1] <= timeDiff( commandsToConfirm[ctx.author.id][0], getTime() ):
        await ctx.send( f'{ctx.author.mention}, you waited too long to confirm. If you still wish to confirm, run your prior command and then confirm.' )
        del( commandsToConfirm[ctx.author.id] )
        return
    
    message = await commandsToConfirm[ctx.author.id][2]
    del( commandsToConfirm[ctx.author.id] )
    
    if type(message) is discord.Embed:
        await ctx.send( embed=message )
        return

    await ctx.send( message )


@bot.command(name='no')
async def denyCommand( ctx ):
    print( commandsToConfirm )
    if not ctx.author.id in commandsToConfirm:
        await ctx.send( f'{ctx.author.mention}, there are no commands needing your confirmation.' )
        return
    
    await ctx.send( f'{ctx.author.mention}, your request has been cancelled.' )

    del( commandsToConfirm[ctx.author.id] )



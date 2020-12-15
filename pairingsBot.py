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


def isPrivateMessage( a_message ) -> bool:
    return str(a_message.channel.type) == 'private'
    
def isTournamentAdmin( a_author ) -> bool:
    retValue = False
    for role in a_author.roles:
        retValue |= str(role).lower() == "tournament admin"
    return retValue

def getTournamentAdminMention( a_guild ) -> str:
    adminMention = "tournament admin"
    for role in a_guild.roles:
        if str(role).lower() == "tournament admin":
            adminMention = role.mention
    return adminMention

def futureGuildTournaments( a_guildName ):
    tourns = {}
    for tourn in futureTournaments:
        if futureTournaments[tourn].hostGuildName == a_guildName:
            tourns[tourn] = futureTournaments[tourn]
    return tourns

def isOpenGuildTournament( a_guildName ) -> bool:
    for tourn in openTournaments:
        if openTournaments[tourn].hostGuildName == a_guildName:
            return True
    return False

def isCorrectGuild( a_tournName, a_guildName ) -> bool:
    if a_tournName in futureTournaments:
        return a_guildName == futureTournaments[a_tournName].hostGuildName
    if a_tournName in openTournaments:
        return a_guildName == openTournaments[a_tournName].hostGuildName
    return False
        
    


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')

futureTournaments = {}
openTournaments = {}
closedTournaments = []


savedTournaments = [ f'openTournaments/{d}' for d in os.listdir( "openTournaments" ) if os.path.isdir( f'openTournaments/{d}' ) ]

for tourn in savedTournaments:
    newTourn = tournament( "", "" )
    newTourn.loadTournament( tourn )
    if newTourn.tournName != "":
        if newTourn.tournStarted:
            openTournaments[newTourn.tournName] = newTourn
        else:
            futureTournaments[newTourn.tournName] = newTourn

newLine = "\n\t- "
print( f'These are the saved tournaments:{newLine}{newLine.join(savedTournaments)}' )
print( f'These are the loaded future tournaments:{newLine}{newLine.join(futureTournaments)}' )
print( f'These are the loaded open tournaments:{newLine}{newLine.join(openTournaments)}' )


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


@bot.command(name='create-tournament')
async def createTournament( ctx, arg = "" ):
    arg = arg.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't create a tournament via private message since each tournament needs to be associated with a guild (server)." )
        return
    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not isTournamentAdmin( ctx.message.author ):
        await ctx.send( ctx.message.author.mention + ", you don't have permissions to create a tournament in this server. Please don't do this again or " + adminMention + " may intervene." )
        return

    if arg == "":
        await ctx.send( ctx.message.author.mention + ', you need to specify what you want the tournament to be called.' )
        return

    if (arg in futureTournaments) or (arg in openTournaments):
        await ctx.send( ctx.message.author.mention + ', it would appear that there is already a tournement named "' + arg + '" either on this server or another. Please pick a different name.' )
    
    futureTournaments[arg] = tournament( arg, ctx.message.guild.name )
    futureTournaments[arg].saveTournament( f'openTournaments/{arg}' )
    await ctx.send( adminMention + ', a new tournament called "' + arg.strip() + '" has been created by ' + ctx.message.author.mention )


@bot.command(name='list-tournaments')
async def listTournament( ctx ):
    if isPrivateMessage( ctx.message ):
        await ctx.send( "A list of tournaments can't be created via private message since each tournament is associated with a guild (server)." )
        return
    if len(futureGuildTournaments( ctx.message.guild.name ) ) == 0:
        await ctx.send( ctx.message.author.mention + ", there are no tournaments currently planned for this guild (server)." )
        return
    await ctx.send( ctx.message.author.mention + ", the following tournaments for this guild (server) are planned but have not been started:\n\t- " + "\n\t- ".join( [name for name in futureGuildTournaments( ctx.message.guild.name)] ) )
    

@bot.command(name='update-reg')
async def startTournament( ctx, arg1 = "", arg2 = "" ):
    tourn  = arg1.strip()
    status = arg2.strip()
    
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't adjust tournament settings via private message since each tournament needs to be associated with a guild (server)." )
        return
    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not isTournamentAdmin( ctx.message.author ):
        await ctx.send( ctx.message.author.mention + ", you don't have permissions to change tournament settings in this server. Please don't do this again or " + adminMention + " may intervene." )
        return
    
    if arg1 == "" or arg2 == "":
        await ctx.send( ctx.message.author.mention + ', it appears that you didn\'t give enough information. To update registeration, you need to first state the tournament name and then "true" or "false".' )
        return
    
    if not isCorrectGuild( tourn, ctx.message.guild.name ):
        await ctx.send( ctx.message.author.mention + ', there is no tournament called "' + tourn + '" for this guild (server).' )
        return
        
    if arg1 in futureTournaments:
        futureTournaments[arg1].setRegStatus( str_to_bool(status) )
        futureTournaments[arg1].saveOverview( f'openTournaments/{tourn}/overview.xml' )
    if arg1 in openTournaments:
        openTournaments[arg1].setRegStatus( str_to_bool(status) )
        openTournaments[arg1].saveOverview( f'openTournaments/{tourn}/overview.xml' )
    await ctx.send( adminMention + ', registeration for the "' + arg1 + '" tournament has been ' + ("opened" if str_to_bool(status) else "closed") + " by " + ctx.message.author.mention ) 


@bot.command(name='start-tournament')
async def startTournament( ctx, arg = "" ):
    arg = arg.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't start a tournament via private message since each tournament needs to be associated with a guild (server)." )
        return
    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not isTournamentAdmin( ctx.message.author ):
        await ctx.send( ctx.message.author.mention + ", you don't have permissions to start a tournament in this server. Please don't do this again or " + adminMention + " may intervene." )
        return

    if arg == "":
        await ctx.send( ctx.message.author.mention + ', you need to specify what tournament you want to start.' )
        return

    if isOpenGuildTournament( ctx.message.guild.name ):
        await ctx.send( ctx.message.author.mention + ", there seems to be an active tournament in this guild. Check with the rest of " + adminMention + " if you think this is an error." )
        return

    if arg in futureTournaments:
        if isCorrectGuild(arg, futureTournaments[arg]):
            openTournaments[arg] = futureTournaments[arg]
            del( futureTournaments[arg] )
            openTournaments[arg].startTourn()
            openTournaments[arg].saveOverview( f'openTournaments/{arg}/overview.xml' )
            await ctx.send( adminMention + ', the "' + arg + '" has been started by ' + ctx.message.author.mention )
            return
    await ctx.send( ctx.message.author.mention + ', there is no tournament called "' + arg + '" for this guild (server).' )
    

@bot.command(name='end-tournament')
async def endTournament( ctx, arg = "" ):
    arg = arg.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't end a tournament via private message since each tournament needs to be associated with a guild (server)." )
        return
    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not isTournamentAdmin( ctx.message.author ):
        await ctx.send( ctx.message.author.mention + ", you don't have permissions to start a tournament in this server. Please don't do this again or " + adminMention + " may intervene." )
        return

    if arg == "":
        await ctx.send( ctx.message.author.mention + ', you need to specify what tournament you want to end.' )
        return

    if isOpenGuildTournament( ctx.message.guild.name ):
        openTournaments[arg].endTourn( )
        openTournaments[arg].saveTournament( f'closedTournaments/{arg}' )
        if os.path.isdir( f'openTournaments/{arg}' ): 
            shutil.rmtree( f'openTournaments/{arg}' )
        del( openTournaments[arg] )
        await ctx.send( adminMention + ', the "' + arg +'" tournament has been closed by ' + ctx.message.author.mention + "." )
        return
    
    if arg in futureTournaments:
        await ctx.send( ctx.message.author.mention + ', the no tournament called "' + arg + '" has not been started yet, so it can\'t end yet. If you want to cancel the tournament, use the cancel-tournament command.' )
        return

    await ctx.send( ctx.message.author.mention + ', there is no tournament called "' + arg + '" for this guild (server).' )
    

@bot.command(name='cancel-tournament')
async def endTournament( ctx, arg = "" ):
    arg = arg.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't end a tournament via private message since each tournament needs to be associated with a guild (server)." )
        return
    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not isTournamentAdmin( ctx.message.author ):
        await ctx.send( ctx.message.author.mention + ", you don't have permissions to start a tournament in this server. Please don't do this again or " + adminMention + " may intervene." )
        return

    if arg == "":
        await ctx.send( ctx.message.author.mention + ', you need to specify what tournament you want to cancel.' )
        return

    tourn = ""
    if arg in futureTournaments:
        tourn = futureTournaments[arg]
    if arg in openTournaments:
        tourn = openTournaments[arg]

    tourn.cancelTourn( )
    tourn.saveTournament( f'closedTournaments/{arg}' )
    if os.path.isdir( f'openTournaments/{arg}' ): 
        shutil.rmtree( f'openTournaments/{arg}' )
    if arg in futureTournaments:
        del( futureTournaments[arg] )
    if arg in openTournaments:
        del( openTournaments[arg] )
    await ctx.send( adminMention + ', the "' + arg +'" tournament has been cancelled by ' + ctx.message.author.mention + "." )
    


@bot.command(name='register')
async def addPlayer( ctx, arg = "" ):
    arg = arg.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't join a tournament via private message since each tournament needs to be associated with a guild (server)." )
        return

    if arg == "":
        await ctx.send( ctx.message.author.mention + ', you need to specify what tournament you want to register for. If you\'re unsure, use the list-tournaments command or talk to a tournament admin.' )
        return

    tourn = ""
    if arg in futureTournaments:
        tourn = futureTournaments[arg]
    if arg in openTournaments:
        tourn = openTournaments[arg]
    
    if tourn == "":
        await ctx.send( ctx.message.author.mention + ', there is not a tournament named "' + arg + '" in this guild (server).' )
        return
    
    if not isCorrectGuild( tourn.tournName, ctx.message.guild.name ):
        await ctx.send( ctx.message.author.mention + ', there is not a tournament named "' + arg + '" in this guild (server).' )
        return
    
    if not tourn.regOpen:
        await ctx.send( ctx.message.author.mention + ', registeration for the tournament named "' + arg + '" appears to be closed. If you think this is an error, please contact tournament staff.' )
        return
        
    if ctx.message.author.name in tourn.activePlayers:
        await ctx.send( ctx.message.author.mention + ', it appears that you have already registered for the tournament named "' + arg + '". Best of luck and long my you reign!!' )
        return

    tourn.addPlayer( ctx.message.author )
    tourn.activePlayers[ctx.message.author.name].addDiscordUser( ctx.message.author )
    tourn.activePlayers[ctx.message.author.name].saveXML( f'openTournaments/{tourn.tournName}/players/{ctx.message.author.name}.xml' )
    await ctx.send( ctx.message.author.mention + ', you have been added to the tournament named "' + arg + '" in this guild (server)!' )


@bot.command(name='list-decks')
async def submitDecklist( ctx, arg = "" ):
    arg = arg.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't list the decks you've submitted for a tournament via private message since each tournament needs to be associated with a guild (server)." )
        return

    if arg == "":
        await ctx.send( ctx.message.author.mention + ', you need to specify what tournament you want to list your decks for. If you\'re unsure of the name of the tournament you need, use the list-tournaments command or talk to a tournament admin.' )
        return
    
    tourn = ""
    if arg in futureTournaments:
        tourn = futureTournaments[arg]
    if arg in openTournaments:
        tourn = openTournaments[arg]

    if not isCorrectGuild( tourn.tournName, ctx.message.guild.name ):
        await ctx.send( ctx.message.author.mention + ', there is not a tournament named "' + arg + '" in this guild (server).' )
        return

    if not ctx.message.author.name in tourn.activePlayers:
        await ctx.send( ctx.message.author.mention + ", you need to register before you can submit a decklist. Please you the register command to do so." )
        return
    
    if len( tourn.activePlayers[ctx.message.author.name].decks ) == 0:
        await ctx.send( ctx.message.author.mention + ', you have not registered any decks for the tournament called "' + arg + '".' )
        return
    
    decks = tourn.activePlayers[ctx.message.author.name].decks
    digest = [ deck + ":  " + str(decks[deck].deckHash) for deck in decks ]
    
    await ctx.send( ctx.message.author.mention + ", here are the decks that you currently have registered:\n\t- " + "\n\t- ".join( digest ) )


@bot.command(name='add-deck')
async def submitDecklist( ctx, arg1, arg2 = "", arg3 = "" ):
    arg1 = arg1.strip()
    arg2 = arg2.strip()
    arg3 = arg3.strip()
    if arg2 == "" or arg3 == "":
        await ctx.send( ctx.message.author.mention + ", it appears that you didn't provide enough information. To submit a decklist, you need to specify a tournament name, a commander, and then a decklist." )
        return
    if len(arg2) > len(arg3):
        tmp = arg2
        arg2 = arg3
        arg3 = tmp

    tourn = ""
    if arg1 in futureTournaments:
        tourn = futureTournaments[arg1]
    if arg1 in openTournaments:
        tourn = openTournaments[arg1]
    
    if tourn == "":
        await ctx.send( ctx.message.author.mention + ', the tournament "' + arg1 + '" doesn\'t exist. Double-check the name. If you still are having issues, contact a tournament admin.' )
        return

    if not ctx.message.author.name in tourn.activePlayers:
        await ctx.send( ctx.message.author.mention + ", you need to register before you can submit a decklist. Please you the register command to do so." )
        return

    if not tourn.regOpen:
        await ctx.send( ctx.message.author.mention + ", it would appear that registeration for this tournament is already closed. If you think this is incorrect, talk to a tournament admin." )
        return
    
    tourn.activePlayers[ctx.message.author.name].addDeck( arg2, arg3 )
    await ctx.send( ctx.message.author.mention + ', your decklist has been submitted. Your deck hash is "' + str(tourn.activePlayers[ctx.message.author.name].decks[arg2].deckHash) + '". If this doesn\'t match your deck hash in Cocktrice, please contact tournament admin.' )
    if not isPrivateMessage( ctx.message ):
        await ctx.send( ctx.message.author.mention + ", for future reference, you can submit your decklist via private message so that you don't have to publicly post your decklist." )
    tourn.activePlayers[ctx.message.author.name].saveXML( f'openTournaments/{tourn.tournName}/players/{ctx.message.author.name}.xml' )

@bot.command(name='remove-deck')
async def submitDecklist( ctx, arg1 = "", arg2 = "" ):
    arg1 = arg1.strip()
    arg2 = arg2.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't join a tournament via private message since each tournament needs to be associated with a guild (server)." )
        return

    if arg1 == "" or arg2 == "":
        await ctx.send( ctx.message.author.mention + ", it appears that you didn't provide enough information. To remove a decklist, you need to specify a tournament name and then either the name given to that deck or the deck's hash." )
        return

    tourn = ""
    if arg1 in futureTournaments:
        tourn = futureTournaments[arg1]
    if arg1 in openTournaments:
        tourn = openTournaments[arg1]
    
    if tourn == "":
        await ctx.send( ctx.message.author.mention + ', the tournament "' + arg1 + '" doesn\'t exist. Double-check the name. If you still are having issues, contact a tournament admin.' )
        return

    if not ctx.message.author.name in tourn.activePlayers:
        await ctx.send( ctx.message.author.mention + ", you need to register before you can submit a decklist. Please you the register command to do so." )
        return
    
    deckName = ""
    print( [ tourn.activePlayers[ctx.message.author.name].decks[deck].deckHash for deck in tourn.activePlayers[ctx.message.author.name].decks ] )
    if arg2 in tourn.activePlayers[ctx.message.author.name].decks:
        deckName = arg2
    if arg2 in [ tourn.activePlayers[ctx.message.author.name].decks[deck].deckHash for deck in tourn.activePlayers[ctx.message.author.name].decks ]:
        deckName = [ deck for deck in tourn.activePlayers[ctx.message.author.name].decks if tourn.activePlayers[ctx.message.author.name].decks[deck].deckHash == arg2 ][0]

    if deckName == "":
        await ctx.send( ctx.message.author.mention + ', it appears that you don\'t have a deck whose name nor deck hash is "' + arg2 + '" registered for the tournament "' + arg1 + '".' )
        return
    
    del( tourn.activePlayers[ctx.message.author.name].decks[deckName] )
    tourn.activePlayers[ctx.message.author.name].saveXML( f'openTournaments/{tourn.tournName}/players/{ctx.message.author.name}.xml' )
    await ctx.send( ctx.message.author.mention + ', your decklist whose name or deck hash was "' + arg2 + '" has been deleted.' )

bot.run(TOKEN)

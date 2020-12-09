# bot.py
import os
import random

from discord.ext import commands
from dotenv import load_dotenv

from tournament.match import match
from tournament.deck import deck
from tournament.player import player
from tournament.tournament import tournament


def stringToBool( s: str ) -> bool:
    s = s.lower()
    if s == "t" or s == "true":
        return True
    return False

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
        if futureTournaments[tourn].hostGuild == a_guildName:
            tourns[tourn] = futureTournaments[tourn]
    return tourns

def isOpenGuildTournament( a_guildName ) -> bool:
    for tourn in openTournaments:
        if openTournaments[tourn].hostGuild == a_guildName:
            return True
    return False

def isCorrectGuild( a_tournName, a_guildName ) -> bool:
    if a_tournName in futureTournaments:
        return a_guildName == futureTournaments[a_tournName].hostGuild
    if a_tournName in openTournaments:
        return a_guildName == openTournaments[a_tournName].hostGuild
    return False
        
    


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')

futureTournaments = {}
openTournaments = {}
closedTournaments = []

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
    
    futureTournaments[arg] = tournament( arg.strip(), ctx.message.guild.name )
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
        
    if tourn in futureTournaments:
        futureTournaments[tourn].setRegStatus( stringToBool(status) )
    if tourn in openTournaments:
        openTournaments[tourn].setRegStatus( stringToBool(status) )
    await ctx.send( adminMention + ', registeration for the "' + tourn + '" tournament has been ' + ("opened" if stringToBool(status) else "closed") + " by " + ctx.message.author.mention ) 


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
        await ctx.send( adminMention + ', the "' + arg +'" tournament has been closed by ' + ctx.message.author.mention + "." )
        return
    
    if arg in futureTournaments:
        await ctx.send( ctx.message.author.mention + ', the no tournament called "' + arg + '" has not been started yet, so it can\'t end yet. If you want to cancel the tournament, use the cancel-tournament command.' )
        return

    await ctx.send( ctx.message.author.mention + ', there is no tournament called "' + arg + '" for this guild (server).' )


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
        

    tourn.addPlayer( ctx.message.author.name, ctx.message.author.display_name )
    await ctx.send( ctx.message.author.mention + ', you have been added to the tournament named "' + arg + '" in this guild (server)!' )


@bot.command(name='deck')
async def submitDecklist( ctx, arg1, arg2 = "" ):
    arg1 = arg1.strip()
    arg2 = arg2.strip()
    if arg2 == "":
        await ctx.send( ctx.message.author.mention + ", it appears that you only gave one argument. To submit a decklist, you need to specify a tournament name and then a decklist." )
        return
    if len(arg1) > len(arg2):
        tmp = arg1
        arg1 = arg2
        arg2 = tmp

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
    
    tourn.activePlayers[ctx.message.author.name].addDeck( arg2 )
    await ctx.send( ctx.message.author.mention + ', your decklist has been submitted. Your deck hash is "' + str(tourn.activePlayers[ctx.message.author.name].decks[-1].deckHash) + '". If this doesn\'t match your deck hash in Cocktrice, please contact tournament admin.' )
    if not isPrivateMessage( ctx.message ):
        await ctx.send( ctx.message.author.mention + ", for future reference, you can submit your decklist via private message so that you don't have to publicly post your decklist." )

bot.run(TOKEN)

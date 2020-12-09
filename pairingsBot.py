# bot.py
import os
import random

from discord.ext import commands
from dotenv import load_dotenv

from tournament.match import match
from tournament.deck import deck
from tournament.player import player
from tournament.tournament import tournament


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
        return a_guildName == futureTournaments[a_tournName]
    if a_tournName in openTournaments:
        return a_guildName == openTournaments[a_tournName]
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
async def createTournament( ctx, arg ):
    arg = arg.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't create a tournament via private message since each tournament needs to be associated with a guild (server)." )
        return
    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not isTournamentAdmin( ctx.message.author ):
        await ctx.send( ctx.message.author.mention + ", you don't have permissions to create a tournament in this server. Please don't do this again or " + adminMention + " may intervene." )
        return
    if (arg in futureTournaments) or (arg in openTournaments):
        await ctx.send( ctx.message.author.mention + ', it would appear that there is already a tournement named "' + arg + '" either on this server or another. Please pick a different name.' )
    
    futureTournaments[arg] = tournament( arg.strip(), ctx.message.guild.name )
    await ctx.send( adminMention + ', a new tournament called "' + arg.strip() + '" has been created by ' + ctx.message.author.mention )

@bot.command(name='list-tournament')
async def listTournament( ctx ):
    if isPrivateMessage( ctx.message ):
        await ctx.send( "A list of tournaments can't be created via private message since each tournament is associated with a guild (server)." )
        return
    await ctx.send( ctx.message.author.mention + ", the following tournaments for this guild (server) are planned but have not been started:\n" + "\n\t- ".join( [name for name in futureGuildTournaments( ctx.message.guild.name)] ) )
    

@bot.command(name='update-reg')
async def startTournament( ctx, arg ):
    arg = arg.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't adjust tournament settings via private message since each tournament needs to be associated with a guild (server)." )
        return
    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not isTournamentAdmin( ctx.message.author ):
        await ctx.send( ctx.message.author.mention + ", you don't have permissions to change tournament settings in this server. Please don't do this again or " + adminMention + " may intervene." )
        return
    tourn  = arg.strip().split(" ")[0].strip()
    status = arg.strip().split(" ")[1].strip()
    
    if not isCorrectGuild( tourn, ctx.message.guild.name ):
        await ctx.send( ctx.message.author.mention + ', there is no tournament called"' + tourn + '" for this guild (server).' )
        return
        
    if tourn in futureTournaments:
        futureTournaments[tourn].setRegStatus( bool(status) )
    if tourn in openTournaments:
        openTournaments[tourn].setRegStatus( bool(status) )
    await ctx.send( adminMention + ', registeration for the "' + tourn + '" tournament has been ' + ("opened" if status.lower() == "true" else "closed") + " by " + ctx.message.author.mention ) 



@bot.command(name='start-tournament')
async def startTournament( ctx, arg ):
    arg = arg.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't start a tournament via private message since each tournament needs to be associated with a guild (server)." )
        return
    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not isTournamentAdmin( ctx.message.author ):
        await ctx.send( ctx.message.author.mention + ", you don't have permissions to start a tournament in this server. Please don't do this again or " + adminMention + " may intervene." )
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
async def endTournament( ctx, arg ):
    arg = arg.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't end a tournament via private message since each tournament needs to be associated with a guild (server)." )
        return
    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not isTournamentAdmin( ctx.message.author ):
        await ctx.send( ctx.message.author.mention + ", you don't have permissions to start a tournament in this server. Please don't do this again or " + adminMention + " may intervene." )
        return

    if isOpenGuildTournament( ctx.message.guild.name ):
        await ctx.send( adminMention + ', the "' + arg +'" tournament has been closed by ' + ctx.message.author.mention + "." )
        return

    await ctx.send( ctx.message.author.mention + ', there is no tournament called "' + arg + '" for this guild (server).' )


@bot.command(name='register')
async def addPlayer( ctx, arg ):
    arg = arg.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't join a tournament via private message since each tournament needs to be associated with a guild (server)." )
        return

    tourn = ""
    if arg in futureTournaments:
        tourn = futureTournaments[arg]
    if arg in openTournaments:
        tourn = openTournaments[arg]
    
    if not isCorrectGuild( tourn.tournName, ctx.message.guild.name ) or tourn == "":
        await ctx.send( ctx.message.author.mention + ', there is not a tournament named "' + arg + '" in this guild (server).' )
        return
    
    if not tourn.regOpen:
        await ctx.send( ctx.message.author.mention + ', registeration for the tournament named "' + arg + '" appears to be closed. If you think this is an error, please contact tournament staff.' )
        return
        

    tourn.addPlayer( ctx.message.author.name, ctx.message.author.display_name )
    print( "New player added!\n\tName: " + players[ctx.message.author.name].playerName +"\n\tDisplay: " + players[ctx.message.author.name].displayName )
    await ctx.send( ctx.message.author.mention + ', you have been added to the tournament named "' + arg + '" in this guild (server)!' )


@bot.command(name='deck')
async def submitDecklist( ctx, arg ):
    arg = arg.strip()

    if not ctx.message.author.name in players:
        await ctx.send( ctx.message.author.mention +", you need to register before you can submit a decklist. Please you the register command to do so." )
    else:
        players[ctx.message.author.name].addDeck( arg )
        print( players[ctx.message.author.name].decks[-1].cards )
        print( players[ctx.message.author.name].decks[-1].deckHash )

bot.run(TOKEN)

import os
import shutil
import random

from discord.ext import commands
from dotenv import load_dotenv

from baseBot import *
from tournament.match import match
from tournament.deck import deck
from tournament.player import player
from tournament.tournament import tournament
from tournament.tournamentUtils import *




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
        await ctx.send( f'{ctx.message.author.mention}, you do not have permissions to create a tournament in this server. Please do n0t do this again or {adminMention} may intervene.' )
        return
    if arg == "":
        await ctx.send( f'{ctx.message.author.mention}, you need to specify what you want the tournament to be called.' )
        return
    if arg in currentTournaments:
        await ctx.send( f'{ctx.message.author.mention}, it appears that there is already a tournament named "{arg}" either on this server or another. Please pick a different name.' )
    
    currentTournaments[arg] = tournament( arg, ctx.message.guild.name )
    currentTournaments[arg].saveTournament( f'currentTournaments/{arg}' )
    await ctx.send( f'{adminMention}, a new tournament called "{arg}" has been created by {ctx.message.author.mention}.' )
    

@bot.command(name='update-reg')
async def updateReg( ctx, arg1 = "", arg2 = "" ):
    tourn  = arg1.strip()
    status = arg2.strip()
    
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't adjust tournament settings via private message since each tournament needs to be associated with a guild (server)." )
        return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not isTournamentAdmin( ctx.message.author ):
        await ctx.send( f'{ctx.message.author.mention}, you do not have permissions to change tournament settings. Please do not do this again or {adminMention} may intervene.' )
        return
    if arg1 == "" or arg2 == "":
        await ctx.send( f'{ctx.message.author.mention}, it appears that you did not give enough information. You need to first state the tournament name and then "true" or "false".' )
        return
    if not arg1 in currentTournaments:
        await ctx.send( f'{ctx.message.author.mention}, it appears that there is not a tournament named "{arg1}". If you think this is an error, talk to fellow tournament admins.' )
        return
    if currentTournaments[arg1].hostGuildName != ctx.message.guild.name:
        await ctx.send( f'{ctx.message.author.mention}, the tournament called "{arg1}" does not belong to this guild. If you think this is an error, talk to fellow tournament admins.' )
        return
    currentTournaments[arg1].setRegStatus( str_to_bool(status) )
    currentTournaments[arg1].saveOverview( f'currentTournaments/{tourn}/overview.xml' )
    await ctx.send( f'{adminMention}, registeration for the "{arg1}" tournament has been {("opened" if str_to_bool(status) else "closed")} by {ctx.message.author.mention}.' ) 


@bot.command(name='start-tournament')
async def startTournament( ctx, arg = "" ):
    arg = arg.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't start a tournament via private message since each tournament needs to be associated with a guild (server)." )
        return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not isTournamentAdmin( ctx.message.author ):
        await ctx.send( f'{ctx.message.author.mention}, you do not have permissions to start a tournament in this server. Please do not do this again or {adminMention} may intervene.' )
        return
    if arg == "":
        await ctx.send( f'{ctx.message.author.mention}, you need to specify what tournament you want to start.' )
        return
    if hasStartedTournament( ctx.message.guild.name ):
        await ctx.send( f'{ctx.message.author.mention}, there seems to be an active tournament in this guild. Check with the rest of {adminMention} if you think this is an error.' )
        return
    if not arg in currentTournaments:
        await ctx.send( ctx.message.author.mention + f', the tournament called "{arg1}" is not a currently available tournament.' )
        return
    if not ctx.message.guild.name == currentTournaments[arg].hostGuildName:
        await ctx.send( f'{ctx.message.author.mention}, there is no tournament called "{arg}" for this guild (server).' )
        return
    if currentTournaments[arg].tournStarted:
        await ctx.send( f'{ctx.message.author.mention}, the tournament called "{arg}" already has been started.' )
        return

    currentTournaments[arg].startTourn()
    currentTournaments[arg].saveOverview( f'currentTournaments/{arg}/overview.xml' )
    await ctx.send( f'{adminMention}, the "{arg}" has been started by {ctx.message.author.mention}.' )
    

@bot.command(name='end-tournament')
async def endTournament( ctx, arg = "" ):
    arg = arg.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't end a tournament via private message since each tournament needs to be associated with a guild (server)." )
        return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not isTournamentAdmin( ctx.message.author ):
        await ctx.send( f'{ctx.message.author.mention}, you do not have permissions to start a tournament in this server. Please do not do this again or {adminMention} may intervene.' )
        return
    if arg == "":
        await ctx.send( f'{ctx.message.author.mention}, you need to specify what tournament you want to end.' )
        return
    if not arg in currentTournaments:
        await ctx.send( f'{ctx.message.author.mention}, there is no tournament called "{arg}" for this guild (server).' )
        return
    if not currentTournaments[arg].tournStarted:
        await ctx.send( f'{ctx.message.author.mention}, the no tournament called "{arg}" that has not been started, so it can not end yet. If you want to cancel the tournament, use the cancel-tournament command.' )
        return
    if currentTournaments[arg].tournCancel:
        await ctx.send( f'{ctx.message.author.mention}, the tournament called "{arg}" has been cancelled. Check with {adminMention} if you think this is an error.' )
        return
    if currentTournaments[arg].hostGuildName != ctx.message.guild.name:
        await ctx.send( f'{ctx.message.author.mention}, the tournament called "{arg}" does not belong to this guild (server), so it can not be changed from here.' )
        return

    currentTournaments[arg].endTourn( )
    currentTournaments[arg].saveTournament( f'closedTournaments/{arg}' )
    if os.path.isdir( f'currentTournaments/{arg}' ): 
        shutil.rmtree( f'currentTournaments/{arg}' )
    closedTournaments.append( currentTournaments[arg] )
    del( currentTournaments[arg] )
    await ctx.send( f'{adminMention}, the "{arg}" tournament has been closed by {ctx.message.author.mention}.' )

    

@bot.command(name='cancel-tournament')
async def endTournament( ctx, arg = "" ):
    arg = arg.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't end a tournament via private message since each tournament needs to be associated with a guild (server)." )
        return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not isTournamentAdmin( ctx.message.author ):
        await ctx.send( f'{ctx.message.author.mention}, you do not have permissions to start a tournament in this server. Please do not do this again or {adminMention} may intervene.' )
        return
    if arg == "":
        await ctx.send( f'{ctx.message.author.mention}, you need to specify what tournament you want to cancel.' )
        return
    if not arg in currentTournaments:
        await ctx.send( f'{ctx.message.author.mention}, there is not a tournament named "{arg}" in this guild (server).' )
        return
    if currentTournaments[arg].tournCancel:
        await ctx.send( f'{ctx.message.author.mention}, the tournament called "{arg}" has been cancelled. Check with {adminMention} if you think this is an error.' )
        return
    if currentTournaments[arg].hostGuildName != ctx.message.guild.name:
        await ctx.send( f'{ctx.message.author.mention}, the tournament called "{arg}" does not belong to this guild (server), so it can not be changed from here.' )
        return
    
    currentTournaments[arg].cancelTourn( )
    currentTournaments[arg].saveTournament( f'closedTournaments/{arg}' )
    if os.path.isdir( f'currentTournaments/{arg}' ): 
        shutil.rmtree( f'currentTournaments/{arg}' )
    closedTournaments.append( currentTournaments[arg] )
    del( currentTournaments[arg] )
    await ctx.send( f'{adminMention}, the "{arg}" tournament has been cancelled by {ctx.message.author.mention}.' )
    


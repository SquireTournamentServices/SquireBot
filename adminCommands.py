import os
import shutil
import random

from discord.ext import commands
from dotenv import load_dotenv

from baseBot import *
from Tournament import * 


@bot.command(name='create-tournament')
async def createTournament( ctx, tourn = "" ):
    tourn = tourn.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't create a tournament via private message since each tournament needs to be associated with a server." )
        return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not isTournamentAdmin( ctx.message.author ):
        await ctx.send( f'{ctx.message.author.mention}, you do not have permissions to create a tournament in this server. Please do n0t do this again or {adminMention} may intervene.' )
        return
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you need to specify what you want the tournament to be called.' )
        return
    if tourn in currentTournaments:
        await ctx.send( f'{ctx.message.author.mention}, it appears that there is already a tournament named "{tourn}" either on this server or another. Please pick a different name.' )
        return
    
    await ctx.message.guild.create_role( name=f'{tourn} Player' )
    currentTournaments[tourn] = tournament( tourn, ctx.message.guild.name )
    currentTournaments[tourn].addDiscordGuild( ctx.message.guild )
    currentTournaments[tourn].saveTournament( f'currentTournaments/{tourn}' )
    await ctx.send( f'{adminMention}, a new tournament called "{tourn}" has been created by {ctx.message.author.mention}.' )
    

@bot.command(name='update-reg')
async def updateReg( ctx, tourn = "", status = "" ):
    tourn  = tourn.strip()
    status = status.strip()
    
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't adjust tournament settings via private message since each tournament needs to be associated with a server." )
        return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not isTournamentAdmin( ctx.message.author ):
        await ctx.send( f'{ctx.message.author.mention}, you do not have permissions to change tournament settings. Please do not do this again or {adminMention} may intervene.' )
        return
    if tourn == "" or status == "":
        await ctx.send( f'{ctx.message.author.mention}, it appears that you did not give enough information. You need to first state the tournament name and then "true" or "false".' )
        return
    if not tourn in currentTournaments:
        await ctx.send( f'{ctx.message.author.mention}, it appears that there is not a tournament named "{tourn}". If you think this is an error, talk to fellow tournament admins.' )
        return
    if currentTournaments[tourn].hostGuildName != ctx.message.guild.name:
        await ctx.send( f'{ctx.message.author.mention}, the tournament called "{tourn}" does not belong to this guild. If you think this is an error, talk to fellow tournament admins.' )
        return

    status = "True" if status.lower() == "open" else status
    status = "False" if status.lower() == "closed" else status

    currentTournaments[tourn].setRegStatus( str_to_bool(status) )
    currentTournaments[tourn].saveOverview( f'currentTournaments/{tourn}/overview.xml' )
    await ctx.send( f'{adminMention}, registeration for the "{tourn}" tournament has been {("opened" if str_to_bool(status) else "closed")} by {ctx.message.author.mention}.' ) 


@bot.command(name='start-tournament')
async def startTournament( ctx, tourn = "" ):
    tourn = tourn.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't start a tournament via private message since each tournament needs to be associated with a server." )
        return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not isTournamentAdmin( ctx.message.author ):
        await ctx.send( f'{ctx.message.author.mention}, you do not have permissions to start a tournament in this server. Please do not do this again or {adminMention} may intervene.' )
        return
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you need to specify what tournament you want to start.' )
        return
    if not tourn in currentTournaments:
        await ctx.send( f'{ctx.message.author.mention}, there is not a tournament called "{tourn}" scheduled.' )
        return
    if not ctx.message.guild.name == currentTournaments[tourn].hostGuildName:
        await ctx.send( f'{ctx.message.author.mention}, {tourn} does not belong to this server, so it can not be changed from here.' )
        return
    if currentTournaments[tourn].tournStarted:
        await ctx.send( f'{ctx.message.author.mention}, {tourn} has already been started.' )
        return

    currentTournaments[tourn].startTourn()
    currentTournaments[tourn].saveOverview( f'currentTournaments/{tourn}/overview.xml' )
    await ctx.send( f'{adminMention}, {tourn} has been started by {ctx.message.author.mention}.' )
    

@bot.command(name='end-tournament')
async def endTournament( ctx, tourn = "" ):
    tourn = tourn.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't end a tournament via private message since each tournament needs to be associated with a server." )
        return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not isTournamentAdmin( ctx.message.author ):
        await ctx.send( f'{ctx.message.author.mention}, you do not have permissions to start a tournament in this server. Please do not do this again or {adminMention} may intervene.' )
        return
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you need to specify what tournament you want to end.' )
        return
    if not tourn in currentTournaments:
        await ctx.send( f'{ctx.message.author.mention}, there is no tournament called "{tourn}" for this server.' )
        return
    if currentTournaments[tourn].hostGuildName != ctx.message.guild.name:
        await ctx.send( f'{ctx.message.author.mention}, {tourn} does not belong to this server, so it can not be changed from here.' )
        return
    if not currentTournaments[tourn].tournStarted:
        await ctx.send( f'{ctx.message.author.mention}, {tourn} has not been started, so it can not end yet. If you want to cancel the tournament, use the cancel-tournament command.' )
        return
    if currentTournaments[tourn].tournCancel:
        await ctx.send( f'{ctx.message.author.mention}, {tourn} has already been cancelled. Check with {adminMention} if you think this is an error.' )
        return

    await currentTournaments[tourn].endTourn( )
    currentTournaments[tourn].saveTournament( f'closedTournaments/{tourn}' )
    if os.path.isdir( f'currentTournaments/{tourn}' ): 
        shutil.rmtree( f'currentTournaments/{tourn}' )
    closedTournaments.append( currentTournaments[tourn] )
    del( currentTournaments[tourn] )
    await ctx.send( f'{adminMention}, {tourn} has been closed by {ctx.message.author.mention}.' )

    

@bot.command(name='cancel-tournament')
async def cancelTournament( ctx, tourn = "" ):
    tourn = tourn.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't cancel a tournament via private message since each tournament needs to be associated with a server." )
        return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not isTournamentAdmin( ctx.message.author ):
        await ctx.send( f'{ctx.message.author.mention}, you do not have permissions to start a tournament in this server. Please do not do this again or {adminMention} may intervene.' )
        return
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you need to specify what tournament you want to cancel.' )
        return
    if not tourn in currentTournaments:
        await ctx.send( f'{ctx.message.author.mention}, there is not a tournament named "{tourn}" in this server.' )
        return
    if currentTournaments[tourn].hostGuildName != ctx.message.guild.name:
        await ctx.send( f'{ctx.message.author.mention}, {tourn} does not belong to this server, so it can not be changed from here.' )
        return
    if currentTournaments[tourn].tournCancel:
        await ctx.send( f'{ctx.message.author.mention}, {tourn} has already been cancelled. Check with {adminMention} if you think this is an error.' )
        return
    
    await currentTournaments[tourn].cancelTourn( )
    currentTournaments[tourn].saveTournament( f'closedTournaments/{tourn}' )
    if os.path.isdir( f'currentTournaments/{tourn}' ): 
        shutil.rmtree( f'currentTournaments/{tourn}' )
    closedTournaments.append( currentTournaments[tourn] )
    del( currentTournaments[tourn] )
    await ctx.send( f'{adminMention}, {tourn} has been cancelled by {ctx.message.author.mention}.' )
    
    
@bot.command(name='admin-register')
async def adminAddPlayer( ctx, tourn = "", plyr = "" ):
    tourn = tourn.strip()
    plyr  = plyr.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't register a player via private message since each tournament needs to be associated with a server." )
        return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not isTournamentAdmin( ctx.message.author ):
        await ctx.send( f'{ctx.message.author.mention}, you do not have permissions to register other players on server. Please do not do this again or {adminMention} may intervene.' )
        return
    if tourn == "" or plyr == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament and player in order to add someone to a tournament.' )
        return
    if not tourn in currentTournaments:
        await ctx.send( f'{ctx.message.author.mention}, there is not a tournament named "{tourn}" in this server.' )
        return
    if currentTournaments[tourn].hostGuildName != ctx.message.guild.name:
        await ctx.send( f'{ctx.message.author.mention}, {tourn} does not belong to this server, so it can not be changed from here.' )
        return
    if currentTournaments[tourn].isDead( ):
        await ctx.send( f'{ctx.message.author.mention}, the tournament called "{tourn}" has either ended or been cancelled. Check with {adminMention} if you think this is an error.' )
        return
    
    member = await findGuildMember( ctx.guild, plyr )
    if member == "":
        await ctx.send( f'{ctx.message.author.mention}, there is not a member of this server whose name nor mention is "{plyr}".' )
        return

    await user.add_roles( findGuildRole( ctx.guild, f'{tourn} Player' ) )
    await currentTournaments[tourn].addPlayer( member )
    currentTournaments[tourn].activePlayers[getUserIdent(member)].saveXML( f'currentTournaments/{currentTournaments[tourn].tournName}/players/{getUserIdent(member)}.xml' )
    await ctx.send( f'{ctx.message.author.mention}, you have added {member.mention} to the tournament named "{tourn}" in this server!' )


@bot.command(name='admin-add-deck')
async def adminAddDeck( ctx, tourn = "", plyr = "", ident = "", decklist = "" ):
    tourn = tourn.strip()
    plyr  =  plyr.strip()
    ident = ident.strip()
    decklist = decklist.strip()
    
    print( f'There are {len(ctx.guild.roles[0].members)} in the role "{ctx.guild.roles[0].name}".' )
    
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't register a deck for a player via private message since each tournament needs to be associated with a server." )
        return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not isTournamentAdmin( ctx.message.author ):
        await ctx.send( f'{ctx.message.author.mention}, you do not have permissions to register decks for other players on server. Please do not do this again or {adminMention} may intervene.' )
        return
    if tourn == "" or plyr == "" or ident == "" or decklist == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament, a player, a deck identifier, and a decklist in order to add a deck for someone.' )
        return
    if not tourn in currentTournaments:
        await ctx.send( f'{ctx.message.author.mention}, there is not a tournament named "{tourn}" in this server.' )
        return
    if currentTournaments[tourn].hostGuildName != ctx.message.guild.name:
        await ctx.send( f'{ctx.message.author.mention}, {tourn} does not belong to this server, so it can not be changed from here.' )
        return
    if currentTournaments[tourn].isDead( ):
        await ctx.send( f'{ctx.message.author.mention}, {tourn} has either ended or been cancelled. Check with {adminMention} if you think this is an error.' )
        return
    
    member = findPlayer( ctx.guild, tourn, plyr )
    userIdent = getUserIdent( member )
    if member == "":
        await ctx.send( f'{ctx.message.author.mention}, a player by "{plyr}" could not be found in the player role for {tourn}. Please verify that they have registered.' )
        return
    if not userIdent in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, a user by "{plyr}" was found in the player role, but they are not active in {tourn}. Make sure they are registered or that they have not dropped.' )
        return
    
    currentTournaments[tourn].activePlayers[userIdent].addDeck( ident, decklist )
    currentTournaments[tourn].activePlayers[userIdent].saveXML( f'currentTournaments/{tourn}/players/{userIdent}.xml' )
    deckHash = str(currentTournaments[tourn].activePlayers[userIdent].decks[ident].deckHash)
    await ctx.send( f'{ctx.message.author.mention}, decklist that you added for {plyr} has been submitted. The deck hash is "{deckHash}".' )
    await member.create_dm().send( f'A decklist has been submitted for {tourn} on the server {ctx.guild.name}. The identifier for the deck is "{ident}" and the deck hash is "{deckHash}". If this deck hash is incorrect or you are not expecting this, please contact tournament admin on that server.' )


@bot.command(name='admin-remove-deck')
async def adminRemoveDeck( ctx, tourn = "", plyr = "", ident = "" ):
    tourn = tourn.strip()
    plyr  =  plyr.strip()
    ident = ident.strip()

    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't register a deck for a player via private message since each tournament needs to be associated with a server." )
        return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not isTournamentAdmin( ctx.message.author ):
        await ctx.send( f'{ctx.message.author.mention}, you do not have permissions to register other players on server. Please do not do this again or {adminMention} may intervene.' )
        return
    if tourn == "" or plyr == "" or ident == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament, a player, a deck identifier, and a decklist in order to add a deck for someone.' )
        return
    if not tourn in currentTournaments:
        await ctx.send( f'{ctx.message.author.mention}, there is not a tournament named "{tourn}" in this server.' )
        return
    if currentTournaments[tourn].hostGuildName != ctx.message.guild.name:
        await ctx.send( f'{ctx.message.author.mention}, {tourn} does not belong to this server, so it can not be changed from here.' )
        return
    if currentTournaments[tourn].isDead( ):
        await ctx.send( f'{ctx.message.author.mention}, {tourn} has either ended or been cancelled. Check with {adminMention} if you think this is an error.' )
        return
    
    member = findPlayer( ctx.guild, tourn, plyr )
    userIdent = getUserIdent( member )
    if member == "":
        await ctx.send( f'{ctx.message.author.mention}, a player by "{plyr}" could not be found in the player role for {tourn}. Please verify that they have registered.' )
        return
    if not userIdent in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, a user by "{plyr}" was found in the player role, but they are not active in the tournament "{tourn}". Make sure they are registered or that they have not dropped.' )
        return
    
    deckName = currentTournaments[tourn].activePlayers[userIdent].getDeckIdent( ident )
    if deckName == "":
        await ctx.send( f'{ctx.message.author.mention}, it appears that {plyr} does not have a deck whose name nor hash is "{ident}" registered for {tourn}.' )
        return

    del( currentTournaments[tourn].activePlayers[userIdent].decks[deckName] )
    currentTournaments[tourn].activePlayers[userIdent].saveXML( f'currentTournaments/{currentTournaments[tourn].tournName}/players/{userIdent}.xml' )
    await ctx.send( f'{ctx.message.author.mention}, decklist that you removed from {plyr} has been processed.' )
    await member.create_dm().send( f'A decklist has been removed for the tournament called "{tourn}" on the server "{ctx.guild.name}". The identifier or deck hash was "{ident}".' )


@bot.command(name='set-deck-count')
async def setDeckCount( ctx, tourn = "", count = "" ):
    tourn = tourn.strip()
    count = count.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't register a deck for a player via private message since each tournament needs to be associated with a server." )
        return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not isTournamentAdmin( ctx.message.author ):
        await ctx.send( f'{ctx.message.author.mention}, you do not have permissions to register other players on server. Please do not do this again or {adminMention} may intervene.' )
        return
    if tourn == "" or count == "" :
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament and a max number of decks.' )
        return
    if not tourn in currentTournaments:
        await ctx.send( f'{ctx.message.author.mention}, there is not a tournament named "{tourn}" in this server.' )
        return
    if currentTournaments[tourn].hostGuildName != ctx.message.guild.name:
        await ctx.send( f'{ctx.message.author.mention}, {tourn} does not belong to this server, so it can not be changed from here.' )
        return
    if currentTournaments[tourn].isDead( ):
        await ctx.send( f'{ctx.message.author.mention}, {tourn} has either ended or been cancelled. Check with {adminMention} if you think this is an error.' )
        return
    
    currentTournaments[tourn].deckCount = int( count )
    currentTournaments[tourn].saveOverview( f'currentTournaments/{tourn}/overview.xml' )
    await ctx.send( f'{adminMention}, the deck count for tournament called "{tourn}" has been changed to {count} by {ctx.message.author.display_name}.' )


@bot.command(name='admin-prune-decks')
async def adminPruneDecks( ctx, tourn = "" ):
    tourn = tourn.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't register a deck for a player via private message since each tournament needs to be associated with a server." )
        return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not isTournamentAdmin( ctx.message.author ):
        await ctx.send( f'{ctx.message.author.mention}, you do not have permissions to register other players on server. Please do not do this again or {adminMention} may intervene.' )
        return
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament and a max number of decks.' )
        return
    if not tourn in currentTournaments:
        await ctx.send( f'{ctx.message.author.mention}, there is not a tournament named "{tourn}" in this server.' )
        return
    if currentTournaments[tourn].hostGuildName != ctx.message.guild.name:
        await ctx.send( f'{ctx.message.author.mention}, {tourn} does not belong to this server, so it can not be changed from here.' )
        return
    if currentTournaments[tourn].isDead( ):
        await ctx.send( f'{ctx.message.author.mention}, {tourn} has either ended or been cancelled. Check with {adminMention} if you think this is an error.' )
        return
    
    await ctx.send( f'{adminMention}, the pruning of decks is starting... now!' )
    for plyr in currentTournaments[tourn].activePlayers:
        Player = currentTournaments[tourn].activePlayers[plyr]
        deckIdents = [ ident for ident in Player.decks ]
        while len( Player.decks ) > currentTournaments[tourn].deckCount:
            del( Player.decks[deckIdents[0]] )
            del( deckIdents[0] )
            await ctx.send( f'{adminMention}, the deck with identifier "{deckIdents[0]}" belonging to {Player.discordUser.display_name} has been pruned.' )
            await Player.discordUser.create_dm().send( f'Your deck with identifier "{ident}" has been pruned from {tourn} on the server "{ctx.guild.name}".' )
        Player.saveXML( f'currentTournaments/{tourn}/players/{plyr}.xml' )


@bot.command(name='admin-list-players')
async def adminListPlayers( ctx, tourn = "", num = "" ):
    tourn = tourn.strip()
    num   = num.strip().lower()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't register a deck for a player via private message since each tournament needs to be associated with a server." )
        return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not isTournamentAdmin( ctx.message.author ):
        await ctx.send( f'{ctx.message.author.mention}, you do not have permissions to register other players on server. Please do not do this again or {adminMention} may intervene.' )
        return
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament in order to list the players.' )
        return
    if not tourn in currentTournaments:
        await ctx.send( f'{ctx.message.author.mention}, there is not a tournament named "{tourn}" in this server.' )
        return
    if currentTournaments[tourn].hostGuildName != ctx.message.guild.name:
        await ctx.send( f'{ctx.message.author.mention}, {tourn} does not belong to this server, so it can not be changed from here.' )
        return
    if currentTournaments[tourn].isDead( ):
        await ctx.send( f'{ctx.message.author.mention}, {tourn} has either ended or been cancelled. Check with {adminMention} if you think this is an error.' )
        return
    
    if len( currentTournaments[tourn].activePlayers ) == 0:
        await ctx.send( f'{ctx.message.author.mention}, there are no players registered for the tournament {tourn}.' )
        return
    if num == "n" or num == "num" or num == "number":
        await ctx.send( f'{ctx.message.author.mention}, there are {len(currentTournaments[tourn].activePlayers)} active players in {tourn}.' )
        return
    else:
        newLine = "\n\t- "
        playerNames = [ currentTournaments[tourn].activePlayers[plyr].discordUser.display_name for plyr in currentTournaments[tourn].activePlayers ]
        await ctx.send( f'{ctx.message.author.mention}, the following are all players registered for {tourn}:{newLine}{newLine.join(playerNames)}' )
    

@bot.command(name='admin-player-profile')
async def adminPlayerProfile( ctx, tourn = "", plyr = "" ):
    tourn = tourn.strip()
    plyr  = plyr.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't register a deck for a player via private message since each tournament needs to be associated with a server." )
        return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not isTournamentAdmin( ctx.message.author ):
        await ctx.send( f'{ctx.message.author.mention}, you do not have permissions to register other players on server. Please do not do this again or {adminMention} may intervene.' )
        return
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament in order to list the players.' )
        return
    if not tourn in currentTournaments:
        await ctx.send( f'{ctx.message.author.mention}, there is not a tournament named "{tourn}" in this server.' )
        return
    if currentTournaments[tourn].hostGuildName != ctx.message.guild.name:
        await ctx.send( f'{ctx.message.author.mention}, {tourn} does not belong to this server, so it can not be changed from here.' )
        return
    if currentTournaments[tourn].isDead( ):
        await ctx.send( f'{ctx.message.author.mention}, {tourn} has either ended or been cancelled. Check with {adminMention} if you think this is an error.' )
        return
        return
    
    member = findPlayer( ctx.guild, tourn, plyr )
    if member == "":
        await ctx.send( f'{ctx.message.author.mention}, a player by "{plyr}" could not be found in the player role for {tourn}. Please verify that they have registered.' )
        return
    if not getUserIdent(member) in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, a user by "{plyr}" was found in the player role, but they are not active in the tournament "{tourn}". Make sure they are registered or that they have not dropped.' )
        return
    
    await ctx.send( f'{ctx.message.author.mention}, the following is the profile for the player "{plyr}":\n{currentTournaments[tourn].activePlayers[getUserIdent(member)]}' )

"""
@bot.command(name='admin-drop-match')
async def adminDropMatch( ctx, tourn = "", match = "", plyr = "" ):

@bot.command(name='admin-match-result')
async def adminMatchResult( ctx, tourn = "", match = "", plyr = "", result = "" ):

@bot.command(name='admin-confirm-result')
async def adminConfirmResult( ctx, tourn = "", match = "", plyr = "" ):

@bot.command(name='admin-drop-tournament')
async def adminDropPlayer( ctx, tourn = "", plyr = "" ):
"""



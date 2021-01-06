import os
import shutil
import random

from discord.ext import commands
from dotenv import load_dotenv


from baseBot import *
from Tournament import *



@bot.command(name='list-tournaments')
async def listTournaments( ctx ):
    if isPrivateMessage( ctx.message ):
        await ctx.send( "A list of tournaments can't be created via private message since each tournament is associated with a guild (server)." )
        return
    
    plannedTourns = futureGuildTournaments( ctx.message.guild.name )

    if len( plannedTourns ) == 0:
        await ctx.send( f'{ctx.message.author.mention}, there are no tournaments currently planned for this guild (server).' )
        return
    
    newLine = "\n\t- "
    await ctx.send( f'{ctx.message.author.mention}, the following tournaments for this guild (server) are planned but have not been started:{newLine}{newLine.join(plannedTourns)}' )


@bot.command(name='register')
async def registerPlayer( ctx, tourn = "" ):
    print( [ member.name for member in ctx.guild.members ] )
    tourn = tourn.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't join a tournament via private message since each tournament needs to be associated with a guild (server)." )
        return

    if tourn == "":
        if len( futureGuildTournaments( ctx.message.guild.name ) ) > 1:
            await ctx.send( f'{ctx.message.author.mention}, there are more than one planned tournaments for this server. Please specify what tournament you want to register for.' )
            return
        elif len( futureGuildTournaments( ctx.message.guild.name ) ) < 1:
            await ctx.send( f'{ctx.message.author.mention}, there are no planned tournaments for this server. If you think this is an error, contact tournament staff.' )
            return
        else:
            tourn = [ name for name in futureGuildTournaments( ctx.message.guild.name ) ][0]
    if not tourn in currentTournaments or currentTournaments[tourn].hostGuildName != ctx.message.guild.name:
        await ctx.send( f'{ctx.message.author.mention}, there is not a tournament named "{tourn}" in this guild (server).' )
        return
    if not currentTournaments[tourn].regOpen:
        await ctx.send( f'{ctx.message.author.mention}, registration for the tournament named "{tourn}" appears to be closed. Please contact tournament staff if you think this is an error.' )
        return
    if getUserIdent(ctx.message.author) in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, it appears that you are already registered for the tournament named "{tourn}". Best of luck and long my you reign!!' )
        return

    await ctx.message.author.add_roles( findGuildRole( ctx.guild, f'{tourn} Player' ) )
    await currentTournaments[tourn].addPlayer( ctx.message.author )
    await currentTournaments[tourn].activePlayers[getUserIdent(ctx.message.author)].addDiscordUser( ctx.message.author )
    currentTournaments[tourn].activePlayers[getUserIdent(ctx.message.author)].saveXML( f'currentTournaments/{currentTournaments[tourn].tournName}/players/{getUserIdent(ctx.message.author)}.xml' )
    await ctx.send( f'{ctx.message.author.mention}, you have been added to the tournament named "{tourn}" in this guild (server)!' )


@bot.command(name='cockatrice-name')
async def addTriceName( ctx, tourn = "", name = "" ):
    tourn = tourn.strip()
    name  = name.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't join a tournament via private message since each tournament needs to be associated with a guild (server)." )
        return

    if tourn == "" and name == "":
        await ctx.send( "You did not provide enough information. You need to specify a tournament and your Cockatrice username." )
        return
    if name == "":
        name = tourn
        tourn == ""
    if tourn == "":
        if len( futureGuildTournaments( ctx.message.guild.name ) ) != 1:
            await ctx.send( f'{ctx.message.author.mention}, there are more than one planned tournaments for this server. Please specify what tournament you want to register for.' )
            return
        else:
            tourn = [ name for name in futureGuildTournaments( ctx.message.guild.name ) ][0]
    if not tourn in currentTournaments or currentTournaments[tourn].hostGuildName != ctx.message.guild.name:
        await ctx.send( f'{ctx.message.author.mention}, there is not a tournament named "{tourn}" in this guild (server).' )
        return
    if not ctx.message.author.display_name in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, it appears that you are not registered for the tournament named "{tourn}". Please register before adding a Cockatrice username.' )
        return
    
    currentTournaments[tourn].activePlayers[getUserIdent(ctx.message.author)].triceName = name
    currentTournaments[tourn].activePlayers[getUserIdent(ctx.message.author)].saveXML( f'currentTournaments/{currentTournaments[tourn].tournName}/players/{getUserIdent(ctx.message.author)}.xml' )
    await ctx.send( f'{ctx.message.author.mention}, "{name}" was added as your Cocktrice username.' )


@bot.command(name='add-deck')
async def submitDecklist( ctx, tourn = "", ident = "", decklist = "" ):
    tourn = tourn.strip()
    ident = ident.strip()
    decklist = decklist.strip()
    if tourn == "" or ident == "" or decklist == "":
        await ctx.send( f'{ctx.message.author.mention}, it appears that you did not provide enough information. You need to specify a tournament name, a deckname, and then a decklist.' )
        return

    if len(ident) > len(decklist):
        tmp = ident
        ident = decklist
        decklist = tmp
    
    if not tourn in currentTournaments:
        await ctx.send( f'{ctx.message.author.mention}, there is not a tournament named "{tourn}" in this guild (server).' )
        return
    if not ctx.message.author.display_name in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, you need to register before you can submit a decklist. Please you the register command to do so.' )
        return
    if not currentTournaments[tourn].regOpen:
        await ctx.send( f'{ctx.message.author.mention}, it appears that registration for this tournament is already closed. If you think this an error, talk to a tournament admin.' )
        return
    
    currentTournaments[tourn].activePlayers[getUserIdent(ctx.message.author)].addDeck( ident, decklist )
    currentTournaments[tourn].activePlayers[getUserIdent(ctx.message.author)].saveXML( f'currentTournaments/{currentTournaments[tourn].tournName}/players/{getUserIdent(ctx.message.author)}.xml' )
    deckHash = str(currentTournaments[tourn].activePlayers[getUserIdent(ctx.message.author)].decks[ident].deckHash)
    currentTournaments[tourn].activePlayers[getUserIdent(ctx.message.author)].saveXML( f'currentTournaments/{currentTournaments[tourn].tournName}/players/{getUserIdent(ctx.message.author)}.xml' )
    await ctx.send( f'{ctx.message.author.mention}, your decklist has been submitted. Your deck hash is "{deckHash}". Please make sure this matches your deck hash in Cocktrice.' )
    if not isPrivateMessage( ctx.message ):
        await ctx.send( f'{ctx.message.author.mention}, for future reference, you can submit your decklist via private message so that you do not have to publicly post your decklist.' )


@bot.command(name='remove-deck')
async def removeDecklist( ctx, tourn = "", ident = "" ):
    tourn = tourn.strip()
    ident = ident.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't join a tournament via private message since each tournament needs to be associated with a guild (server)." )
        return

    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provided enough information. Please provide either your deckname or deck hash to remove your deck.' )
        return
    if ident == "":
        if len( futureGuildTournaments( ctx.message.guild.name ) ) != 1:
            await ctx.send( f'{ctx.message.author.mention}, there are more than one planned tournaments for this server. Please specify a tournament to remove your deck.' )
            return
        else:
            ident = tourn
            tourn = [ name for name in futureGuildTournaments( ctx.message.guild.name ) ][0]
    if not tourn in currentTournaments:
        await ctx.send( f'{ctx.message.author.mention}, the tournament "{tourn}" does not exist. Double-check the name. If you still are having issues, contact a tournament admin.' )
        return
    if not ctx.message.author.display_name in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, you need to register before managing your decklists. Please you the register command to do so.' )
        return
    
    deckName = ""
    print( [ currentTournaments[tourn].activePlayers[getUserIdent(ctx.message.author)].decks[deck].deckHash for deck in currentTournaments[tourn].activePlayers[getUserIdent(ctx.message.author)].decks ] )
    if ident in currentTournaments[tourn].activePlayers[getUserIdent(ctx.message.author)].decks:
        deckName = ident
    # Is the second argument in the player's deckhashes? Yes, then deckName will equal the name of the deck that corresponds to that hash.
    for deck in currentTournaments[tourn].activePlayers[getUserIdent(ctx.message.author)].decks:
        if ident == currentTournaments[tourn].activePlayers[getUserIdent(ctx.message.author)].decks[deck].deckHash:
            deckName = deck 
    if deckName == "":
        await ctx.send( f'{ctx.message.author.mention}, it appears that you do not have a deck whose name nor hash is "{ident}" registered for the tournament "{tourn}".' )
        return
    
    del( currentTournaments[tourn].activePlayers[getUserIdent(ctx.message.author)].decks[deckName] )
    currentTournaments[tourn].activePlayers[getUserIdent(ctx.message.author)].saveXML( f'currentTournaments/{currentTournaments[tourn].tournName}/players/{getUserIdent(ctx.message.author)}.xml' )
    await ctx.send( f'{ctx.message.author.mention}, your decklist whose name or deck hash was "{ident}" has been deleted.' )


@bot.command(name='list-decks')
async def listDecklists( ctx, tourn = "" ):
    tourn = tourn.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't list the decks you've submitted for a tournament via private message since each tournament needs to be associated with a guild (server)." )
        return

    if tourn == "":
        if len( futureGuildTournaments( ctx.message.guild.name ) ) != 1:
            await ctx.send( f'{ctx.message.author.mention}, there are more than one planned tournaments for this server. Please specify a tournament to list your decks.' )
            return
        else:
            tourn = [ name for name in futureGuildTournaments( ctx.message.guild.name ) ][0]
    if not tourn in currentTournaments or currentTournaments[tourn].hostGuildName != ctx.message.guild.name:
        await ctx.send( f'{ctx.message.author.mention}, there is not a tournament named "{tourn}" in this guild (server).' )
        return
    if not ctx.message.author.display_name in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, you need to register before you can submit a decklist. Please you the register command to do so.' )
        return
    if len( currentTournaments[tourn].activePlayers[ctx.message.author.display_name].decks ) == 0:
        await ctx.send( f'{ctx.message.author.mention}, you have not registered any decks for the tournament called "{tourn}".' )
        return
    
    decks  = currentTournaments[tourn].activePlayers[getUserIdent(ctx.message.author)].decks
    digest = [ deck + ":  " + str(decks[deck].deckHash) for deck in decks ]
    
    newLine = "\n\t- "
    await ctx.send( f'{ctx.message.author.mention}, here are the decks that you currently have registered:{newLine}{newLine.join( digest )}' )
    

@bot.command(name='drop-tournament')
async def dropTournament( ctx, tourn = "" ):
    tourn = tourn.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't list the decks you've submitted for a tournament via private message since each tournament needs to be associated with a guild (server)." )
        return
    
    name = getUserIdent(ctx.message.author) 
    if tourn == "":
        if len( futureGuildTournaments( ctx.message.guild.name ) ) != 1:
            await ctx.send( f'{ctx.message.author.mention}, there are more than one planned tournaments for this server. Please specify a tournament to list your decks.' )
            return
        else:
            tourn = [ name for name in futureGuildTournaments( ctx.message.guild.name ) ][0]
    if not tourn in currentTournaments or currentTournaments[tourn].hostGuildName != ctx.message.guild.name:
        await ctx.send( f'{ctx.message.author.mention}, there is not a tournament named "{tourn}" in this guild (server).' )
        return
    if not name in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, you need to register before you can drop from a tournament... but maybe you should try playing first.' )
        return
    
    if not name in playersToBeDropped:
        playersToBeDropped.append( name )
        await ctx.send( f'{ctx.message.author.mention}, you are listed to be dropped from the tournament. Dropping from a tournament can not be reversed. If you are sure you want to drop, re-enter this command.' )
        return
    
    currentTournaments[tourn].dropPlayer( name )
    currentTournaments[tourn].activePlayers[getUserIdent(ctx.message.author)].saveXML( f'currentTournaments/{currentTournaments[tourn].tournName}/players/{getUserIdent(ctx.message.author)}.xml' )
    await ctx.send( f'{ctx.message.author.mention}, you have been dropped from the tournament "{tourn}".' )


@bot.command(name='lfg')
async def queuePlayer( ctx, tourn = "" ):
    tourn = tourn.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't list the decks you've submitted for a tournament via private message since each tournament needs to be associated with a guild (server)." )
        return
    
    if tourn == "":
        if len( futureGuildTournaments( ctx.message.guild.name ) ) != 1:
            await ctx.send( f'{ctx.message.author.mention}, there are more than one planned tournaments for this server. Please specify a tournament to list your decks.' )
            return
        else:
            tourn = [ name for name in futureGuildTournaments( ctx.message.guild.name ) ][0]
    if not tourn in currentTournaments or currentTournaments[tourn].hostGuildName != ctx.message.guild.name:
        await ctx.send( f'{ctx.message.author.mention}, there is not a tournament named "{tourn}" in this guild (server).' )
        return
    if not ctx.message.author.display_name in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, you need to register before you can drop from a tournament... but maybe you should try playing first.' )
        return
    playerMatch = currentTournaments[tourn].activePlayers[ctx.message.author.display_name].matches[-1]
    if playerMatch.status != "certified" and ctx.message.author.display_name in playerMatch.activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, you are currently in a match that is not confirmed. Please finish your match or make sure the result is confirmed before starting a new match.' )
        return
    
    currentTournaments[tourn].addPlayerToQueue( getUserIdent(ctx.message.author) )
    currentTournaments[tourn].saveOverview( f'currentTournaments/{currentTournaments[tourn].tournName}/overview.xml' ) 
    await ctx.send( f'{ctx.message.author.mention}, you have been added to the match queue.' )


@bot.command(name='match-result')
async def matchResult( ctx, tourn = "", result = "" ):
    tourn  = tourn.strip()
    result = result.strip().lower()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't list the decks you've submitted for a tournament via private message since each tournament needs to be associated with a guild (server)." )
        return
    
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you need to specify the result of the match.' )
        return
    if result == "":
        if len( futureGuildTournaments( ctx.message.guild.name ) ) != 1:
            await ctx.send( f'{ctx.message.author.mention}, there are more than one planned tournaments for this server. Please specify a tournament to list your decks.' )
            return
        else:
            result = tourn
            tourn = [ name for name in futureGuildTournaments( ctx.message.guild.name ) ][0]
    if not tourn in currentTournaments or currentTournaments[tourn].hostGuildName != ctx.message.guild.name:
        await ctx.send( f'{ctx.message.author.mention}, there is not a tournament named "{tourn}" in this guild (server).' )
        return
    if not getUserIdent(ctx.message.author) in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, you need to register before you can drop from a tournament... but maybe you should try playing first.' )
        return

    playerMatch = currentTournaments[tourn].activePlayers[getUserIdent(ctx.message.author)].matches[-1]
    if not getUserIdent(ctx.message.author) in playerMatch.activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, you are not an active player in your latest match, so there is nothing to report.' )
        return
    if playerMatch.status == "certified":
        await ctx.send( f'{ctx.message.author.mention}, your latest match has already been certified. There is no need to report anything.' )
        return
        
    if result == "w" or result == "win" or result == "winner":
        currentTournaments[tourn].recordMatchWin( getUserIdent(ctx.message.author) )
        await ctx.send( f'{currentTournaments[tourn].activePlayers[getUserIdent(ctx.message.author)].matches[-1].matchMention}, {ctx.message.author.mention} has been record as the winner of your match. Please confirm the result.' )
    elif result == "d" or result == "draw":
        currentTournament[tourn].recordMatchDraw( getUserIdent(ctx.message.author) )
        await ctx.send( f'{currentTournaments[tourn].activePlayers[getUserIdent(ctx.message.author)].matches[-1].matchMention}, the result of your match was recorded as a draw by {ctx.message.author.mention}. Please confirm the result.' )
    elif result == "l" or result == "loss" or result == "loser":
        currentTournament[tourn].playerMatchDrop( getUserIdent(ctx.message.author) )
        await ctx.send( f'{ctx.message.author.mention}, you have been dropped from your match. You will not be able to start a new match until this match finishes, but you will not need to confirm the result.' )
    else:
        await ctx.send( f'{ctx.message.author.mention}, you have provided an incorrect result. The options for "win", "loss", and "draw". Please re-enter the correct result.' )


@bot.command(name='confirm-result')
async def confirmMatchResult( ctx, tourn = "" ):
    tourn  = tourn.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't list the decks you've submitted for a tournament via private message since each tournament needs to be associated with a guild (server)." )
        return
    
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you need to specify the result of the match.' )
        return
    if result == "":
        if len( futureGuildTournaments( ctx.message.guild.name ) ) != 1:
            await ctx.send( f'{ctx.message.author.mention}, there are more than one planned tournaments for this server. Please specify a tournament to list your decks.' )
            return
        else:
            tourn = [ name for name in futureGuildTournaments( ctx.message.guild.name ) ][0]
    if not tourn in currentTournaments or currentTournaments[tourn].hostGuildName != ctx.message.guild.name:
        await ctx.send( f'{ctx.message.author.mention}, there is not a tournament named "{tourn}" in this guild (server).' )
        return
    if not getUserIdent(ctx.message.author) in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, you are not registered for this tournament.' )
        return

    playerMatch = currentTournaments[tourn].activePlayers[getUserIdent(ctx.message.author)].matches[-1]
    if not getUserIdent(ctx.message.author) in playerMatch.activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, you are not an active player in your latest match, so there is nothing to report.' )
        return
    if playerMatch.status == "certified":
        await ctx.send( f'{ctx.message.author.mention}, your latest match has already been certified. There is no need to report anything.' )
        return
    
    currentTournaments[tourn].playerCertifyResult( getUserIdent(ctx.message.author) )
    

    
"""
Future commands:

@bot.command(name='standings')
async def standings( ctx, name = "" ):

"""






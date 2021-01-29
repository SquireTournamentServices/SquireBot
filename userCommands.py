import os
import shutil
import random

from discord.ext import commands
from dotenv import load_dotenv


from baseBot import *
from Tournament import *



@bot.command(name='list-tournaments')
async def listTournaments( ctx ):
    if await isPrivateMessage( ctx ): return
    
    tourns = currentGuildTournaments( ctx.message.guild.name )
    if len( tourns ) == 0:
        await ctx.send( f'{ctx.message.author.mention}, there are no tournaments currently planned for this server.' )
        return
    
    newLine = "\n\t- "
    await ctx.send( f'{ctx.message.author.mention}, the following tournaments for this server are planned but have not been started:{newLine}{newLine.join(tourns)}' )


@bot.command(name='register')
async def registerPlayer( ctx, tourn = "" ):
    print( discord.utils.get( ctx.guild.categories, name="Matches" ) )
    tourn = tourn.strip()
    if await isPrivateMessage( ctx ): return

    if tourn == "":
        if len( currentGuildTournaments( ctx.message.guild.name ) ) > 1:
            await ctx.send( f'{ctx.message.author.mention}, there are more than one planned tournaments for this server. Please specify what tournament you want to register for.' )
            return
        elif len( currentGuildTournaments( ctx.message.guild.name ) ) < 1:
            await ctx.send( f'{ctx.message.author.mention}, there are no planned tournaments for this server. If you think this is an error, contact tournament staff.' )
            return
        else:
            tourn = [ name for name in currentGuildTournaments( ctx.message.guild.name ) ][0]
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if not currentTournaments[tourn].regOpen:
        await ctx.send( f'{ctx.message.author.mention}, registration for {tourn} is closed. Please contact tournament staff if you think this is an error.' )
        return

    userIdent = getUserIdent( ctx.message.author )
    if userIdent in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, it appears that you are already registered for the tournament named "{tourn}". Best of luck and long my you reign!!' )
        return

    await ctx.message.author.add_roles( currentTournaments[tourn].role )
    currentTournaments[tourn].addPlayer( ctx.message.author )
    currentTournaments[tourn].activePlayers[userIdent].saveXML( f'currentTournaments/{tourn}/players/{userIdent}.xml' )
    await ctx.send( f'{ctx.message.author.mention}, you have been added to the tournament named "{tourn}" in this server!' )


@bot.command(name='cockatrice-name')
async def addTriceName( ctx, tourn = "", name = "" ):
    tourn = tourn.strip()
    name  = name.strip()
    if await isPrivateMessage( ctx ): return

    if tourn == "" and name == "":
        await ctx.send( "You did not provide enough information. You need to at least specify your Cockatrice username." )
        return
    if name == "":
        name = tourn
        tourn = ""
    if tourn == "":
        if len( currentGuildTournaments( ctx.message.guild.name ) ) > 1:
            await ctx.send( f'{ctx.message.author.mention}, there are more than one planned tournaments for this server. Please specify what tournament you are playing in.' )
            return
        elif len( currentGuildTournaments( ctx.message.guild.name ) ) < 1:
            await ctx.send( f'{ctx.message.author.mention}, there are no planned tournaments for this server. If you think this is an error, contact tournament staff.' )
            return
        else:
            tourn = [ name for name in currentGuildTournaments( ctx.message.guild.name ) ][0]

    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    
    userIdent = getUserIdent( ctx.message.author )
    if not userIdent in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, it appears that you are not registered for the tournament named "{tourn}". Please register before adding a Cockatrice username.' )
        return
    
    currentTournaments[tourn].activePlayers[userIdent].triceName = name
    currentTournaments[tourn].activePlayers[userIdent].saveXML( f'currentTournaments/{tourn}/players/{userIdent}.xml' )
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

    if not await checkTournExists( tourn, ctx ): return

    userIdent = getUserIdent( ctx.message.author )
    if not userIdent in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, you need to register before you can submit a decklist. Please use the register command to do so.' )
        return
    if not currentTournaments[tourn].regOpen:
        await ctx.send( f'{ctx.message.author.mention}, it appears that registration for this tournament is already closed. If you think this an error, talk to a tournament admin.' )
        return
    
    currentTournaments[tourn].activePlayers[userIdent].addDeck( ident, decklist )
    currentTournaments[tourn].activePlayers[userIdent].saveXML( f'currentTournaments/{tourn}/players/{userIdent}.xml' )
    deckHash = str(currentTournaments[tourn].activePlayers[userIdent].decks[ident].deckHash)
    await ctx.send( f'{ctx.message.author.mention}, your decklist has been submitted. Your deck hash is "{deckHash}". Please make sure this matches your deck hash in Cocktrice.' )
    if not await isPrivateMessage( ctx, False ):
        await ctx.send( f'{ctx.message.author.mention}, for future reference, you can submit your decklist via private message so that you do not have to publicly post your decklist.' )


@bot.command(name='remove-deck')
async def removeDecklist( ctx, tourn = "", ident = "" ):
    tourn = tourn.strip()
    ident = ident.strip()
    if await isPrivateMessage( ctx ): return

    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provided enough information. Please provide either your deckname or deck hash to remove your deck.' )
        return
    if ident == "":
        tourns = currentGuildTournaments( ctx.message.guild.name )
        if len( tourns ) > 1:
            await ctx.send( f'{ctx.message.author.mention}, there are more than one planned tournaments for this server. Please specify what tournament you are playing in.' )
            return
        elif len( tourns ) < 1:
            await ctx.send( f'{ctx.message.author.mention}, there are no planned tournaments for this server. If you think this is an error, contact tournament staff.' )
            return
        else:
            ident = tourn
            tourn = [ name for name in tourns ][0]

    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    
    userIdent = getUserIdent( ctx.message.author )
    if not userIdent in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, you need to register before managing your decklists. Please you the register command to do so.' )
        return
    
    deckName = ""
    if ident in currentTournaments[tourn].activePlayers[userIdent].decks:
        deckName = ident
    # Is the second argument in the player's deckhashes? Yes, then deckName will equal the name of the deck that corresponds to that hash.
    for deck in currentTournaments[tourn].activePlayers[userIdent].decks:
        if ident == currentTournaments[tourn].activePlayers[userIdent].decks[deck].deckHash:
            deckName = deck 
            break
    if deckName == "":
        await ctx.send( f'{ctx.message.author.mention}, it appears that you do not have a deck whose name nor hash is "{ident}" registered for tourn.' )
        return
    
    del( currentTournaments[tourn].activePlayers[userIdent].decks[deckName] )
    currentTournaments[tourn].activePlayers[userIdent].saveXML( f'currentTournaments/{tourn}/players/{userIdent}.xml' )
    await ctx.send( f'{ctx.message.author.mention}, your decklist whose name or deck hash was "{ident}" has been deleted.' )


@bot.command(name='list-decks')
async def listDecklists( ctx, tourn = "" ):
    tourn = tourn.strip()
    if await isPrivateMessage( ctx ): return

    if tourn == "":
        tourns = currentGuildTournaments( ctx.message.guild.name )
        if len( tourns ) > 1:
            await ctx.send( f'{ctx.message.author.mention}, there are more than one planned tournaments for this server. Please specify what tournament you are playing in.' )
            return
        elif len( tourns ) < 1:
            await ctx.send( f'{ctx.message.author.mention}, there are no planned tournaments for this server. If you think this is an error, contact tournament staff.' )
            return
        else:
            tourn = [ name for name in tourns ][0]

    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    
    userIdent = getUserIdent( ctx.message.author )
    if not userIdent in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, you need to register before managing your decklists. Please you the register command to do so.' )
        return

    if len( currentTournaments[tourn].activePlayers[userIdent].decks ) == 0:
        await ctx.send( f'{ctx.message.author.mention}, you have not registered any decks for {tourn}.' )
        return
    
    digest = [ f'{deck}:\t{currentTournaments[tourn].activePlayers[userIdent].decks[deck].deckHash}' for deck in currentTournaments[tourn].activePlayers[userIdent].decks ]
    
    newLine = "\n\t- "
    await ctx.send( f'{ctx.message.author.mention}, here are the decks that you currently have registered:{newLine}{newLine.join( digest )}' )
    

@bot.command(name='drop-tournament')
async def dropTournament( ctx, tourn = "" ):
    tourn = tourn.strip()
    if await isPrivateMessage( ctx ): return
    
    if tourn == "":
        tourns = currentGuildTournaments( ctx.message.guild.name )
        if len( tourns ) > 1:
            await ctx.send( f'{ctx.message.author.mention}, there are more than one planned tournaments for this server. Please specify what tournament you are playing in.' )
            return
        elif len( tourns ) < 1:
            await ctx.send( f'{ctx.message.author.mention}, there are no planned tournaments for this server. If you think this is an error, contact tournament staff.' )
            return
        else:
            tourn = [ name for name in tourns ][0]
    
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return

    userIdent = getUserIdent(ctx.message.author) 
    if not userIdent in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, you need to register before you can drop from a tournament... but maybe you should try playing first.' )
        return
    
    if not userIdent in playersToBeDropped:
        playersToBeDropped.append( userIdent )
        await ctx.send( f'{ctx.message.author.mention}, you are going to be dropped from the tournament. Dropping from a tournament can not be reversed. If you are sure you want to drop, re-enter this command.' )
        return
    
    await currentTournaments[tourn].dropPlayer( userIdent )
    currentTournaments[tourn].droppedPlayers[userIdent].saveXML( f'currentTournaments/{tourn}/players/{userIdent}.xml' )
    await ctx.send( f'{ctx.message.author.mention}, you have been dropped from the tournament "{tourn}".' )


@bot.command(name='lfg')
async def queuePlayer( ctx, tourn = "" ):
    tourn = tourn.strip()
    if await isPrivateMessage( ctx ): return
    
    if tourn == "":
        tourns = currentGuildTournaments( ctx.message.guild.name )
        if len( tourns ) > 1:
            await ctx.send( f'{ctx.message.author.mention}, there are more than one planned tournaments for this server. Please specify what tournament you are playing in.' )
            return
        elif len( tourns ) < 1:
            await ctx.send( f'{ctx.message.author.mention}, there are no planned tournaments for this server. If you think this is an error, contact tournament staff.' )
            return
        else:
            tourn = [ name for name in tourns ][0]

    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return

    if not currentTournaments[tourn].isActive():
        await ctx.send( f'{ctx.message.author.mention}, the tournament "{tourn}" has not started yet. Please wait until the admin starts the tournament.' )
        return

    userIdent = getUserIdent( ctx.message.author )
    if not userIdent in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, you need to register before you can drop from a tournament... but maybe you should try playing first.' )
        return

    if currentTournaments[tourn].activePlayers[userIdent].hasOpenMatch( ):
        await ctx.send( f'{ctx.message.author.mention}, you are currently in a match that is not confirmed. Please finish your match or make sure the result is confirmed before starting a new match.' )
        return
    
    await currentTournaments[tourn].addPlayerToQueue( userIdent )
    currentTournaments[tourn].saveOverview( f'currentTournaments/{tourn}/overview.xml' ) 
    currentTournaments[tourn].saveMatches( f'currentTournaments/{tourn}/' ) 
    await ctx.send( f'{ctx.message.author.mention}, you have been added to the match queue.' )


@bot.command(name='match-result')
async def matchResult( ctx, tourn = "", result = "" ):
    tourn  = tourn.strip()
    result = result.strip().lower()
    if await isPrivateMessage( ctx ): return
    
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you need to specify the result of the match.' )
        return

    if result == "":
        tourns = currentGuildTournaments( ctx.message.guild.name )
        if len( tourns ) > 1:
            await ctx.send( f'{ctx.message.author.mention}, there are more than one planned tournaments for this server. Please specify what tournament you are playing in.' )
            return
        elif len( tourns ) < 1:
            await ctx.send( f'{ctx.message.author.mention}, there are no planned tournaments for this server. If you think this is an error, contact tournament staff.' )
            return
        else:
            result = tourn
            tourn = [ name for name in tourns ][0]

    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
        
    userIdent = getUserIdent( ctx.message.author )
    if not userIdent in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, you are not an active player in {tourn}. As such, you can not record match results.' )
        return

    if not currentTournaments[tourn].activePlayers[userIdent].hasOpenMatch( ):
        await ctx.send( f'{ctx.message.author.mention}, you are not an active player in a match, so there is nothing to report.' )
        return
    
    playerMatch = currentTournaments[tourn].activePlayers[userIdent].findOpenMatch()
    if result == "w" or result == "win" or result == "winner":
        await ctx.send( f'{playerMatch.role.mention}, {ctx.message.author.mention} has been record as the winner of your match. Please confirm the result.' )
        await currentTournaments[tourn].recordMatchWin( userIdent )
    elif result == "d" or result == "draw":
        await ctx.send( f'{playerMatch.role.mention}, the result of your match was recorded as a draw by {ctx.message.author.mention}. Please confirm the result.' )
        await currentTournaments[tourn].recordMatchDraw( userIdent )
    elif result == "l" or result == "loss" or result == "loser":
        await ctx.send( f'{ctx.message.author.mention}, you have been dropped from your match. You will not be able to start a new match until this match finishes, but you will not need to confirm the result.' )
        await currentTournaments[tourn].playerMatchDrop( userIdent )
    else:
        await ctx.send( f'{ctx.message.author.mention}, you have provided an incorrect result. The options are "win", "loss", and "draw". Please re-enter the correct result.' )
        return
    
    playerMatch.saveXML( f'currentTournaments/{tourn}/matches/match_{playerMatch.matchNumber}.xml' )


@bot.command(name='confirm-result')
async def confirmMatchResult( ctx, tourn = "" ):
    tourn  = tourn.strip()
    if await isPrivateMessage( ctx ): return
    
    if tourn == "":
        tourns = currentGuildTournaments( ctx.message.guild.name )
        if len( tourns ) > 1:
            await ctx.send( f'{ctx.message.author.mention}, there are more than one planned tournaments for this server. Please specify what tournament you are playing in.' )
            return
        elif len( tourns ) < 1:
            await ctx.send( f'{ctx.message.author.mention}, there are no planned tournaments for this server. If you think this is an error, contact tournament staff.' )
            return
        else:
            tourn = [ name for name in tourns ][0]

    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return

    userIdent = getUserIdent( ctx.message.author )
    if not userIdent in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, you are not registered for this tournament, so you can not confirm the result of a match.' )
        return

    if not currentTournaments[tourn].activePlayers[userIdent].hasOpenMatch( ):
        await ctx.send( f'{ctx.message.author.mention}, you are not an active player in any match, so there is nothing to confirm.' )
        return
    
    playerMatch = currentTournaments[tourn].activePlayers[userIdent].findOpenMatch( )
    if userIdent in playerMatch.confirmedPlayers:
        await ctx.send( f'{ctx.message.author.mention}, you have already confirmed the result of your open match. The rest of your match still needs to confirm.' )
        return
    
    await currentTournaments[tourn].playerCertifyResult( userIdent )
    playerMatch.saveXML( f'currentTournaments/{tourn}/matches/match_{playerMatch.matchNumber}.xml' )
    await ctx.send( f'{ctx.message.author.mention}, your confirmation of your match has been recorded.' )
    

@bot.command(name='standings')
async def standings( ctx, tourn = "" ):
    tourn  = tourn.strip()
    if await isPrivateMessage( ctx ): return
    
    if tourn == "":
        tourns = currentGuildTournaments( ctx.message.guild.name )
        if len( tourns ) > 1:
            await ctx.send( f'{ctx.message.author.mention}, there are more than one planned tournaments for this server. Please specify what tournament you are playing in.' )
            return
        elif len( tourns ) < 1:
            await ctx.send( f'{ctx.message.author.mention}, there are no planned tournaments for this server. If you think this is an error, contact tournament staff.' )
            return
        else:
            tourn = [ name for name in tourns ][0]

    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    
    await ctx.send( f'{ctx.message.author.mention}, the starting for {tourn} are:' )
    for msg in splitMessage( currentTournaments[tourn].getStandings() ):
        await ctx.send( msg )







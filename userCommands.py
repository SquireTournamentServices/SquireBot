import os
import shutil
import random

from discord.ext import commands
from dotenv import load_dotenv


from baseBot import *
from Tournament import *


def createStandingsEmbeds( places: List[str], names: List[str], points: List[str], GWP: List[str], OWP: List[str] ):
    length = len(places)
    limit  = 1024
    if   len(names ) < length: length = len(names )
    elif len(points) < length: length = len(points)
    elif len(GWP   ) < length: length = len(GWP   )
    elif len(OWP   ) < length: length = len(OWP   )

    digest  = [ ]
    headers = [ "Name:", "Points & Win Percent:", "Opp. WP" ]
    lengths = [ len(s) for s in headers ]
    values  = [ "", "", "" ]
    
    for i in range(length):
        line = [ f'{places[i]}) {names[i]}\n', f'{points[i]},\t{trunk(GWP[i])}%\n', f'{trunk(OWP[i])}%\n' ]
        line_lengths = [ len(s) for s in line ]
        if (lengths[0] + line_lengths[0] <= limit) and (lengths[1] + line_lengths[1] <= limit) and (lengths[2] + line_lengths[2] <= limit):
            values  = [ values[i] + line[i] for i in range(len(values)) ]
            lengths = [ lengths[i] + line_lengths[i] for i in range(len(lengths)) ]
        else:
            digest.append( discord.Embed() )
            if len(digest) > 0:
                for i in range(len(headers)):
                    digest[-1].add_field( name="\u200b", value=values[i] )
            else:
                for i in range(len(headers)):
                    digest[-1].add_field( name=headers[i], value=values[i] )
            values = [ "", "", "" ]

    if len(digest) == 0:
        digest.append( discord.Embed() )
        for i in range(len(headers)):
            digest[-1].add_field( name=headers[i], value=values[i] )
    
    return digest
        


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
    if not tournaments[tourn].regOpen:
        await ctx.send( f'{ctx.message.author.mention}, registeration for {tourn} is closed. If you believe this is an error, contact tournament admin.' )
        return

    re = False # Is the player re-enrolling?
    userIdent = getUserIdent( ctx.message.author )
    if await hasRegistered( tourn, userIdent, ctx, False ) :
        if await isActivePlayer( tourn, userIdent, ctx, False ):
            await ctx.send( f'{ctx.message.author.mention}, you are already an active player in {tourn}. There is no need to re-enroll.' )
            return
        re = True

    await ctx.message.author.add_roles( tournaments[tourn].role )
    await tournaments[tourn].addPlayer( ctx.message.author )
    tournaments[tourn].players[userIdent].saveXML( )
    if re:
        await ctx.send( f'{ctx.message.author.mention}, you have been re-enrolled in {tourn}!' )
    else:
        await ctx.send( f'{ctx.message.author.mention}, you have been added to {tourn}!' )


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
    if not await hasRegistered( tourn, userIdent, ctx ): return
    if not await isActivePlayer( tourn, userIdent, ctx ): return
    
    tournaments[tourn].players[userIdent].triceName = name
    tournaments[tourn].players[userIdent].saveXML( )
    await ctx.send( f'{ctx.message.author.mention}, "{name}" was added as your Cocktrice username.' )


@bot.command(name='add-deck')
async def submitDecklist( ctx, tourn = "", ident = "", decklist = "" ):
    tourn = tourn.strip()
    ident = ident.strip()
    decklist = decklist.strip()

    if tourn == "" or ident == "" or decklist == "":
        await ctx.send( f'{ctx.message.author.mention}, it appears that you did not provide enough information. You need to specify a tournament name, a deckname, and then a decklist.' )
        return

    if not await checkTournExists( tourn, ctx ): return

    userIdent = getUserIdent( ctx.message.author )
    if not await hasRegistered( tourn, userIdent, ctx ): return
    if not await isActivePlayer( tourn, userIdent, ctx ): return
    if not tournaments[tourn].regOpen:
        await ctx.send( f'{ctx.message.author.mention}, deck registeration for {tourn} is closed. If you believe this is an error, contact tournament admin.' )
        return
    
    tournaments[tourn].players[userIdent].addDeck( ident, decklist )
    tournaments[tourn].players[userIdent].saveXML( )
    deckHash = str( tournaments[tourn].players[userIdent].decks[ident].deckHash)
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
    if not await hasRegistered( tourn, userIdent, ctx ): return
    if not await isActivePlayer( tourn, userIdent, ctx ): return
    
    deckName = tournaments[tourn].players[userIdent].getDeckIdent( ident )
    if deckName == "":
        await ctx.send( f'{ctx.message.author.mention}, it appears that you do not have a deck whose name nor hash is "{ident}" registered for tourn.' )
        return
    
    del( tournaments[tourn].players[userIdent].decks[deckName] )
    tournaments[tourn].players[userIdent].saveXML( )
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
    if not await hasRegistered( tourn, userIdent, ctx ): return
    if not await isActivePlayer( tourn, userIdent, ctx ): return

    if len( tournaments[tourn].players[userIdent].decks ) == 0:
        await ctx.send( f'{ctx.message.author.mention}, you have not registered any decks for {tourn}.' )
        return
    
    names  = [ deck for deck in tournaments[tourn].players[userIdent].decks ]
    hashes = [ str(deck.deckHash) for deck in tournaments[tourn].players[userIdent].decks.values() ]
    embed = discord.Embed( )
    embed.add_field( name="Deck Names", value="\n".join(names) )
    embed.add_field( name="Deck Hashes", value="\n".join(hashes) )
    
    await ctx.send( content=f'{ctx.message.author.mention}, here are the decks that you currently have registered:', embed=embed )
    

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
    if not await hasRegistered( tourn, userIdent, ctx ): return
    if not await isActivePlayer( tourn, userIdent, ctx ): return
    
    if not userIdent in playersToBeDropped:
        playersToBeDropped.append( userIdent )
        await ctx.send( f'{ctx.message.author.mention}, you are going to be dropped from {tourn}. Dropping from a tournament can not be reversed. If you are sure you want to drop, re-enter this command.' )
        return
    
    await tournaments[tourn].dropPlayer( userIdent )
    tournaments[tourn].players[userIdent].saveXML( )
    await ctx.send( f'{ctx.message.author.mention}, you have been dropped from {tourn}.' )


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

    if not tournaments[tourn].isActive():
        await ctx.send( f'{ctx.message.author.mention}, the tournament "{tourn}" has not started yet. Please wait until the admin starts the tournament.' )
        return

    userIdent = getUserIdent( ctx.message.author )
    if not await hasRegistered( tourn, userIdent, ctx ): return
    if not await isActivePlayer( tourn, userIdent, ctx ): return
    if not await isTournRunning( tourn, ctx ): return
    
    for lvl in tournaments[tourn].queue:
        for plyr in lvl:
            if plyr.name == userIdent:
                await ctx.send( f'{ctx.message.author.mention}, you are already in the queue. You will be paired for a match when more people join the queue.' )
                return
    
    tournaments[tourn].addPlayerToQueue( userIdent )
    tournaments[tourn].saveOverview( )
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
    if not await hasRegistered( tourn, userIdent, ctx ): return
    if not await isActivePlayer( tourn, userIdent, ctx ): return
    if not await hasOpenMatch( tourn, userIdent, ctx ): return
    
    playerMatch = tournaments[tourn].players[userIdent].findOpenMatch()
    if result == "w" or result == "win" or result == "winner":
        await ctx.send( f'{playerMatch.role.mention}, {ctx.message.author.mention} has been record as the winner of your match. Please confirm the result.' )
        await tournaments[tourn].recordMatchWin( userIdent )
    elif result == "d" or result == "draw":
        await ctx.send( f'{playerMatch.role.mention}, the result of your match was recorded as a draw by {ctx.message.author.mention}. Please confirm the result.' )
        await tournaments[tourn].recordMatchDraw( userIdent )
    elif result == "l" or result == "loss" or result == "loser":
        await ctx.send( f'{ctx.message.author.mention}, you have been dropped from your match. You will not be able to start a new match until this match finishes, but you will not need to confirm the result.' )
        await tournaments[tourn].playerMatchDrop( userIdent )
    else:
        await ctx.send( f'{ctx.message.author.mention}, you have provided an incorrect result. The options are "win", "loss", and "draw". Please re-enter the correct result.' )
        return
    
    playerMatch.saveXML( )


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
    if not await hasRegistered( tourn, userIdent, ctx ): return
    if not await isActivePlayer( tourn, userIdent, ctx ): return
    if not await hasOpenMatch( tourn, userIdent, ctx ): return
    
    playerMatch = tournaments[tourn].players[userIdent].findOpenMatch( )
    if userIdent in playerMatch.confirmedPlayers:
        await ctx.send( f'{ctx.message.author.mention}, you have already confirmed the result of your open match. The rest of your match still needs to confirm.' )
        return
    
    await tournaments[tourn].playerCertifyResult( userIdent )
    playerMatch.saveXML( )
    await ctx.send( f'{ctx.message.author.mention}, your confirmation for your match has been recorded.' )
    

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
    
    standings = tournaments[tourn].getStandings( )
    embeds = createStandingsEmbeds( standings[0], standings[1], standings[2], standings[3], standings[4] )
    await ctx.send( content=f'{ctx.message.author.mention}, the standings for {tourn} are:', embed=embeds[0] )
    for bed in embeds[1:]:
        await ctx.send( embed=bed )







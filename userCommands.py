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
        tourns = currentGuildTournaments( ctx.message.guild.name )
        if len( tourns ) > 1:
            await ctx.send( f'{ctx.message.author.mention}, there are multiple tournaments planned in this server. Please specify which tournament you would like to register for.' )
            return
        elif len( tourns ) < 1:
            await ctx.send( f'{ctx.message.author.mention}, there are no planned tournaments for this server. If you think this is an error, contact tournament staff.' )
            return
        else:
            tourn = [ name for name in tourns ][0]

    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if not tournaments[tourn].regOpen:
        await ctx.send( f'{ctx.message.author.mention}, registration for {tourn} is closed. If you believe this is an error, contact tournament staff.' )
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
        await ctx.send( f'{ctx.message.author.mention}, you have been enrolled in {tourn}!' )


@bot.command(name='cockatrice-name')
async def addTriceName( ctx, tourn = "", name = "" ):
    tourn = tourn.strip()
    name  = name.strip()
    
    if await isPrivateMessage( ctx ): return

    if tourn == "" and name == "":
        await ctx.send( "{ctx.message.author.mention}, not enough information provided: You must include your Cockatrice username." )
        return
    if name == "":
        name = tourn
        tourn = ""
    if tourn == "":
        tourns = currentGuildTournaments( ctx.message.guild.name )
        if len( tourns ) > 1:
            await ctx.send( f'{ctx.message.author.mention}, there are multiple tournaments planned in this server. Please specify which tournament you are playing in.' )
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
    
    tournaments[tourn].players[userIdent].triceName = name
    tournaments[tourn].players[userIdent].saveXML( )
    await ctx.send( f'{ctx.message.author.mention}, "{name}" was added as your Cockatrice username.' )


@bot.command(name='add-deck')
async def submitDecklist( ctx, tourn = "", ident = "", decklist = "" ):
    tourn = tourn.strip()
    ident = ident.strip()
    decklist = decklist.strip()

    if tourn == "" or ident == "" or decklist == "":
        await ctx.send( f'{ctx.message.author.mention}, not enough information provided: You must include the tournament name, the deckname, and your decklist.' )
        return

    if not await checkTournExists( tourn, ctx ): return

    userIdent = getUserIdent( ctx.message.author )
    if not await hasRegistered( tourn, userIdent, ctx ): return
    if not await isActivePlayer( tourn, userIdent, ctx ): return
    if not tournaments[tourn].regOpen:
        await ctx.send( f'{ctx.message.author.mention}, registration for {tourn} is closed. If you believe this is an error, contact tournament staff.' )
        return
    
    tournaments[tourn].players[userIdent].addDeck( ident, decklist )
    tournaments[tourn].players[userIdent].saveXML( )
    deckHash = str( tournaments[tourn].players[userIdent].decks[ident].deckHash )
    await ctx.send( f'{ctx.message.author.mention}, your deck has been successfully registered. Your deck hash is "{deckHash}"; this must match your deck hash in Cockatrice. If these hashes do not match, refer to the FAQ or contact tournament staff.' )
    if not await isPrivateMessage( ctx, False ):
        await ctx.send( f'{ctx.message.author.mention}, for future reference, you can submit your decklist via private message so that you do not have to publicly post your decklist.' )


@bot.command(name='remove-deck')
async def removeDecklist( ctx, tourn = "", ident = "" ):
    tourn = tourn.strip()
    ident = ident.strip()
    if await isPrivateMessage( ctx ): return

    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, not enough information provided: Please provide your deckname or deck hash to remove your deck.' )
        return
    if ident == "":
        tourns = currentGuildTournaments( ctx.message.guild.name )
        if len( tourns ) > 1:
            await ctx.send( f'{ctx.message.author.mention}, there are multiple tournaments planned in this server. Please specify which tournament you are playing in.' )
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
        decks = tournaments[tourn].players[userIdent].decks
        if len( decks ) < 1:
            await ctx.send( f'{ctx.message.author.mention}, you do not have any decks registered for {tourn}.' )
        else:
            embed = discord.Embed( )
            embed.add_field( name="Deck Names", value="\n".join( decks) )
            embed.add_field( name="Deck Hashes", value="\n".join( [ str(d.deckHash) for d in decks.values() ] ) )
            await ctx.send( content=f'{ctx.message.author.mention}, invalid deck name/hash: You have not registered "{ident}". Here are your registered decks:', embed=embed )
        return

    if hasCommandWaiting( ctx, userIdent ):
        del( commandsToConfirm[userIdent] )

    commandsToConfirm[userIdent] = ( getTime(), 30, tournaments[tourn].players[userIdent].removeDeckCoro( deckName ) )
    await ctx.send( f'{ctx.message.author.mention}, in order to remove your deck, you need to confirm your request. Are you sure you want to remove it? (!yes/!no)' )
    

@bot.command(name='list-decks')
async def listDecklists( ctx, tourn = "" ):
    tourn = tourn.strip()
    if await isPrivateMessage( ctx ): return

    if tourn == "":
        tourns = currentGuildTournaments( ctx.message.guild.name )
        if len( tourns ) > 1:
            await ctx.send( f'{ctx.message.author.mention}, there are multiple tournaments planned in this server. Please specify which tournament you are playing in.' )
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
    

@bot.command(name='drop')
async def dropTournament( ctx, tourn = "" ):
    tourn = tourn.strip()
    if await isPrivateMessage( ctx ): return
    
    if tourn == "":
        tourns = currentGuildTournaments( ctx.message.guild.name )
        if len( tourns ) > 1:
            await ctx.send( f'{ctx.message.author.mention}, there are multiple tournaments planned in this server. Please specify which tournament you are playing in.' )
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
    
    if hasCommandWaiting( ctx, userIdent ):
        del( commandsToConfirm[userIdent] )

    commandsToConfirm[userIdent] = (getTime(), 30, tournaments[tourn].dropPlayer( userIdent ) )
    await ctx.send( f'{ctx.message.author.mention}, in order to drop from {tourn}, you need to confirm your request. Are you sure you want to drop? (!yes/!no)' )


@bot.command(name='lfg')
async def queuePlayer( ctx, tourn = "" ):
    tourn = tourn.strip()
    if await isPrivateMessage( ctx ): return
    
    if tourn == "":
        tourns = currentGuildTournaments( ctx.message.guild.name )
        if len( tourns ) > 1:
            await ctx.send( f'{ctx.message.author.mention}, there are multiple tournaments planned in this server. Please specify which tournament you are playing in.' )
            return
        elif len( tourns ) < 1:
            await ctx.send( f'{ctx.message.author.mention}, there are no planned tournaments for this server. If you think this is an error, contact tournament staff.' )
            return
        else:
            tourn = [ name for name in tourns ][0]

    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return

    if not await isTournRunning( tourn, ctx ): return

    userIdent = getUserIdent( ctx.message.author )
    if not await hasRegistered( tourn, userIdent, ctx ): return
    if not await isActivePlayer( tourn, userIdent, ctx ): return
    
    for lvl in tournaments[tourn].queue:
        for plyr in lvl:
            if plyr.name == userIdent:
                await ctx.send( f'{ctx.message.author.mention}, you are already in the queue. You will be paired for a match when more people join the queue.' )
                return
    
    tournaments[tourn].addPlayerToQueue( userIdent )
    tournaments[tourn].saveOverview( )
    await ctx.send( f'{ctx.message.author.mention}, you have been added to the queue.' )


@bot.command(name='match-result')
async def matchResult( ctx, tourn = "", result = "" ):
    tourn  = tourn.strip()
    result = result.strip().lower()
    if await isPrivateMessage( ctx ): return
    
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you must specify the result of the match (win/draw/loss).' )
        return

    if result == "":
        tourns = currentGuildTournaments( ctx.message.guild.name )
        if len( tourns ) > 1:
            await ctx.send( f'{ctx.message.author.mention}, there are multiple tournaments planned in this server. Please specify which tournament you are playing in.' )
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
        await ctx.send( f'{ctx.message.author.mention} has recorded themself as the winner of match #{playerMatch.matchNumber}. {playerMatch.role.mention}, please confirm with "!confirm-result".' )
        await tournaments[tourn].recordMatchWin( userIdent )
    elif result == "d" or result == "draw":
        await ctx.send( f'{ctx.message.author.mention} has recorded the result of match #{playerMatch.matchNumber} as a draw. {playerMatch.role.mention}, please confirm with "!confirm-result".' )
        await tournaments[tourn].recordMatchDraw( userIdent )
    elif result == "l" or result == "loss" or result == "lose" or result == "loser":
        await ctx.send( f'{ctx.message.author.mention}, you have been dropped from your match. You will not be able to start a new match until match #{playerMatch.matchNumber} finishes. You will not need to confirm the result of the match.' )
        await tournaments[tourn].playerMatchDrop( userIdent )
    else:
        await ctx.send( f'{ctx.message.author.mention}, invalid result: Use "win", "loss", or "draw". Please re-enter.' )
        return
    
    playerMatch.saveXML( )


@bot.command(name='confirm-result')
async def confirmMatchResult( ctx, tourn = "" ):
    tourn  = tourn.strip()
    if await isPrivateMessage( ctx ): return
    
    if tourn == "":
        tourns = currentGuildTournaments( ctx.message.guild.name )
        if len( tourns ) > 1:
            await ctx.send( f'{ctx.message.author.mention}, there are multiple tournaments planned in this server. Please specify which tournament you are playing in.' )
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
        await ctx.send( f'{ctx.message.author.mention}, you have already confirmed the result of match #{playerMatch.matchNumber}. Your opponents are still confirming.' )
        return
    
    await tournaments[tourn].playerCertifyResult( userIdent )
    playerMatch.saveXML( )
    await ctx.send( f'{ctx.message.author.mention}, you have confirmed the result of match #{playerMatch.matchNumber}.' )
    

@bot.command(name='standings')
async def standings( ctx, tourn = "" ):
    tourn  = tourn.strip()
    if await isPrivateMessage( ctx ): return
    if ctx.message.channel.id != int( os.getenv("STANDINGS_CHANNEL_ID" ) ):
        await ctx.send( f'{ctx.message.author.mention}, this is not the correct channel to see standings. Please go to <#{os.getenv("STANDINGS_CHANNEL_ID" )}> to see standings.' )
        return
    
    if tourn == "":
        tourns = currentGuildTournaments( ctx.message.guild.name )
        if len( tourns ) > 1:
            await ctx.send( f'{ctx.message.author.mention}, there are multiple tournaments planned in this server. Please specify which tournament you would like to see the standings of.' )
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




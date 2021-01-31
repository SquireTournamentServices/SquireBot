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
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you need to specify what you want the tournament to be called.' )
        return
    if tourn in currentTournaments:
        await ctx.send( f'{ctx.message.author.mention}, there is already a tournament call {tourn} either on this server or another. Pick a different name.' )
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
    
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn == "" or status == "":
        await ctx.send( f'{ctx.message.author.mention}, it appears that you did not give enough information. You need to first state the tournament name and then "true" or "false".' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return

    status = "True" if status.lower() == "open" else status
    status = "False" if status.lower() == "closed" else status

    currentTournaments[tourn].setRegStatus( str_to_bool(status) )
    currentTournaments[tourn].saveOverview( f'currentTournaments/{tourn}/overview.xml' )
    await ctx.send( f'{adminMention}, registeration for the "{tourn}" tournament has been {("opened" if str_to_bool(status) else "closed")} by {ctx.message.author.mention}.' ) 


@bot.command(name='start-tournament')
async def startTournament( ctx, tourn = "" ):
    tourn = tourn.strip()
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you need to specify what tournament you want to start.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if currentTournaments[tourn].tournStarted:
        await ctx.send( f'{ctx.message.author.mention}, {tourn} has already been started.' )
        return

    currentTournaments[tourn].startTourn()
    currentTournaments[tourn].saveOverview( f'currentTournaments/{tourn}/overview.xml' )
    await ctx.send( f'{adminMention}, {tourn} has been started by {ctx.message.author.mention}.' )
    

@bot.command(name='end-tournament')
async def endTournament( ctx, tourn = "" ):
    tourn = tourn.strip()
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you need to specify what tournament you want to end.' )
        return
    if not tourn in currentTournaments:
        await ctx.send( f'{ctx.message.author.mention}, there is no tournament called "{tourn}" for this server.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
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
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you need to specify what tournament you want to cancel.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
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
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn == "" or plyr == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament and player in order to add someone to a tournament.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    member = findGuildMember( ctx.guild, plyr )
    if member == "":
        await ctx.send( f'{ctx.message.author.mention}, there is not a member of this server whose name nor mention is "{plyr}".' )
        return
    userIdent = getUserIdent( member )
    
    if userIdent in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, {plyr} is already registered for {tourn}.' )
        return

    await member.add_roles( currentTournaments[tourn].role )
    currentTournaments[tourn].activePlayers[userIdent] = player( userIdent )
    currentTournaments[tourn].activePlayers[userIdent].addDiscordUser( member )
    currentTournaments[tourn].activePlayers[userIdent].saveXML( f'currentTournaments/{tourn}/players/{userIdent}.xml' )
    await currentTournaments[tourn].activePlayers[userIdent].discordUser.send( content=f'You have been registered for {tourn} on the server "{ctx.guild.name}".' )
    await ctx.send( f'{ctx.message.author.mention}, you have added {member.mention} to {tourn}!' )


@bot.command(name='admin-add-deck')
async def adminAddDeck( ctx, tourn = "", plyr = "", ident = "", decklist = "" ):
    tourn = tourn.strip()
    plyr  =  plyr.strip()
    ident = ident.strip()
    decklist = decklist.strip()
    
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn == "" or plyr == "" or ident == "" or decklist == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament, a player, a deck identifier, and a decklist in order to add a deck for someone.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    member = findPlayer( ctx.guild, tourn, plyr )
    if member == "":
        await ctx.send( f'{ctx.message.author.mention}, a player by "{plyr}" could not be found in the player role for {tourn}. Please verify that they have registered.' )
        return
    
    userIdent = getUserIdent( member )
    if not userIdent in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, a user by "{plyr}" was found in the player role, but they are not active in {tourn}. Make sure they are registered or that they have not dropped.' )
        return
    
    currentTournaments[tourn].activePlayers[userIdent].addDeck( ident, decklist )
    currentTournaments[tourn].activePlayers[userIdent].saveXML( f'currentTournaments/{tourn}/players/{userIdent}.xml' )
    deckHash = str(currentTournaments[tourn].activePlayers[userIdent].decks[ident].deckHash)
    await ctx.send( f'{ctx.message.author.mention}, decklist that you added for {plyr} has been submitted. The deck hash is "{deckHash}".' )
    await currentTournaments[tourn].activePlayers[userIdent].discordUser.send( content=f'A decklist has been submitted for {tourn} on the server {ctx.guild.name} on your behave. The identifier for the deck is "{ident}" and the deck hash is "{deckHash}". If this deck hash is incorrect or you are not expecting this, please contact tournament admin on that server.' )


@bot.command(name='admin-remove-deck')
async def adminRemoveDeck( ctx, tourn = "", plyr = "", ident = "" ):
    tourn = tourn.strip()
    plyr  =  plyr.strip()
    ident = ident.strip()

    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn == "" or plyr == "" or ident == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament, a player, a deck identifier, and a decklist in order to add a deck for someone.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    member = findPlayer( ctx.guild, tourn, plyr )
    if member == "":
        await ctx.send( f'{ctx.message.author.mention}, a player by "{plyr}" could not be found in the player role for {tourn}. Please verify that they have registered.' )
        return

    userIdent = getUserIdent( member )
    if not userIdent in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, a user by "{plyr}" was found in the player role, but they are not active in the tournament "{tourn}". Make sure they are registered or that they have not dropped.' )
        return
    
    deckName = currentTournaments[tourn].activePlayers[userIdent].getDeckIdent( ident )
    if deckName == "":
        await ctx.send( f'{ctx.message.author.mention}, it appears that {plyr} does not have a deck whose name nor hash is "{ident}" registered for {tourn}.' )
        return
    deckHash = currentTournaments[tourn].activePlayers[userIdent].decks[deckName].deckHash

    del( currentTournaments[tourn].activePlayers[userIdent].decks[deckName] )
    currentTournaments[tourn].activePlayers[userIdent].saveXML( f'currentTournaments/{currentTournaments[tourn].tournName}/players/{userIdent}.xml' )
    await ctx.send( f'{ctx.message.author.mention}, decklist that you removed from {plyr} has been processed.' )
    await currentTournaments[tourn].activePlayers[userIdent].discordUser.send( content=f'The deck has been removed from {tourn} on the server {ctx.guild.name}. The identifier was "{ident}" and the deck hash was "{deckHash}".' )


@bot.command(name='set-deck-count')
async def setDeckCount( ctx, tourn = "", count = "" ):
    tourn = tourn.strip()
    count = count.strip()
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn == "" or count == "" :
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament and a max number of decks.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    currentTournaments[tourn].deckCount = int( count )
    currentTournaments[tourn].saveOverview( f'currentTournaments/{tourn}/overview.xml' )
    await ctx.send( f'{adminMention}, the deck count for tournament called "{tourn}" has been changed to {count} by {ctx.message.author.display_name}.' )


@bot.command(name='admin-prune-decks')
async def adminPruneDecks( ctx, tourn = "" ):
    tourn = tourn.strip()
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament and a max number of decks.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    await ctx.send( f'{adminMention}, the pruning of decks is starting... now!' )
    for plyr in currentTournaments[tourn].activePlayers:
        Player = currentTournaments[tourn].activePlayers[plyr]
        deckIdents = [ ident for ident in Player.decks ]
        while len( Player.decks ) > currentTournaments[tourn].deckCount:
            del( Player.decks[deckIdents[0]] )
            await ctx.send( f'{adminMention}, the deck with identifier "{deckIdents[0]}" belonging to {Player.discordUser.display_name} has been pruned.' )
            await Player.discordUser.send( content=f'Your deck with identifier "{deckIdents[0]}" has been pruned from {tourn} on the server "{ctx.guild.name}".' )
            del( deckIdents[0] )
        Player.saveXML( f'currentTournaments/{tourn}/players/{plyr}.xml' )


@bot.command(name='admin-list-players')
async def adminListPlayers( ctx, tourn = "", num = "" ):
    tourn = tourn.strip()
    num   = num.strip().lower()
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament in order to list the players.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    if len( currentTournaments[tourn].activePlayers ) == 0:
        await ctx.send( f'{ctx.message.author.mention}, there are no players registered for the tournament {tourn}.' )
        return
    if num == "n" or num == "num" or num == "number":
        await ctx.send( f'{ctx.message.author.mention}, there are {len(currentTournaments[tourn].activePlayers)} active players in {tourn}.' )
        return
    else:
        newLine = "\n\t- "
        playerNames = [ currentTournaments[tourn].activePlayers[plyr].discordUser.display_name for plyr in currentTournaments[tourn].activePlayers ]
        await ctx.send( f'{ctx.message.author.mention}, the following are all active players registered for {tourn}:' )
        message = f'{newLine}{newLine.join(playerNames)}'
        for msg in splitMessage( message ):
            await ctx.send( msg )
    

@bot.command(name='admin-player-profile')
async def adminPlayerProfile( ctx, tourn = "", plyr = "" ):
    tourn = tourn.strip()
    plyr  = plyr.strip()
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament in order to list the players.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    member = findPlayer( ctx.guild, tourn, plyr )
    if member == "":
        await ctx.send( f'{ctx.message.author.mention}, a player by "{plyr}" could not be found in the player role "{tourn} Player". Please verify that they have registered.' )
        return

    userIdent = getUserIdent( member )
    if not userIdent in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, a user by "{plyr}" was found in the player role, but they are not active in the tournament "{tourn}". Make sure they are registered or that they have not dropped.' )
        return
    
    await ctx.send( f'{ctx.message.author.mention}, the following is the profile for the player "{plyr}":\n{currentTournaments[tourn].activePlayers[userIdent]}' )


@bot.command(name='admin-match-result')
async def adminMatchResult( ctx, tourn = "", plyr = "", mtch = "", result = "" ):
    tourn  = tourn.strip()
    plyr   = plyr.strip()
    mtch   = mtch.strip()
    result = result.strip()
    
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if not await isTournamentAdmin( ctx ):
        await ctx.send( f'{ctx.message.author.mention}, you do not have permissions to remove players from a match. Please do not do this again or {adminMention} may intervene.' )
        return
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament, match number, player, and result in order to remove a player from a match.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    member = findPlayer( ctx.guild, tourn, plyr )
    if member == "":
        await ctx.send( f'{ctx.message.author.mention}, a player by "{plyr}" could not be found in the player role "{tourn} Player". Please verify that they have registered.' )
        return
    
    userIdent = getUserIdent( member )
    if not userIdent in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, a user by "{plyr}" was found in the player role, but they are not active in the tournament "{tourn}". Make sure they are registered or that they have not dropped.' )
        return
    
    try:
        mtch = int( mtch )
    except:
        await ctx.send( f'{ctx.message.author.mention}, you did not provide a match number. Please specify a match number as a number.' )
        return
    
    if mtch > len(currentTournaments[tourn].matches):
        await ctx.send( f'{ctx.message.author.mention}, the match number that you specified is greater than the number of matches. Double check the match number.' )
        return
        
    Match = currentTournaments[tourn].activePlayers[userIdent].getMatch( mtch )
    if Match.matchNumber == -1:
        await ctx.send( f'{ctx.message.author.mention}, {member.mention} is not a player in Match #{mtch}. Double check the match number.' )
        return
        
    if result == "w" or result == "win" or result == "winner":
        message = f'{Match.role.mention}, {member.mention} has been recorded as the winner of your match by tournament admin.'
        if Match.isCertified( ):
            Match.winner = userIdent
            await currentTournaments[tourn].pairingsChannel.send( f'{message} There is no need to recertify the result of this match.' )
        else:
            msg = await Match.recordWinner( userIdent )
            if msg == "":
                await currentTournaments[tourn].pairingsChannel.send( f'{message} Please certify this result.' )
            else:
                await currentTournaments[tourn].pairingsChannel.send( msg )
    elif result == "d" or result == "draw":
        message = f'{Match.role.mention}, your match has been recorded as a draw by tournament admin.'
        if Match.isCertified( ):
            Match.winner = "This match is a draw."
            await currentTournaments[tourn].pairingsChannel.send( f'{message} There is no need to recertify the result of this match.' )
        else:
            msg  = await Match.recordWinner( "" )
            msg += await Match.confirmResult( userIdent )
            if msg == "":
                await currentTournaments[tourn].pairingsChannel.send( f'{message} Please certify this result.' )
            else:
                await currentTournaments[tourn].pairingsChannel.send( msg )
    elif result == "l" or result == "loss" or result == "loser":
        message = await Match.dropPlayer( userIdent )
        if message != "":
            await currentTournaments[tourn].pairingsChannel.send( message )
        await currentTournaments[tourn].activePlayers[userIdent].discordUser.send( content=f'You were dropped from Match #{mtch} in {tourn} on the server {ctx.guild.name}. If you believe this was an error, contact tournament admin.' )
    else:
        await ctx.send( f'{ctx.message.author.mention}, you have provided an incorrect result. The options are "win", "loss", and "draw". Please re-enter the correct result.' )
        return

    Match.saveXML( f'currentTournaments/{tourn}/matches/match_{mtch}.xml' )



@bot.command(name='admin-create-pairing')
async def adminCreatePairing( ctx, tourn = "", *plyrs ):
    tourn  = tourn.strip()
    plyrs  = [ plyr.strip() for plyr in plyrs ]
    
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament, match number, player, and result in order to remove a player from a match.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    if len(plyrs) != currentTournaments[tourn].playersPerMatch:
        await ctx.send( f'{ctx.message.author.mention}, {tourn} requires {currentTournaments[tourn].playersPerMatch} be in a match, but you specified {len(plyrs)} players.' )
        return
        
    print( plyrs )
    members = [ findPlayer( ctx.guild, tourn, plyr ) for plyr in plyrs ]
    print( members )
    if "" in members:
        await ctx.send( f'{ctx.message.author.mention}, at least one of the members that you specified is not a part of the tournament. Verify that they have the "{tourn} Player" role.' )
        return
    
    userIdents = [ getUserIdent( member ) for member in members ]
    for userIdent in userIdents:
        if not userIdent in currentTournaments[tourn].activePlayers:
            await ctx.send( f'{ctx.message.author.mention}, a user by "{member.mention}" was found in the player role, but they are not active in {tourn}. Make sure they are registered or that they have not dropped.' )
            return
    
    for ident in userIdents:
        found = False
        for lvl in currentTournaments[tourn].queue:
            if ident in lvl:
                found = True
                del( lvl[lvl.index(ident)] )
                break
        if not found:
            currentTournaments[tourn].queueActivity.append( (ident, datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f') ) )
    
    await currentTournaments[tourn].addMatch( userIdents )
    currentTournaments[tourn].matches[-1].saveXML( f'currentTournaments/{tourn}/matches/match_{currentTournaments[tourn].matches[-1].matchNumber}.xml' )
    await ctx.send( f'{ctx.message.author.mention}, the players you specified for the match are now paired. Their match number is #{currentTournaments[tourn].matches[-1].matchNumber}.' )


@bot.command(name='create-pairings-list')
async def createPairingsList( ctx, tourn = "" ):
    tourn  = tourn.strip()
    
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament, match number, player, and result in order to remove a player from a match.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return

    def searchForOpponents( lvl: int, i: int ) -> List[Tuple[int,int]]:
        if lvl > 0:
            lvl = -1*(lvl+1)
        
        plyr   = queue[lvl][i]
        plyrs  = [ queue[lvl][i] ]
        digest = [ (lvl, i) ]
        
        # Sweep through the rest of the level we start in
        for k in range(i+1,len(queue[lvl])):
            if queue[lvl][k].areValidOpponents( plyrs ):
                plyrs.append( queue[lvl][k] )
                # We want to store the shifted inner index since any players in
                # front of this player will be removed
                digest.append( (lvl, k - len(digest) ) )
                if len(digest) == currentTournaments[tourn].playersPerMatch:
                    # print( f'Match found: {", ".join([ p.name for p in plyrs ])}.' ) 
                    return digest
        
        # Starting from the priority level directly below the given level and
        # moving towards the lowest priority level, we sweep across each
        # remaining level looking for a match
        for l in reversed(range(-1*len(queue),lvl)):
            count = 0
            for k in range(len(queue[l])):
                if queue[l][k].areValidOpponents( plyrs ):
                    plyrs.append( queue[l][k] )
                    # We want to store the shifted inner index since any players in
                    # front of this player will be removed
                    digest.append( (l, k - count ) )
                    count += 1
                    if len(digest) == currentTournaments[tourn].playersPerMatch:
                        # print( f'Match found: {", ".join([ p.name for p in plyrs ])}.' ) 
                        return digest

        # A full match couldn't be formed. Return an empty list
        return [ ]
        
    # Even though this is a single list in a list, this could change to have several component lists
    queue    = [ [ lvl for lvl in currentTournaments[tourn].activePlayers.values() ] ]
    newQueue = [ [] for _ in range(len(queue)+1) ]
    plyrs    = [ ]
    indices  = [ ]
    pairings = [ ]

    for lvl in queue:
        random.shuffle( lvl )
    oldQueue = queue
    
    lvl = -1
    while lvl >= -1*len(queue):
        while len(queue[lvl]) > 0:
            indices = searchForOpponents( lvl, 0 )
            # If an empty array is returned, no match was found
            # Add the current player to the end of the new queue
            # and remove them from the current queue
            if len(indices) == 0:
                newQueue[lvl].append(queue[lvl][0])
                del( queue[lvl][0] )
            else:
                plyrs = [ ] 
                for index in indices:
                    plyrs.append( f'"{queue[index[0]][index[1]].discordUser.display_name}"' )
                    del( queue[index[0]][index[1]] )
                pairings.append( "\t".join( plyrs ) )
        lvl -= 1
    
    await ctx.send( f'{ctx.message.author.mention}, here is a list of possible pairings. There would be {sum( [ len(lvl) for lvl in newQueue ] )} players left unmatched.' )
    message = "\n".join( pairings )
    for msg in splitMessage( message ):
        if msg == "":
            break
        await ctx.send( msg )
    

@bot.command(name='players-per-match')
async def playersPerMatch( ctx, tourn = "", num = "" ):
    tourn  = tourn.strip()
    num    = num.strip()
    
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn == "" or num == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament and a number of players for a match.' )
        return
    try:
        num = int(num)
    except:
        await ctx.send( f'{ctx.message.author.mention}, "{num}" could not be converted to a number. Please make sure you only use digits.' )
        return

    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    currentTournaments[tourn].playersPerMatch = num
    currentTournaments[tourn].saveOverview( f'currentTournaments/{tourn}/overview.xml' )
    await ctx.send( f'{adminMention}, the number of players per match for {tourn} was changed to {num} by {ctx.message.author.mention}.' )
    currentTournaments[tourn].saveOverview( f'currentTournaments/{tourn}/overview.xml' )

@bot.command(name='set-match-length')
async def setMatchLength( ctx, tourn = "", num = "" ):
    tourn  = tourn.strip()
    num    = num.strip()
    
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn == "" or num == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament and a length in minutes.' )
        return
    try:
        num = int(num)
    except:
        await ctx.send( f'{ctx.message.author.mention}, "{num}" could not be converted to a number. Please make sure you only use digits.' )
        return

    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    currentTournaments[tourn].matchLength = num*60
    currentTournaments[tourn].saveOverview( f'currentTournaments/{tourn}/overview.xml' )
    await ctx.send( f'{adminMention}, the length of a match for {tourn} was changed to {num} minutes by {ctx.message.author.mention}.' )
    currentTournaments[tourn].saveOverview( f'currentTournaments/{tourn}/overview.xml' )

@bot.command(name='admin-confirm-result')
async def adminConfirmResult( ctx, tourn = "", plyr = "", mtch = "" ):
    tourn  = tourn.strip()
    plyr   = plyr.strip()
    mtch   = mtch.strip()
    
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if not await isTournamentAdmin( ctx ):
        await ctx.send( f'{ctx.message.author.mention}, you do not have permissions to remove players from a match. Please do not do this again or {adminMention} may intervene.' )
        return
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament, match number, player, and result in order to remove a player from a match.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    member = findPlayer( ctx.guild, tourn, plyr )
    if member == "":
        await ctx.send( f'{ctx.message.author.mention}, a player by "{plyr}" could not be found in the player role "{tourn} Player". Please verify that they have registered.' )
        return
    
    userIdent = getUserIdent( member )
    if not userIdent in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, a user by "{plyr}" was found in the player role, but they are not active in the tournament "{tourn}". Make sure they are registered or that they have not dropped.' )
        return
    
    try:
        mtch = int( mtch )
    except:
        await ctx.send( f'{ctx.message.author.mention}, you did not provide a match number. Please specify a match number using digits.' )
        return
    
    if mtch > len(currentTournaments[tourn].matches):
        await ctx.send( f'{ctx.message.author.mention}, the match number that you specified is greater than the number of matches. Double check the match number.' )
        return
        
    Match = currentTournaments[tourn].activePlayers[userIdent].getMatch( mtch )
    if Match.matchNumber == -1:
        await ctx.send( f'{ctx.message.author.mention}, {member.mention} is not a player in Match #{mtch}. Double check the match number.' )
        return
    
    if Match.isCertified( ):
        await ctx.send( f'{ctx.message.author.mention}, match #{mtch} is already certified. There is no need confirm the result again.' )
        return
    if userIdent in Match.confirmedPlayers:
        await ctx.send( f'{ctx.message.author.mention}, match #{mtch} is not certified, but {plyr} has already certified the result. There is no need to do this twice.' )
        return
    
    Match.saveXML( f'currentTournaments/{tourn}/matches/match_{mtch}.xml' )
    await currentTournaments[tourn].activePlayers[userIdent].discordUser.send( content=f'The result of match #{mtch} for {tourn} has been certified by tournament admin on your behave.' )
    msg = await Match.confirmResult( userIdent )
    if msg != "":
        await currentTournaments[tourn].pairingsChannel.send( msg )
    await ctx.send( f'{ctx.message.author.mention}, you have certified the result of match #{mtch} on behave of {plyr}.' )
        

@bot.command(name='admin-drop-player')
async def adminDropPlayer( ctx, tourn = "", plyr = "" ):
    tourn = tourn.strip()
    plyr  =  plyr.strip()

    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn == "" or plyr == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament and a player.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    member = findPlayer( ctx.guild, tourn, plyr )
    if member == "":
        await ctx.send( f'{ctx.message.author.mention}, a player by "{plyr}" could not be found in the player role for {tourn}. Please verify that they have registered.' )
        return

    userIdent = getUserIdent( member )
    if not userIdent in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, a user by "{plyr}" was found in the player role, but they are not active in the tournament "{tourn}". They may have already dropped from the tournament.' )
        return
    
    await currentTournaments[tourn].dropPlayer( userIdent )
    currentTournaments[tourn].droppedPlayers[userIdent].saveXML( f'currentTournaments/{tourn}/players/{userIdent}.xml' )
    await ctx.send( f'{ctx.message.author.mention}, {plyr} has been dropped from the tournament.' )
    await currentTournaments[tourn].droppedPlayers[userIdent].discordUser.send( content=f'You have been dropped from {tourn} on the server "{ctx.message.guild.name}" by tournament admin. If you believe this is an error, check with them.' )



"""

@bot.command(name='tournament-report')
async def adminDropPlayer( ctx, tourn = "" ):

"""



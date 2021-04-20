import os
import shutil
import random

from discord.ext import commands
from dotenv import load_dotenv

from baseBot import *
from Tournament import * 



commandSnippets["create-tournament"] = "- create-tournament : Creates a tournament" 
commandCategories["management"].append("create-tournament")
@bot.command(name='create-tournament')
async def createTournament( ctx, tourn = "" ):
    tourn = tourn.strip()
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you need to specify what you want the tournament to be called.' )
        return
    if tourn in tournaments:
        await ctx.send( f'{ctx.message.author.mention}, there is already a tournament call {tourn} either on this server or another. Pick a different name.' )
        return
    
    await ctx.message.guild.create_role( name=f'{tourn} Player' )
    tournaments[tourn] = tournament( tourn, ctx.message.guild.name, TRICE_BOT_AUTH_TOKEN, TRICE_BOT_ENABLED )
    tournaments[tourn].saveLocation = f'currentTournaments/{tourn}/'
    tournaments[tourn].addDiscordGuild( ctx.message.guild )
    tournaments[tourn].loop = bot.loop
    tournaments[tourn].saveTournament( f'currentTournaments/{tourn}' )
    await ctx.send( f'{adminMention}, a new tournament called "{tourn}" has been created by {ctx.message.author.mention}.' )
    

commandSnippets["update-reg"] = "- update-reg : Opens or closes registration" 
commandCategories["management"].append("update-reg")
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

    tournaments[tourn].setRegStatus( str_to_bool(status) )
    tournaments[tourn].saveOverview( )
    await ctx.send( f'{adminMention}, registration for the "{tourn}" tournament has been {("opened" if str_to_bool(status) else "closed")} by {ctx.message.author.mention}.' ) 


commandSnippets["start-tournament"] = "- start-tournament : Starts the tournament, which closes registration and let's players LFG" 
commandCategories["management"].append("start-tournament")
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
    if tournaments[tourn].tournStarted:
        await ctx.send( f'{ctx.message.author.mention}, {tourn} has already been started.' )
        return

    tournaments[tourn].startTourn()
    tournaments[tourn].saveOverview( )
    await ctx.send( f'{adminMention}, {tourn} has been started by {ctx.message.author.mention}.' )
    

commandSnippets["end-tournament"] = "- end-tournament : Ends a tournament that's been started" 
commandCategories["management"].append("end-tournament")
@bot.command(name='end-tournament')
async def endTournament( ctx, tourn = "" ):
    tourn = tourn.strip()
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you need to specify what tournament you want to end.' )
        return
    if not tourn in tournaments:
        await ctx.send( f'{ctx.message.author.mention}, there is no tournament called "{tourn}" for this server.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if tournaments[tourn].tournCancel:
        await ctx.send( f'{ctx.message.author.mention}, {tourn} has already been cancelled. Check with {adminMention} if you think this is an error.' )
        return

    authorIdent = getUserIdent( ctx.message.author )
    if await hasCommandWaiting( ctx, authorIdent ):
        del( commandsToConfirm[authorIdent] )

    commandsToConfirm[authorIdent] = ( getTime(), 30, tournaments[tourn].endTourn( adminMention, ctx.message.author.mention ) )
    await ctx.send( f'{adminMention}, in order to end {tourn}, confirmation is needed. {ctx.message.author.mention}, are you sure you want to end {tourn}?' )


commandSnippets["cancel-tournament"] = "- cancel-tournament : Ends any tournament" 
commandCategories["management"].append("cancel-tournament")
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
    

    authorIdent = getUserIdent( ctx.message.author )
    if await hasCommandWaiting( ctx, authorIdent ):
        del( commandsToConfirm[authorIdent] )

    commandsToConfirm[authorIdent] = ( getTime(), 30, tournaments[tourn].cancelTourn( adminMention, ctx.message.author.mention ) )
    await ctx.send( f'{adminMention}, in order to cancel {tourn}, confirmation is needed. {ctx.message.author.mention}, are you sure you want to cancel {tourn}?' )


commandSnippets["set-deck-count"] = "- set-deck-count : Sets the number of decks a player can have after pruning" 
commandCategories["properties"].append("set-deck-count")
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
    
    tournaments[tourn].deckCount = int( count )
    tournaments[tourn].saveOverview( )
    await ctx.send( f'{adminMention}, the deck count for tournament called "{tourn}" has been changed to {count} by {ctx.message.author.mention}.' )


commandSnippets["prune-decks"] = "- prune-decks : Removes decks from players until they have the max number" 
commandCategories["day-of"].append("prune-decks")
@bot.command(name='prune-decks')
async def adminPruneDecks( ctx, tourn = "" ):
    tourn = tourn.strip()
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    authorIdent = getUserIdent( ctx.message.author )
    if await hasCommandWaiting( ctx, authorIdent ):
        del( commandsToConfirm[authorIdent] )

    commandsToConfirm[authorIdent] = ( getTime(), 30, tournaments[tourn].pruneDecks( ctx ) )
    await ctx.send( f'{adminMention}, in order to prune decks, confirmation is needed. {ctx.message.author.mention}, are you sure you want to prune decks?' )


commandSnippets["prune-players"] = "- prune-players : Drops players that didn't submit a deck" 
commandCategories["day-of"].append("prune-players")
@bot.command(name='prune-players')
async def adminPruneDecks( ctx, tourn = "" ):
    tourn = tourn.strip()
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    authorIdent = getUserIdent( ctx.message.author )
    if await hasCommandWaiting( ctx, authorIdent ):
        del( commandsToConfirm[authorIdent] )

    commandsToConfirm[authorIdent] = ( getTime(), 30, tournaments[tourn].prunePlayers( ctx ) )
    await ctx.send( f'{adminMention}, in order to prune players, confirmation is needed. {ctx.message.author.mention}, are you sure you want to prune players?' )


commandSnippets["create-match"] = "- create-match : Creates a match" 
commandCategories["day-of"].append("create-match")
@bot.command(name='create-match')
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
    if len(plyrs) != tournaments[tourn].playersPerMatch:
        await ctx.send( f'{ctx.message.author.mention}, {tourn} requires {tournaments[tourn].playersPerMatch} be in a match, but you specified {len(plyrs)} players.' )
        return
        
    members = [ findPlayer( ctx.guild, tourn, plyr ) for plyr in plyrs ]
    if "" in members:
        await ctx.send( f'{ctx.message.author.mention}, at least one of the members that you specified is not a part of the tournament. Verify that they have the "{tourn} Player" role.' )
        return
    
    userIdents = [ getUserIdent( member ) for member in members ]
    for userIdent in userIdents:
        if not userIdent in tournaments[tourn].players:
            await ctx.send( f'{ctx.message.author.mention}, a user by "{member.mention}" was found in the player role, but they are not active in {tourn}. Make sure they are registered or that they have not dropped.' )
            return
    
    for ident in userIdents:
        found = False
        for lvl in tournaments[tourn].queue:
            if ident in lvl:
                found = True
                del( lvl[lvl.index(ident)] )
                break
        if not found:
            tournaments[tourn].queueActivity.append( (ident, datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f') ) )
    
    await tournaments[tourn].addMatch( userIdents )
    tournaments[tourn].matches[-1].saveXML( )
    tournaments[tourn].saveOverview( )
    await ctx.send( f'{ctx.message.author.mention}, the players you specified for the match are now paired. Their match number is #{tournaments[tourn].matches[-1].matchNumber}.' )


commandSnippets["create-pairings-list"] = "- create-pairings-list : Creates a list of possible match pairings (unweighted)" 
commandCategories["day-of"].append("create-pairings-list")
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

    def searchForOpponents( lvl: int, i: int, queue ) -> List[Tuple[int,int]]:
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
                if len(digest) == tournaments[tourn].playersPerMatch:
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
                    if len(digest) == tournaments[tourn].playersPerMatch:
                        # print( f'Match found: {", ".join([ p.name for p in plyrs ])}.' ) 
                        return digest

        # A full match couldn't be formed. Return an empty list
        return [ ]

    def pairingAttempt( ):
        # Even though this is a single list in a list, this could change to have several component lists
        queue    = [ [ plyr for plyr in tournaments[tourn].players.values() if plyr.isActive() ] ]
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
                indices = searchForOpponents( lvl, 0, queue )
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
                    pairings.append( " ".join( plyrs ) )
            lvl -= 1
        
        return pairings, newQueue
        
    tries = 25
    results = []
     
    for _ in range(tries):
        results.append( pairingAttempt() )
        # Have we paired the maximum number of people, i.e. does the remainder of the queue by playersPerMatch equal the new queue
        if sum( [ len(lvl) for lvl in results[-1][1] ] ) == sum( [len(lvl) for lvl in tournaments[tourn].queue] )%tournaments[tourn].playersPerMatch:
            break

    results.sort( key=lambda x: len(x) ) 
    pairings = results[-1][0]
    newQueue = results[-1][1]
 
    newLine = "\n- "
    if sum( [ len(lvl) for lvl in newQueue ] ) == 0:
        await ctx.send( f'{ctx.message.author.mention}, here is a list of possible pairings. There would be no players left unmatched.' )
    else:
        plyrs = [ f'"{plyr.discordUser.display_name}"' for lvl in newQueue for plyr in lvl ]
        message = f'{ctx.message.author.mention}, here is a list of possible pairings. These players would be left unmatched:{newLine}{newLine.join(plyrs)}'
        for msg in splitMessage( message ):
            if msg == "":
                break
            await ctx.send( msg )
        
    await ctx.send( f'\nThese are all the complete pairings.' ) 
    message = "\n".join( pairings )
    for msg in splitMessage( message ):
        if msg == "":
            break
        await ctx.send( msg )
    

commandSnippets["set-pairing-threshold"] = "- set-pairing-threshold : Sets the number of players needed to pair the queue" 
commandCategories["properties"].append("set-pairing-threshold")
@bot.command(name='set-pairing-threshold')
async def pairingsThreshold( ctx, tourn = "", num = "" ):
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
    
    tournaments[tourn].updatePairingsThreshold( num )
    tournaments[tourn].saveOverview( )
    await ctx.send( f'{adminMention}, the pairings threshold for {tourn} was changed to {num} by {ctx.message.author.mention}.' )


commandSnippets["set-match-size"] = "- set-match-size : Sets the number of players needed for a match" 
commandCategories["properties"].append("set-match-size")
@bot.command(name='set-match-size')
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
    
    tournaments[tourn].playersPerMatch = num
    tournaments[tourn].saveOverview( )
    await ctx.send( f'{adminMention}, the number of players per match for {tourn} was changed to {num} by {ctx.message.author.mention}.' )


commandSnippets["set-match-length"] = "- set-match-length : Sets the amount of time for a match (in minutes)" 
commandCategories["properties"].append("set-match-length")
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
    
    tournaments[tourn].matchLength = num*60
    tournaments[tourn].saveOverview( )
    await ctx.send( f'{adminMention}, the length of a match for {tourn} was changed to {num} minutes by {ctx.message.author.mention}.' )


commandSnippets["admin-drop"] = "- admin-drop : Removes a player for a tournament" 
commandCategories["day-of"].append("admin-drop")
@bot.command(name='admin-drop')
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
    if not userIdent in tournaments[tourn].players:
        await ctx.send( f'{ctx.message.author.mention}, a user by "{plyr}" was found in the player role, but they are not active in the tournament "{tourn}". They may have already dropped from the tournament.' )
        return

    authorIdent = getUserIdent( ctx.message.author )
    if await hasCommandWaiting( ctx, authorIdent ):
        del( commandsToConfirm[authorIdent] )

    commandsToConfirm[authorIdent] = ( getTime(), 30, tournaments[tourn].dropPlayer( userIdent, ctx.message.author.mention ) )
    await ctx.send( f'{adminMention}, in order to drop {member.mention}, confirmation is needed. {ctx.message.author.mention}, are you sure you want to drop this player?' )


commandSnippets["give-bye"] = "- give-bye : Grants a bye to a player" 
commandCategories["day-of"].append("give-bye")
@bot.command(name='give-bye')
async def adminGiveBye( ctx, tourn = "", plyr = "" ):
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
    if not userIdent in tournaments[tourn].players:
        await ctx.send( f'{ctx.message.author.mention}, a user by "{plyr}" was found in the player role, but they are not active in the tournament "{tourn}". They may have already dropped from the tournament.' )
        return
    
    if tournaments[tourn].players[userIdent].hasOpenMatch( ):
        await ctx.send( f'{ctx.message.author.mention}, {plyr} currently has an open match in the tournament. That match needs to be certified before they can be given a bye.' )
        return
    
    tournaments[tourn].addBye( userIdent )
    tournaments[tourn].players[userIdent].saveXML( )
    await ctx.send( f'{ctx.message.author.mention}, {plyr} has been given a bye.' )
    await tournaments[tourn].players[userIdent].discordUser.send( content=f'You have been given a bye from the tournament admin for {tourn} on the server {ctx.guild.name}.' )


commandSnippets["remove-match"] = "- remove-match : Removes a match" 
commandCategories["day-of"].append("remove-match")
@bot.command(name='remove-match')
async def adminRemoveMatch( ctx, tourn = "", mtch = "" ):
    tourn = tourn.strip()
    mtch  =  mtch.strip()

    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn == "" or mtch == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament and a player.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    try:
        mtch = int( mtch )
    except:
        await ctx.send( f'{ctx.message.author.mention}, you did not provide a match number. Please specify a match number using digits.' )
        return
    
    if mtch > len(tournaments[tourn].matches):
        await ctx.send( f'{ctx.message.author.mention}, the match number that you specified is greater than the number of matches. Double check the match number.' )
        return
        
    authorIdent = getUserIdent( ctx.message.author )
    if await hasCommandWaiting( ctx, authorIdent ):
        del( commandsToConfirm[authorIdent] )

    commandsToConfirm[authorIdent] = ( getTime(), 30, tournaments[tourn].removeMatch( mtch, ctx.message.author.mention ) )
    await ctx.send( f'{adminMention}, in order to remove match #{mtch}, confirmation is needed. {ctx.message.author.mention}, are you sure you want to remove this match?' )


commandSnippets["view-queue"] = "- view-queue : Prints the currect matchmaking queue" 
commandCategories["day-of"].append("view-queue")
@bot.command(name='view-queue')
async def viewQueue( ctx, tourn = "" ):
    tourn = tourn.strip()

    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament to view the queue.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    if sum( [ len(lvl) for lvl in tournaments[tourn].queue ] ) == 0:
        await ctx.send( f'{ctx.message.author.mention}, the current matchmaking queue for {tourn} is empty:' )
        return
    
    embed = discord.Embed( )
    value =  ""
    count = 0
    
    for lvl in range(len(tournaments[tourn].queue)):
        value += f'{lvl+1}) ' + ", ".join( [ plyr.discordUser.display_name for plyr in tournaments[tourn].queue[lvl] ] ) + "\n"
        if len(value) > 1024:
            embed.add_field( name = f'{tourn} Queue' if count == 0 else "\u200b", value = value, inline=False )
            value = ""
            count += 1
    
    if value != "":
        embed.add_field( name = f'{tourn} Queue' if count == 0 else "\u200b", value = value, inline=False )
        
    await ctx.send( f'{ctx.message.author.mention}, here is the current matchmaking queue for {tourn}:', embed=embed )


"""

@bot.command(name='tournament-report')
async def adminDropPlayer( ctx, tourn = "" ):

"""



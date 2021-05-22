import os
import shutil
import random

from discord.ext import commands
from dotenv import load_dotenv

from baseBot import *
from Tournament import * 

commandSnippets["create-tournament"] = "- create-tournament : Creates a tournament and has a toggle to enable tricebot." 
commandCategories["management"].append("create-tournament")
@bot.command(name='create-tournament')
async def createTournament( ctx, tournName = None, tournType = None, *args ):
    mention = ctx.message.author.mention
    if await isPrivateMessage( ctx ): return

    if not await isTournamentAdmin( ctx ): return
    
    tournProps = generateTournProps( *args )
    if len(tournProps) != "".join(args).count("="):
        print( tournProps )
        await ctx.send( f'{mention}, there is an issue with the tournament properties that you gave. Check your spelling and consult the "!squirebot-help" command for more help' )
        return
    
    adminMention = getTournamentAdminMention( ctx.message.guild )
    if tournName is None or tournType is None:
        await ctx.send( f'{mention}, you need to specify what you want the tournament name and type.' )
        return
    elif isPathSafeName(tournName):        
        await ctx.send( f'{mention}, you cannot have that as a tournament name.' )
        return
    
    if tournName in tournaments:
        await ctx.send( f'{mention}, there is already a tournament call {tournName} either on this server or another. Pick a different name.' )
        return
    
    triceBotFlag = False
    if "tricebot-enabled" in tournProps:
        if tournProps["tricebot-enabled"] == "true":
            tournProps["tricebot-enabled"] = True
        elif tournProps["tricebot-enabled"] == "false":
            tournProps["tricebot-enabled"] = False
        else:
            await ctx.send( f'{ctx.message.author.mention}, please enter either true or false for the tricebot toggle.' )
            return 
    
    newTourn = getTournamentType( tournType, tournName, ctx.guild.name, tournProps )
    if newTourn is None:
        newLine = "\n\t- "
        await ctx.send( f'{mention}, invalid tournament type of {tournType}. The supported tournament types are:{newLine}{newLine.join(tournamentTypes)}.' )
        return
    
    newTourn.saveLocation = f'currentTournaments/{tournName}/'
    await newTourn.addDiscordGuild( ctx.message.guild )
    newTourn.loop = bot.loop
    newTourn.saveTournament( f'currentTournaments/{tournName}' )
    tournaments[tournName] = newTourn
    await ctx.send( f'{adminMention}, a new tournament called "{tournName}" has been created by {ctx.message.author.mention}.' )
    
    if triceBotFlag:
        await ctx.send( f'{adminMention}, tricebot has been enabled for "{tournName}" by {ctx.message.author.mention}. It is using the default settings (spectators are allowed, do not need a password, cannot chat, cannot see hands and, players must be registered).' )


commandSnippets["update-properties"] = "- update-properties : Changes the properties of a tournament." 
commandCategories["properties"].append("update-properties")
@bot.command(name='update-properties')
async def updateTournProperties( ctx, tournName = None, *args ):
    mention = ctx.message.author.mention
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tournName is None:
        await ctx.send( f'{mention}, you did not provide enough information. You need to specify a tournament and a number of players for a match.' )
        return

    if not await checkTournExists( tournName, ctx ): return
    if not await correctGuild( tournName, ctx ): return
    if await isTournDead( tournName, ctx ): return
    
    tournProps = generateTournProps( *args )
    if len(tournProps) != "".join(args).count("=") or len(tournProps) == 0:
        print( tournProps )
        await ctx.send( f'{mention}, there is an issue with the tournament properties that you gave. Check your spelling and consult the "!squirebot-help" command for more help' )
        return

    message = tournaments[tournName].setProperties( tournProps )
    tournaments[tournName].saveOverview( )
    await ctx.send( f'{adminMention}, {mention} has updated the properties of {tournName}.\n{message}' )


commandSnippets["tricebot-status"] = "- tricebot-status : Displays the status of tricebot for a tournament" 
commandCategories["management"].append("tricebot-status")
@bot.command(name='tricebot-status')
async def triceBotStatus( ctx, tourn = "" ):  
    tourn = tourn.strip()
    
    if await isPrivateMessage( ctx ): return

    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you need to specify what you want the tournament to be called.' )
        return
        
    if (tournaments[tourn].triceBotEnabled):  
        settings_str = "Spectators allowed: " + str(tournaments[tourn].spectators_allowed)
        settings_str += "\nSpectator need password: " + str(tournaments[tourn].spectators_need_password)        
        settings_str += "\nSpectator can chat: " + str(tournaments[tourn].spectators_can_chat)
        settings_str += "\nSpectator can see hands: " + str(tournaments[tourn].spectators_can_see_hands)
        settings_str += "\nOnly allow registered users: " + str(tournaments[tourn].only_registered)
        
        await ctx.send( f'{adminMention}, tricebot is enabled for "{tourn} and has the follwing settings:\n```{settings_str}```' )
    else:
        await ctx.send( f'{adminMention}, tricebot is not enabled for "{tourn}.' )

    
commandSnippets["update-reg"] = "- update-reg : Opens or closes registration" 
commandCategories["management"].append("update-reg")
@bot.command(name='update-reg')
async def updateReg( ctx, tourn = None, status = None ):
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn is None or status is None:
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
async def startTournament( ctx, tourn = None ):
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn is None:
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
async def endTournament( ctx, tourn = None ):
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn is None:
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

    if await hasCommandWaiting( ctx, ctx.message.author.id ):
        del( commandsToConfirm[ctx.message.author.id] )

    commandsToConfirm[ctx.message.author.id] = ( getTime(), 30, tournaments[tourn].endTourn( adminMention, ctx.message.author.mention ) )
    await ctx.send( f'{adminMention}, in order to end {tourn}, confirmation is needed. {ctx.message.author.mention}, are you sure you want to end {tourn} (!yes/!no)?' )


commandSnippets["cancel-tournament"] = "- cancel-tournament : Ends any tournament" 
commandCategories["management"].append("cancel-tournament")
@bot.command(name='cancel-tournament')
async def cancelTournament( ctx, tourn = None ):
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn is None:
        await ctx.send( f'{ctx.message.author.mention}, you need to specify what tournament you want to cancel.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    

    if await hasCommandWaiting( ctx, ctx.message.author.id ):
        del( commandsToConfirm[ctx.message.author.id] )

    commandsToConfirm[ctx.message.author.id] = ( getTime(), 30, tournaments[tourn].cancelTourn( adminMention, ctx.message.author.mention ) )
    await ctx.send( f'{adminMention}, in order to cancel {tourn}, confirmation is needed. {ctx.message.author.mention}, are you sure you want to cancel {tourn} (!yes/!no)?' )


commandSnippets["prune-decks"] = "- prune-decks : Removes decks from players until they have the max number" 
commandCategories["day-of"].append("prune-decks")
@bot.command(name='prune-decks')
async def adminPruneDecks( ctx, tourn = None ):
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx, tourn ): return
    if tourn is None:
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    if await hasCommandWaiting( ctx, ctx.message.author.id ):
        del( commandsToConfirm[ctx.message.author.id] )

    commandsToConfirm[ctx.message.author.id] = ( getTime(), 30, tournaments[tourn].pruneDecks( ctx ) )
    await ctx.send( f'{adminMention}, in order to prune decks, confirmation is needed. {ctx.message.author.mention}, are you sure you want to prune decks (!yes/!no)?' )


commandSnippets["prune-players"] = "- prune-players : Drops players that didn't submit a deck" 
commandCategories["day-of"].append("prune-players")
@bot.command(name='prune-players')
async def adminPruneDecks( ctx, tourn = None ):
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn is None:
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    if await hasCommandWaiting( ctx, ctx.message.author.id ):
        del( commandsToConfirm[ctx.message.author.id] )

    commandsToConfirm[ctx.message.author.id] = ( getTime(), 30, tournaments[tourn].prunePlayers( ctx ) )
    await ctx.send( f'{adminMention}, in order to prune players, confirmation is needed. {ctx.message.author.mention}, are you sure you want to prune players (!yes/!no)?' )


commandSnippets["create-match"] = "- create-match : Creates a match" 
commandCategories["day-of"].append("create-match")
@bot.command(name='create-match')
async def adminCreatePairing( ctx, tourn = None, *plyrs ):
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn is None:
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament, match number, player, and result in order to remove a player from a match.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    if len(plyrs) != tournaments[tourn].playersPerMatch:
        await ctx.send( f'{ctx.message.author.mention}, {tourn} requires {tournaments[tourn].playersPerMatch} be in a match, but you specified {len(plyrs)} players.' )
        return
        
    members = [ findPlayer( ctx.guild, tourn, plyr ) for plyr in plyrs ]
    if None in members:
        await ctx.send( f'{ctx.message.author.mention}, at least one of the members that you specified is not a part of the tournament. Verify that they have the "{tourn} Player" role.' )
        return
    
    for member in members:
        if not member.id in tournaments[tourn].players:
            await ctx.send( f'{ctx.message.author.mention}, a user by "{member.mention}" was found in the player role, but they are not active in {tourn}. Make sure they are registered or that they have not dropped.' )
            return
    
    await tournaments[tourn].addMatch( [ member.id for member in members ] )
    tournaments[tourn].matches[-1].saveXML( )
    tournaments[tourn].saveOverview( )
    await ctx.send( f'{ctx.message.author.mention}, the players you specified for the match are now paired. Their match number is #{tournaments[tourn].matches[-1].matchNumber}.' )


commandSnippets["create-pairings-list"] = "- create-pairings-list : Creates a list of possible match pairings (unweighted)" 
commandCategories["day-of"].append("create-pairings-list")
@bot.command(name='create-pairings-list')
async def createPairingsList( ctx, tourn = None ):
    
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn is None:
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
async def pairingsThreshold( ctx, tourn = None, num = None ):
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn is None or num is None:
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


commandSnippets["admin-drop"] = "- admin-drop : Removes a player for a tournament" 
commandCategories["day-of"].append("admin-drop")
@bot.command(name='admin-drop')
async def adminDropPlayer( ctx, tourn = None, plyr = None ):
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn is None or plyr is None:
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament and a player.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    member = findPlayer( ctx.guild, tourn, plyr )
    if member is None:
        await ctx.send( f'{ctx.message.author.mention}, a player by "{plyr}" could not be found in the player role for {tourn}. Please verify that they have registered.' )
        return

    if not member.id in tournaments[tourn].players:
        await ctx.send( f'{ctx.message.author.mention}, a user by "{plyr}" was found in the player role, but they are not active in the tournament "{tourn}". They may have already dropped from the tournament.' )
        return

    if await hasCommandWaiting( ctx, ctx.message.author.id ):
        del( commandsToConfirm[ctx.message.author.id] )

    commandsToConfirm[ctx.message.author.id] = ( getTime(), 30, tournaments[tourn].dropPlayer( member.id, ctx.message.author.mention ) )
    await ctx.send( f'{adminMention}, in order to drop {member.mention}, confirmation is needed. {ctx.message.author.mention}, are you sure you want to drop this player (!yes/!no)?' )


commandSnippets["give-bye"] = "- give-bye : Grants a bye to a player" 
commandCategories["day-of"].append("give-bye")
@bot.command(name='give-bye')
async def adminGiveBye( ctx, tourn = None, plyr = None ):
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn is None or plyr is None:
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament and a player.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    member = findPlayer( ctx.guild, tourn, plyr )
    if member is None:
        await ctx.send( f'{ctx.message.author.mention}, a player by "{plyr}" could not be found in the player role for {tourn}. Please verify that they have registered.' )
        return

    if not member.id in tournaments[tourn].players:
        await ctx.send( f'{ctx.message.author.mention}, a user by "{plyr}" was found in the player role, but they are not active in the tournament "{tourn}". They may have already dropped from the tournament.' )
        return
    
    if tournaments[tourn].players[member.id].hasOpenMatch( ):
        await ctx.send( f'{ctx.message.author.mention}, {plyr} currently has an open match in the tournament. That match needs to be certified before they can be given a bye.' )
        return
    
    tournaments[tourn].addBye( member.id )
    tournaments[tourn].players[member.id].saveXML( )
    await ctx.send( f'{ctx.message.author.mention}, {plyr} has been given a bye.' )
    await tournaments[tourn].players[member.id].discordUser.send( content=f'You have been given a bye from the tournament admin for {tourn} on the server {ctx.guild.name}.' )


commandSnippets["remove-match"] = "- remove-match : Removes a match" 
commandCategories["day-of"].append("remove-match")
@bot.command(name='remove-match')
async def adminRemoveMatch( ctx, tourn = None, mtch = None ):
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn is None or mtch is None:
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
        
    if await hasCommandWaiting( ctx, ctx.message.author.id ):
        del( commandsToConfirm[ctx.message.author.id] )

    commandsToConfirm[ctx.message.author.id] = ( getTime(), 30, tournaments[tourn].removeMatch( mtch, ctx.message.author.mention ) )
    await ctx.send( f'{adminMention}, in order to remove match #{mtch}, confirmation is needed. {ctx.message.author.mention}, are you sure you want to remove this match (!yes/!no)?' )


commandSnippets["view-queue"] = "- view-queue : Prints the currect matchmaking queue" 
commandCategories["day-of"].append("view-queue")
@bot.command(name='view-queue')
async def viewQueue( ctx, tourn = None ):
    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn is None:
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


commandSnippets["tricebot-kick-player"] = "- tricebot-kick-player : Kicks a player from a cockatrice match when tricebot is enabled for that match" 
commandCategories["day-of"].append("tricebot-kick-player")
@bot.command(name='tricebot-kick-player')
async def tricebotKickPlayer( ctx, tourn = "", mtch = "", playerName = "" ):
    tourn = tourn.strip()
    mtch  =  mtch.strip()
    playerName = playerName.strip()

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
    
    if not tournaments[tourn].matches[mtch - 1].triceMatch:
        await ctx.send( f'{ctx.message.author.mention}, that match is not a match with tricebot enabled.' )
        return
    
    result = tournaments[tourn].kickTricePlayer(mtch, playerName)    
    
    #  1 success
    #  0 auth token is bad or error404 or network issue
    # -1 player not found
    # -2 an unknown error occurred
    
    if result == 1:
        await ctx.send( f'{ctx.message.author.mention}, "{playerName}" was kicked from match {mtch}.' )
    elif result == -1:
        await ctx.send( f'{ctx.message.author.mention}, "{playerName}" was not found in match {mtch}.' )
    else:
        await ctx.send( f'{ctx.message.author.mention}, An error has occured whilst kicking "{playerName}" from match {mtch}.' )        
        
        
"""

@bot.command(name='tournament-report')
async def adminDropPlayer( ctx, tourn = None ):

"""



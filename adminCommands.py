import os
import shutil
import random
import tempfile

from discord.ext import commands
from dotenv import load_dotenv

from baseBot import *
from Tournament import *


commandSnippets["setup"] = "- setup : Creates a tournament and has a toggle to enable tricebot."
commandCategories["management"].append("setup")
@bot.command(name='setup')
async def setupGuild( ctx ):
    mention = ctx.author.mention

    if await isPrivateMessage( ctx ): return
    gld = guildSettingsObjects[ctx.guild.id]

    if not gld.isGuildAdmin( ctx.author ):
        await ctx.send( f'{mention}, you are not an admin on this server, so you can not run this command.' )
        return

    if gld.isConfigured():
        await ctx.send( f'{mention}, {ctx.guild.name} is already setup to run tournaments. If you want to change what channels are used, either use the !update-properties or !update-server-defaults commands. Instructions those commands can be found be using the !squirebot-help command followed by the command name.' )
        return

    if await hasCommandWaiting( ctx, ctx.author.id ):
        del( commandsToConfirm[ctx.author.id] )

    embed = gld.checkConfiguration()
    commandsToConfirm[ctx.author.id] = ( getTime(), 30, gld.configureGuild( ctx.author ) )
    await ctx.send( content=f'{mention}, below are the channels/categories that are going to be created. They can be moved around as desired. Are you sure you want to finish setting up (!yes/!no)?', embed=embed )


commandSnippets["create-tournament"] = "- create-tournament : Creates a tournament and has a toggle to enable tricebot."
commandCategories["management"].append("create-tournament")
@bot.command(name='create-tournament')
async def createTournament( ctx, tournName = None, tournType = None, *args ):
    mention = ctx.author.mention
    gld = guildSettingsObjects[ctx.guild.id]

    if await isPrivateMessage( ctx ): return

    if not await isTournamentAdmin( ctx ): return

    tournProps = generatePropsDict( *args )
    if len(tournProps) != "".join(args).count("="):
        await ctx.send( f'{mention}, there is an issue with the tournament properties that you gave. Check that you entered them correctly and consult the "!squirebot-help" command for more help' )
        return

    adminMention = gld.getTournAdminRole().mention
    if tournName is None or tournType is None:
        await ctx.send( f'{mention}, you need to specify what you want the tournament name and type.' )
        return
    elif isPathSafeName(tournName) or "@everyone" in tournName:
        await ctx.send( f'{mention}, you cannot have that as a tournament name.' )
        return

    shouldBeNone = gld.getTournament( tournName )
    if not (shouldBeNone is None):
        await ctx.send( f'{mention}, there is already a tournament call {tournName} on this server. Pick a different name.' )
        return

    try:
        message = await gld.createTournament( tournType, tournName, tournProps )
    except NotImplementedError as e:
        print(e)
        newLine = "\n\t- "
        await ctx.send( f'{mention}, invalid tournament type of {tournType}. The supported tournament types are:{newLine}{newLine.join(tournamentTypes)}.' )
        return

    trice = ""
    # Was tricebot specified and was it specified to be True?
    if "tricebot-enabled" in tournProps and tournProps["tricebot-enabled"]:
        trice = f' with TriceBot enabled'

    await ctx.send( f'{adminMention}, a new tournament called {tournName} was created{trice} by {mention}:\n{message}' )

    gld.getTournament( tournName ).saveTournament()


commandSnippets["update-properties"] = "- update-properties : Changes the properties of a tournament."
commandCategories["properties"].append("update-properties")
@bot.command(name='update-properties')
async def updateTournProperties( ctx, tournName = None, *args ):
    mention = ctx.author.mention
    gld = guildSettingsObjects[ctx.guild.id]

    if await isPrivateMessage( ctx ): return

    if not await isTournamentAdmin( ctx ): return

    adminMention = gld.getTournAdminRole( ).mention

    if tournName is None:
        await ctx.send( f'{mention}, you did not provide enough information. You need to specify a tournament and a number of players for a match.' )
        return

    tournObj = gld.getTournament( tournName )
    if tournObj is None:
        await ctx.send( f'{mention}, there is not a tournament called {tournName!r} on this server.' )
        return

    tournProps = generatePropsDict( *args )
    if len(tournProps) != "".join(args).count("="):
        print( tournProps )
        await ctx.send( f'{mention}, there is an issue with the tournament properties that you gave. Check your spelling and consult the "!squirebot-help" command for more help' )
        return

    message = tournObj.setProperties( tournProps )
    tournObj.saveOverview( )
    await ctx.send( f'{adminMention}, {mention} has updated the properties of {tournName}.\n{message}' )
    await tournObj.updateInfoMessage()


commandSnippets["update-server-defaults"] = "- update-server-defaults : Changes the properties of a tournament."
commandCategories["properties"].append("update-server-defaults")
@bot.command(name='update-server-defaults')
async def updateTournProperties( ctx, *args ):
    mention = ctx.author.mention
    gld = guildSettingsObjects[ctx.guild.id]

    if await isPrivateMessage( ctx ): return

    if not gld.isGuildAdmin( ctx.author ):
        await ctx.send( f'{mention}, you do not have permissions to change the tournament settings on this server.' )
        return

    guildDefaults = generatePropsDict( *args )

    message = gld.updateDefaults( guildDefaults )

    gld.saveSettings( )
    await ctx.send( f'{mention}, you have updated the tournament settings for the server.\n{message}' )


commandSnippets["tricebot-status"] = "- tricebot-status : Displays the status and settings of tricebot for a tournament"
commandCategories["management"].append("tricebot-status")
@bot.command(name='tricebot-status')
async def triceBotStatus( ctx, tourn = None ):
    mention = ctx.author.mention
    gld = guildSettingsObjects[ctx.guild.id]

    if await isPrivateMessage( ctx ): return

    if not await isTournamentAdmin( ctx ): return

    adminMention = gld.getTournAdminRole().mention

    if tourn is None:
        await ctx.send( f'{mention}, you need to specify what tournament you want to know the settings for.' )
        return

    tournObj = gld.getTournament( tourn )
    if tournObj is None:
        await ctx.send( f'{mention}, there is not a tournament called {tourn!r} on this server.' )
        return

    if tournObj.triceBotEnabled:
        settings_str  = f'Spectators allowed: {tournObj.spectators_allowed}'
        settings_str += f'\nSpectator need password: {tournObj.spectators_need_password}'
        settings_str += f'\nSpectator can chat: {tournObj.spectators_can_chat}'
        settings_str += f'\nSpectator can see hands: {tournObj.spectators_can_see_hands}'
        settings_str += f'\nOnly allow registered users: {tournObj.only_registered}'
        settings_str += f'\nPlayer deck verification: {tournObj.player_deck_verification}'
        await ctx.send( f'{adminMention}, tricebot is enabled for {tourn!r} and has the following settings:\n```{settings_str}```' )
    else:
        await ctx.send( f'{adminMention}, tricebot is not enabled for "{tourn}."' )


commandSnippets["update-reg"] = "- update-reg : Opens or closes registration"
commandCategories["management"].append("update-reg")
@bot.command(name='update-reg')
async def updateReg( ctx, tourn = None, status = None ):
    mention = ctx.author.mention
    gld = guildSettingsObjects[ctx.guild.id]

    if await isPrivateMessage( ctx ): return

    if not await isTournamentAdmin( ctx ): return
    adminMention = gld.getTournAdminRole().mention

    if tourn is None or status is None:
        await ctx.send( f'{mention}, it appears that you did not give enough information. You need to first state the tournament name and then "true" or "false".' )
        return

    tournObj = gld.getTournament( tourn )
    if tournObj is None:
        await ctx.send( f'{mention}, there is not tournament called {tourn!r} on this server.' )
        return

    status = "True" if status.lower() == "open" else status
    status = "False" if status.lower() == "closed" else status

    tournObj.setRegStatus( str_to_bool(status) )
    tournObj.saveOverview( )
    await ctx.send( f'{adminMention}, registration for the {tourn!r} tournament has been {("opened" if str_to_bool(status) else "closed")} by {mention}.' )
    await tournObj.updateInfoMessage()


commandSnippets["start-tournament"] = "- start-tournament : Starts the tournament, which closes registration and let's players LFG"
commandCategories["management"].append("start-tournament")
@bot.command(name='start-tournament')
async def startTournament( ctx, tourn = None ):
    mention = ctx.author.mention
    gld = guildSettingsObjects[ctx.guild.id]

    if await isPrivateMessage( ctx ): return

    if not await isTournamentAdmin( ctx ): return
    adminMention = gld.getTournAdminRole().mention

    if tourn is None:
        await ctx.send( f'{mention}, you need to specify what tournament you want to start.' )
        return

    tournObj = gld.getTournament( tourn )
    if tournObj is None:
        await ctx.send( f'{mention}, there is not a tournament called {tourn!r} on this server.' )
        return
    if tournObj.tournStarted:
        await ctx.send( f'{mention}, {tourn} has already been started.' )
        return

    tournObj.startTourn()
    tournObj.saveOverview( )
    await ctx.send( f'{adminMention}, {tourn} has been started by {mention}.' )
    await tournObj.updateInfoMessage()


commandSnippets["end-tournament"] = "- end-tournament : Ends a tournament"
commandCategories["management"].append("end-tournament")
@bot.command(name='end-tournament')
async def endTournament( ctx, tourn: str = None ):
    mention = ctx.author.mention
    gld = guildSettingsObjects[ctx.guild.id]

    if await isPrivateMessage( ctx ): return

    if not await isTournamentAdmin( ctx ): return
    adminMention = gld.getTournAdminRole().mention

    if tourn is None:
        await ctx.send( f'{mention}, you need to specify what tournament you want to end.' )
        return

    tournObj = gld.getTournament( tourn )
    if tournObj is None:
        await ctx.send( f'{mention}, there is not tournament called {tourn!r} on this server.' )
        return

    if await hasCommandWaiting( ctx, ctx.author.id ):
        del( commandsToConfirm[ctx.author.id] )

    commandsToConfirm[ctx.author.id] = ( getTime(), 30, gld.endTournament( tourn, mention ) )
    await ctx.send( f'{adminMention}, in order to end {tourn}, confirmation is needed. {mention}, are you sure you want to end {tourn} (!yes/!no)?' )
    await tournObj.updateInfoMessage()


commandSnippets["prune-decks"] = "- prune-decks : Removes decks from players until they have the max number"
commandCategories["day-of"].append("prune-decks")
@bot.command(name='prune-decks')
async def adminPruneDecks( ctx, tourn = None ):
    mention = ctx.author.mention
    gld = guildSettingsObjects[ctx.guild.id]

    if await isPrivateMessage( ctx ): return

    if not await isTournamentAdmin( ctx ): return
    adminMention = gld.getTournAdminRole().mention

    if tourn is None:
        await ctx.send( f'{mention}, you did not provide enough information. You need to specify a tournament.' )
        return

    tournObj = gld.getTournament( tourn )
    if tournObj is None:
        await ctx.send( f'{mention}, there is not tournament called {tourn!r} on this server.' )
        return

    if await hasCommandWaiting( ctx, ctx.author.id ):
        del( commandsToConfirm[ctx.author.id] )

    commandsToConfirm[ctx.author.id] = ( getTime(), 30, tournObj.pruneDecks( ctx ) )
    await ctx.send( f'{adminMention}, in order to prune decks, confirmation is needed. {mention}, are you sure you want to prune decks (!yes/!no)?' )


commandSnippets["prune-players"] = "- prune-players : Drops players that didn't submit a deck"
commandCategories["day-of"].append("prune-players")
@bot.command(name='prune-players')
async def adminPruneDecks( ctx, tourn = None ):
    mention = ctx.author.mention
    gld = guildSettingsObjects[ctx.guild.id]

    if await isPrivateMessage( ctx ): return

    if not await isTournamentAdmin( ctx ): return
    adminMention = gld.getTournAdminRole().mention

    if tourn is None:
        await ctx.send( f'{mention}, you did not provide enough information. You need to specify a tournament.' )
        return

    tournObj = gld.getTournament( tourn )
    if tournObj is None:
        await ctx.send( f'{mention}, there is not a tournament called {tourn!r} on this server.' )
        return

    if await hasCommandWaiting( ctx, ctx.author.id ):
        del( commandsToConfirm[ctx.author.id] )

    commandsToConfirm[ctx.author.id] = ( getTime(), 30, tournObj.prunePlayers( ctx ) )
    await ctx.send( f'{adminMention}, in order to prune players, confirmation is needed. {mention}, are you sure you want to prune players (!yes/!no)?' )


commandSnippets["create-match"] = "- create-match : Creates a match"
commandCategories["day-of"].append("create-match")
@bot.command(name='create-match')
async def adminCreatePairing( ctx, tourn = None, *plyrs ):
    mention = ctx.author.mention
    gld = guildSettingsObjects[ctx.guild.id]
    plyrs = [ get_ID_from_mention( plyr ) for plyr in plyrs ]

    if await isPrivateMessage( ctx ): return

    if not await isTournamentAdmin( ctx ): return
    adminMention = gld.getTournAdminRole().mention

    if tourn is None:
        await ctx.send( f'{mention}, you did not provide enough information. You need to specify a tournament, match number, player, and result in order to remove a player from a match.' )
        return

    tournObj = gld.getTournament( tourn )
    if tournObj is None:
        await ctx.send( f'{mention}, there is not a tournament called {tourn!r} on this server.' )
        return

    if len(plyrs) != tournObj.playersPerMatch:
        await ctx.send( f'{mention}, {tourn} requires {tournObj.playersPerMatch} be in a match, but you specified {len(plyrs)} players.' )
        return

    # Sets can't have duplicate entries, so it filters them out
    if len(set(plyrs)) != len(plyrs):
        await ctx.send(f'{mention}, you cannot have duplicate players in a match.')
        return

    message = ""
    # This should be done in the tournament class, but will require a not method that wraps the addMatch function
    for plyr in plyrs:
        Plyr = tournObj.getPlayer( get_ID_from_mention(plyr) )
        if Plyr is None:
            message += f'{mention}, a player by {plyr!r} is not registerd for {tourn}.\n'
        if not Plyr.isActive():
            message += f'{mention}, {Plyr.getMention()} is registered but is not an active player in {tourn}.\n'

    if len(message) != 0:
        await ctx.send( content=f'{message}So, the match could not be created.' )
        return

    await tournObj.addMatch( plyrs )
    tournObj.matches[-1].saveXML( )
    tournObj.saveOverview( )
    await ctx.send( f'{mention}, the players you specified for the match are now paired. Their match number is #{tournObj.matches[-1].matchNumber}.' )


commandSnippets["pair-round"] = "- pair-round : Creates the pairings for the next round."
commandCategories["day-of"].append("pair-round")
@bot.command(name='pair-round')
async def pairRound( ctx, tourn = None ):
    mention = ctx.author.mention

    if await isPrivateMessage( ctx ): return
    gld = guildSettingsObjects[ctx.guild.id]

    if not await isTournamentAdmin( ctx ): return
    adminMention = gld.getTournAdminRole().mention

    if tourn is None:
        await ctx.send( f'{mention}, you did not provide enough information. You need to specify a tournament to pair it for its next round.' )
        return

    tournObj = gld.getTournament( tourn )
    if tournObj is None:
        await ctx.send( f'{mention}, there is not a tournament called {tourn!r} on this server.' )
        return

    response = tournObj.createPairings( mention )
    await response.send( ctx )

    if await hasCommandWaiting( ctx, ctx.author.id ):
        del( commandsToConfirm[ctx.author.id] )

    commandsToConfirm[ctx.author.id] = ( getTime(), 30, tournObj.confirmPairings( mention ) )
    await ctx.send( f'{adminMention}, in order to pair the next round, confirmation is needed. {mention}, are you sure you want to start the next round (!yes/!no)?' )


# This method will soon be depricated and will be removed when the Swiss tournament type is added
commandSnippets["create-pairings-list"] = "- create-pairings-list : Creates a list of possible match pairings (unweighted)"
commandCategories["day-of"].append("create-pairings-list")
@bot.command(name='create-pairings-list')
async def createPairingsList( ctx, tourn = None ):
    mention = ctx.author.mention

    if await isPrivateMessage( ctx ): return
    gld = guildSettingsObjects[ctx.guild.id]

    if not await isTournamentAdmin( ctx ): return
    adminMention = gld.getTournAdminRole().mention

    if tourn is None:
        await ctx.send( f'{mention}, you did not provide enough information. You need to specify a tournament, match number, player, and result in order to remove a player from a match.' )
        return

    tournObj = gld.getTournament( tourn )
    if tournObj is None:
        await ctx.send( f'{mention}, there is not a tournament called {tourn!r} on this server.' )
        return

    queue = pairingQueue( )
    for plyr in tournObj.players:
        if not plyr.isActive():
            continue
        queue.addPlayer( plyr )

    if not queue.readyToPair( tournObj.playersPerMatch ):
        await ctx.send( f'{mention}, there are not enough players in {tourn} to create a match.' )
        return

    pairings = queue.createPairings( tournObj.playersPerMatch )
    for pairing in pairings:
        for plyr in pairing:
            queue.removePlayer( tournObjself.getPlayer(plyr) )

    if queue.size() == 0:
        await ctx.send( f'{mention}, here is a list of possible pairings. No players are left unmatched.' )
    else:
        plyrs = [ f'{plyr.getMention()!r}' for lvl in queue.queue for plyr in lvl ]
        message = f'{mention}, here is a list of possible pairings. These players would be left unmatched:\n{", ".join(plyrs)}'
        for msg in splitMessage( message ):
            if msg == "":
                break
            await ctx.send( msg )

    await ctx.send( f'\nThese are the complete pairings.' )
    queueStr = [ [ f'{tournObjself.getPlayer(plyr).getMention()!r}' for plyr in pairing ] for pairing in pairings ]
    message  = "\n".join( [ ", ".join( pairing ) for pairing in queueStr ] )
    for msg in splitMessage( message ):
        if msg == "":
            break
        await ctx.send( msg )


# TODO: This should be a property
commandSnippets["set-pairing-threshold"] = "- set-pairing-threshold : Sets the number of players needed to pair the queue"
commandCategories["properties"].append("set-pairing-threshold")
@bot.command(name='set-pairing-threshold')
async def pairingsThreshold( ctx, tourn = None, num = None ):
    mention = ctx.author.mention
    gld = guildSettingsObjects[ctx.guild.id]

    if await isPrivateMessage( ctx ): return

    if not await isTournamentAdmin( ctx ): return
    adminMention = gld.getTournAdminRole().mention

    if tourn is None or num is None:
        await ctx.send( f'{mention}, you did not provide enough information. You need to specify a tournament and a number of players for a match.' )
        return

    try:
        num = int(num)
    except:
        await ctx.send( f'{mention}, {num!r} could not be converted to a number. Please make sure you only use digits.' )
        return

    tournObj = gld.getTournament( tourn )
    if tournObj is None:
        await ctx.send( f'{mention}, there is not a tournament called {tourn!r} on this server.' )
        return

    tournObj.updatePairingsThreshold( num )
    tournObj.saveOverview( )
    await ctx.send( f'{adminMention}, the pairings threshold for {tourn} was changed to {num} by {mention}.' )


commandSnippets["admin-drop"] = "- admin-drop : Removes a player for a tournament"
commandCategories["day-of"].append("admin-drop")
@bot.command(name='admin-drop')
async def adminDropPlayer( ctx, tourn = None, plyr = None ):
    mention = ctx.author.mention
    gld = guildSettingsObjects[ctx.guild.id]
    plyr = get_ID_from_mention( plyr )

    if await isPrivateMessage( ctx ): return

    if not await isTournamentAdmin( ctx ): return
    adminMention = gld.getTournAdminRole().mention

    if tourn is None or plyr is None:
        await ctx.send( f'{mention}, you did not provide enough information. You need to specify a tournament and a player.' )
        return

    tournObj = gld.getTournament( tourn )
    if tournObj is None:
        await ctx.send( f'{mention}, there is not a tournament called {tourn!r} on this server.' )
        return

    if await hasCommandWaiting( ctx, ctx.author.id ):
        del( commandsToConfirm[ctx.author.id] )

    commandsToConfirm[ctx.author.id] = ( getTime(), 30, tournObj.dropPlayerAdmin( plyr, mention ) )
    await ctx.send( f'{adminMention}, in order to drop {plyr}, confirmation is needed. {mention}, are you sure you want to drop this player (!yes/!no)?' )


commandSnippets["give-bye"] = "- give-bye : Grants a bye to a player"
commandCategories["day-of"].append("give-bye")
@bot.command(name='give-bye')
async def adminGiveBye( ctx, tourn = None, plyr = None ):
    mention = ctx.author.mention
    gld = guildSettingsObjects[ctx.guild.id]
    plyr = get_ID_from_mention( plyr )

    if await isPrivateMessage( ctx ): return

    if not await isTournamentAdmin( ctx ): return
    adminMention = gld.getTournAdminRole().mention

    if tourn is None or plyr is None:
        await ctx.send( f'{mention}, you did not provide enough information. You need to specify a tournament and a player.' )
        return

    tournObj = gld.getTournament( tourn )
    if tournObj is None:
        await ctx.send( f'{mention}, there is not a tournament called {tourn!r} on this server.' )
        return

    response = await tournObj.addBye( plyr, mention )
    await response.send( ctx )


commandSnippets["remove-match"] = "- remove-match : Removes a match"
commandCategories["day-of"].append("remove-match")
@bot.command(name='remove-match')
async def adminRemoveMatch( ctx, tourn = None, mtch = None ):
    mention = ctx.author.mention
    gld = guildSettingsObjects[ctx.guild.id]

    if await isPrivateMessage( ctx ): return

    if not await isTournamentAdmin( ctx ): return
    adminMention = gld.getTournAdminRole().mention

    if tourn is None or mtch is None:
        await ctx.send( f'{mention}, you did not provide enough information. You need to specify a tournament and a player.' )
        return

    tournObj = gld.getTournament( tourn )
    if tournObj is None:
        await ctx.send( f'{mention}, there is not a tournament called {tourn!r} on this server.' )
        return

    try:
        mtch = int( mtch )
    except:
        await ctx.send( f'{mention}, you did not provide a match number. Please specify a match number using digits.' )
        return

    # TODO: Tagging this to remember to moving this into the tournament method
    if mtch > len(tournObj.matches):
        await ctx.send( f'{mention}, the match number that you specified is greater than the number of matches. Double check the match number.' )
        return

    if await hasCommandWaiting( ctx, ctx.author.id ):
        del( commandsToConfirm[ctx.author.id] )

    commandsToConfirm[ctx.author.id] = ( getTime(), 30, tournObj.removeMatch( mtch, mention ) )
    await ctx.send( f'{adminMention}, in order to remove match #{mtch}, confirmation is needed. {mention}, are you sure you want to remove this match (!yes/!no)?' )


commandSnippets["tournament-status"] = "- tournament-status : Prints the currect matchmaking queue"
commandCategories["day-of"].append("tournament-status")
@bot.command(name='tournament-status')
async def viewQueue( ctx, tourn = None ):
    mention = ctx.author.mention
    gld = guildSettingsObjects[ctx.guild.id]

    if await isPrivateMessage( ctx ): return

    if not await isTournamentAdmin( ctx ): return
    adminMention = gld.getTournAdminRole().mention

    if tourn is None:
        await ctx.send( f'{mention}, you did not provide enough information. You need to specify a tournament to view the queue.' )
        return

    tournObj = gld.getTournament( tourn )
    if tournObj is None:
        await ctx.send( f'{mention}, there is not a tournament called {tourn!r} on this server.' )
        return

    tournInfo: discord.Embed = tournObj.getTournamentStatusEmbed()

    message = await ctx.send( embed=tournInfo )
    tournObj.infoMessage = message
    tournObj.saveOverview()


commandSnippets["tricebot-kick-player"] = "- tricebot-kick-player : Kicks a player from a cockatrice match when tricebot is enabled for that match"
commandCategories["day-of"].append("tricebot-kick-player")
@bot.command(name='tricebot-kick-player')
async def tricebotKickPlayer( ctx, tourn = None, mtch = None, playerName = None ):
    mention = ctx.author.mention
    gld = guildSettingsObjects[ctx.guild.id]

    if await isPrivateMessage( ctx ): return

    if not await isTournamentAdmin( ctx ): return
    adminMention = gld.getTournAdminRole().mention

    if tourn is None or mtch is None:
        await ctx.send( f'{mention}, you did not provide enough information. You need to specify a tournament and a player.' )
        return

    tournObj = gld.getTournament( tourn )
    if tournObj is None:
        await ctx.send( f'{mention}, there is not a tournament called {tourn!r} on this server.' )
        return

    try:
        mtch = int( mtch )
    except:
        await ctx.send( f'{mention}, you did not provide a match number. Please specify a match number using digits.' )
        return

    if mtch > len(tournObj.matches):
        await ctx.send( f'{mention}, the match number that you specified is greater than the number of matches. Double check the match number.' )
        return

    Match = tournObj.matches[mtch - 1]

    if not Match.triceMatch:
        await ctx.send( f'{mention}, that match is not a match with tricebot enabled.' )
        return

    result = tournObj.kickTricePlayer(Match.gameID, playerName)

    #  1 success
    #  0 auth token is bad or error404 or network issue
    # -1 player not found
    # -2 an unknown error occurred

    if result == 1:
        await ctx.send( f'{mention}, {playerName!r} was kicked from match {mtch}.' )
    elif result == -1:
        await ctx.send( f'{mention}, {playerName!r} was not found in match {mtch}.' )
    else:
        await ctx.send( f'{mention}, An error has occured whilst kicking {playerName!r} from match {mtch}.' )


commandSnippets["tricebot-disable-pdi"] = "- tricebot-disable-pdi : Disables player deck verification."
commandCategories["day-of"].append("tricebot-disable-pdi")
@bot.command(name='tricebot-disable-pdi')
async def triceBotUpdatePlayer( ctx, tourn = None, mtch = None ):
    mention = ctx.author.mention
    gld = guildSettingsObjects[ctx.guild.id]

    if await isPrivateMessage( ctx ): return

    if not await isTournamentAdmin( ctx ): return
    adminMention = gld.getTournAdminRole().mention

    if tourn is None or mtch is None:
        await ctx.send( f'{mention}, you did not provide enough information. You need to specify a tournament and a player.' )
        return

    tournObj = gld.getTournament( tournName )
    if tournObj is None:
        await ctx.send( f'{mention}, there is not a tournament called {tournName!r} on this server.' )
        return

    # Get match
    try:
        mtch = int( mtch )
    except:
        await ctx.send( f'{mention}, you did not provide a match number. Please specify a match number using digits.' )
        return

    if mtch > len(tournObj.matches):
        await ctx.send( f'{mention}, the match number that you specified is greater than the number of matches. Double check the match number.' )
        return

    Match = tournObj.matches[mtch - 1]

    if not Match.triceMatch:
        await ctx.send( f'{mention}, that match is not a match with tricebot enabled.' )
        return
    if not Match.playerDeckVerification:
        await ctx.send( f'{mention}, that match is not a match with player deck verification enabled.' )
        return

    # Send update command
    result = trice_bot.disablePlayerDeckVerificatoin(match.gameID)
    if result == 1:
        match.playerDeckVerification = False
        await ctx.send( f'{mention}, player deck verification was disabled.' )
    else:
        await ctx.send( f'{mention}, an error occurred.' )


commandSnippets["tricebot-update-player"] = "- tricebot-update-player : Updates the cockatrice username for a player, for a game that is ongoing."
commandCategories["day-of"].append("tricebot-update-player")
@bot.command(name='tricebot-update-player')
async def triceBotUpdatePlayer( ctx, tourn = None, mtch = None, plyr = None, newTriceName = None ):
    mention = ctx.author.mention
    gld = guildSettingsObjects[ctx.guild.id]
    plyr = get_ID_from_mention( plry )

    if await isPrivateMessage( ctx ): return

    if not await isTournamentAdmin( ctx ): return
    adminMention = gld.getTournAdminRole().mention

    if tourn is None or mtch is None or plyr is None or newTriceName is None:
        await ctx.send( f'{mention}, you did not provide enough information. You need to specify a tournament, a match, a player, and their new name.' )
        return

    tournObj = gld.getTournament( tourn )
    if tournObj is None:
        await ctx.send( f'{mention}, there is not a tournament called {tourn!r} on this server.' )
        return

    # Get match
    try:
        mtch = int( mtch )
    except ValueError:
        await ctx.send( f'{mention}, you did not provide a match number. Please specify a match number using digits.' )
        return

    if mtch > len(tournObj.matches):
        await ctx.send( f'{mention}, the match number that you specified is greater than the number of matches. Double check the match number.' )
        return

    Match = tournObj.matches[mtch - 1]

    if not Match.triceMatch:
        await ctx.send( f'{mention}, that match is not a match with tricebot enabled.' )
        return
    if not Match.playerDeckVerification:
        await ctx.send( f'{mention}, that match is not a match with player deck verification enabled.' )
        return

    # Get player
    member = gld.getMember( plyr )
    oldTriceName = plyr
    if member is None:
        await ctx.send( f'{mention}, there is not a member of this server by {plyr!r}, assuming this is the problematic cockatrice name.' )

    else:
        if member.id in tournObj.players:
            oldTriceName = tournObj.players[member.id].triceName
        else:
            await ctx.send( f'{mention}, a player by {plyr!r} was found, but they have not registered for {tourn}. Make sure they register first.' )
            return

    # Send update command
    result = trice_bot.changePlayerInfo(Match.gameID, oldTriceName, newTriceName)

    # Handle result
    if result == 0:
        await ctx.send( f'{mention}, there was an error updating the game room.' )
    elif result == 1:
        await ctx.send( f'{mention}, the player information was successfully updated.' )
        if not member is None:
            tournObj.setPlayerTriceName( member.id, newTriceName ) # Update trice name
    elif result == 2:
        await ctx.send( f'{mention}, the player information was successfully updated, however a player using that player\'s name is in the game.' )
        if not member is None:
            tournObj.setPlayerTriceName( member.id, newTriceName ) # Update trice name
    elif result == -1:
        await ctx.send( f'{mention}, the game was not found, so the player information was not updated, as there no action was taken.' )
    elif result == -2:
        await ctx.send( f'{mention}, the player was not found, so no action was taken. If there are multiple players with no cockatrice names then you can ignore this error as they are still able to join.' )
    else:
        await ctx.send( f'{mention}, an unknown error has occurred.' )
        raise TriceBotAPIError( f'tricebot-update-player failed with code {result}' )


commandSnippets["download-replays"] = "- download-replays : Downloads all replays for a tournament"
commandCategories["management"].append("download-replays")
@bot.command(name='download-replays')
async def downloadReplays( ctx, tourn = None ):
    mention = ctx.message.author.mention
    gld = guildSettingsObjects[ctx.guild.id]

    if await isPrivateMessage( ctx ): return

    adminMention = getTournamentAdminMention( ctx.message.guild )
    if not await isTournamentAdmin( ctx ): return
    if tourn is None:
        await ctx.send( f'{mention}, you did not provide enough information. You need to specify a tournament to download the replays for.' )
        return

    tournObj = gld.getTournament( tourn )
    if tournObj is None:
        await ctx.send( f'{mention}, there is not a tournament called {tourn!r} on this server.' )
        return

    replayURLs = []

    # Iterate over matches
    for match in tournObj.matches:
        if match.triceMatch and match.replayURL != "":
            replayURLs.append(match.replayURL)

    if len(replayURLs) == 0:
        await ctx.send( f'{mention}, there were no replays to download.' )
        return

    # Download replays
    replaysNotFound = []
    replayFile = trice_bot.downloadReplays(replayURLs, replaysNotFound)
    if replayFile is None:
        await ctx.send( f'{mention}, an error occurred downloading the replays.' )
        return

    message = ""
    for replay in replaysNotFound:
        message += "\n\t- " + replay
    if message != "":
        message = "The following replays were unable to be downloaded:" + message

    await ctx.send( f'{mention}, here are the replays for {tourn}.\n{message}', file=discord.File(replayFile, f"{tourn}- replays.zip") )
    replayFile.close()


commandSnippets["raw-standings"] = "- raw-standings : Creates a text file with standings for Mike."
commandCategories["misc"].append( "raw-standings" )
@bot.command(name='raw-standings')
async def rawStandings( ctx, tourn = None ):
    mention = ctx.author.mention

    if await isPrivateMessage( ctx ): return
    gld = guildSettingsObjects[ctx.guild.id]

    if not await isTournamentAdmin( ctx ): return
    adminMention = gld.getTournAdminRole().mention

    if tourn is None:
        tourns = gld.currentTournaments()
        if len( tourns ) > 1:
            await ctx.send( f'{mention}, there are multiple tournaments planned in this server. Please specify which tournament you would like to see the standings of.' )
            return
        elif len( tourns ) < 1:
            await ctx.send( f'{mention}, there are no planned tournaments for this server. If you think this is an error, contact tournament staff.' )
            return
        else:
            tournObj = tourns[0]
            tourn = tournObj.name
    else:
        tournObj = gld.getTournament( tourn )
        if tournObj is None:
            await ctx.send( f'{mention}, there is not a tournament called {tourn!r} in this server".' )
            return

    standings = tournObj.getStandings( )
    if len(tournObj.players) < 1:
        await ctx.send( "There are no players registered in this tournament." )
        return

    with open( "standings.txt", mode="w+" ) as attachment:
        attachment.write( "Placement, Players, Match Points, Win Percentage, Opponent WP\n" )
        length = len(standings[0])
        for i in range(length):
            attachment.write( f'{standings[0][i]}, {standings[1][i].name.replace(",", "")}, {standings[2][i]}, {trunk(standings[3][i])}, {trunk(standings[4][i])}\n' )

    with open( "standings.txt", mode="r" ) as attachment:
        await ctx.send( content=f'{mention}, the standings for {tourn} are in the attached file.', file = discord.File( attachment, "standings.txt" ) )


async def cutTopXCoroFunc(ctx, mention, standings, tournObj, tourn, x):
    # Cut the players
    digest = commandResponse( )
    playersDropped = []
    for i in range(x, len(standings[1])):
        # Drop this player
        await tournObj.dropPlayer(standings[1][i].discordID, ctx.author.mention)
        playersDropped.append(standings[1][i].getMention())

    newLine = "\n\t- "
    digest.setContent( f'{mention}, {tourn} was cut to the top {x} players, the following players were dropped:{newLine}{newLine.join(playersDropped)}' )
    return digest

commandSnippets["cut-to-top"] = "- cut-to-top: Cuts a tournament to the top X players."
commandCategories["management"].append("cut-to-top")
@bot.command(name='cut-to-top')
async def cutToTopX( ctx, tourn = None, x = None):
    mention = ctx.author.mention
    gld = guildSettingsObjects[ctx.guild.id]

    if await isPrivateMessage( ctx ): return

    if not await isTournamentAdmin( ctx ): return
    adminMention = gld.getTournAdminRole().mention

    if tourn is None or x is None:
        await ctx.send( f'{mention}, you did not provide enough information. You need to specify a tournament and the number of players to cut to.' )
        return

    tournObj = gld.getTournament( tourn )
    if tournObj is None:
        await ctx.send( f'{mention}, there is not a tournament called {tourn!r} on this server.' )
        return

    # Validate the value of x
    try:
        x = int (x)
    except:
        await ctx.send( f"{mention}, you must insert a whole number for the amount of players to cut to." )
        return
    if x < 2:
        # Minimum to create a match
        await ctx.send( f"{mention}, you cannot cut to less than 2 players." )
        return

    standings = tournObj.getStandings( )
    if x > len(standings[1]):
        await ctx.send( f"{mention}, there are not enough players with standings to make this cut." )
        return

    # Get command confirmation
    if await hasCommandWaiting( ctx, ctx.author.id ):
        del( commandsToConfirm[ctx.author.id] )

    commandsToConfirm[ctx.author.id] = ( getTime(), 30, cutTopXCoroFunc(ctx, mention, standings, tournObj, tourn, x) )
    await ctx.send( f'{adminMention}, in order to cut players to the top {x}, confirmation is needed. {mention}, are you sure you want to remove this match (!yes/!no)?' )


"""

@bot.command(name='tournament-report')
async def adminDropPlayer( ctx, tourn = None ):

"""



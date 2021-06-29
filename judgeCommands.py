import os
import shutil
import random
import re

from discord.ext import commands
from dotenv import load_dotenv

from baseBot import *
from Tournament import * 


commandSnippets["admin-register"] = "- admin-register : Registers a player for a tournament"
commandCategories["admin-registration"].append("admin-register")
@bot.command(name='admin-register')
async def adminAddPlayer( ctx, tourn = None, plyr = None ):
    mention = ctx.author.mention
    gld = guildSettingsObjects[ctx.guild.id]

    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
    
    if tourn is None or plyr is None:
        await ctx.send( f'{mention}, you did not provide enough information. You need to specify a tournament and player in order to add someone to a tournament.' )
        return

    tournObj = gld.getTournament( tourn )
    if tournObj is None: 
        await ctx.send( f'{mention}, there is not tournament called "{tourn}" on this server.' )
        return
    
    member = gld.getMember( plyr )
    if member is None:
        await ctx.send( f'{mention}, there is not a member of this server by "{plyr}".' )
        return
    
    if member.id in tournObj.players and tournObj.players[member.id].isActive():
        await ctx.send( f'{mention}, {plyr} is already registered for {tourn}.' )
        return

    message = await tournObj.addPlayer( member, admin=True )
    tournObj.players[member.id].saveXML( )
    await ctx.send( f'{mention}, {message}' )
    await tournObj.updateInfoMessage()


commandSnippets["admin-add-deck"] = "- admin-add-deck : Registers a deck for a player in a tournament" 
commandCategories["admin-registration"].append("admin-add-deck")
@bot.command(name='admin-add-deck')
async def adminAddDeck( ctx, tourn = None, plyr = None, ident = None ):
    mention = ctx.author.mention
    gld = guildSettingsObjects[ctx.guild.id]

    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
    
    if tourn is None or plyr is None or ident is None:
        await ctx.send( f'{mention}, you did not provide enough information. You need to specify a tournament, a player, a deck identifier, and a decklist in order to add a deck for someone.' )
        return

    tournObj = gld.getTournament( tourn )
    if tournObj is None: 
        await ctx.send( f'{mention}, there is not tournament called "{tourn}" on this server.' )
        return
    
    member = gld.getMember( plyr )
    if member is None:
        await ctx.send( f'{mention}, there is not a member of this server by "{plyr}".' )
        return
    
    if not member.id in tournObj.players:
        await ctx.send( f'{mention}, a player by "{plyr}" was found, but they have not registered for {tourn}. Make sure they register first.' )
        return

    if not tournObj.players[member.id].isActive():
        await ctx.send( f'{mention}, a player by "{plyr}" was found, and they have dropped from {tourn}. Make sure they re-register first.' )
        return
    
    index = ctx.message.content.find( ident ) + len(ident)
    decklist = re.sub( "^[^A-Za-z0-9\w\/]+", "", ctx.message.content[index:].replace('"', "") ).strip() 
    decklist = re.sub( "[^A-Za-z0-9\w\/]+$", "", decklist )
    
    if decklist == "":
        await ctx.send( f'{mention}, not enough information provided: Please provide your deckname and decklist to add a deck.' )
        return
    
    print( ident, decklist )
    message = ""
    try:
        message = await tournObj.addDeck( member.id, ident, decklist, admin=True )
    except:
        await ctx.send( f'{mention}, there was an error while processing the deck list. Make sure you follow the instructions for submitting a deck. To find them, use "!squirebot-help add-deck".' )
        return

    tournObj.players[member.id].saveXML( )
    await ctx.send( f'{mention}, {message}' )
    await tournObj.updateInfoMessage()


commandSnippets["admin-remove-deck"] = "- admin-remove-deck : Removes a deck for a player in a tournament" 
commandCategories["admin-registration"].append("admin-remove-deck")
@bot.command(name='admin-remove-deck')
async def adminRemoveDeck( ctx, tourn = None, plyr = None, ident = None ):
    mention = ctx.author.mention
    gld = guildSettingsObjects[ctx.guild.id]

    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
    
    if tourn is None or plyr is None or ident is None:
        await ctx.send( f'{mention}, you did not provide enough information. You need to specify a tournament, a player, a deck identifier, and a decklist in order to add a deck for someone.' )
        return

    tournObj = gld.getTournament( tourn )
    if tournObj is None: 
        await ctx.send( f'{mention}, there is not tournament called "{tourn}" on this server.' )
        return
    
    member = gld.getMember( plyr )
    if member is None:
        await ctx.send( f'{mention}, there is not a member of this server by "{plyr}".' )
        return
    
    if not member.id in tournObj.players:
        await ctx.send( f'{mention}, a player by "{plyr}" was found, but they have not registered for {tourn}. Make sure they register first.' )
        return

    if not tournObj.players[member.id].isActive():
        await ctx.send( f'{mention}, a player by "{plyr}" was found, and they have dropped from {tourn}. Make sure they re-register first.' )
        return
    
    deckName = tournObj.players[member.id].getDeckIdent( ident )
    if deckName == "":
        await ctx.send( f'{mention}, it appears that {plyr} does not have a deck whose name nor hash is "{ident}" registered for {tourn}.' )
        return
        
    if await hasCommandWaiting( ctx, ctx.author.id ):
        del( commandsToConfirm[ctx.author.id] )

    commandsToConfirm[ctx.author.id] = ( getTime(), 30, tournObj.players.removeDeck( member.id, deckName, mention ) )
    await ctx.send( f'{mention}, in order to remove the deck {deckName} from {member.mention}, confirmation is needed. Are you sure you want to remove the deck (!yes/!no)?' )


commandSnippets["list-players"] = "- list-players : Lists all player (or the number of players) in a tournament " 
commandCategories["admin-misc"].append("list-players")
@bot.command(name='list-players')
async def adminListPlayers( ctx, tourn = None, num = None ):
    mention = ctx.author.mention
    gld = guildSettingsObjects[ctx.guild.id]

    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
    
    if tourn is None:
        await ctx.send( f'{mention}, you did not provide enough information. You need to specify a tournament in order to list the players.' )
        return

    tournObj = gld.getTournament( tourn )
    if tournObj is None: 
        await ctx.send( f'{mention}, there is not tournament called "{tourn}" on this server.' )
        return
    
    if len( tournObj.players ) == 0:
        await ctx.send( f'{mention}, there are no players registered for the tournament {tourn}.' )
        return
    
    # We check to see if the discordUser is None to see if the player has left the server.
    # TODO: There are plans to track players that leave
    # Moreover, the addition of dummy players will cause issues
    playerNames = [ tournObj.players[plyr].getMention() for plyr in tournObj.players if tournObj.players[plyr].isActive() and not tournObj.players[plyr].discordUser is None ]
    if num == "n" or num == "num" or num == "number":
        await ctx.send( f'{mention}, there are {len(playerNames)} active players in {tourn}.' )
        return
    else:
        newLine = "\n\t- "
        await ctx.send( f'{mention}, the following are all active players registered for {tourn}:' )
        message = f'{newLine}{newLine.join(playerNames)}'
        for msg in splitMessage( message ):
            await ctx.send( msg )
    

commandSnippets["player-profile"] = "- player-profile : Lists out a player's profile, including decks names, matches, and status" 
commandCategories["admin-misc"].append("player-profile")
@bot.command(name='player-profile')
async def adminPlayerProfile( ctx, tourn = None, plyr = None ):
    mention = ctx.author.mention
    gld = guildSettingsObjects[ctx.guild.id]

    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
    
    if tourn is None:
        await ctx.send( f'{mention}, you did not provide enough information. You need to specify a tournament in order to list the players.' )
        return

    tournObj = gld.getTournament( tourn )
    if tournObj is None: 
        await ctx.send( f'{mention}, there is not tournament called "{tourn}" on this server.' )
        return
    
    member = gld.getMember( plyr )
    if member is None:
        await ctx.send( f'{mention}, there is not a member of this server by "{plyr}".' )
        return
    
    if not member.id in tournObj.players:
        await ctx.send( f'{mention}, a player by "{plyr}" was found, but they have not registered for {tourn}. Make sure they register first.' )
        return
    
    await ctx.send( content=f'{mention}, the following is the profile for {plyr}:', embed=tournObj.getPlayerProfileEmbed(member.id) )


commandSnippets["admin-match-result"] = "- admin-match-result : Record the result of a match for a player" 
commandCategories["admin-playing"].append("admin-match-result")
@bot.command(name='admin-match-result')
async def adminMatchResult( ctx, tourn = None, plyr = None, mtch = None, result = None ):
    mention = ctx.author.mention
    gld = guildSettingsObjects[ctx.guild.id]

    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
    
    if tourn is None:
        await ctx.send( f'{mention}, you did not provide enough information. You need to specify a tournament, match number, player, and result in order to remove a player from a match.' )
        return

    tournObj = gld.getTournament( tourn )
    if tournObj is None: 
        await ctx.send( f'{mention}, there is not tournament called "{tourn}" on this server.' )
        return
    
    member = gld.getMember( plyr )
    if member is None:
        await ctx.send( f'{mention}, there is not a member of this server by "{plyr}".' )
        return
    
    if not member.id in tournObj.players:
        await ctx.send( f'{mention}, a player by "{plyr}" was found, but they have not registered for {tourn}. Make sure they register first.' )
        return

    if not tournObj.players[member.id].isActive():
        await ctx.send( f'{mention}, a player by "{plyr}" was found, and they have dropped from {tourn}. Make sure they re-register first.' )
        return
    
    try:
        mtch = int( mtch )
    except ValueError:
        await ctx.send( f'{mention}, you did not provide a match number. Please specify a match number as a number.' )
        return
    
    if mtch > len(tournObj.matches):
        await ctx.send( f'{mention}, the match number that you specified is greater than the number of matches. Double check the match number.' )
        return
        
    Match = tournObj.players[member.id].getMatch( mtch )
    if Match.matchNumber == -1:
        await ctx.send( f'{mention}, {member.mention} is not a player in Match #{mtch}. Double check the match number.' )
        return
        
    message = await tournObj.recordMatchResult( member.id, result, mtch, admin=True )
    Match.saveXML( )
    await ctx.send( message )
    await tournObj.updateInfoMessage()
    

commandSnippets["admin-confirm-result"] = "- admin-confirm-result : Confirms the result of a match on a player's behalf" 
commandCategories["admin-playing"].append("admin-confirm-result")
@bot.command(name='admin-confirm-result')
async def adminConfirmResult( ctx, tourn = None, plyr = None, mtch = None ):
    mention = ctx.author.mention
    gld = guildSettingsObjects[ctx.guild.id]

    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
    
    if tourn is None:
        await ctx.send( f'{mention}, you did not provide enough information. You need to specify a tournament, match number, player, and result in order to remove a player from a match.' )
        return

    tournObj = gld.getTournament( tourn )
    if tournObj is None: 
        await ctx.send( f'{mention}, there is not tournament called "{tourn}" on this server.' )
        return
    
    member = gld.getMember( plyr )
    if member is None:
        await ctx.send( f'{mention}, there is not a member of this server by "{plyr}".' )
        return
    
    if not member.id in tournObj.players:
        await ctx.send( f'{mention}, a player by "{plyr}" was found, but they have not registered for {tourn}. Make sure they register first.' )
        return

    if not tournObj.players[member.id].isActive():
        await ctx.send( f'{mention}, a player by "{plyr}" was found, and they have dropped from {tourn}. Make sure they re-register first.' )
        return
    
    try:
        mtch = int( mtch )
    except ValueError:
        await ctx.send( f'{mention}, you did not provide a match number. Please specify a match number using digits.' )
        return
    
    if mtch > len(tournObj.matches):
        await ctx.send( f'{mention}, the match number that you specified is greater than the number of matches. Double check the match number.' )
        return
        
    Match = tournObj.players[member.id].getMatch( mtch )
    if Match.matchNumber == -1:
        await ctx.send( f'{mention}, {member.mention} is not a player in Match #{mtch}. Double check the match number.' )
        return
    
    if Match.isCertified( ):
        await ctx.send( f'{mention}, match #{mtch} is already certified. There is no need confirm the result again.' )
        return
    if member.id in Match.confirmedPlayers:
        await ctx.send( f'{mention}, match #{mtch} is not certified, but {plyr} has already certified the result. There is no need to do this twice.' )
        return
    
    message = await tournObj.confirmResult( member.id, Match.matchNumber )
    Match.saveXML( )
    await ctx.send( f'{mention}, {message}.' )
    await tournObj.updateInfoMessage()



commandSnippets["give-time-extension"] = "- give-time-extension : Give a match more time in their match" 
commandCategories["admin-playing"].append("give-time-extension")
@bot.command(name='give-time-extension')
async def giveTimeExtension( ctx, tourn = None, mtch = None, t = None ):
    mention = ctx.author.mention
    gld = guildSettingsObjects[ctx.guild.id]

    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
    
    if tourn is None or mtch is None or t is None:
        await ctx.send( f'{mention}, you did not provide enough information. You need to specify a tournament, a match number, and an amount of time.' )
        return

    tournObj = gld.getTournament( tourn )
    if tournObj is None: 
        await ctx.send( f'{mention}, there is not tournament called "{tourn}" on this server.' )
        return
    
    try:
        mtch = int( mtch )
    except:
        await ctx.send( f'{mention}, you did not provide a match number correctly. Please specify a match number using digits.' )
        return
    
    if mtch > len(tournObj.matches):
        await ctx.send( f'{mention}, the match number that you specified is greater than the number of matches. Double check the match number.' )
        return
    
    if tournObj.matches[mtch - 1].stopTimer:
        await ctx.send( f'{mention}, match #{mtch} does not have a timer set. Make sure the match is not already over.' )
        return
    
    try:
        t = int( t )
    except:
        await ctx.send( f'{mention}, you did not provide an amount of time correctly. Please specify a match number using digits.' )
        return
    
    if t < 1:
        await ctx.send( f'{mention}, you can not give time extension of less than one minute in length.' )
        return
        
    tournObj.matches[mtch - 1].giveTimeExtension( t*60 )
    tournObj.matches[mtch - 1].saveXML( )
    for plyr in tournObj.matches[mtch - 1].activePlayers:
        await tournObj.players[plyr].discordUser.send( content=f'Your match (#{mtch}) in {tourn} has been given a time extension of {t} minute{"" if t == 1 else "s"}.' )
    await ctx.send( f'{mention}, you have given match #{mtch} a time extension of {t} minute{"" if t == 1 else "s"}.' )


commandSnippets["admin-decklist"] = "- admin-decklist : Posts a decklist of a player" 
commandCategories["admin-misc"].append( "admin-decklist" )
@bot.command(name='admin-decklist')
async def adminPrintDecklist( ctx, tourn = None, plyr = None, ident = None ):
    mention = ctx.author.mention
    gld = guildSettingsObjects[ctx.guild.id]

    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
    
    if tourn is None or plyr is None or ident is None:
        await ctx.send( f'{mention}, you did not provide enough information. You need to specify a tournament, a player, a deck identifier, and a decklist in order to add a deck for someone.' )
        return

    tournObj = gld.getTournament( tourn )
    if tournObj is None: 
        await ctx.send( f'{mention}, there is not tournament called "{tourn}" on this server.' )
        return
    
    member = gld.getMember( plyr )
    if member is None:
        await ctx.send( f'{mention}, there is not a member of this server by "{plyr}".' )
        return
    
    if not member.id in tournObj.players:
        await ctx.send( f'{mention}, a player by "{plyr}" was found, but they have not registered for {tourn}. Make sure they register first.' )
        return
    
    deckName = tournObj.players[member.id].getDeckIdent( ident )
    if deckName == "":
        await ctx.send( f'{mention}, {plyr} does not have any decks registered for {tourn}.' )
        return

    await ctx.send( embed = await tournObj.players[member.id].getDeckEmbed( deckName ) )


commandSnippets["match-status"] = "- match-status : View the currect status of a match" 
commandCategories["admin-misc"].append("match-status")
@bot.command(name='match-status')
async def matchStatus( ctx, tourn = None, mtch = None ):
    mention = ctx.author.mention
    gld = guildSettingsObjects[ctx.guild.id]

    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
    
    if tourn == "" or mtch == "":
        await ctx.send( f'{mention}, you did not provide enough information. You need to specify a tournament, a match number, and an amount of time.' )
        return

    tournObj = gld.getTournament( tourn )
    if tournObj is None: 
        await ctx.send( f'{mention}, there is not tournament called "{tourn}" on this server.' )
        return
    
    try:
        mtch = int( mtch )
    except:
        await ctx.send( f'{mention}, you did not provide a match number correctly. Please specify a match number using digits.' )
        return
    
    if mtch > len(tournObj.matches):
        await ctx.send( f'{mention}, the match number that you specified is greater than the number of matches. Double check the match number.' )
        return
    
    await ctx.send( f'{mention}, here is the status of match #{mtch}:', embed=tournObj.getMatchEmbed( mtch-1 ) )



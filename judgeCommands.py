import os
import shutil
import random

from discord.ext import commands
from dotenv import load_dotenv

from baseBot import *
from Tournament import * 


commandSnippets["admin-register"] = "- admin-register : Registers a player for a tournament"
commandCategories["admin-registration"].append("admin-register")
@bot.command(name='admin-register')
async def adminAddPlayer( ctx, tourn = "", plyr = "" ):
    tourn = tourn.strip()
    plyr  = plyr.strip()
    
    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
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
    
    if userIdent in tournaments[tourn].players:
        await ctx.send( f'{ctx.message.author.mention}, {plyr} is already registered for {tourn}.' )
        return

    await member.add_roles( tournaments[tourn].role )
    await tournaments[tourn].addPlayer( member, admin=True )
    tournaments[tourn].players[userIdent].saveXML( )
    await tournaments[tourn].players[userIdent].discordUser.send( content=f'You have been registered for {tourn} on the server "{ctx.guild.name}".' )
    await ctx.send( f'{ctx.message.author.mention}, you have added {member.mention} to {tourn}.' )


commandSnippets["admin-add-deck"] = "- admin-add-deck : Registers a deck for a player in a tournament" 
commandCategories["admin-registration"].append("admin-add-deck")
@bot.command(name='admin-add-deck')
async def adminAddDeck( ctx, tourn = "", plyr = "", ident = "", *decklist ):
    tourn = tourn.strip()
    plyr  =  plyr.strip()
    ident = ident.strip()
    decklist = " ".join( [ "\n"+card.strip() if isNumber(card) else card.strip() for card in decklist  ] )
    
    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
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
    if not userIdent in tournaments[tourn].players:
        await ctx.send( f'{ctx.message.author.mention}, a user by "{plyr}" was found in the player role, but they are not active in {tourn}. Make sure they are registered or that they have not dropped.' )
        return
    
    tournaments[tourn].players[userIdent].addDeck( ident, decklist )
    tournaments[tourn].players[userIdent].saveXML( )
    deckHash = str(tournaments[tourn].players[userIdent].decks[ident].deckHash)
    await ctx.send( f'{ctx.message.author.mention}, decklist that you added for {plyr} has been submitted. The deck hash is "{deckHash}".' )
    await tournaments[tourn].players[userIdent].discordUser.send( content=f'A decklist has been submitted for {tourn} on the server {ctx.guild.name} on your behalf. The name of the deck is "{ident}" and the deck hash is "{deckHash}". If this deck hash is incorrect or you are not expecting this, please contact tournament staff.' )


commandSnippets["admin-remove-deck"] = "- admin-remove-deck : Removes a deck for a player in a tournament" 
commandCategories["admin-registration"].append("admin-remove-deck")
@bot.command(name='admin-remove-deck')
async def adminRemoveDeck( ctx, tourn = "", plyr = "", ident = "" ):
    tourn = tourn.strip()
    plyr  =  plyr.strip()
    ident = ident.strip()

    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
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
    if not userIdent in tournaments[tourn].players:
        await ctx.send( f'{ctx.message.author.mention}, a user by "{plyr}" was found in the player role, but they are not active in the tournament "{tourn}". Make sure they are registered or that they have not dropped.' )
        return
    
    deckName = tournaments[tourn].players[userIdent].getDeckIdent( ident )
    if deckName == "":
        await ctx.send( f'{ctx.message.author.mention}, it appears that {plyr} does not have a deck whose name nor hash is "{ident}" registered for {tourn}.' )
        return
        
    authorIdent = getUserIdent( ctx.message.author )
    if await hasCommandWaiting( ctx, authorIdent ):
        del( commandsToConfirm[authorIdent] )

    commandsToConfirm[authorIdent] = ( getTime(), 30, tournaments[tourn].players[userIdent].removeDeckCoro( deckName, ctx.message.author.mention ) )
    await ctx.send( f'{ctx.message.author.mention}, in order to remove the deck {deckName} from {member.mention}, confirmation is needed. Are you sure you want to remove the deck?' )


commandSnippets["list-players"] = "- list-players : Lists all player (or the number of players) in a tournament " 
commandCategories["admin-misc"].append("list-players")
@bot.command(name='list-players')
async def adminListPlayers( ctx, tourn = "", num = "" ):
    tourn = tourn.strip()
    num   = num.strip().lower()
    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament in order to list the players.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    if len( tournaments[tourn].players ) == 0:
        await ctx.send( f'{ctx.message.author.mention}, there are no players registered for the tournament {tourn}.' )
        return
    
    playerNames = [ tournaments[tourn].players[plyr].discordUser.mention for plyr in tournaments[tourn].players if tournaments[tourn].players[plyr].isActive() and not tournaments[tourn].players[plyr].discordUser is None ]
    if num == "n" or num == "num" or num == "number":
        await ctx.send( f'{ctx.message.author.mention}, there are {len(playerNames)} active players in {tourn}.' )
        return
    else:
        newLine = "\n\t- "
        await ctx.send( f'{ctx.message.author.mention}, the following are all active players registered for {tourn}:' )
        message = f'{newLine}{newLine.join(playerNames)}'
        for msg in splitMessage( message ):
            await ctx.send( msg )
    

commandSnippets["player-profile"] = "- player-profile : Lists out a player's profile, including decks names, matches, and status" 
commandCategories["admin-misc"].append("player-profile")
@bot.command(name='player-profile')
async def adminPlayerProfile( ctx, tourn = "", plyr = "" ):
    tourn = tourn.strip()
    plyr  = plyr.strip()
    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
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
    if not userIdent in tournaments[tourn].players:
        await ctx.send( f'{ctx.message.author.mention}, a user by "{plyr}" was found in the player role, but they are not active in the tournament "{tourn}". Make sure they are registered or that they have not dropped.' )
        return
    
    #await ctx.send( f'{ctx.message.author.mention}, the following is the profile for the player "{plyr}":\n{tournaments[tourn].players[userIdent]}' )
    await ctx.send( content=f'{ctx.message.author.mention}, the following is the profile for {plyr}:', embed=tournaments[tourn].getPlayerProfileEmbed(userIdent) )


commandSnippets["admin-match-result"] = "- admin-match-result : Record the result of a match for a player" 
commandCategories["admin-playing"].append("admin-match-result")
@bot.command(name='admin-match-result')
async def adminMatchResult( ctx, tourn = "", plyr = "", mtch = "", result = "" ):
    tourn  = tourn.strip()
    plyr   = plyr.strip()
    mtch   = mtch.strip()
    result = result.strip()
    
    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
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
    if not userIdent in tournaments[tourn].players:
        await ctx.send( f'{ctx.message.author.mention}, a user by "{plyr}" was found in the player role, but they are not active in the tournament "{tourn}". Make sure they are registered or that they have not dropped.' )
        return
    
    try:
        mtch = int( mtch )
    except:
        await ctx.send( f'{ctx.message.author.mention}, you did not provide a match number. Please specify a match number as a number.' )
        return
    
    if mtch > len(tournaments[tourn].matches):
        await ctx.send( f'{ctx.message.author.mention}, the match number that you specified is greater than the number of matches. Double check the match number.' )
        return
        
    Match = tournaments[tourn].players[userIdent].getMatch( mtch )
    if Match.matchNumber == -1:
        await ctx.send( f'{ctx.message.author.mention}, {member.mention} is not a player in Match #{mtch}. Double check the match number.' )
        return
        
    if result == "w" or result == "win" or result == "winner":
        message = f'{Match.role.mention}, {member.mention} has been recorded as the winner of your match by tournament admin.'
        if Match.isCertified( ):
            Match.winner = userIdent
            await ctx.send( f'{ctx.message.author.mention}, match #{mtch} is already certified. There is no need to recertify the result of this match.' )
        else:
            msg = await Match.recordWinner( userIdent )
            if msg == "":
                await tournaments[tourn].pairingsChannel.send( f'{message} Please certify this result.' )
            else:
                await tournaments[tourn].pairingsChannel.send( msg )
    elif result == "d" or result == "draw":
        message = f'{Match.role.mention}, your match has been recorded as a draw by tournament admin.'
        if Match.isCertified( ):
            Match.winner = "This match is a draw."
            await tournaments[tourn].pairingsChannel.send( f'{message} There is no need to recertify the result of this match.' )
        else:
            msg  = await Match.recordWinner( "" )
            msg += await Match.confirmResult( userIdent )
            if msg == "":
                await tournaments[tourn].pairingsChannel.send( f'{message} Please certify this result.' )
            else:
                await tournaments[tourn].pairingsChannel.send( msg )
    elif result == "l" or result == "loss" or result == "loser":
        message = await Match.dropPlayer( userIdent )
        if message != "":
            await tournaments[tourn].pairingsChannel.send( message )
        await tournaments[tourn].players[userIdent].discordUser.send( content=f'You were dropped from Match #{mtch} in {tourn} on the server {ctx.guild.name}. If you believe this was an error, contact tournament admin.' )
        await ctx.send( f'{ctx.message.author.mention}, you have recorded {plyr} as a loser in match #{mtch}.' )
    else:
        await ctx.send( f'{ctx.message.author.mention}, you have provided an incorrect result. The options are "win", "loss", and "draw". Please re-enter the correct result.' )
        return
    
    await ctx.send( f'{ctx.message.author.mention}, the players in match #{mtch} have been notified of this change.' )

    Match.saveXML( )
    

commandSnippets["admin-confirm-result"] = "- admin-confirm-result : Confirms the result of a match on a player's behalf" 
commandCategories["admin-playing"].append("admin-confirm-result")
@bot.command(name='admin-confirm-result')
async def adminConfirmResult( ctx, tourn = "", plyr = "", mtch = "" ):
    tourn  = tourn.strip()
    plyr   = plyr.strip()
    mtch   = mtch.strip()
    
    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
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
    if not userIdent in tournaments[tourn].players:
        await ctx.send( f'{ctx.message.author.mention}, a user by "{plyr}" was found in the player role, but they are not active in the tournament "{tourn}". Make sure they are registered or that they have not dropped.' )
        return
    
    try:
        mtch = int( mtch )
    except:
        await ctx.send( f'{ctx.message.author.mention}, you did not provide a match number. Please specify a match number using digits.' )
        return
    
    if mtch > len(tournaments[tourn].matches):
        await ctx.send( f'{ctx.message.author.mention}, the match number that you specified is greater than the number of matches. Double check the match number.' )
        return
        
    Match = tournaments[tourn].players[userIdent].getMatch( mtch )
    if Match.matchNumber == -1:
        await ctx.send( f'{ctx.message.author.mention}, {member.mention} is not a player in Match #{mtch}. Double check the match number.' )
        return
    
    if Match.isCertified( ):
        await ctx.send( f'{ctx.message.author.mention}, match #{mtch} is already certified. There is no need confirm the result again.' )
        return
    if userIdent in Match.confirmedPlayers:
        await ctx.send( f'{ctx.message.author.mention}, match #{mtch} is not certified, but {plyr} has already certified the result. There is no need to do this twice.' )
        return
    
    await tournaments[tourn].players[userIdent].discordUser.send( content=f'The result of match #{mtch} for {tourn} has been certified by tournament staff on your behalf.' )
    msg = await Match.confirmResult( userIdent )
    Match.saveXML( )
    if msg != "":
        await tournaments[tourn].pairingsChannel.send( msg )
    await ctx.send( f'{ctx.message.author.mention}, you have certified the result of match #{mtch} on behalf of {plyr}.' )



commandSnippets["give-time-extension"] = "- give-time-extension : Give a match more time in their match" 
commandCategories["admin-playing"].append("give-time-extension")
@bot.command(name='give-time-extension')
async def giveTimeExtension( ctx, tourn = "", mtch = "", t = "" ):
    tourn = tourn.strip()
    mtch  =  mtch.strip()
    t     =  t.strip()

    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
    if tourn == "" or mtch == "" or t == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament, a match number, and an amount of time.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    try:
        mtch = int( mtch )
    except:
        await ctx.send( f'{ctx.message.author.mention}, you did not provide a match number correctly. Please specify a match number using digits.' )
        return
    
    if mtch > len(tournaments[tourn].matches):
        await ctx.send( f'{ctx.message.author.mention}, the match number that you specified is greater than the number of matches. Double check the match number.' )
        return
    
    if tournaments[tourn].matches[mtch - 1].stopTimer:
        await ctx.send( f'{ctx.message.author.mention}, match #{mtch} does not have a timer set. Make sure the match is not already over.' )
        return
    
    try:
        t = int( t )
    except:
        await ctx.send( f'{ctx.message.author.mention}, you did not provide an amount of time correctly. Please specify a match number using digits.' )
        return
    
    if t < 1:
        await ctx.send( f'{ctx.message.author.mention}, you can not give time extension of less than one minute in length.' )
        return
        
    tournaments[tourn].matches[mtch - 1].giveTimeExtension( t*60 )
    tournaments[tourn].matches[mtch - 1].saveXML( )
    for plyr in tournaments[tourn].matches[mtch - 1].activePlayers:
        await tournaments[tourn].players[plyr].discordUser.send( content=f'Your match (#{mtch}) in {tourn} has been given a time extension of {t} minute{"" if t == 1 else "s"}.' )
    await ctx.send( f'{ctx.message.author.mention}, you have given match #{mtch} a time extension of {t} minute{"" if t == 1 else "s"}.' )



commandSnippets["admin-decklist"] = "- admin-decklist : Posts a decklist of a player" 
commandCategories["admin-misc"].append( "admin-decklist" )
@bot.command(name='admin-decklist')
async def adminPrintDecklist( ctx, tourn = "", plyr = "", ident = "" ):
    tourn = tourn.strip()
    plyr  =  plyr.strip()
    ident = ident.strip()

    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
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
    if not userIdent in tournaments[tourn].players:
        await ctx.send( f'{ctx.message.author.mention}, a user by "{plyr}" was found in the player role, but they are not active in the tournament "{tourn}". Make sure they are registered or that they have not dropped.' )
        return
    
    deckName = tournaments[tourn].players[userIdent].getDeckIdent( ident )
    if deckName == "":
        await ctx.send( f'{ctx.message.author.mention}, {plyr} does not have any decks registered for {tourn}.' )
        return

    await ctx.send( embed = await tournaments[tourn].players[userIdent].getDeckEmbed( deckName ) )


commandSnippets["match-status"] = "- match-status : View the currect status of a match" 
commandCategories["admin-misc"].append("match-status")
@bot.command(name='match-status')
async def matchStatus( ctx, tourn = "", mtch = "" ):
    tourn = tourn.strip()
    mtch  =  mtch.strip()

    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
    if tourn == "" or mtch == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament, a match number, and an amount of time.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    try:
        mtch = int( mtch )
    except:
        await ctx.send( f'{ctx.message.author.mention}, you did not provide a match number correctly. Please specify a match number using digits.' )
        return
    
    if mtch > len(tournaments[tourn].matches):
        await ctx.send( f'{ctx.message.author.mention}, the match number that you specified is greater than the number of matches. Double check the match number.' )
        return
    
    await ctx.send( f'{ctx.message.author.mention}, here is the status of match #{mtch}:', embed=tournaments[tourn].getMatchEmbed( mtch-1 ) )




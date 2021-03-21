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
    values  = [ "", "", "" ]
    
    for i in range(length):
        line = [ f'{places[i]}) {names[i]}\n', f'{points[i]},\t{trunk(GWP[i])}%\n', f'{trunk(OWP[i])}%\n' ]
        line_lengths = [ len(s) for s in line ]
        if (len(values[0]) + line_lengths[0] <= limit) and (len(values[1]) + line_lengths[1] <= limit) and (len(values[2]) + line_lengths[2] <= limit):
            values  = [ values[i] + line[i] for i in range(len(values)) ]
        else:
            digest.append( discord.Embed() )
            for i in range(len(headers)):
                digest[-1].add_field( name=headers[i], value=values[i] )
            values = line.copy()

    if len(digest) == 0:
        digest.append( discord.Embed() )
        for i in range(len(headers)):
            digest[-1].add_field( name=headers[i], value=values[i] )
    
    return digest
        

commandSnippets["list-tournaments"] = "- list-tournaments : Registers you for a tournament"
commandCategories["registration"].append( "list-tournaments" )
@bot.command(name='list-tournaments')
async def listTournaments( ctx ):
    if await isPrivateMessage( ctx ): return
    
    tourns = currentGuildTournaments( ctx.message.guild.name )
    if len( tourns ) == 0:
        await ctx.send( f'{ctx.message.author.mention}, there are no tournaments currently planned for this server.' )
        return
    
    newLine = "\n\t- "
    await ctx.send( f'{ctx.message.author.mention}, the following tournaments for this server are planned but have not been started:{newLine}{newLine.join(tourns)}' )


commandSnippets["register"] = "- register : Registers you for a tournament"
commandCategories["registration"].append( "register" )
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


commandSnippets["cockatrice-name"] = "- cockatrice-name : Adds your Cockatrice username to your profile" 
commandCategories["registration"].append( "cockatrice-name" )
@bot.command(name='cockatrice-name')
async def addTriceName( ctx, tourn = "", name = "" ):
    tourn = tourn.strip()
    name  = name.strip()
    
    if await isPrivateMessage( ctx ): return

    if tourn == "" and name == "":
        await ctx.send( f'{ctx.message.author.mention}, not enough information provided: You must include your Cockatrice username.' )
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


commandSnippets["add-deck"] = "- add-deck : Registers a deck for a tournament (should be sent via DM)" 
commandCategories["registration"].append( "add-deck" )
@bot.command(name='add-deck')
async def submitDecklist( ctx, tourn = "", ident = "", *decklist ):
    tourn = tourn.strip()
    ident = ident.strip()
    decklist = " ".join( [ "\n"+card.strip() if isNumber(card) else card.strip() for card in decklist  ] )

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
    await ctx.send( f'{ctx.message.author.mention}, your deck has been successfully registered. Your deck hash is "{deckHash}"; this must match your deck hash in Cockatrice. If these hashes do not match, check to see how your decklist looks using !decklist "{ident}" or !decklist {deckHash}. If there is still an error, contact tournament staff.' )
    if not await isPrivateMessage( ctx, False ):
        await ctx.send( f'{ctx.message.author.mention}, for future reference, you can submit your decklist via private message so that you do not have to publicly post your decklist.' )


commandSnippets["remove-deck"] = "- remove-deck : Removes a deck you registered" 
commandCategories["registration"].append( "remove-deck" )
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

    if await hasCommandWaiting( ctx, userIdent ):
        del( commandsToConfirm[userIdent] )

    commandsToConfirm[userIdent] = ( getTime(), 30, tournaments[tourn].players[userIdent].removeDeckCoro( deckName ) )
    await ctx.send( f'{ctx.message.author.mention}, in order to remove your deck, you need to confirm your request. Are you sure you want to remove it? (!yes/!no)' )
    

commandSnippets["list-decks"] = "- list-decks : Lists the names and hashes of the decks you've registered"
commandCategories["registration"].append( "list-decks" )
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
    

commandSnippets["drop"] = "- drop : Removes you from the tournament" 
commandCategories["registration"].append( "drop" )
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
    
    if await hasCommandWaiting( ctx, userIdent ):
        del( commandsToConfirm[userIdent] )

    commandsToConfirm[userIdent] = (getTime(), 30, tournaments[tourn].dropPlayer( userIdent ) )
    await ctx.send( f'{ctx.message.author.mention}, in order to drop from {tourn}, you need to confirm your request. Are you sure you want to drop? (!yes/!no)' )


commandSnippets["lfg"] ="- lfg : Places you into the matchmaking queue" 
commandCategories["playing"].append( "lfg" )
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
    if tournaments[tourn].players[userIdent].hasOpenMatch( ):
        await ctx.send( f'{ctx.message.author.mention}, you are in an match that is not uncertified. Please confirm the result using !confirm-result.' )
        return
    
    for lvl in tournaments[tourn].queue:
        for plyr in lvl:
            if plyr.name == userIdent:
                await ctx.send( f'{ctx.message.author.mention}, you are already in the queue. You will be paired for a match when more people join the queue.' )
                return
    
    tournaments[tourn].addPlayerToQueue( userIdent )
    tournaments[tourn].saveOverview( )
    await ctx.send( f'{ctx.message.author.mention}, you have been added to the queue.' )


commandSnippets["match-result"] = "- match-result : Records you as the winner of your match or that the match was a draw" 
commandCategories["playing"].append( "match-result" )
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


commandSnippets["confirm-result"] = "- confirm-result : Records that you agree with the declared result" 
commandCategories["playing"].append( "confirm-result" )
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
    

commandSnippets["standings"] = "- standings : Prints out the current standings" 
commandCategories["misc"].append( "standings" )
@bot.command(name='standings')
async def standings( ctx, tourn = "", printAll = "" ):
    tourn  = tourn.strip()
    if await isPrivateMessage( ctx ): return

    if tourn != "" and printAll == "":
        if not tourn in tournaments and tourn.lower() != "all":
            await ctx.send( f'{ctx.message.author.mention}, invalid option, please specify a tournament name and/or the word "all".' )
            return
        printAll = tourn
        tourn = ""
    
    if not printAll.lower() != "all" and not printAll != "":
        await ctx.send( f'{ctx.message.author.mention}, invalid option, to see the entire standings please use the word "all".' )
        return
    else:
        printAll = True if printAll.lower() == "all" else False
    
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
    
    if printAll and (ctx.message.channel.id != int( os.getenv("STANDINGS_CHANNEL_ID" ) ) and not await isTournamentAdmin( ctx, send=False )):
        await ctx.send( f'{ctx.message.author.mention}, this is not the correct channel to see the full standings. Please go to <#{os.getenv("STANDINGS_CHANNEL_ID" )}> to use this command.' )
        return
    
    standings = tournaments[tourn].getStandings( )
    name = ctx.message.author.display_name
    
    if name in standings[1] and not printAll:
        index = standings[1].index(name)
        upper = index - 12
        lower = index + 12
        if upper < 0:
            upper = 0
        for i in range(len(standings)):
            standings[i] = standings[i][upper:lower]
        
    embeds = createStandingsEmbeds( standings[0], standings[1], standings[2], standings[3], standings[4] )
    await ctx.send( content=f'{ctx.message.author.mention}, the standings for {tourn} are:', embed=embeds[0] )
    for bed in embeds[1:]:
        await ctx.send( content=" ", embed=bed )
    print( "End of the standings command" )


commandSnippets["misfortune"] = "- misfortune : Helps you resolve Wheel of Misfortune" 
commandCategories["misc"].append( "misfortune" )
@bot.command(name='misfortune')
async def misfortune( ctx, num = "" ):
    num = num.strip()
    
    userIdent = getUserIdent( ctx.message.author )
    
    playerMatch = ""
    count = 0

    for mtch in listOfMisfortunes:
        if userIdent in mtch[1].activePlayers:
            playerMatch = mtch[1]
            break
        count += 1
    
    if playerMatch == "":
        if not await isPrivateMessage( ctx, send=False ):
            await createMisfortune( ctx )
            return
        else:
            await ctx.send( f'{ctx.message.author.mention}, in order to prevent too much misfortune, you must send this inciting command from the server that is hosting your tournament.' )
            return

    try:
        num = int( num )
    except:
        await ctx.send( f'{ctx.message.author.mention}, invalid number: You must specify a number using digits. Please re-enter.' )
        return

    delete = await recordMisfortune( ctx, mtch, num )
    if delete:
        del( listOfMisfortunes[count] )


commandSnippets["flip-coins"] = f'- flip-coins : Flips coins for you (limit of {MAX_COIN_FLIPS} coins)' 
commandCategories["misc"].append( "flip-coins" )
@bot.command(name='flip-coins')
async def flipCoin( ctx, num = "", thumb = "" ):
    tmumb = thumb.strip().lower()
    try:
        num = int( num.strip() )
    except:
        await ctx.send( f'{ctx.message.author.mention}, you need to specify a number of coins to flip (using digits, not words).' )
        return
    
    if await isPrivateMessage( ctx ): return
    
    if thumb == "":
        if num > MAX_COIN_FLIPS:
            await ctx.send( f'{ctx.message.author.mention}, you specified too many coins. I can flip at most {MAX_COIN_FLIPS} at a time. I will flip that many, but you still need to have {num - MAX_COIN_FLIPS} flipped.' )
            num = MAX_COIN_FLIPS
     
        count = 0
        tmp = getrandbits( num )
        for i in range( num ):
            if ( (tmp >> i) & 1) != 0:
                count += 1
     
        await ctx.send( f'{ctx.message.author.mention}, out of {num} coin flip{"" if num == 1 else "s"} you won {count} time{"" if count == 1 else "s"}.' )

    elif thumb == "thumb" or thumb == "krark":
        if num > MAX_COIN_FLIPS/2:
            await ctx.send( f'{ctx.message.author.mention}, you specified too many coins. I can flip at most {int(MAX_COIN_FLIPS/2)} at a time with Krark\'s Thumb. I will flip that many, but you still need to have {num - int(MAX_COIN_FLIPS/2)} flipped.' )
            num = int(MAX_COIN_FLIPS/2)
     
        count = 0
        tmp = getrandbits( 2*num )
        for i in range( num ):
            if ( (tmp >> (2*i) ) & 3 ) != 0:
                count += 1
     
        await ctx.send( f'{ctx.message.author.mention}, out of {num} coin flip{"" if num == 1 else "s"} you won {count} time{"" if count == 1 else "s"}.' )
    else:
        await ctx.send( f'{ctx.message.author.mention}, invalid argument, to specify that you want to use Krark\'s Thumb, use the word "thumb" or "krark" after your number.' )
        return
    


commandSnippets["decklist"] = "- decklist : Posts one of your decklists" 
commandCategories["misc"].append( "decklist" )
@bot.command(name='decklist')
async def printDecklist( ctx, tourn = "", ident = "" ):
    tourn = tourn.strip()
    ident = ident.strip()
    
    private = await isPrivateMessage( ctx, send = False )

    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, not enough information provided: Please provide your deckname or deck hash to list your deck.' )
        return
    if ident == "":
        if private:
            await ctx.send( f'{ctx.message.author.mention}, not enough information provided: You must specify the tournament name via DM.' )
            return
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

    if not private:
        if not await correctGuild( tourn, ctx ): return
    
    userIdent = getUserIdent( ctx.message.author )
    if not await hasRegistered( tourn, userIdent, ctx ): return
    if not await isActivePlayer( tourn, userIdent, ctx ): return
    
    deckName = tournaments[tourn].players[userIdent].getDeckIdent( ident )
    if deckName == "":
        await ctx.send( f'{ctx.message.author.mention}, you do not have any decks registered for {tourn}.' )
        return

    if await isPrivateMessage( ctx, send=False ):
        await ctx.send( embed = await tournaments[tourn].players[userIdent].getDeckEmbed( deckName ) )
    else:
        if await hasCommandWaiting( ctx, userIdent ):
            del( commandsToConfirm[userIdent] )
        commandsToConfirm[userIdent] = ( getTime(), 30, tournaments[tourn].players[userIdent].getDeckEmbed( deckName ) )
        await ctx.send( f'{ctx.message.author.mention}, since you are about to post your decklist publicly, you need to confirm your request. Are you sure you want to post it? (!yes/!no)' )







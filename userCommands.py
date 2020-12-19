import os
import shutil
import random

from discord.ext import commands
from dotenv import load_dotenv


from baseBot import *
from tournament.match import match
from tournament.deck import deck
from tournament.player import player
from tournament.tournament import tournament
from tournament.tournamentUtils import *




@bot.command(name='list-tournaments')
async def listTournaments( ctx ):
    if isPrivateMessage( ctx.message ):
        await ctx.send( "A list of tournaments can't be created via private message since each tournament is associated with a guild (server)." )
        return
    
    plannedTourns = futureGuildTournaments( ctx.message.guild.name )

    if len( plannedTourns ) == 0:
        await ctx.send( f'{ctx.message.author.mention}, there are no tournaments currently planned for this guild (server).' )
        return
    
    newLine = "\n\t- "
    await ctx.send( f'{ctx.message.author.mention}, the following tournaments for this guild (server) are planned but have not been started:{newLine}{newLine.join(plannedTourns)}' )

@bot.command(name='register')
async def registerPlayer( ctx, tourn = "" ):
    tourn = tourn.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't join a tournament via private message since each tournament needs to be associated with a guild (server)." )
        return

    if tourn == "":
        if len( futureGuildTournaments( ctx.message.guild.name ) ) != 1:
            await ctx.send( f'{ctx.message.author.mention}, there are more than one planned tournaments for this server. Please specify what tournament you want to register for.' )
            return
        else:
            tourn = [ name for name in futureGuildTournaments( ctx.message.guild.name ) ][0]
    if not tourn in currentTournaments or currentTournaments[tourn].hostGuildName != ctx.message.guild.name:
        await ctx.send( f'{ctx.message.author.mention}, there is not a tournament named "{tourn}" in this guild (server).' )
        return
    if not currentTournaments[tourn].regOpen:
        await ctx.send( f'{ctx.message.author.mention}, registration for the tournament named "{tourn}" appears to be closed. Please contact tournament staff if you think this is an error.' )
        return
    if ctx.message.author.name in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, it appears that you are already registered for the tournament named "{tourn}". Best of luck and long my you reign!!' )
        return

    currentTournaments[tourn].addPlayer( ctx.message.author )
    currentTournaments[tourn].activePlayers[ctx.message.author.name].addDiscordUser( ctx.message.author )
    currentTournaments[tourn].activePlayers[ctx.message.author.name].saveXML( f'currentTournaments/{currentTournaments[tourn].tournName}/players/{ctx.message.author.name}.xml' )
    await ctx.send( f'{ctx.message.author.mention}, you have been added to the tournament named "{tourn}" in this guild (server)!' )


@bot.command(name='list-decks')
async def listDecklists( ctx, tourn = "" ):
    tourn = tourn.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't list the decks you've submitted for a tournament via private message since each tournament needs to be associated with a guild (server)." )
        return

    if tourn == "":
        if len( futureGuildTournaments( ctx.message.guild.name ) ) != 1:
            await ctx.send( f'{ctx.message.author.mention}, there are more than one planned tournaments for this server. Please specify a tournament to list your decks.' )
            return
        else:
            tourn = [ name for name in futureGuildTournaments( ctx.message.guild.name ) ][0]
    if not tourn in currentTournaments or currentTournaments[tourn].hostGuildName != ctx.message.guild.name:
        await ctx.send( f'{ctx.message.author.mention}, there is not a tournament named "{tourn}" in this guild (server).' )
        return
    if not ctx.message.author.name in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, you need to register before you can submit a decklist. Please you the register command to do so.' )
        return
    if len( currentTournaments[tourn].activePlayers[ctx.message.author.name].decks ) == 0:
        await ctx.send( f'{ctx.message.author.mention}, you have not registered any decks for the tournament called "{tourn}".' )
        return
    
    decks  = currentTournaments[tourn].activePlayers[ctx.message.author.name].decks
    digest = [ deck + ":  " + str(decks[deck].deckHash) for deck in decks ]
    
    newLine = "\n\t- "
    await ctx.send( f'{ctx.message.author.mention}, here are the decks that you currently have registered:{newLine}{newLine.join( digest )}' )


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
    
    if not tourn in currentTournaments:
        await ctx.send( f'{ctx.message.author.mention}, there is not a tournament named "{tourn}" in this guild (server).' )
        return
    if not ctx.message.author.name in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, you need to register before you can submit a decklist. Please you the register command to do so.' )
        return
    if not currentTournaments[tourn].regOpen:
        await ctx.send( f'{ctx.message.author.mention}, it appears that registration for this tournament is already closed. If you think this an error, talk to a tournament admin.' )
        return
    
    currentTournaments[tourn].activePlayers[ctx.message.author.name].addDeck( ident, decklist )
    currentTournaments[tourn].activePlayers[ctx.message.author.name].saveXML( f'currentTournaments/{currentTournaments[tourn].tournName}/players/{ctx.message.author.name}.xml' )
    deckHash = str(currentTournaments[tourn].activePlayers[ctx.message.author.name].decks[ident].deckHash)
    await ctx.send( f'{ctx.message.author.mention}, your decklist has been submitted. Your deck hash is "{deckHash}". Please make sure this matches your deck hash in Cocktrice.' )
    if not isPrivateMessage( ctx.message ):
        await ctx.send( f'{ctx.message.author.mention}, for future reference, you can submit your decklist via private message so that you do not have to publicly post your decklist.' )

@bot.command(name='remove-deck')
async def removeDecklist( ctx, tourn = "", ident = "" ):
    tourn = tourn.strip()
    ident = ident.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't join a tournament via private message since each tournament needs to be associated with a guild (server)." )
        return

    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provided enough information. Please provide either your deckname or deck hash to remove your deck.' )
        return
    if ident == "":
        if len( futureGuildTournaments( ctx.message.guild.name ) ) != 1:
            await ctx.send( f'{ctx.message.author.mention}, there are more than one planned tournaments for this server. Please specify a tournament to remove your deck.' )
            return
        else:
            ident = tourn
            tourn = [ name for name in futureGuildTournaments( ctx.message.guild.name ) ][0]
    if not tourn in currentTournaments:
        await ctx.send( f'{ctx.message.author.mention}, the tournament "{tourn}" does not exist. Double-check the name. If you still are having issues, contact a tournament admin.' )
        return
    if not ctx.message.author.name in currentTournaments[tourn].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, you need to register before managing your decklists. Please you the register command to do so.' )
        return
    
    deckName = ""
    print( [ currentTournaments[tourn].activePlayers[ctx.message.author.name].decks[deck].deckHash for deck in currentTournaments[tourn].activePlayers[ctx.message.author.name].decks ] )
    if ident in currentTournaments[tourn].activePlayers[ctx.message.author.name].decks:
        deckName = ident
    # Is the second argument in the player's deckhashes? Yes, then deckName will equal the name of the deck that corresponds to that hash.
    for deck in currentTournaments[tourn].activePlayers[ctx.message.author.name].decks:
        if ident == currentTournaments[tourn].activePlayers[ctx.message.author.name].decks[deck].deckHash:
            deckName = deck 
    if deckName == "":
        await ctx.send( f'{ctx.message.author.mention}, it appears that you do not have a deck whose name nor hash is "{ident}" registered for the tournament "{arg1}".' )
        return
    
    del( currentTournaments[arg1].activePlayers[ctx.message.author.name].decks[deckName] )
    currentTournaments[arg1].activePlayers[ctx.message.author.name].saveXML( f'currentTournaments/{currentTournaments[arg1].tournName}/players/{ctx.message.author.name}.xml' )
    await ctx.send( f'{ctx.message.author.mention}, your decklist whose name or deck hash was "{ident}" has been deleted.' )
    
"""
Future commands:

@bot.command(name='queue')
async def queuePlayer( ctx, tourn = "" ):

@bot.command(name='trice-name')
async def addTriceName( ctx, name = "" ):

"""






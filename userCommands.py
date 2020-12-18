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
async def registerPlayer( ctx, arg = "" ):
    arg = arg.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't join a tournament via private message since each tournament needs to be associated with a guild (server)." )
        return

    if arg == "":
        if len( futureGuildTournaments( ctx.message.guild.name ) ) != 1:
            await ctx.send( f'{ctx.message.author.mention}, there are more than one planned tournaments for this server. Please specify what tournament you want to register for.' )
            return
        else:
            arg = [ name for name in futureGuildTournaments( ctx.message.guild.name ) ][0]
    if not arg in currentTournaments or currentTournaments[arg].hostGuildName != ctx.message.guild.name:
        await ctx.send( f'{ctx.message.author.mention}, there is not a tournament named "{arg}" in this guild (server).' )
        return
    if not currentTournaments[arg].regOpen:
        await ctx.send( f'{ctx.message.author.mention}, registration for the tournament named "{arg}" appears to be closed. Please contact tournament staff if you think this is an error.' )
        return
    if ctx.message.author.name in currentTournaments[arg].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, it appears that you are already registered for the tournament named "{arg}". Best of luck and long my you reign!!' )
        return

    currentTournaments[arg].addPlayer( ctx.message.author )
    currentTournaments[arg].activePlayers[ctx.message.author.name].addDiscordUser( ctx.message.author )
    currentTournaments[arg].activePlayers[ctx.message.author.name].saveXML( f'currentTournaments/{currentTournaments[arg].tournName}/players/{ctx.message.author.name}.xml' )
    await ctx.send( f'{ctx.message.author.mention}, you have been added to the tournament named "{arg}" in this guild (server)!' )


@bot.command(name='list-decks')
async def listDecklists( ctx, arg = "" ):
    arg = arg.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't list the decks you've submitted for a tournament via private message since each tournament needs to be associated with a guild (server)." )
        return

    if arg == "":
        if len( futureGuildTournaments( ctx.message.guild.name ) ) != 1:
            await ctx.send( f'{ctx.message.author.mention}, there are more than one planned tournaments for this server. Please specify a tournament to list your decks.' )
            return
        else:
            arg = [ name for name in futureGuildTournaments( ctx.message.guild.name ) ][0]
    if not arg in currentTournaments or currentTournaments[arg].hostGuildName != ctx.message.guild.name:
        await ctx.send( f'{ctx.message.author.mention}, there is not a tournament named "{arg}" in this guild (server).' )
        return
    if not ctx.message.author.name in currentTournaments[arg].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, you need to register before you can submit a decklist. Please you the register command to do so.' )
        return
    if len( currentTournaments[arg].activePlayers[ctx.message.author.name].decks ) == 0:
        await ctx.send( f'{ctx.message.author.mention}, you have not registered any decks for the tournament called "{arg}".' )
        return
    
    decks  = currentTournaments[arg].activePlayers[ctx.message.author.name].decks
    digest = [ deck + ":  " + str(decks[deck].deckHash) for deck in decks ]
    
    newLine = "\n\t- "
    await ctx.send( f'{ctx.message.author.mention}, here are the decks that you currently have registered:{newLine}{newLine.join( digest )}' )


@bot.command(name='add-deck')
async def submitDecklist( ctx, arg1 = "", arg2 = "", arg3 = "" ):
    arg1 = arg1.strip()
    arg2 = arg2.strip()
    arg3 = arg3.strip()
    if arg1 == "" or arg2 == "" or arg3 == "":
        await ctx.send( f'{ctx.message.author.mention}, it appears that you did not provide enough information. You need to specify a tournament name, a deckname, and then a decklist.' )
        return

    if len(arg2) > len(arg3):
        tmp = arg2
        arg2 = arg3
        arg3 = tmp
    
    if not arg1 in currentTournaments:
        await ctx.send( f'{ctx.message.author.mention}, there is not a tournament named "{arg1}" in this guild (server).' )
        return
    if not ctx.message.author.name in currentTournaments[arg1].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, you need to register before you can submit a decklist. Please you the register command to do so.' )
        return
    if not currentTournaments[arg1].regOpen:
        await ctx.send( f'{ctx.message.author.mention}, it appears that registration for this tournament is already closed. If you think this an error, talk to a tournament admin.' )
        return
    
    currentTournaments[arg1].activePlayers[ctx.message.author.name].addDeck( arg2, arg3 )
    currentTournaments[arg1].activePlayers[ctx.message.author.name].saveXML( f'currentTournaments/{currentTournaments[arg1].tournName}/players/{ctx.message.author.name}.xml' )
    deckHash = str(currentTournaments[arg1].activePlayers[ctx.message.author.name].decks[arg2].deckHash)
    await ctx.send( f'{ctx.message.author.mention}, your decklist has been submitted. Your deck hash is "{deckHash}". Please make sure this matches your deck hash in Cocktrice.' )
    if not isPrivateMessage( ctx.message ):
        await ctx.send( f'{ctx.message.author.mention}, for future reference, you can submit your decklist via private message so that you do not have to publicly post your decklist.' )

@bot.command(name='remove-deck')
async def removeDecklist( ctx, arg1 = "", arg2 = "" ):
    arg1 = arg1.strip()
    arg2 = arg2.strip()
    if isPrivateMessage( ctx.message ):
        await ctx.send( "You can't join a tournament via private message since each tournament needs to be associated with a guild (server)." )
        return

    if arg1 == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provided enough information. Please provide either your deckname or deck hash to remove your deck.' )
        return
    if arg2 == "":
        if len( futureGuildTournaments( ctx.message.guild.name ) ) != 1:
            await ctx.send( f'{ctx.message.author.mention}, there are more than one planned tournaments for this server. Please specify a tournament to remove your deck.' )
            return
        else:
            arg2 = arg1
            arg1 = [ name for name in futureGuildTournaments( ctx.message.guild.name ) ][0]
    if not arg1 in currentTournaments:
        await ctx.send( f'{ctx.message.author.mention}, the tournament "{arg1}" does not exist. Double-check the name. If you still are having issues, contact a tournament admin.' )
        return
    if not ctx.message.author.name in currentTournaments[arg1].activePlayers:
        await ctx.send( f'{ctx.message.author.mention}, you need to register before managing your decklists. Please you the register command to do so.' )
        return
    
    deckName = ""
    print( [ currentTournaments[arg1].activePlayers[ctx.message.author.name].decks[deck].deckHash for deck in currentTournaments[arg1].activePlayers[ctx.message.author.name].decks ] )
    if arg2 in currentTournaments[arg1].activePlayers[ctx.message.author.name].decks:
        deckName = arg2
    # Is the second argument in the player's deckhashes? Yes, then deckName will equal the name of the deck that corresponds to that hash.
    for deck in currentTournaments[arg1].activePlayers[ctx.message.author.name].decks:
        if arg2 == currentTournaments[arg1].activePlayers[ctx.message.author.name].decks[deck].deckHash:
            deckName = deck 
    if deckName == "":
        await ctx.send( f'{ctx.message.author.mention}, it appears that you do not have a deck whose name nor hash is "{arg2}" registered for the tournament "{arg1}".' )
        return
    
    del( currentTournaments[arg1].activePlayers[ctx.message.author.name].decks[deckName] )
    currentTournaments[arg1].activePlayers[ctx.message.author.name].saveXML( f'currentTournaments/{currentTournaments[arg1].tournName}/players/{ctx.message.author.name}.xml' )
    await ctx.send( ctx.message.author.mention + ', your decklist whose name or deck hash was "' + arg2 + '" has been deleted.' )


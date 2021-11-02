import os
import traceback
import datetime
import discord
import random
import re
import sys
import subprocess
import uuid
import psycopg2
from random import getrandbits
from discord import Activity, ActivityType
from discord.ext import commands
from dotenv import load_dotenv

from Tournament import *


# ---------------- Help Message Methods ----------------

LINK_TO_PLAYER_CMD_DOC   = "https://gitlab.com/monarch3/SquireBot/-/tree/development/docs/UserCommands.md"
LINK_TO_JUDGE_CMD_DOC    = "https://gitlab.com/monarch3/SquireBot/-/tree/development/docs/JudgeCommands.md"
LINK_TO_ADMIN_CMD_DOC    = "https://gitlab.com/monarch3/SquireBot/-/tree/development/docs/AdminCommands.md"
LINK_TO_CRASH_COURSE_DOC = "https://gitlab.com/monarch3/SquireBot/-/tree/development/docs/CrashCourse.md"

commandSnippets = { }
commandEmbeds = { }
commandCategories = { "registration": [ ], "playing": [ ], "misc": [ ],
                      "admin-registration": [ ], "admin-playing": [ ], "admin-misc": [ ],
                      "management": [ ], "properties": [ ], "day-of": [ ] }

async def sendAdminHelpMessage( ctx ) -> None:
    embed = discord.Embed( )

    embed.add_field( name="\u200b", value="**__User Commands__**", inline = False )

    embed.add_field( name="**Registration**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["registration"] ]), inline=False )
    embed.add_field( name="**Match**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["playing"] ]), inline=False )
    embed.add_field( name="**Miscellaneous**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["misc"] ]),inline=False )

    embed.add_field( name="\u200b", value="**__Judge Commands__**", inline = False )

    embed.add_field( name="**Registration**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["admin-registration"] ]), inline=False )
    embed.add_field( name="**Match**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["admin-playing"] ]), inline=False )
    embed.add_field( name="**Miscellaneous**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["admin-misc"] ]),inline=False )

    embed.add_field( name="\u200b", value="**__Admin Commands__**", inline = False )

    embed.add_field( name="**Manage Tournament**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["management"] ]), inline=False )
    embed.add_field( name="**Properties**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["properties"] ]), inline=False )
    embed.add_field( name="**Day-Of**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["day-of"] ]),inline=False )

    embed.add_field( name="**__Additional Information__**", value=f'The full documentation for the judge commands can be found [here]({LINK_TO_JUDGE_CMD_DOC}) and admin commands [here]({LINK_TO_ADMIN_CMD_DOC}). The user commands are [here]({LINK_TO_PLAYER_CMD_DOC}), and the crash course is [here]({LINK_TO_PLAYER_CMD_DOC}). If you have ideas about how to improve this bot, [let us know](https://forms.gle/jt9Hpaz3ZcVNfeiRA)!',inline=False )

    await ctx.send( embed=embed )
    return

async def sendJudgeHelpMessage( ctx ) -> None:
    embed = discord.Embed( )

    embed.add_field( name="\u200b", value="**__User Commands__**", inline = False )

    embed.add_field( name="**Registration**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["registration"] ]), inline=False )
    embed.add_field( name="**Match**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["playing"] ]), inline=False )
    embed.add_field( name="**Miscellaneous**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["misc"] ]),inline=False )

    embed.add_field( name="\u200b", value="**__Judge Commands__**", inline = False )

    embed.add_field( name="**Registration**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["admin-registration"] ]), inline=False )
    embed.add_field( name="**Match**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["admin-playing"] ]), inline=False )
    embed.add_field( name="**Miscellaneous**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["admin-misc"] ]),inline=False )

    embed.add_field( name="**__Additional Information__**", value=f'The full documentation for the judge commands can be found [here]({LINK_TO_JUDGE_CMD_DOC}). The user commands are [here]({LINK_TO_PLAYER_CMD_DOC}), and the crash course is [here]({LINK_TO_CRASH_COURSE_DOC}). If you have ideas about how to improve this bot, [let us know](https://forms.gle/jt9Hpaz3ZcVNfeiRA)!',inline=False )

    await ctx.send( embed=embed )
    return

async def sendUserHelpMessage( ctx ) -> None:
    embed = discord.Embed( )

    embed.add_field( name="**__Registration Commands__**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["registration"] ]), inline=False )
    embed.add_field( name="**__Match Commands__**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["playing"] ]), inline=False )
    embed.add_field( name="**__Miscellaneous Commands__**", value="\n".join([ commandSnippets[cmd] for cmd in commandCategories["misc"] ]),inline=False )

    embed.add_field( name="**__Additional Information__**", value=f'Additional information about each command can be found [here]({LINK_TO_PLAYER_CMD_DOC}). There is also a [crash course]({LINK_TO_CRASH_COURSE_DOC}) for new users. If you have ideas about how to improve this bot, [let us know](https://forms.gle/jt9Hpaz3ZcVNfeiRA)!',inline=False )

    await ctx.send( embed=embed )
    return

# ---------------- Command Util Methods ----------------

# Looks through all guilds, finds the guilds where the user is a member, and
# gets the tournaments they are registered for
def getTournamentsByPlayer( user: discord.Member ) -> List:
    digest: list = [ ]
    for gld in guildSettingsObjects:
        if not guildSettingsObjects[gld].isMember( user ):
            continue
        digest += guildSettingsObjects[gld].getPlayerTournaments( user )
    return digest

async def isPrivateMessage( ctx, send: bool = True ) -> bool:
    digest = (str(ctx.message.channel.type) == 'private')
    if digest and send:
        await ctx.send( f'You are not allowed to send most commands via DM. To see what commands you can send via DM, use the !squirebot-help command.' )
    return digest

async def isAdmin( ctx, send: bool = True ) -> bool:
    digest = False
    judgeMention = getJudgeMention( ctx.guild )
    adminMention = getTournamentAdminMention( ctx.guild )
    for role in ctx.author.roles:
        digest |= str(role).lower() == "tournament admin"
        digest |= str(role).lower() == "judge"
    if not digest and send:
        await ctx.send( f'{ctx.author.mention}, invalid permissions: You are not tournament staff. Please do not use this command again or {adminMention} or {judgeMention} may intervene.' )
    return digest

async def isTournamentAdmin( ctx, send: bool = True ) -> bool:
    digest = False

    adminMention = getTournamentAdminMention( ctx.message.guild )
    for role in ctx.author.roles:
        digest |= str(role).lower() == "tournament admin"
    if not digest and send:
        await ctx.send( f'{ctx.author.mention}, invalid permissions: You are not tournament staff. Please do not use this command again or {adminMention} may intervene.' )
    return digest

async def isTournDead( tourn, ctx, send: bool = True ) -> bool:
    digest = tourn.isDead( )
    if digest and send:
        await ctx.send( f'{ctx.author.mention}, {tourn} has ended or been cancelled. Contact {tourn.tournAdminRole} if you think this is an error.' )
    return digest

async def isTournRunning( tourn, ctx, send: bool = True ) -> bool:
    digest = tourn.isActive() and not await isTournDead( tourn, ctx, False )
    if not digest and send:
        await ctx.send( f'{ctx.author.mention}, {tourn.name} has not started yet.' )
    return digest

async def isRegOpen( tourn, ctx, send: bool = True ) -> bool:
    digest = tourn.regOpen
    if send and not digest:
        await ctx.send( f'{ctx.author.mention}, registration for {tourn} is closed. Please contact tournament staff if you think this is an error.' )
    return digest

async def hasRegistered( tourn, plyr, ctx, send: bool = True ) -> bool:
    digest = plyr in tourn.players
    if send and not digest:
        await ctx.send( f'{ctx.author.mention}, you are not registered for {tourn.name}. Please register before trying to access the tournament.' )
    return digest

async def isActivePlayer( tourn, plyr, ctx, send: bool = True ) -> bool:
    digest = tournself.getPlayer(plyr).isActive( )
    if send and not digest:
        await ctx.send( f'{ctx.author.mention}, you registered for {tourn.name} but have been dropped. Contact tournament staff if you think this is an error.' )
    return digest

async def hasOpenMatch( tourn, plyr, ctx, send: bool = True ) -> bool:
    digest = tournself.getPlayer(plyr).hasOpenMatch( )
    if send and not digest:
        await ctx.send( f'{ctx.author.mention}, you are not an active player in a match. You do not need to do anything.' )
    return digest

async def hasCommandWaiting( ctx, user: int, send: bool = True ) -> bool:
    digest = user in commandsToConfirm
    if send and digest:
        await ctx.send( f'{ctx.author.mention}, you have a command waiting for your confirmation. That confirmation request is being overwriten by this one.' )
    return digest

async def createMisfortune( ctx ) -> None:
    playerMatch = None
    tourns = guildSettingsObjects[ctx.guild.id].getPlayerTournaments( ctx.author )
    for tourn in tourns:
        if tourn.players[ctx.author.id].hasOpenMatch():
            playerMatch = tourn.players[ctx.author.id].findOpenMatch()
            break
    if playerMatch is None:
        await ctx.send( f'{ctx.author.mention}, you are not in an open match, so you can not create any misfortune.' )
        return

    await ctx.send( f'{ctx.author.mention}, you have created misfortune for {playerMatch.getMention()}. How will you all respond? (send via DM)' )
    for plyr in playerMatch.activePlayers:
        await tournself.getPlayer(plyr).sendMessage( content=f'Misfortune has been created in your match. Tell me how you will respond (with "!misfortune [number]")!' )

    listOfMisfortunes.append( (ctx, playerMatch) )

async def recordMisfortune( ctx, misfortune, num: int ) -> bool:
    misfortune[1].misfortunes[ctx.author.id] = num
    await ctx.send( f'{ctx.author.mention}, your response to this misfortune has been recorded!' )
    if len( misfortune[1].misfortunes ) == len( misfortune[1].activePlayers ):
        tourns = currentGuildTournaments( misfortune[0].message.guild.name )
        for tourn in tourns.values():
            if not ctx.author.id in tourn.players:
                continue
            if tourn.players[ctx.author.id].hasOpenMatch():
                break
        newLine = "\n\t"
        printout = newLine.join( [ f'{tournself.getPlayer(plyr).getMention()}: {misfortune[1].misfortunes[plyr]}' for plyr in misfortune[1].misfortunes ] )
        await misfortune[0].send( f'{misfortune[1].role.mention}, the results of your misfortune are in!{newLine}{printout}' )
        misfortune[1].misfortunes = { }
        return True
    return False


def getJudgeMention( a_guild ) -> str:
    digest = ""
    for role in a_guild.roles:
        if str(role).lower() == "judge":
            digest = role.mention
            break
    return digest

def getTournamentAdminMention( a_guild ) -> str:
    adminMention = ""
    for role in a_guild.roles:
        if str(role).lower() == "tournament admin":
            adminMention = role.mention
            break
    return adminMention

def splitMessage( msg: str, limit: int = 2000, delim: str = "\n" ) -> List[str]:
    if len(msg) <= limit:
        return [ msg ]
    msg = msg.split( delim )
    digest = [ "" ]
    for submsg in msg:
        if len(digest[-1]) + len(submsg) <= limit:
            digest[-1] += delim + submsg
        else:
            digest.append( submsg )
    return digest


# ---------------- The Bot Base ----------------

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
MAX_COIN_FLIPS = int( os.getenv('MAX_COIN_FLIPS') )

DEV_SERVER_ID: int = None
if not os.getenv('DEV_SERVER_ID') is None:
    DEV_SERVER_ID = int( os.getenv('DEV_SERVER_ID') )

ERROR_LOG_CHANNEL_ID: int = None
if not os.getenv('ERROR_LOG_CHANNEL_ID') is None:
    ERROR_LOG_CHANNEL_ID = int( os.getenv('ERROR_LOG_CHANNEL_ID') )

random.seed( )

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

guildSettingsObjects = { }

# A dictionary indexed by user idents and consisting of creation time, duration, and a coro to be awaited
commandsToConfirm = { }

# A list of matches that we currently resolving Wheel of Misfortune
listOfMisfortunes = [ ]

savedGuildSettings = [ f'guilds/{d}' for d in os.listdir( "guilds" ) if os.path.isdir( f'guilds/{d}' ) ]


# When a player leaves a guild, the bot is to drop them from all tournaments within the guild.
@bot.event
async def on_member_remove( member ):
    for tourn in guildSettingsObjects[member.guild.id].tournaments:
        if member.id in tourn.players:
            message = await tourn.dropPlayer( member.id )
            await member.send( message )


class dbPlayer:
    def __init__(self, uuid, name, discordid, tplayers):
        self.uuid = uuid
        self.name = name
        self.discordid = discordid
        self.tplayers = tplayers

# When ready, the bot needs to looks at each pre-loaded tournament and add a discord user to each player.
@bot.event
async def on_ready():
    await bot.wait_until_ready( )
    players = []
    tournaments = []
    
    playerCount = 0
    
    print("Getting tournament data")
    for guild in bot.guilds:
        print( f'This bot is connected to {guild.name} which has {len(guild.members)}!' )
        playerCount += len(guild.members)
        
        # Read tournament data
        try:
            guildSettingsObjects[guild.id] = guildSettings( guild )
            if os.path.isdir( f'guilds/{guild.id}' ):
                await guildSettingsObjects[guild.id].load( f'guilds/{guild.id}/' )
            #else:
                #guildSettingsObjects[guild.id].save( f'guilds/{guild.id}/' )
            #guildSettingsObjects[guild.id].setEventLoop( bot.loop )
                      
            # Merge all players
            for tourn in guildSettingsObjects[guild.id].tournaments:
                print(f"Loading data for {tourn.name}")
                tournaments.append(tourn)
                tourn.uuid = str(uuid.uuid4())
                
                # get all dbPlayers
                for player in tourn.players:
                    add = True
                    for player2 in players:
                        if (player.discordID is not None and player.discordID == player2.discordid) or player.name == player2.name:
                            add = False
                            player.puuid = player2.uuid
                            player.tuuid = tourn.uuid
                            player2.tplayers.append(player)
                            break
                    if add:
                        print(f"New player {player.name} found")
                        puuid = str(uuid.uuid4())
                        player.puuid = puuid
                        player.tuuid = tourn.uuid
                        players.append(dbPlayer(puuid, player.name, player.discordID, [player]))
                            
        except Exception as ex:
            print(f'Error loading settings for {guild.name}')
            print(ex)
            traceback.print_exception(type(ex), ex, ex.__traceback__)
            
    print(f"There are {playerCount} players")
    
    # Read database details
    userfile = open("/home/danny/monarchdata/user.txt", "r")
    userfiledata = userfile.read().split("\n")
    userfile.close()

    username = userfiledata[0]
    password = userfiledata[1]
            
    # Connect to the database
    conn = psycopg2.connect(database="monarchdb", user=username, password=password, host="127.0.0.1", port="6446")
    cursor = conn.cursor()
            
    # Add players to the database
    for player in players:        
        print(f"Adding player {player.name}(<@{player.discordid}>)")
        cursor.execute("INSERT INTO Players Values (%s, %s, %s);", (player.uuid, player.name[0:30], player.discordid))
    
    # Add tournaments to the database
    for tournament in tournaments:
        print(f"Adding tournament {tournament.name}")
        format = tournament.format.lower()
        if format == "edh":
            format = "cedh"
        
        cursor.execute("INSERT INTO Tournaments (TournamentID, Format, Location, Structure, Date, TournamentName) Values (%s, %s, %s, %s, %s, %s);", (tournament.uuid, format, "discord", "fluid", getTime(), tournament.name))
    
    # Add player-tournaments to the databases
    for player in players:
        print(f"Adding tournamentplayer entries for {player.name}")
        tids = []
        for p in player.tplayers:
            if p.tuuid not in tids:
                if p.triceName is not None and p.triceName != "" and p.triceName != "None":
                    cursor.execute("INSERT INTO TournamentPlayers Values (%s, %s, %s);", (p.tuuid, player.uuid, player.triceName))
                else:                    
                    cursor.execute("INSERT INTO TournamentPlayers Values (%s, %s, NULL);", (p.tuuid, player.uuid))
                tids.append(p.tuuid)
    
    # Add decks to the database
    # parallel arrays for hashes and ids
    uniqueDecks = []
    uniqueDeckHashes = []
    uniqueDeckIDs = []
    for player in players:
        print(f"Adding decks for {player.name}")
        for p in player.tplayers:
            for deck_ in p.decks:
                deck = p.decks[deck_]
                hash = deck.deckHash
                deck_all = ""
                for i in range(len(deck.cards)):
                   deck.cards[i] = deck.cards[i].lower().replace("  ", "").strip()
                deck.cards.sort()
                for card in deck.cards:
                    sb = "SB:" in card
                    card_ = None
                    if not "SB:" in card:
                        try:
                            int( card[0] )
                            card = card.split(" ", 1)
                        except Exception:
                            card = [ card ]
                        if len( card ) == 1:
                            number = 1

                            name = card[0]
                            try:
                                card_   = cardsDB.getCard(name)
                            except CardNotFoundError as ex:
                                pass
                        else:
                            number = int( card[0].strip() )

                            name = card[1]
                            try:
                                card_   = cardsDB.getCard(name)
                            except CardNotFoundError as ex:
                                pass
                    else:
                        card = card.split(" ", 2)
                        number = int( card[1].strip() )
                        name = card[2]
                        try:
                            card_   = cardsDB.getCard(name)
                        except CardNotFoundError as ex:
                            pass
                    if card_ is not None:
                        deck_all += card_.name
                # If the deck is unique then add it to the database
                duplicateHash = False
                if hash in uniqueDeckHashes:
	                for i in range(len(uniqueDecks)):
	                    if uniqueDeckHashes[i] == hash:
                             if uniqueDecks[i] != deck_all:
                                 duplicateHash = True
                                 break
                if (hash not in uniqueDeckHashes) or duplicateHash:
                    deckID = str( uuid.uuid4() )
                    uniqueDeckHashes.append(hash)
                    uniqueDeckIDs.append(deckID)
                    uniqueDecks.append(deck_all)
                    cursor.execute("INSERT INTO Decks Values (%s, %s);", (deckID, hash))
                else:
                    for i in range(len(uniqueDecks)):
                        if uniqueDecks[i] == deck_all:
                            deckID = uniqueDeckIDs[i]
                            break
                # Add the player deck to the database
                deck.deckID = deckID
                cursor.execute("INSERT INTO TournamentDecks Values (%s, %s, %s, %s);", (deckID, player.uuid, p.tuuid, deck.ident[0:30]))
            
    # Add card-decks to the database
    for player in players:
        print(f"Adding deckcards for {player.name}")
        for p in player.tplayers:
            for deck_ in p.decks:
                deck = p.decks[deck_]
                for card in deck.cards:
                    card_ = None
                    sb = False
                    if not "SB:" in card:
                        try:
                            int( card[0] )
                            card = card.split(" ", 1)
                        except Exception:
                            card = [ card ]
                        if len( card ) == 1:
                            number = 1

                            name = card[0]
                            try:
                                card_   = cardsDB.getCard(name)
                            except CardNotFoundError as ex:
                                pass
                        else:
                            number = int( card[0].strip() )

                            name = card[1]
                            try:
                                card_   = cardsDB.getCard(name)
                            except CardNotFoundError as ex:
                                pass
                    else:
                        sb = True
                        card = card.split(" ", 2)
                        number = int( card[1].strip() )
                        name = card[2]
                        try:
                            card_   = cardsDB.getCard(name)
                        except CardNotFoundError as ex:
                            pass
                    if card_ is not None:
                        cursor.execute("INSERT INTO DeckCards Values (%s, %s, %s, %s);", (deck.deckID, card_.uuid, number, sb))
                
    # Add matches
    for tournament in tournaments:
        for match in tournament.matches:
            match.uuid = str(uuid.uuid4())
            print(f"Adding tournamentmatches {tournament.name} match {match.matchNumber}")
            replayURL = "NULL"
            if match.replayURL != "":
                replayURL = match.replayURL
            
            endTime = match.endTime
            if endTime is None or endTime == "None":
                endTime = getTime()
            
            if match.winner is not None and not isinstance(match.winner, str):
                print(f"Added {match.winner.puuid} (case 1)")
                cursor.execute("INSERT INTO Matches (MatchID, TournamentID, WinnerID, ReplayURL, Turns, Spectators, StartTime, EndTime, TimeExtension, MatchNumber, TriceMatch) Values (%s, %s, %s, %s, NULL, NULL, %s, %s, %s, %s, %s);", (match.uuid, tournament.uuid, match.winner.puuid, replayURL, match.startTime, endTime, match.timeExtension, match.matchNumber, match.triceMatch))
            elif tournament.getPlayer(match.winner) is not None:
                puuid = tournament.getPlayer(match.winner).puuid
                print(f"Added {puuid} (case 2)")
                cursor.execute("INSERT INTO Matches (MatchID, TournamentID, WinnerID, ReplayURL, Turns, Spectators, StartTime, EndTime, TimeExtension, MatchNumber, TriceMatch) Values (%s, %s, %s, %s, NULL, NULL, %s, %s, %s, %s, %s);", (match.uuid, tournament.uuid, puuid, replayURL, match.startTime, endTime, match.timeExtension, match.matchNumber, match.triceMatch))
            else:
                print("Added but draw/bye")
                cursor.execute("INSERT INTO Matches (MatchID, TournamentID, WinnerID, ReplayURL, Turns, Spectators, StartTime, EndTime, TimeExtension, MatchNumber, TriceMatch) Values (%s, %s, NULL, %s, NULL, NULL, %s, %s, %s, %s, %s);", (match.uuid, tournament.uuid, replayURL, match.startTime, endTime, match.timeExtension, match.matchNumber, match.triceMatch))
        
    # Add match players                        
    for tournament in tournaments:
        print(f"Adding matchplayers {tournament.name}")
        for match in tournament.matches:
            for player in match.confirmedPlayers:
                if player is not None:
                    cursor.execute("INSERT INTO MatchPlayers Values (%s, %s, NULL);", (player.puuid, match.uuid))
                    
    # Parse trice replay data
    for tournament in tournaments:
        for match in tournament.matches:
            if match.triceMatch:
                # Get replay
                replay = f"/home/danny/TriceBot/replays/{match.replayURL.split("replays/")[1]}"
                
                # Parse match with replay analysis tool
                proc = subprocess.Popen(["java", "-jar", "replaytool.jar", replay], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                                
                out, err = proc.communicate()
                exitcode = proc.returncode
                
                if exitcode != 0:
                    print(f"Error with replay analysis for match {match.replayURL}.\n{out}\n{err}")                    
                    continue
                
                players = []
                deckHashes = []
                spectators = 0
                turnsTaken = 0
                for line in out.split("\n"):
                    start = line.split(":")[0]
                    rest = line.split(":")[1:]
                    if start == "spectators":
                        spectators = int(rest)
                    elif start == "player":
                        players.append(rest.split(" ")[0])
                        deckHashes.append(rest.split(" ")[1])
                    elif start == "turnstaken":
                        turnsTaken = int(rest)
                
                # Get the deck ids from hashes
                deckIds = []
                for i in range(len(deckHashes)):
                    for hash in uniqueDeckHashes:
                        if hash == deckHashes[i]:
                            deckIds[i] = uniqueDeckIDs[i]
                            break
                
                # Add turns and spectators
                cursor.execute("UPDATE Matches SET Turns=%s Spectators=%s WHERE matches.matchid=%s;", (turns, spectators, match.uuid))
                
                # Assign decks played to players
                for player in match.players:
                    if p.triceName is not None and p.triceName != "" and p.triceName != "None":
                        for i in range(len(players)):
                            if players[i] == p.triceName:
                                cursor.execute("UPDATE MatchPlayers SET DeckID=%s WHERE matchplayers.playerid=%s and matchplayers.matchid=%s;", (deckIDs[i], player.puuid, match.uuid))
                
    conn.commit()
    conn.close()
    
    print("Successfully added all data to the database")
    bot.close()

# When the bot is added to a new guild, a settings object needs to be added for that guild
@bot.event
async def on_guild_join( guild ):
    if not (guild.id in guildSettingsObjects):
        guildSettingsObjects[guild.id] = guildSettings( guild )
        guildSettingsObjects[guild.id].save( f'guilds/{guild.id}/' )


# When an uncaught error occurs, the tracebot of the error needs to be printed
# to stderr, logged, and sent to the development server's error log channel
@bot.event
async def on_command_error( ctx: discord.ext.commands.Context, error: Exception ):
    error = getattr(error, 'original', error)
    traceback.print_exception( type(error), error, error.__traceback__ )

    mention = ctx.message.author.mention
    if isinstance( error, discord.ext.commands.CommandNotFound ):
        return
    elif isinstance(error, DeckRetrievalError ):
        await ctx.send( f'{mention}, your decklist can not be retrieved. Check that your URL is correct.' )
        return
    elif isinstance(error, CodFileError ):
        await ctx.send( f'{mention}, there is an error in your .cod file. Check that the file was not changed after you saved it.' )
        return
    elif isinstance(error, DecklistError ):
        await ctx.send( f'{mention}, there is an error in your decklist. Check that you entered it correctly.' )
        return
    else:
        await ctx.send( f'{mention}, there was an error while processing your command.' )

    message: str = f'{getTime()}: An error has occured on the server {ctx.guild.name}. Below is the context of the error and traceback.\n\n'
    message     += f'{ctx.message.content}\n'

    with open( "squireBotError.log", "a" ) as errorFile:
        errorFile.write( message + "".join(traceback.format_exception( type(error), error, error.__traceback__ )) )

    devServer = bot.get_guild( DEV_SERVER_ID )
    if devServer is None:
        return
    errorChannel = devServer.get_channel( ERROR_LOG_CHANNEL_ID )
    if isinstance( errorChannel, discord.TextChannel ):
        await errorChannel.send( message + f'```{"".join(traceback.format_exception( type(error), error, error.__traceback__ ))}```' )

    return


bot.remove_command( "help" )
@bot.command(name='help')
async def printHelp( ctx ):
    await ctx.send( f'{ctx.author.mention}, use the command "!squirebot-help" to see the list of my commands.' )


@bot.command(name='squirebot-help')
async def printHelp( ctx, cmd: str = "" ):
    if cmd in commandEmbeds:
        await ctx.send( embed = commandEmbeds[cmd] )
        return
    if await isPrivateMessage( ctx, send=False ):
        await sendUserHelpMessage( ctx )
        return
    if await isTournamentAdmin( ctx, send=False ):
        await sendAdminHelpMessage( ctx )
    elif await isAdmin( ctx, send=False ):
        await sendJudgeHelpMessage( ctx )
    else:
        await sendUserHelpMessage( ctx )


@bot.command(name='yes')
async def confirmCommand( ctx ):
    if not ctx.author.id in commandsToConfirm:
        await ctx.send( f'{ctx.author.mention}, there are no commands needing your confirmation.' )
        return

    if commandsToConfirm[ctx.author.id][1] <= timeDiff( commandsToConfirm[ctx.author.id][0], getTime() ):
        await ctx.send( f'{ctx.author.mention}, you waited too long to confirm. If you still wish to confirm, run your prior command and then confirm.' )
        del( commandsToConfirm[ctx.author.id] )
        return

    response = await commandsToConfirm[ctx.author.id][2]
    del( commandsToConfirm[ctx.author.id] )

    await response.send( ctx )


@bot.command(name='no')
async def denyCommand( ctx ):
    print( commandsToConfirm )
    if not ctx.author.id in commandsToConfirm:
        await ctx.send( f'{ctx.author.mention}, there are no commands needing your confirmation.' )
        return

    del( commandsToConfirm[ctx.author.id] )
    await ctx.send( f'{ctx.author.mention}, your request has been cancelled.' )

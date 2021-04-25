import os
import shutil
import xml.etree.ElementTree as ET
import random
import threading
import time
import discord
import asyncio
import warnings

from tricebot import TriceBot

from typing import List
from typing import Tuple

from .utils import *
from .match import match
from .player import player
from .deck import deck
from dotenv import load_dotenv

load_dotenv()
# Trice bot auth token must be the same as in config.conf for the tricebot
# is whitespace sensitive
TRICE_BOT_AUTH_TOKEN = os.getenv('TRICE_BOT_AUTH_TOKEN')
# This is the external URL of the tricebot for replay downloads, this is different
# to the apiURL which is a loopback address or internal IP address allowing for
# nginx or similar to be setup.
EXTERN_URL = os.getenv('EXTERN_URL')
API_URL = os.getenv('API_URL')

#init trice bot object
trice_bot = TriceBot(TRICE_BOT_AUTH_TOKEN, apiURL=API_URL, externURL=EXTERN_URL)


"""
    This is a tournament class. The bulk of data management for a tournament is handled by this class.
    It also holds certain metadata about the tournament, such as the tournament's name and host guild's name.

    These are the current functionalities that this class has (those they might not have an explicit method):
        - Tracks players, matches, and the status of the tournament (state of registeration, whether or not the tournament has started, etc.)
        - Matches can be added
        - The results for a match can be recorded and verified

    Things that will be added in the future:
        - 
    
    The class has the following member variables:
        - tournName: The name of the tournament
        - hostGuildName: The name of the server that is hosting the tournament
        - format: The format of the tournament
        - regOpen: Whether or not registeration is open
        - tournStarted: Whether or not the tournament has started
        - tournEnded: Whether or not the tournament has ended
        - tournCancel: Whether or not the tournament has been canceled
        - playersPerMatch: The number of players that will be paired per match
        - queue: A list of player names (strings) representing the players that are waiting to be paired for a match
        - activePlayers: A dict that index-s player objects that haven't dropped with their names (for ease of referencing)
        - droppedPlayers: A dict that index-s player objects that have dropped with their names (for ease of referencing)
        - matches: A list of all match objects in the tournament, regardless of status
"""
class tournament:
    def __init__( self, a_tournName: str, a_hostGuildName: str, trice_enabled: bool = False, a_format: str = "EDH", spectators_allowed: bool = True, spectators_need_password: bool = False, spectators_can_chat : bool = False, spectators_can_see_hands: bool = False, only_registered: bool = True):     
        self.tournName = a_tournName   
        #Safety Checks!!
        self.tournName.replace("\.\./", "")
        
        self.hostGuildName = a_hostGuildName
        self.format    = a_format
        
        self.saveLocation = f'currentTournaments/{self.tournName}'

        self.guild   = ""
        self.guildID = ""
        self.role    = ""
        self.roleID  = ""
        self.pairingsChannel = ""
        
        self.regOpen      = True
        self.tournStarted = False
        self.tournEnded   = False
        self.tournCancel  = False
        
        self.loop = asyncio.new_event_loop( )
        self.fail_count = 0
        
        self.queue             = [ [] ]
        self.playersPerMatch   = 2
        self.pairingsThreshold = self.playersPerMatch * 2 # + 3
        self.pairingWaitTime   = 5
        self.queueActivity     = [ ]
        self.matchLength       = 60*60 # Length of matches in seconds
        self.highestPriority   = 0
        self.pairingsThread    = threading.Thread( target=self.launch_pairings, args=(self.pairingWaitTime,) )
        
        self.deckCount = 1

        self.players  = {}
        
        self.matches = []
        
        #Create bot class and store the game creation settings
        self.triceBotEnabled = trice_enabled
        self.spectators_allowed = spectators_allowed
        self.spectators_need_password = spectators_need_password 
        self.spectators_can_chat = spectators_can_chat 
        self.spectators_can_see_hands = spectators_can_see_hands 
        self.only_registered = only_registered
            
    def isPlanned( self ) -> bool:
        return not ( self.tournStarted or self.tournEnded or self.tournCancel )
    
    def isActive( self ) -> bool:
        return self.tournStarted and not ( self.tournEnded or self.tournCancel )
    
    def isDead( self ) -> bool:
        return self.tournEnded or self.tournCancel

    def getPlayerProfileEmbed( self, a_plyr ) -> discord.Embed:
        digest = discord.Embed()
        deckPairs = [ f'{d}: {self.players[a_plyr].decks[d].deckHash}' for d in self.players[a_plyr].decks ]
        digest.add_field( name="Decks:", value=("\u200b" + "\n".join(deckPairs)) )
        for mtch in self.players[a_plyr].matches:
            players = mtch.activePlayers + mtch.droppedPlayers
            status = f'Status: {mtch.status}'
            if mtch.winner in self.players:
                winner = f'Winner: {self.players[mtch.winner].discordUser.mention}'
            else:
                winner = f'Winner: {mtch.winner if mtch.winner else "N/A"}'
            oppens = "Opponents: " + ", ".join( [ self.players[plyr].discordUser.mention for plyr in players if plyr != a_plyr ] )
            digest.add_field( name=f'Match #{mtch.matchNumber}', value=f'{status}\n{winner}\n{oppens}' )
        return digest

    def getMatchEmbed( self, mtch: int ):
        digest = discord.Embed( )
        Match = self.matches[mtch] 
        digest.add_field( name="Status", value=Match.status )
        digest.add_field( name="Active Players", value="\u200b" + ", ".join( [ self.players[plyr].discordUser.mention for plyr in Match.activePlayers ] ) )
        if len(Match.droppedPlayers) != 0:
            digest.add_field( name="Dropped Players", value=", ".join( [ self.players[plyr].discordUser.mention for plyr in Match.droppedPlayers ] ) )
        if not ( Match.isCertified() or Match.stopTimer ):
            t = Match.getTimeElapsed()
            if t > self.matchLength/60:
                digest.add_field( name="Time Remaining", value=f'0 minutes' )
            else:
                digest.add_field( name="Time Remaining", value=f'{round(self.matchLength/60 - t)} minutes' )
        if Match.winner != "":
            if Match.winner in self.players:
                digest.add_field( name="Winner", value=self.players[Match.winner].discordUser.mention )
            else:
                digest.add_field( name="Winner", value=Match.winner )
        if len(Match.confirmedPlayers) != 0:
            digest.add_field( name="Confirmed Players", value=", ".join( [ self.players[plyr].discordUser.mention for plyr in Match.confirmedPlayers ] ) )
            
        if Match.triceMatch:
            digest.addfield( name="Tricebot Match", value = ("Replay at" + replayURL) )
            
        return digest
    
    def updatePairingsThreshold( self, count: int ) -> None:
        self.pairingsThreshold = count
        if sum( [ len(level) for level in self.queue ] ) >= self.pairingsThreshold and not self.pairingsThread.is_alive():
            self.pairingsThread = threading.Thread( target=self.launch_pairings, args=(self.pairingWaitTime,) )
            self.pairingsThread.start( )

    
    def addDiscordGuild( self, a_guild ) -> None:
        self.guild = a_guild
        self.hostGuildName = a_guild.name
        self.guildID = self.guild.id
        if self.roleID != "":
            self.role = a_guild.get_role( self.roleID )
        else:
            self.role = discord.utils.get( a_guild.roles, name=f'{self.tournName} Player' )
        self.pairingsChannel = discord.utils.get( a_guild.channels, name="match-pairings" )
    
    # The name of players ought to be their Discord name + discriminator
    def assignGuild( self, a_guild ) -> None:
        print( f'The guild "{a_guild}" is being assigned to {self.tournName}.' )
        print( f'There are {len(self.players)} players in this tournament!\n' )
        self.addDiscordGuild( a_guild )
        for player in self.players:
            ID = self.players[player].discordID
            if ID != "":
                self.players[player].addDiscordUser( self.guild.get_member( ID ) )
        for match in self.matches:
            if match.roleID != "":
                match.addMatchRole( a_guild.get_role( match.roleID ) )
            if match.VC_ID != "":
                match.addMatchVC( a_guild.get_channel( match.VC_ID ) )

    def setRegStatus( self, a_status: bool ) -> str:
        if not ( self.tournEnded or self.tournCancel ):
            self.regOpen = a_status
            return ""
        elif self.tournEnded:
            return "This tournament has already ended. As such, registeration can't be opened."
        elif self.tournCancel:
            return "This tournament has been cancelled. As such, registeration can't be opened."
    
    def startTourn( self ) -> str:
        if not (self.tournStarted or self.tournEnded or self.tournCancel):
            self.tournStarted = True
            self.regOpen = False
            return ""
        elif self.tournEnded:
            return "This tournament has already ended. As such, it can't be started."
        elif self.tournCancel:
            return "This tournament has been cancelled. As such, it can't be started."
    
    async def purgeTourn( self ) -> None:
        for match in self.matches:
            match.stopTimer = True
            if type( match.VC ) == discord.VoiceChannel:
                try:
                    await match.VC.delete( )
                except:
                    pass
            if type( match.role ) == discord.Role:
                try:
                    await match.role.delete( )
                except:
                    pass
        if type( self.role ) == discord.Role:
            try:
                await self.role.delete( )
            except:
                pass
    
    async def endTourn( self, adminMention: str = "", author: str = "" ) -> str:
        if not self.tournStarted:
            return f'{self.tournName} has not started, so it can not be ended. However, it can be cancelled.'
        await self.purgeTourn( )
        self.tournEnded = False
        self.saveTournament( f'closedTournaments/{self.tournName}' )
        if os.path.isdir( f'currentTournaments/{self.tournName}' ): 
            shutil.rmtree( f'currentTournaments/{self.tournName}' )
        return f'{adminMention}, {self.tournName} has been closed by {author}.'
    
    async def cancelTourn( self, adminMention: str = "", author: str = "") -> str:
        await self.purgeTourn( )
        self.tournCancel = True
        self.saveTournament( f'closedTournaments/{self.tournName}' )
        if os.path.isdir( f'currentTournaments/{self.tournName}' ): 
            shutil.rmtree( f'currentTournaments/{self.tournName}' )
        return f'{adminMention}, {self.tournName} has been cancelled by {author}.'
    
    async def pruneDecks( self, ctx ) -> str:
        await ctx.send( f'Pruning decks starting... now!' )
        for plyr in self.players.values():
            deckIdents = [ ident for ident in plyr.decks ]
            while len( plyr.decks ) > self.deckCount:
                del( plyr.decks[deckIdents[0]] )
                await ctx.send( f'The deck {deckIdents[0]} belonging to {plyr.discordUser.mention} has been pruned.' )
                await plyr.discordUser.send( content=f'Your deck {deckIdents[0]} has been pruned from the tournament {self.tournName} on {ctx.guild.name} by tournament admin.' )
                del( deckIdents[0] )
            plyr.saveXML( )
        return f'Decks have been pruned. All players have at most {self.deckCount} deck{"" if self.deckCount == 1 else "s"}.'
    
    async def prunePlayers( self, ctx ) -> str:
        await ctx.send( f'Pruning players starting... now!' )
        for plyr in self.players:
            if len(self.players[plyr].decks) == 0:
                await self.dropPlayer( plyr ) 
                await ctx.send( f'{self.players[plyr].discordUser.mention} has been pruned.' )
                await self.players[plyr].discordUser.send( content=f'You have been dropped from the tournament {self.tournName} on {ctx.guild.name} by tournament staff for not submitting a deck. If you believe this is an error, contact them immediately.' )
                self.players[plyr].saveXML( )
        return f'All players that did not submit a deck have been pruned.'
    
    async def addPlayer( self, a_discordUser, admin=False ) -> str:
        if not admin and self.tournCancel:
            return "Sorry but this tournament has been cancelled. If you believe this to be incorrect, please contact the tournament officials."
        if not admin and self.tournEnded:
            return "Sorry, but this tournament has already ended. If you believe this to be incorrect, please contact the tournament officials."
        if not ( admin or self.regOpen ):
            return "Sorry, but registeration for the tounament is closed."
        ident = getUserIdent( a_discordUser )
        if ident in self.players:
            self.players[ident].status = "active"
            await self.players[ident].discordUser.add_roles( self.role )
            return ""
        else:
            self.players[ident] = player( ident )
            self.players[ident].saveLocation = f'{self.saveLocation}/players/{ident}.xml'
            self.players[ident].addDiscordUser( a_discordUser )
            return ""
    
    # There will be a far more sofisticated pairing system in the future. Right now, the dummy version will have to do for testing
    # This is a prime canidate for adjustments when players how copies of match results.
    def addPlayerToQueue( self, a_plyr: str ) -> None:
        for lvl in self.queue:
            if a_plyr in lvl:
                return "You are already in the matchmaking queue."
        if a_plyr not in self.players:
            return "You are not registered for this tournament."
        if not self.players[a_plyr].isActive( ):
            return "You are registered but are not an active player."
        
        self.queue[0].append(self.players[a_plyr])
        self.queueActivity.append( (a_plyr, datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f') ) )
        if sum( [ len(level) for level in self.queue ] ) >= self.pairingsThreshold and not self.pairingsThread.is_alive():
            self.pairingsThread = threading.Thread( target=self.launch_pairings, args=(self.pairingWaitTime,) )
            self.pairingsThread.start( )
        return "You have been successfully added to the queue."
    
    def removePlayerFromQueue( self, a_plyr: str ) -> None:
        for lvl in self.queue:
            for i in range(len(lvl)):
                if lvl[i].name == a_plyr:
                    del( lvl[i] )
                    self.saveOverview( )
                    return
    
    async def send_match_warning( self, msg: str ) -> None:
        await self.pairingsChannel.send( content=msg )

    def launch_match_warning( self, msg: str ) -> None:
        if self.loop.is_running( ):
            fut_send = asyncio.run_coroutine_threadsafe( self.send_match_warning(msg), self.loop )
            fut_send.result( )
        else:
            self.loop.run_until_complete( self.send_match_warning(msg) )

    def matchTimer( self, mtch: match, t: int = -1 ) -> None:
        if t == -1:
            t = self.matchLength
        oneMin  = 60
        fiveMin = 300
        margin  = 1
        
        timeLeft = t + margin + mtch.timeExtension - timeDiff( mtch.startTime, getTime() )
        lastTimeExt = mtch.timeExtension
        sentWarningOne = False
        sentWarningTwo = False
        while timeLeft > 0 and not mtch.stopTimer:
            time.sleep( oneMin )
            if lastTimeExt != mtch.timeExtension:
                sentWarningOne = False
                sentWarningTwo = False
            lastTimeExt = mtch.timeExtension
            timeLeft = t + margin + mtch.timeExtension - timeDiff( mtch.startTime, getTime() )
                    
            if mtch.role != None:
                if timeLeft <= oneMin:
                    if not sentWarningTwo:
                        task = threading.Thread( target=self.launch_match_warning, args=(f'{mtch.role.mention}, you have one minute left in your match.',) )
                        task.start( )
                        sentWarningOne = True
                elif timeLeft <= fiveMin:
                    if not sentWarningOne:
                        task = threading.Thread( target=self.launch_match_warning, args=(f'{mtch.role.mention}, you have five minutes left in your match.',) )
                        task.start( )
                        sentWarningOne = True

        if not mtch.stopTimer:            
            if mtch.role != None:
                task = threading.Thread( target=self.launch_match_warning, args=(f'{mtch.role.mention}, time in your match is up!!',) )
                task.start( )
                task.join( )
            
    
    async def addMatch( self, a_plyrs: List[str] ) -> None:
        for plyr in a_plyrs:
            self.queueActivity.append( (plyr, getTime() ) )
        newMatch = match( a_plyrs )
        self.matches.append( newMatch )
        newMatch.matchNumber = len(self.matches)
        newMatch.saveLocation = f'{self.saveLocation}/matches/match_{newMatch.matchNumber}.xml'
        if type( self.guild ) == discord.Guild:
            matchRole = await self.guild.create_role( name=f'Match {newMatch.matchNumber}' )
            overwrites = { self.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                           getAdminRole(self.guild): discord.PermissionOverwrite(read_messages=True),
                           getJudgeRole(self.guild): discord.PermissionOverwrite(read_messages=True),
                           matchRole: discord.PermissionOverwrite(read_messages=True) }
            matchCategory = discord.utils.get( self.guild.categories, name="Matches" ) 
            if len(matchCategory.channels) >= 50:
                matchCategory = category=discord.utils.get( self.guild.categories, name="More Matches" ) 
                
            #Save replay into a folder on the bot end
            game_name: str = f'{self.tournName}/Match {newMatch.matchNumber}'
            
            newMatch.VC    = await matchCategory.create_voice_channel( name=game_name, overwrites=overwrites ) 
            newMatch.role  = matchRole
            newMatch.timer = threading.Thread( target=self.matchTimer, args=(newMatch,) )
            
            message = f'\n{matchRole.mention} of {self.tournName}, you have been paired. A voice channel has been created for you. Below is information about your opponents.\n'
            embed   = discord.Embed( )   
            
            if(self.triceBotEnabled):                        
                #Try to create the game
                creation_success: bool = False
                replay_download_link: str = ""
                game_id: int = -1
                tries: int = 0
                max_tries: int = 3
                
                game_password: str = "game-" + str(newMatch.matchNumber)
                
                #Try up to three times
                while not creation_success and tries < max_tries:
                    game_made = trice_bot.createGame(game_name, game_password, len(a_plyrs), self.spectators_allowed, self.spectators_need_password, self.spectators_can_chat, self.spectators_can_see_hands, self.only_registered)
                    
                    creation_success = game_made.success
                    replay_download_link = trice_bot.getDownloadLink(game_made.replayName)
                    game_id = game_made.gameID
                    tries+=1
                    
                if creation_success:
                    #Game was made
                    newMatch.triceMatch = True
                    newMatch.gameID = game_id
                    newMatch.replayURL = replay_download_link
                    
                    message += "A cockatrice game was automatically made for you it is called " + game_name 
                    message += " and has a password of `" + game_password + "`\n"
                
                    #TODO: move replay download link?
                    message +="Replay download link " + replay_download_link + " (available on game end)\n"
                else:
                    #Game was not made
                    message += "A cockatrice game was not automatically made for you.\n"
        for plyr in a_plyrs:
            self.removePlayerFromQueue( plyr )
            self.players[plyr].matches.append( newMatch )
            for p in a_plyrs:
                if p != plyr:
                    self.players[plyr].opponents.append( p )
            if type( self.guild ) == discord.Guild:
                self.players[plyr].saveXML()
                await self.players[plyr].discordUser.add_roles( matchRole )
                embed.add_field( name=self.players[plyr].getDisplayName(), value=self.players[plyr].pairingString() )
        
        if type( self.guild ) is discord.Guild:
            await self.pairingsChannel.send( content=message, embed=embed )
            
        newMatch.timer.start( )
        newMatch.saveXML()
    
    # See tricebot.py for retun details
    # copy pasta of them is here. accurate as of 25/04/21
    
    #  1 if success
    #  0 auth token is bad or error404 or network issue
    # -1 if player not found
    # -2 if an unknown error occurred
    def kickTricePlayer(self, a_matchNum, playerName):
        match = self.matches[a_matchNum - 1]
        return trice_bot.kickPlayer(match.gameID, playerName)
    
    def addBye( self, a_plyr: str ) -> None:
        self.removePlayerFromQueue( a_plyr )
        newMatch = match( [ a_plyr ] )
        self.matches.append( newMatch )
        newMatch.matchNumber = len(self.matches)
        newMatch.saveLocation = f'{self.saveLocation}/matches/match_{newMatch.matchNumber}.xml'
        newMatch.recordBye( )
        self.players[a_plyr].matches.append( newMatch )
        newMatch.saveXML( )
    
    async def removeMatch( self, a_matchNum: int, author: str = "" ) -> str:
        if self.matches[a_matchNum - 1] != a_matchNum:
            self.matches.sort( key=lambda x: x.matchNumber )

        for plyr in self.matches[a_matchNum - 1].activePlayers:
            await self.players[plyr].removeMatch( a_matchNum )
            await self.players[plyr].discordUser.send( content=f'You were a particpant in match #{a_matchNum} in the tournament {self.tournName} on the server {self.hostGuildName}. This match has been removed by tournament admin. If you think this is an error, contact them.' )
        for plyr in self.matches[a_matchNum - 1].droppedPlayers:
            await self.players[plyr].removeMatch( a_matchNum )
            await self.players[plyr].discordUser.send( content=f'You were a particpant in match #{a_matchNum} in the tournament {self.tournName} on the server {self.hostGuildName}. This match has been removed by tournament admin. If you think this is an error, contact them.' )

        await self.matches[a_matchNum - 1].killMatch( )
        self.matches[a_matchNum - 1].saveXML( )
        
        return f'{author}, match #{a_matchNum} has been removed.'
        
    
    # Wrapper for self.pairQueue so that it can be ran on a seperate thread
    def launch_pairings( self, a_waitTime ):
        time.sleep( a_waitTime )
        fut_pairings = asyncio.run_coroutine_threadsafe( self.pairQueue(a_waitTime), self.loop )
        fut_pairings.result( )
    
    # Starting from the given position, searches through the queue to find opponents for the player at the given position.
    # Returns the positions of the closest players that can form a match.
    # If a match can't be formed, we return an empty list
    # This method is intended to only be used in pairQueue method
    def searchForOpponents( self, lvl: int, i: int, a_queue = [] ) -> List[Tuple[int,int]]:
        if len(a_queue) == []:
            a_queue = self.queue
        if lvl > 0:
            lvl = -1*(lvl+1)
        
        plyr   = a_queue[lvl][i]
        plyrs  = [ a_queue[lvl][i] ]
        digest = [ (lvl, i) ]
        
        # Sweep through the rest of the level we start in
        for k in range(i+1,len(a_queue[lvl])):
            if a_queue[lvl][k].areValidOpponents( plyrs ):
                plyrs.append( a_queue[lvl][k] )
                # We want to store the shifted inner index since any players in
                # front of this player will be removed
                digest.append( (lvl, k - len(digest) ) )
                if len(digest) == self.playersPerMatch:
                    return digest
        
        # Starting from the priority level directly below the given level and
        # moving towards the lowest priority level, we sweep across each
        # remaining level looking for a match
        for l in reversed(range(-1*len(a_queue),lvl)):
            count = 0
            for k in range(len(a_queue[l])):
                if a_queue[l][k].areValidOpponents( plyrs ):
                    plyrs.append( a_queue[l][k] )
                    # We want to store the shifted inner index since any players in
                    # front of this player will be removed
                    digest.append( (l, k - count ) )
                    count += 1
                    if len(digest) == self.playersPerMatch:
                        return digest
        return [ ]
        
    def pairingAttempt( self, queue = [] ):
        if len(queue) == 0:
            queue = self.queue.copy()
        newQueue = []
        for _ in range(len(queue) + 1):
            newQueue.append( [] )
        plyrs = [ ]
        indices = [ ]
        digest = [ ]

        for lvl in queue:
            random.shuffle( lvl )
        
        lvl = -1
        while lvl >= -1*len(queue):
            while len(queue[lvl]) > 0:
                indices = self.searchForOpponents( lvl, 0, queue )
                # If an empty array is returned, no match was found
                # Add the current player to the end of the new queue
                # and remove them from the current queue
                if len(indices) == 0:
                    newQueue[lvl].append(queue[lvl][0])
                    del( queue[lvl][0] )
                else:
                    plyrs = [ ] 
                    for index in indices:
                        plyrs.append( queue[index[0]][index[1]].name )
                        del( queue[index[0]][index[1]] )
                    digest.append( self.addMatch( plyrs ) )
            lvl -= 1
        
        return digest, newQueue
    
    async def pairQueue( self, a_waitTime: int ) -> None:
        tries = 25
        tempQueue = [ lvl.copy() for lvl in self.queue ]
        results = []
        
        for _ in range(tries):
            results.append( self.pairingAttempt( tempQueue ) )
            # Have we paired the maximum number of people, i.e. does the remainder of the queue by playersPerMatch equal the new queue
            if sum( [ len(lvl) for lvl in results[-1][1] ] ) == sum( [len(lvl) for lvl in self.queue] )%self.playersPerMatch:
                break

        results.sort( key=lambda x: len(x[0]) ) 
        matchTasks = results[-1][0]
        newQueue   = results[-1][1]
        
        # Waiting for the tasks to be made
        for task in matchTasks:
            await task
        

        # Trimming empty bins from the top of the new queue
        while len(newQueue) > 1:
            if len(newQueue[-1]) != 0:
                break
            del( newQueue[-1] )
        
        

        # Check to see if the new queue is the same as the old queue
        isSame = True
        if [ len(lvl) for lvl in self.queue ] == [ len(lvl) for lvl in newQueue ]:
            for i in range(len(self.queue)):
                self.queue[i].sort( key=lambda x: x.name )
                newQueue[i].sort( key=lambda x: x.name )
            for i in range(len(self.queue)):
                for j in range(len(self.queue[i])):
                    isSame &= self.queue[i][j] == newQueue[i][j] 
                    if not isSame: break
                if not isSame: break

        for plyr in self.queue[0]:
            isInQueue = False
            for lvl in newQueue:
                isInQueue |= plyr not in lvl
            if not isInQueue:
                newQueue[0].append( plyr )
        
        self.queue = newQueue

        if len(self.queue) > self.highestPriority:
            self.highestPriority = len(self.queue)
        
        self.saveOverview()
        
        if sum( [ len(level) for level in self.queue ] ) >= self.pairingsThreshold and not isSame:
            self.pairingsThread = threading.Thread( target=self.launch_pairings, args=(0,) )
            self.pairingsThread.start( )
        
        return
    
    
    def getStandings( self ) -> List[List]:
        rough = [ ]
        for plyr in self.players.values():
            if not plyr.isActive( ):
                continue
            if plyr.discordUser is None:
                continue
            if len(plyr.matches) == 0:
                continue
            # Match Points
            points = plyr.getMatchPoints()
            # Match Win Percentage
            MWP = plyr.getMatchWinPercentage( withBye=False )
            # Opponent Match Win Percentage
            OWP = 0.0
            if len(plyr.opponents) > 0:
                wins  = sum( [ self.players[opp].getNumberOfWins( ) for opp in plyr.opponents ] )
                games = sum( [len(self.players[opp].getCertMatches( withBye=False )) for opp in plyr.opponents] )
                if games != 0:
                    OWP = wins/games
                #OWP = sum( [ self.players[opp].getMatchWinPercentage( withBye=False ) for opp in plyr.opponents ] )/len(plyr.opponents)
            rough.append( (points, MWP, OWP, plyr.discordUser.display_name) )
        
        # sort() is stable, so relate order similar elements is preserved
        rough.sort( key= lambda x: x[2], reverse=True )
        rough.sort( key= lambda x: x[1], reverse=True )
        rough.sort( key= lambda x: x[0], reverse=True )
        
        # Place, Player name, Points, MWP, OWP
        digest =  [ [ i+1 for i in range(len(rough))], \
                    [ i[3] for i in rough ], \
                    [ i[0] for i in rough ], \
                    [ i[1]*100 for i in rough ], \
                    [ i[2]*100 for i in rough ] ]

        return digest

    
    def getMatch( self, a_matchNum: int ) -> match:
        if a_matchNum > len(self.matches) + 1:
            return match( [] )
        if self.matches[a_matchNum - 1].matchNumber == a_matchNum:
            return self.matches[a_matchNum - 1]
        for mtch in self.matches:
            if mtch.matchNumber == a_matchNum:
                return mtch
    
    async def playerMatchDrop( self, a_plyr: str ) -> None:
        if not a_plyr in self.players:
            return
        while self.players[a_plyr].findOpenMatchIndex() < 0:
            await self.players[a_plyr].findOpenMatch().dropPlayer( a_plyr )
    
    async def dropPlayer( self, a_plyr: str, author: str = "" ) -> None:
        await self.playerMatchDrop( a_plyr )
        await self.players[a_plyr].discordUser.remove_roles( self.role )
        await self.players[a_plyr].drop( )
        self.players[a_plyr].saveXML()
        if author != "":
            await self.players[a_plyr].discordUser.send( content=f'You have been dropped from {self.tournName} on {self.guild.name} by tournament admin. If you believe this is an error, check with them.' )
            return f'{author}, {self.players[a_plyr].discordUser.mention} has been dropped from the tournament.'
        return f'{self.players[a_plyr].discordUser.mention}, you have been dropped from {self.tournName}.'
    
    async def playerCertifyResult( self, a_plyr: str ) -> None:
        if not a_plyr in self.players:
            return
        message = await self.players[a_plyr].certifyResult( )
        if message != "":
            await self.pairingsChannel.send( message )
    
    async def recordMatchWin( self, a_winner: str ) -> None:
        if not a_winner in self.players:
            return
        message = await self.players[a_winner].recordWin( )
        if message != "":
            await self.pairingsChannel.send( message )
    
    async def recordMatchDraw( self, a_plyr: str ) -> None:
        if not a_plyr in self.players:
            return
        message = await self.players[a_plyr].recordDraw( )
        if message != "":
            await self.pairingsChannel.send( message )

    def saveTournament( self, a_unsafe_dirName: str = "" ) -> None:        
        a_dirName = a_unsafe_dirName.replace("\.\./", "") 
        #Check on folder creation, event though input should be safe
        
        if a_dirName == "":
            a_dirName = self.saveLocation
        if not (os.path.isdir( f'{a_dirName}' ) and os.path.exists( f'{a_dirName}' )):
           os.mkdir( f'{a_dirName}' ) 
        self.saveOverview( f'{a_dirName}/overview.xml' )
        self.saveMatches( a_dirName )
        self.savePlayers( a_dirName )
    
    def saveOverview( self, a_filename: str = "" ):
        if a_filename == "":
            a_filename = f'{self.saveLocation}/overview.xml'
        digest  = "<?xml version='1.0'?>\n"
        digest += '<tournament>\n'
        digest += f'\t<name>{toSafeXML(self.tournName)}</name>\n'
        digest += f'\t<guild id="{toSafeXML(self.guild.id if type(self.guild) == discord.Guild else str())}">{toSafeXML(self.hostGuildName)}</guild>\n'
        digest += f'\t<role id="{toSafeXML(self.role.id if type(self.role) == discord.Role else str())}"/>\n'
        digest += f'\t<format>{toSafeXML(self.format)}</format>\n'
        digest += f'\t<regOpen>{toSafeXML(self.regOpen)}</regOpen>\n'
        digest += f'\t<status started="{toSafeXML(self.tournStarted)}" ended="{self.tournEnded}" canceled="{toSafeXML(self.tournCancel)}"/>\n'
        digest += f'\t<deckCount>{toSafeXML(self.deckCount)}</deckCount>\n'
        digest += f'\t<matchLength>{toSafeXML(self.matchLength)}</matchLength>\n'
        
        # Save tricebot settings under a tricebot tag
        digest += f'\t\t<triceBotEnabled>{toSafeXML(self.triceBotEnabled)}</triceBotEnabled>\n'
        digest += f'\t\t<spectatorsAllowed>{toSafeXML(self.spectators_allowed)}</spectatorsAllowed>\n'
        digest += f'\t\t<spectatorsNeedPassword>{toSafeXML(self.spectators_need_password)}</spectatorsNeedPassword>\n'
        digest += f'\t\t<spectatorsCanChat>{toSafeXML(self.spectators_can_chat)}</spectatorsCanChat>\n'
        digest += f'\t\t<spectatorsCanSeeHands>{toSafeXML(self.spectators_can_see_hands)}</spectatorsCanSeeHands>\n'
        digest += f'\t\t<onlyRegistered>{toSafeXML(self.only_registered)}</onlyRegistered>\n'
        
        digest += f'\t<queue size="{toSafeXML(self.playersPerMatch)}" threshold="{toSafeXML(self.pairingsThreshold)}">\n'
        for level in range(len(self.queue)):
            for plyr in self.queue[level]:
                digest += f'\t\t<player name="{toSafeXML(plyr.name)}" priority="{toSafeXML(level)}"/>\n'
        digest += f'\t</queue>\n'
        digest += f'\t<queueActivity>\n'
        for act in self.queueActivity:
            digest += f'\t\t<event player="{toSafeXML(act[0])}" time="{toSafeXML(act[1])}"/>\n'
        digest += f'\t</queueActivity>\n'
        digest += '</tournament>'
        
        with open( a_filename, 'w' ) as xmlFile:
            xmlFile.write( digest )
    
    def savePlayers( self, a_dirName: str = "" ) -> None:
        if a_dirName == "":
            a_dirName = self.saveLocation
        if not (os.path.isdir( f'{a_dirName}/players/' ) and os.path.exists( f'{a_dirName}/players/' )):
           os.mkdir( f'{a_dirName}/players/' ) 

        for player in self.players:
            self.players[player].saveXML( f'{a_dirName}/players/{self.players[player].name}.xml' )

    def saveMatches( self, a_dirName: str = "" ) -> None:
        if a_dirName == "":
            a_dirName = self.saveLocation
        if not (os.path.isdir( f'{a_dirName}/matches/' ) and os.path.exists( f'{a_dirName}/matches/' )):
           os.mkdir( f'{a_dirName}/matches/' ) 

        for match in self.matches:
            match.saveXML( f'{a_dirName}/matches/match_{match.matchNumber}.xml' )
        
    def loadTournament( self, a_dirName: str ) -> None:
        self.saveLocation = a_dirName
        self.loadPlayers( f'{a_dirName}/players/' )
        self.loadOverview( f'{a_dirName}/overview.xml' )
        self.loadMatches( f'{a_dirName}/matches/' )
    
    def loadOverview( self, a_filename: str ) -> None:
        xmlTree = ET.parse( a_filename )
        tournRoot = xmlTree.getroot() 
        self.tournName = fromXML(tournRoot.find( 'name' ).text)
        self.guildID   = int( fromXML(tournRoot.find( 'guild' ).attrib["id"]) )
        self.roleID    = int( fromXML(tournRoot.find( 'role' ).attrib["id"]) )
        self.format    = fromXML(tournRoot.find( 'format' ).text)
        self.deckCount = int( fromXML(tournRoot.find( 'deckCount' ).text) )
        
        # Load tricebot settings
        self.triceBotEnabled = str_to_bool ( fromXML(tournRoot.find('triceBotEnabled').text) )
        self.spectators_allowed = str_to_bool ( fromXML(tournRoot.find('spectatorsAllowed').text) )
        self.spectators_need_password = str_to_bool ( fromXML(tournRoot.find('spectatorsNeedPassword').text) )
        self.spectators_can_chat = str_to_bool ( fromXML(tournRoot.find('spectatorsCanChat').text) )
        self.spectators_can_see_hands = str_to_bool ( fromXML(tournRoot.find('spectatorsCanSeeHands').text) )
        self.only_registered = str_to_bool ( fromXML(tournRoot.find('onlyRegistered').text) )
        
        self.regOpen      = str_to_bool( fromXML(tournRoot.find( 'regOpen' ).text ))
        self.tournStarted = str_to_bool( fromXML(tournRoot.find( 'status' ).attrib['started'] ))
        self.tournEnded   = str_to_bool( fromXML(tournRoot.find( 'status' ).attrib['ended'] ))
        self.tournCancel  = str_to_bool( fromXML(tournRoot.find( 'status' ).attrib['canceled'] ))

        self.playersPerMatch = int( fromXML(tournRoot.find( 'queue' ).attrib['size'] ))
        self.pairingsThreshold = int( fromXML(tournRoot.find( 'queue' ).attrib['threshold'] ))
        self.matchLength     = int( fromXML(tournRoot.find( 'matchLength' ).text ))
        
        acts    = tournRoot.find( 'queueActivity' ).findall( 'event' )
        for act in acts:
            self.queueActivity.append( fromXML( (act.attrib['player'], act.attrib['time'] ) ) )
        players = tournRoot.find( 'queue' ).findall( 'player' )
        maxLevel = 1
        for plyr in players:
            if int( plyr.attrib['priority'] ) > maxLevel:
                maxLevel = int( fromXML(plyr.attrib['priority']) )
        for _ in range(maxLevel):
            self.queue.append( [] )
        for plyr in players:
            self.queue[int(plyr.attrib['priority'])].append( fromXML(self.players[ plyr.attrib['name'] ] ))
        if sum( [ len(level) for level in self.queue ] ) >= self.pairingsThreshold and not self.pairingsThread.is_alive( ):
            self.pairingsThread = threading.Thread( target=self.launch_pairings, args=(self.pairingWaitTime,) )
            self.pairingsThread.start( )
    
    def loadPlayers( self, a_dirName: str ) -> None:
        playerFiles = [ f'{a_dirName}/{f}' for f in os.listdir(a_dirName) if os.path.isfile( f'{a_dirName}/{f}' ) ]
        for playerFile in playerFiles:
            print( playerFile )
            newPlayer = player( "" )
            newPlayer.saveLocation = playerFile
            newPlayer.loadXML( playerFile )
            self.players[newPlayer.name] = newPlayer
    
    def loadMatches( self, a_dirName: str ) -> None:
        matchFiles = [ f'{a_dirName}/{f}' for f in os.listdir(a_dirName) if os.path.isfile( f'{a_dirName}/{f}' ) ]
        for matchFile in matchFiles:
            newMatch = match( [] )
            newMatch.saveLocation = matchFile
            newMatch.loadXML( matchFile )
            self.matches.append( newMatch )
            for aPlayer in newMatch.activePlayers:
                if aPlayer in self.players:
                    self.players[aPlayer].addMatch( newMatch )
            for dPlayer in newMatch.droppedPlayers:
                if dPlayer in self.players:
                    self.players[dPlayer].addMatch( newMatch )
            if not ( self.matches[-1].isCertified() or self.matches[-1].isDead() ) and not self.matches[-1].stopTimer:
                self.matches[-1].timer = threading.Thread( target=self.matchTimer, args=(self.matches[-1],) )
                self.matches[-1].timer.start( )
        self.matches.sort( key= lambda x: x.matchNumber )
        for plyr in self.players.values():
            plyr.matches.sort( key= lambda x: x.matchNumber )



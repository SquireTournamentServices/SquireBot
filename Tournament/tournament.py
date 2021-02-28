import os
import xml.etree.ElementTree as ET
import random
import threading
import time
import discord
import asyncio
import warnings

from typing import List
from typing import Tuple

from .utils import *
from .match import match
from .player import player
from .deck import deck


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
    def __init__( self, a_tournName: str, a_hostGuildName: str, a_format: str = "EDH" ):
        self.tournName = a_tournName
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
        self.pairingsThreshold = self.playersPerMatch #* 2 + 3
        self.pairingWaitTime   = 20
        self.queueActivity     = [ ]
        self.matchLength       = 60*60 # Length of matches in seconds
        self.highestPriority   = 0
        self.pairingsThread    = threading.Thread( target=self.launch_pairings, args=(self.pairingWaitTime,) )
        
        self.deckCount = 1

        self.players  = {}
        self.droppedPlayers = {}
        
        self.matches = []
    
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
    
    async def endTourn( self ) -> str:
        await self.purgeTourn( )
        if not self.tournStarted:
            return "The tournament has not started. As such, it can't be ended; however, it can be cancelled. Please use the cancel command if that's what you intended to do."
        else:
            self.tournEnded = False
    
    async def cancelTourn( self ) -> str:
        await self.purgeTourn( )
        self.tournCancel = True
        return "This tournament has been canceled."
    
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
        if self.matchLength < 300:
            return
        oneMin  = 60
        fiveMin = 300
        if t >= fiveMin:
            time.sleep( t - fiveMin )
            if mtch.isCertified( ) or mtch.stopTimer:
                return
            task = threading.Thread( target=self.launch_match_warning, args=(f'{mtch.role.mention}, you have five minutes left in your round.',) )
            task.start( )
            t = fiveMin
        if t >= oneMin:
            time.sleep( t - oneMin )
            if mtch.isCertified( ) or mtch.stopTimer:
                return
            task = threading.Thread( target=self.launch_match_warning, args=(f'{mtch.role.mention}, you have one minute left in your round.',) )
            task.start( )
            t = oneMin
        time.sleep( t )
        if mtch.isCertified( ) or mtch.stopTimer:
            return
        task = threading.Thread( target=self.launch_match_warning, args=(f'{mtch.role.mention}, time is up for this match.',) )
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
                           matchRole: discord.PermissionOverwrite(read_messages=True) }
            newMatch.VC = await self.guild.create_voice_channel( name=f'{self.tournName} Match {newMatch.matchNumber}', overwrites=overwrites, category=discord.utils.get( self.guild.categories, name="Matches" ) ) 
            newMatch.role = matchRole
            newMatch.timer = threading.Thread( target=self.matchTimer, args=(newMatch,) )
            newMatch.timer.start( )
            newMatch.saveXML()
            
            message = f'\n{matchRole.mention} of {self.tournName}, you have been paired. A voice channel has been created for you. Below is information about your opponents.\n'
            embed   = discord.Embed( )
        
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
        
        if type( self.guild ) == discord.Guild:
            await self.pairingsChannel.send( content=message, embed=embed )
    
    def addBye( self, a_plyr: str ) -> None:
        self.removePlayerFromQueue( a_plyr )
        newMatch = match( [ a_plyr ] )
        self.matches.append( newMatch )
        newMatch.matchNumber = len(self.matches)
        newMatch.saveLocation = f'{self.saveLocation}/matches/match_{newMatch.matchNumber}.xml'
        newMatch.recordBye( )
        self.players[a_plyr].matches.append( newMatch )
        newMatch.saveXML( )
    
    async def removeMatch( self, a_matchNum: int ) -> None:
        if self.matches[a_matchNum - 1] != a_matchNum:
            self.matches.sort( key=lambda x: x.matchNumber )

        for plyr in self.matches[a_matchNum - 1].activePlayers:
            self.players[plyr].removeMatch( a_matchNum )
            await self.players[plyr].discordUser.send( content=f'You were a particpant in match #{a_matchNum} in the tournament {self.tournName} on the server {self.hostGuildName}. This match has been removed by tournament admin. If you think this is an error, contact them.' )
        for plyr in self.matches[a_matchNum - 1].droppedPlayers:
            self.players[plyr].removeMatch( a_matchNum )
            await self.players[plyr].discordUser.send( content=f'You were a particpant in match #{a_matchNum} in the tournament {self.tournName} on the server {self.hostGuildName}. This match has been removed by tournament admin. If you think this is an error, contact them.' )

        await self.matches[a_matchNum - 1].killMatch( )
        
    
    # Wrapper for self.pairQueue so that it can be ran on a seperate thread
    def launch_pairings( self, a_waitTime ):
        time.sleep( 10**-3 )
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
        
    def pairingAttempt( self ):
        queue = [ [ i for i in lvl ] for lvl in self.queue ]
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
        time.sleep( a_waitTime )
        
        tries = 25
        results = []
        
        for _ in range(tries):
            results.append( self.pairingAttempt() )
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
            # Match Points
            points = plyr.getMatchPoints()
            # Match Win Percentage
            MWP = plyr.getMatchWinPercentage( withBye=False )
            # Opponent Match Win Percentage
            OWP = 0.0
            if len(plyr.opponents) > 0:
                OWP = sum( [ self.players[opp].getMatchWinPercentage( withBye=False ) for opp in plyr.opponents ] )/len(plyr.opponents)
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
        while self.players[a_plyr].findOpenMatchIndex() != 1:
            await self.players[a_plyr].findOpenMatch().dropPlayer( a_plyr )
    
    async def dropPlayer( self, a_plyr: str ) -> None:
        await self.playerMatchDrop( a_plyr )
        await self.players[a_plyr].discordUser.remove_roles( self.role )
        await self.players[a_plyr].drop( )
        self.players[a_plyr].saveXML()
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

    def saveTournament( self, a_dirName: str = "" ) -> None:
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
        digest += f'\t<name>{self.tournName}</name>\n'
        digest += f'\t<guild id="{self.guild.id if type(self.guild) == discord.Guild else str()}">{self.hostGuildName}</guild>\n'
        digest += f'\t<role id="{self.role.id if type(self.role) == discord.Role else str()}"/>\n'
        digest += f'\t<format>{self.format}</format>\n'
        digest += f'\t<regOpen>{self.regOpen}</regOpen>\n'
        digest += f'\t<status started="{self.tournStarted}" ended="{self.tournEnded}" canceled="{self.tournCancel}"/>\n'
        digest += f'\t<deckCount>{self.deckCount}</deckCount>\n'
        digest += f'\t<matchLength>{self.matchLength}</matchLength>\n'
        digest += f'\t<queue size="{self.playersPerMatch}" threshold="{self.pairingsThreshold}">\n'
        for level in range(len(self.queue)):
            for plyr in self.queue[level]:
                digest += f'\t\t<player name="{plyr.name}" priority="{level}"/>\n'
        digest += f'\t</queue>\n'
        digest += '</tournament>'
        
        with open( a_filename, 'w' ) as xmlFile:
            xmlFile.write( digest )
    
    def savePlayers( self, a_dirName: str = "" ) -> None:
        if a_dirName == "":
            a_dirName = self.saveLocation
        if not (os.path.isdir( f'{a_dirName}/players/' ) and os.path.exists( f'{a_dirName}/players/' )):
           os.mkdir( f'{a_dirName}/players/' ) 

        for player in self.players:
            self.players[player].saveXML( )

    def saveMatches( self, a_dirName: str = "" ) -> None:
        if a_dirName == "":
            a_dirName = self.saveLocation
        if not (os.path.isdir( f'{a_dirName}/matches/' ) and os.path.exists( f'{a_dirName}/matches/' )):
           os.mkdir( f'{a_dirName}/matches/' ) 

        for match in self.matches:
            match.saveXML( )
        
    def loadTournament( self, a_dirName: str ) -> None:
        self.saveLocation = a_dirName
        self.loadPlayers( f'{a_dirName}/players/' )
        self.loadOverview( f'{a_dirName}/overview.xml' )
        self.loadMatches( f'{a_dirName}/matches/' )
    
    def loadOverview( self, a_filename: str ) -> None:
        xmlTree = ET.parse( a_filename )
        tournRoot = xmlTree.getroot() 
        self.tournName = tournRoot.find( 'name' ).text
        self.guildID   = int( tournRoot.find( 'guild' ).attrib["id"] )
        self.roleID    = int( tournRoot.find( 'role' ).attrib["id"] )
        self.format    = tournRoot.find( 'format' ).text
        self.deckCount = int( tournRoot.find( 'deckCount' ).text )

        self.regOpen      = str_to_bool( tournRoot.find( 'regOpen' ).text )
        self.tournStarted = str_to_bool( tournRoot.find( 'status' ).attrib['started'] )
        self.tournEnded   = str_to_bool( tournRoot.find( 'status' ).attrib['ended'] )
        self.tournCancel  = str_to_bool( tournRoot.find( 'status' ).attrib['canceled'] )

        self.playersPerMatch = int( tournRoot.find( 'queue' ).attrib['size'] )
        self.pairingsThreshold = int( tournRoot.find( 'queue' ).attrib['threshold'] )
        self.matchLength     = int( tournRoot.find( 'matchLength' ).text )
        
        players = tournRoot.find( 'queue' ).findall( 'player' )
        maxLevel = 1
        for plyr in players:
            if int( plyr.attrib['priority'] ) > maxLevel:
                maxLevel = int( plyr.attrib['priority'] )
        for _ in range(maxLevel):
            self.queue.append( [] )
        for plyr in players:
            self.queue[int(plyr.attrib['priority'])].append( self.players[ plyr.attrib['name'] ] )
        if sum( [ len(level) for level in self.queue ] ) >= self.pairingsThreshold and not self.pairingsThread.is_alive( ):
            self.pairingsThread = threading.Thread( target=self.launch_pairings, args=(self.pairingWaitTime,) )
            self.pairingsThread.start( )
    
    def loadPlayers( self, a_dirName: str ) -> None:
        playerFiles = [ f'{a_dirName}/{f}' for f in os.listdir(a_dirName) if os.path.isfile( f'{a_dirName}/{f}' ) ]
        for playerFile in playerFiles:
            newPlayer = player( "" )
            newPlayer.saveLocation = playerFile
            newPlayer.loadXML( playerFile )
            self.players[newPlayer.name]  = newPlayer
    
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
            if self.matches[-1].status != "certified":
                t = int( self.matchLength - timeDiff( getTime(), self.matches[-1].startTime ) )
                if t <= 0:
                    continue
                self.matches[-1].timer = threading.Thread( target=self.matchTimer, args=(self.matches[-1],t,) )
                self.matches[-1].timer.start( )
        self.matches.sort( key= lambda x: x.matchNumber )
        for plyr in self.players.values():
            plyr.matches.sort( key= lambda x: x.matchNumber )



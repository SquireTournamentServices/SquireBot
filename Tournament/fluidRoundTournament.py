import os
import shutil
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
from .tournament import tournament
from .match import match
from .player import player
from .deck import deck


"""
    This is a tournament class. The bulk of data management for a tournament is handled by this class.
    It also holds certain metadata about the tournament, such as the tournament's name and host guild's name.
"""
class fluidRoundTournament(tournament):
    def __init__( self, name: str, hostGuildName: str, props: dict = { } ):     
        self.name = name.replace("\.\./", "")
        self.hostGuildName = hostGuildName
        self.format    = "Pioneer"
        
        self.saveLocation = f'currentTournaments/{self.name}'

        self.guild   = None
        self.guildID = ""
        self.role    = None
        self.roleID  = ""
        self.pairingsChannel = None
        self.pairingsChannelID = ""
        
        self.regOpen      = True
        self.tournStarted = False
        self.tournEnded   = False
        self.tournCancel  = False
        
        self.loop = asyncio.new_event_loop( )
        self.fail_count = 0
        
        self.playersPerMatch   = 2
        self.matchLength       = 60*60 # Length of matches in seconds
        
        self.queue             = [ [] ]
        self.pairingsThreshold = self.playersPerMatch * 2 # + 3
        self.pairingWaitTime   = 5
        self.queueActivity     = [ ]
        self.highestPriority   = 0
        self.pairingsThread    = threading.Thread( target=self._launch_pairings, args=(self.pairingWaitTime,) )
        
        self.deckCount = 1

        self.players  = {}
        
        self.matches = []
        
        #Create bot class and store the game creation settings
        self.triceBotEnabled = False
        self.spectators_allowed = False
        self.spectators_need_password = False 
        self.spectators_can_chat = False 
        self.spectators_can_see_hands = False 
        self.only_registered = False
        self.player_deck_verification = False
                
        if len(props) != 0:
            self.setProperties(props)
        
    
    # ---------------- Property Accessors ---------------- 

    def updatePairingsThreshold( self, count: int ) -> None:
        self.pairingsThreshold = count
        if sum( [ len(level) for level in self.queue ] ) >= self.pairingsThreshold and not self.pairingsThread.is_alive():
            self.pairingsThread = threading.Thread( target=self._launch_pairings, args=(self.pairingWaitTime,) )
            self.pairingsThread.start( )
    
    # ---------------- Misc ---------------- 

    # ---------------- Embed Generators ---------------- 
    
    # ---------------- Player Accessors ---------------- 
    
    # ---------------- Tournament Status ---------------- 

    # ---------------- Player Management ---------------- 
    
    # ---------------- Match Management ---------------- 

    # ---------------- Matchmaking Queue ---------------- 
    
    # There will be a far more sofisticated pairing system in the future. Right now, the dummy version will have to do for testing
    # This is a prime canidate for adjustments when players how copies of match results.
    def addPlayerToQueue( self, plyr: str ) -> None:
        for lvl in self.queue:
            if plyr in lvl:
                return "you are already in the matchmaking queue. You will be paired for when more people join the queue."
        if plyr not in self.players:
            return "you are not registered for this tournament."
        if not self.players[plyr].isActive( ):
            return "you are registered but are not an active player."
        
        self.queue[0].append(self.players[plyr])
        self.queueActivity.append( (plyr, datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f') ) )
        if sum( [ len(level) for level in self.queue ] ) >= self.pairingsThreshold and not self.pairingsThread.is_alive():
            self.pairingsThread = threading.Thread( target=self._launch_pairings, args=(self.pairingWaitTime,) )
            self.pairingsThread.start( )
        return "you have been added to the queue."
    
    def removePlayerFromQueue( self, plyr: str ) -> None:
        for lvl in self.queue:
            for i in range(len(lvl)):
                if lvl[i].name == plyr:
                    del( lvl[i] )
                    self.saveOverview( )
                    return None
        return None

    # Wrapper for self._pairQueue so that it can be ran on a seperate thread
    def _launch_pairings( self, waitTime ):
        time.sleep( waitTime )
        fut_pairings = asyncio.run_coroutine_threadsafe( self._pairQueue(waitTime), self.loop )
        fut_pairings.result( )
    
    # Starting from the given position, searches through the queue to find opponents for the player at the given position.
    # Returns the positions of the closest players that can form a match.
    # If a match can't be formed, we return an empty list
    # This method is intended to only be used in _pairQueue method
    def _searchForOpponents( self, lvl: int, i: int, q = [] ) -> List[Tuple[int,int]]:
        if len(q) == []:
            q = self.queue
        if lvl > 0:
            lvl = -1*(lvl+1)
        
        plyr   = q[lvl][i]
        plyrs  = [ q[lvl][i] ]
        digest = [ (lvl, i) ]
        
        # Sweep through the rest of the level we start in
        for k in range(i+1,len(q[lvl])):
            if q[lvl][k].areValidOpponents( plyrs ):
                plyrs.append( q[lvl][k] )
                # We want to store the shifted inner index since any players in
                # front of this player will be removed
                digest.append( (lvl, k - len(digest) ) )
                if len(digest) == self.playersPerMatch:
                    return digest
        
        # Starting from the priority level directly below the given level and
        # moving towards the lowest priority level, we sweep across each
        # remaining level looking for a match
        for l in reversed(range(-1*len(q),lvl)):
            count = 0
            for k in range(len(q[l])):
                if q[l][k].areValidOpponents( plyrs ):
                    plyrs.append( q[l][k] )
                    # We want to store the shifted inner index since any players in
                    # front of this player will be removed
                    digest.append( (l, k - count ) )
                    count += 1
                    if len(digest) == self.playersPerMatch:
                        return digest
        return [ ]
        
    def _pairingAttempt( self, q = [] ):
        if len(q) == 0:
            q = [ lvl.copy() for lvl in self.queue ]
        newQueue = []
        for _ in range(len(q) + 1):
            newQueue.append( [] )
        plyrs = [ ]
        indices = [ ]
        digest = [ ]

        for lvl in q:
            random.shuffle( lvl )
        
        lvl = -1
        while lvl >= -1*len(q):
            while len(q[lvl]) > 0:
                indices = self._searchForOpponents( lvl, 0, q )
                # If an empty array is returned, no match was found
                # Add the current player to the end of the new queue
                # and remove them from the current queue
                if len(indices) == 0:
                    newQueue[lvl].append(q[lvl][0])
                    del( q[lvl][0] )
                else:
                    plyrs = [ ] 
                    for index in indices:
                        plyrs.append( q[index[0]][index[1]].name )
                        del( q[index[0]][index[1]] )
                    digest.append( self.addMatch( plyrs ) )
            lvl -= 1
        
        return digest, newQueue
    
    async def _pairQueue( self, waitTime: int ) -> None:
        tries = 25
        tempQueue = [ lvl.copy() for lvl in self.queue ]
        results = []
        
        for _ in range(tries):
            results.append( self._pairingAttempt( tempQueue ) )
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

        if len(self.queue) > self.highestPriority:
            self.highestPriority = len(self.queue)
        
        self.saveOverview()
        
        if sum( [ len(level) for level in self.queue ] ) >= self.pairingsThreshold and not isSame:
            self.pairingsThread = threading.Thread( target=self._launch_pairings, args=(0,) )
            self.pairingsThread.start( )
        
        return

    # ---------------- XML Saving/Loading ---------------- 
    
    def saveTournamentType( self, filename: str = "" ) -> None:
        print( "Fluid Round tournament type being saved." )
        with open( filename, 'w' ) as xmlfile:
            xmlfile.write( "<?xml version='1.0'?>\n<type>fluidRoundTournament</type>" )
   
    def saveOverview( self, filename: str = "" ) -> None:
        print( "Fluid Round Overview being saved." )
        if filename == "":
            filename = f'{self.saveLocation}/overview.xml'
        digest  = "<?xml version='1.0'?>\n"
        digest += '<tournament>\n'
        digest += f'\t<name>{self.name}</name>\n'
        digest += f'\t<guild id="{self.guild.id if type(self.guild) == discord.Guild else str()}">{self.hostGuildName}</guild>\n'
        digest += f'\t<role id="{self.role.id if type(self.role) == discord.Role else str()}"/>\n'
        digest += f'\t<pairingsChannel id="{self.pairingsChannelID}"/>\n'
        digest += f'\t<format>{self.format}</format>\n'
        digest += f'\t<regOpen>{self.regOpen}</regOpen>\n'
        digest += f'\t<status started="{self.tournStarted}" ended="{self.tournEnded}" canceled="{self.tournCancel}"/>\n'
        digest += f'\t<deckCount>{self.deckCount}</deckCount>\n'
        digest += f'\t<matchLength>{self.matchLength}</matchLength>\n'
        digest += f'\t<triceBotEnabled>{self.triceBotEnabled}</triceBotEnabled>\n'
        digest += f'\t<spectatorsAllowed>{self.spectators_allowed}</spectatorsAllowed>\n'
        digest += f'\t<spectatorsNeedPassword>{self.spectators_need_password}</spectatorsNeedPassword>\n'
        digest += f'\t<spectatorsCanChat>{self.spectators_can_chat}</spectatorsCanChat>\n'
        digest += f'\t<spectatorsCanSeeHands>{self.spectators_can_see_hands}</spectatorsCanSeeHands>\n'
        digest += f'\t<onlyRegistered>{self.only_registered}</onlyRegistered>\n'
        digest += f'\t<playerDeckVerification>{self.player_deck_verification}</playerDeckVerification>\n'
        digest += f'\t<queue size="{self.playersPerMatch}" threshold="{self.pairingsThreshold}">\n'
        for level in range(len(self.queue)):
            for plyr in self.queue[level]:
                digest += f'\t\t<player name="{plyr.name}" priority="{level}"/>\n'
        digest += f'\t</queue>\n'
        digest += f'\t<queueActivity>\n'
        for act in self.queueActivity:
            digest += f'\t\t<event player="{act[0]}" time="{act[1]}"/>\n'
        digest += f'\t</queueActivity>\n'
        digest += '</tournament>' 
        
        with open( filename, 'w' ) as xmlfile:
            xmlfile.write( toSafeXML(digest) )
    
    def loadOverview( self, filename: str ) -> None:
        xmlTree = ET.parse( filename )
        tournRoot = xmlTree.getroot() 
        self.name = fromXML(tournRoot.find( 'name' ).text)
        self.guildID   = int( fromXML(tournRoot.find( 'guild' ).attrib["id"]) )
        self.roleID    = int( fromXML(tournRoot.find( 'role' ).attrib["id"]) )
        self.pairingsChannelID = int( fromXML(tournRoot.find( 'pairingsChannel' ).attrib["id"]) )

        self.format    = fromXML(tournRoot.find( 'format' ).text)
        self.deckCount = int( fromXML(tournRoot.find( 'deckCount' ).text) )

        self.regOpen      = str_to_bool( fromXML(tournRoot.find( 'regOpen' ).text ))
        self.tournStarted = str_to_bool( fromXML(tournRoot.find( 'status' ).attrib['started'] ))
        self.tournEnded   = str_to_bool( fromXML(tournRoot.find( 'status' ).attrib['ended'] ))
        self.tournCancel  = str_to_bool( fromXML(tournRoot.find( 'status' ).attrib['canceled'] ))

        self.playersPerMatch = int( fromXML(tournRoot.find( 'queue' ).attrib['size'] ))
        self.pairingsThreshold = int( fromXML(tournRoot.find( 'queue' ).attrib['threshold'] ))
        self.matchLength     = int( fromXML(tournRoot.find( 'matchLength' ).text ))
        
        self.triceBotEnabled = str_to_bool( fromXML(tournRoot.find( "triceBotEnabled" ) ) )
        self.spectators_allowed = str_to_bool( fromXML(tournRoot.find( "spectatorsAllowed" ) ) )
        self.spectators_need_password = str_to_bool( fromXML(tournRoot.find( "spectatorsNeedPassword" ) ) )
        self.spectators_can_chat = str_to_bool( fromXML(tournRoot.find( "spectatorsCanChat" ) ) )
        self.spectators_can_see_hands = str_to_bool( fromXML(tournRoot.find( "spectatorsCanSeeHands" ) ) )
        self.only_registered = str_to_bool( fromXML(tournRoot.find( "onlyRegistered" ) ) )
        self.player_deck_verification = str_to_bool( fromXML(tournRoot.find( "playerDeckVerification" ) ) )
        
        acts    = tournRoot.find( 'queueActivity' ).findall( 'event' )
        for act in acts:
            self.queueActivity.append( ( fromXML( act.attrib['player'] ), fromXML(act.attrib['time'] ) ) )
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
            self.pairingsThread = threading.Thread( target=self._launch_pairings, args=(self.pairingWaitTime,) )
            self.pairingsThread.start( )





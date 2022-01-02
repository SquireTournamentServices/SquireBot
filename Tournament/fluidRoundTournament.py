import os
import shutil
import xml.etree.ElementTree as ET
import random
import threading
import discord
import asyncio
import warnings
import uuid

from time import sleep
from typing import List, Tuple

from .utils import *
from .tournament import tournament
from .commandResponse import commandResponse
from .player import player
from .match import match
from .deck import deck
from .pairingQueue import *


"""
    This is a tournament class. The bulk of data management for a tournament is handled by this class.
    It also holds certain metadata about the tournament, such as the tournament's name and host guild's name.
"""
class fluidRoundTournament(tournament):
    def __init__( self, name: str, hostGuildName: str, props: dict = { } ):
        super().__init__( name, hostGuildName, props )
        self.queue             = pairingQueue( )
        self.pairingsThreshold = self.playersPerMatch * 2 # + 3
        self.pairingWaitTime   = 5
        self.queueActivity     = [ ]
        self.highestPriority   = 0
        self.pairingsThread    = threading.Thread( target=self._launch_pairings, args=(self.pairingWaitTime,) )

    # ---------------- Property Accessors ----------------

    def updatePairingsThreshold( self, count: int ) -> None:
        self.pairingsThreshold = count
        if self.queue.readyToPair( self.pairingsThreshold ) and not self.pairingsThread.is_alive():
            self.pairingsThread = threading.Thread( target=self._launch_pairings, args=(self.pairingWaitTime,) )
            self.pairingsThread.start( )

    # ---------------- Misc ----------------

    # ---------------- Embed Generators ----------------
    def getTournamentStatusEmbed( self ) -> discord.Embed:
        digest = super().getTournamentStatusEmbed( )
        queueMessage = f'There are {self.queue.size()} players in the queue.'
        queueStr  = f' The queue looks like:\n{str(self.queue)}' if self.queue.size() > 0 else ""
        if len(queueMessage) + len(queueStr) <= 1024:
            queueMessage += queueStr
        digest.add_field( name="**Queue Info.**", value=queueMessage )

        return digest

    # ---------------- Player Accessors ----------------

    # ---------------- Tournament Status ----------------

    # ---------------- Player Management ----------------

    # ---------------- Match Management ----------------

    # ---------------- Matchmaking Queue ----------------

    # There will be a far more sofisticated pairing system in the future. Right now, the dummy version will have to do for testing
    # This is a prime canidate for adjustments when players how copies of match results.
    async def addPlayerToQueue( self, plyr: int ) -> commandResponse:
        Plyr = self.getPlayer( plyr )
        digest = commandResponse( )
        if Plyr is None:
            digest.setContent( f'<@{plyr}>, you are not registered for {self.name}.' )
        elif not Plyr.isActive( ):
            digest.setContent( f'<@{plyr}>, you are not an active player in {self.name}.' )
        elif not self.isActive( ):
            digest.setContent( f'<@{plyr}>, {self.name} has not started yet.' )
        elif Plyr.hasOpenMatch( ):
            digest.setContent( f'<@{plyr}>, you are in a match that is not certified. Make sure that everyone in your last match has confirmed the result.' )
        elif len(Plyr.decks) == 0:
            digest.setContent( f'<@{plyr}>, you have not submitted a deck for {self.name}. You need to do so before playing.' )
        else:
            digest.setContent( self.queue.addPlayer( Plyr ) )
            self.queueActivity.append( (plyr, datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f') ) )
            self.saveOverview( )
            await self.updateInfoMessage( )
            if self.queue.readyToPair( self.pairingsThreshold ) and not self.pairingsThread.is_alive():
                self.pairingsThread = threading.Thread( target=self._launch_pairings, args=(self.pairingWaitTime,) )
                self.pairingsThread.start( )

        return digest

    # TODO: This method need to be renamed
    async def removePlayerFromQueue( self, plyr: int ) -> commandResponse:
        Plyr = self.getPlayer( plyr )
        digest = commandResponse( )
        if Plyr is None:
            digest.setContent( f'<@{plyr}>, you are not registered for {self.name}.' )
        elif not Plyr.isActive( ):
            digest.setContent( f'{Plyr.getMention()}, you are not an active player in {self.name}.' )
        elif not self.isActive( ):
            digest.setContent( f'{Plyr.getMention()}, {self.name} has not started yet.' )
        else:
            digest.setContent( self.queue.removePlayer( Plyr ) )
            self.saveOverview( )
            await self.updateInfoMessage( )

        return digest

    # Wrapper for self._pairQueue so that it can be ran on a seperate thread
    def createPairings( self, waitTime ):
        sleep( waitTime )
        print( "Launching task" )
        fut_pairings = asyncio.run_coroutine_threadsafe( self._pairQueue(waitTime), self.loop )
        fut_pairings.result( )

    async def _pairQueue( self, waitTime: int ) -> None:
        startingStr = str( self.queue )
        pairings: List = self.queue.createPairings( self.playersPerMatch )
        for pairing in pairings:
            await self.addMatch( pairing )

        endStr = str( self.queue )

        self.queue.bump( )

        self.saveOverview()

        if self.queue.readyToPair( self.pairingsThreshold ) and startingStr != endStr:
            self.pairingsThread = threading.Thread( target=self._launch_pairings, args=(0,) )
            self.pairingsThread.start( )

        return

    # ---------------- XML Saving/Loading ----------------

    def saveTournamentType( self, filename: str = "" ) -> None:
        print( "Fluid Round tournament type being saved." )
        with open( filename, 'w+' ) as xmlfile:
            xmlfile.write( "<?xml version='1.0'?>\n<type>fluidRoundTournament</type>" )

    def _getInnerXMLString( self ) -> str:
        digest  = super()._getInnerXMLString()
        digest += f'\t<queue size="{self.playersPerMatch}" threshold="{self.pairingsThreshold}">\n'
        digest += self.queue.exportToXML( "\t\t" )
        digest += f'\t</queue>\n'
        digest += f'\t<queueActivity>\n'
        for act in self.queueActivity:
            digest += f'\t\t<event player="{act[0]}" time="{act[1]}"/>\n'
        digest += f'\t</queueActivity>\n'

        return digest

    def loadOverview( self, filename: str ) -> None:
        super().loadOverview( filename )
        xmlTree = ET.parse( filename )
        tournRoot = xmlTree.getroot()

        self.playersPerMatch = int( fromXML(tournRoot.find( 'queue' ).attrib['size'] ))
        self.pairingsThreshold = int( fromXML(tournRoot.find( 'queue' ).attrib['threshold'] ))
        self.matchLength     = int( fromXML(tournRoot.find( 'matchLength' ).text ))

        acts    = tournRoot.find( 'queueActivity' ).findall( 'event' )
        for act in acts:
            self.queueActivity.append( ( fromXML( act.attrib['player'] ), fromXML(act.attrib['time'] ) ) )
        players = tournRoot.find( 'queue' ).findall( 'player' )
        for plyr in players:
            self.queue.addPlayer( self.playerReg.getPlayer( int(fromXML(plyr.attrib['name'])) ), int(plyr.attrib['priority']) )
        if self.queue.readyToPair( self.pairingsThreshold ) and not self.pairingsThread.is_alive( ):
            self.pairingsThread = threading.Thread( target=self._launch_pairings, args=(self.pairingWaitTime,) )
            self.pairingsThread.start( )



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
from .match import match
from .player import player
from .deck import deck
from .swissSystem import *


"""
    This is a tournament class. The bulk of data management for a tournament is handled by this class.
    It also holds certain metadata about the tournament, such as the tournament's name and host guild's name.
"""
class swissTournament(tournament):
    def __init__( self, name: str, hostGuildName: str, props: dict = { } ):
        super().__init__( name, hostGuildName, props )
        self.pairingSystem     = swissSsystem( )

        if len(props) != 0:
            self.setProperties(props)

    # ---------------- Property Accessors ----------------

    # ---------------- Misc ----------------

    # ---------------- Embed Generators ----------------

    # ---------------- Player Accessors ----------------

    # ---------------- Tournament Status ----------------

    # ---------------- Player Management ----------------

    # TODO: Ditto, rename method
    async def removePlayerFromQueue( self, plyr: str ) -> commandResponse:
        Plyr = self.getPlayer( plyr )
        digest = commandResponse( )
        if Plyr is None:
            digest.setContent( f'<@{plyr}>, you are not registered for {self.name}.' )
        elif not Plyr.isActive( ):
            digest.setContent( f'{Plyr.getMention()}, you are not an active player in {self.name}.' )
        elif not self.isActive( ):
            digest.setContent( f'{Plyr.getMention()}, {self.name} has not started yet.' )
        else:
            digest.setContent( self.pairingSystem.removePlayer( Plyr ) )
            self.saveOverview( )
            await self.updateInfoMessage( )

        return digest

    # ---------------- Match Management ----------------


    def createPairings( self, mention: str ) -> commandResponse:
        """ Creates the pairings for the next round. Needs confirmation for matches are created. """
        digest = commandResponse( )
        uncertMatches = [ mtch for mtch in self.matches if not mtch.isCertified() ]
        if len(uncertMatches) != 0:
            newLine = "\n\t- "
            digest.setContent( f'{mention}, below are the matches that are not certified. They their result needs to be confirmed before pairing the next round.{newLine}{newLine.join([mtch.matchNumber for mtch in uncertMatches ] )}' )
        else:
            for plyr in self.players:
                self.pairingSystem.addPlayer( plyr )
            self.pairingSystem.createPairings( )
            digest.setContent( f'{mention}, below are pairings and byes that will be created.' )
            digest.setEmbed( self.pairingSystem.getPairingsEmbed() )

        return digest

    async def confirmPairings( self, mention: str ) -> commandResponse:
        """ Confirms that the stored round pairings are good. """
        digest = commandResponse( )
        digest.setContent( f'{mention}, the round has been paired.' )
        return

    # ---------------- XML Saving/Loading ----------------

    def saveTournamentType( self, filename: str = "" ) -> None:
        print( "Fluid Round tournament type being saved." )
        with open( filename, 'w+' ) as xmlfile:
            xmlfile.write( "<?xml version='1.0'?>\n<type>swissTournament</type>" )


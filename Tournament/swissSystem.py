""" This module contains the queue object that is used to create pairings in the fluidRound tournament"""
# Imports of standard libraries

# Partial imports from standard libraries
import random

# Include typing help
from typing import List, Tuple

# External libraries
import discord

# Local modules
from .utils import *
from .player import *
from .pairingSystem import *


class swissSystem( pairingSystem ):
    """ This class takes in player objects and pairs them together for match creation. """
    def __init__( self ):
        """ Constructor """
        self.queue: List = [ ]
        self.savedPairings = [ ]
        self.savedByes = [ ]

    def __str__( self ):
        """ Returns a string representation of the queue. """
        return ", ".join( [ plyr.getMention() for plyr in self.savedPairings ] )

    def size( self ) -> int:
        """ Calculates the number of people in the queue """
        return len( self.queue )

    def height( self ) -> int:
        """ Calculates the number of levels in the queue """
        return 1

    def _copyQueue( self ) -> List:
        """ Deepcopy struggles with copying player objects. This method creates a psuedo-deepcopy """
        return [ plyr for plyr in self.queue ]

    def _isInQueue( self, plyr: player ) -> bool:
        """ Determines if a player is in the queue """
        return plyr in self.queue

    def _linearize( self, q: List = None ) -> List:
        """ Flattens the queue into a single list """
        return self._copyQueue( )

    def _shuffle( self ) -> List:
        """ Returns a copy of the current queue, but with each level shuffled """
        digest: List = self._copyQueue( )
        random.shuffle( digest )
        return digest

    def _trim( self ) -> None:
        """ Removes any empty list at the end of the queue (formed when players are removed) """
        return None

    def _attemptPairing( self, matchSize: int ) -> List[List]:
        """ Creates a potential list of pairings """
        return [ ]

    def bump( self ) -> None:
        """ Not needs for Swiss pairings. """
        return None

    def addPlayer( self, plyr: player, index: int = 0 ) -> str:
        """ Adds a player to the queue """
        if self._isInQueue( plyr ):
            return f'{plyr.getMention()}, you are already in the pairings.'
        self.queue.append( plyr )
        return f'{plyr.getMention()}, you have been added to the pairings.'

    def removePlayer( self, plyr: player ) -> str:
        """ Removes a player from the queue """
        if not self._isInQueue( plyr ):
            return f'{plyr.getMention()}, you are not in the pairings.'
        self.queue.remove(plyr)
        return f'{plyr.getMention()}, you have been removed from the pairings.'

    def readyToPair( self, threshold: int ) -> bool:
        """ Determines if there are enough people to create pairings """
        return True

    def _isValidGroup( self, plyrs: List ) -> bool:
        """ Determines if a group of players are all mutually valid opponents. """
        # Creates each pair of player and determines if they can be paired
        # together and logically ANDs the results
        return Intersection( [ A.isValidOpponent(B) for i, A in enumerate(plyrs) for B in plyrs[i+1:] ] )

    def _attemptPairing( self, players: List, matchSize: int ) -> List[List]:
        """ Creates a potential list of pairings."""
        digest: List = [ ]
        copyOfPlayers = [ p for p in players ]
        random.shuffle( copyOfPlayers )
        # The pairings process can begin
        pairingFound = True
        # There has to be a more pythonic way of doing...
        while pairingFound and len(copyOfPlayers) != 0:
            pairingFound = False
            pairing = [ copyOfPlayers[0] ]
            del copyOfPlayers[0]
            for plyr in copyOfPlayers:
                pairing.append( plyr )
                if not self._isValidGroup( pairing ):
                    del pairing[-1]
                if len(pairing) == matchSize:
                    digest.append( pairing )
                    pairingFound = True
                    break
            if pairingFound:
                for plyr in digest[-1][1:]:
                    copyOfPlayers.remove( plyr )

        return digest

    # This simply pairs the queue. Players are removed by the tournament
    def createPairings( self, standings: List, matchSize: int ) -> List:
        """ Pairs the players in the queue """
        # Standings should be in first-to-last-place order (descending score)
        standings.reverse()
        self.savedByes: List = [ ]
        self.savedPairings: List = [ ]
        for i in range(len(standings)%matchSize):
            self.savedByes.append( standings[0] )
            del standings[0]
        tries : List = [ ]
        for _ in range( 250 ):
            tries.append( self._attemptPairing( standings, matchSize ) )
            # Would the new queue be smaller than the match size
            if matchSize*len(tries[-1]) == len(standings):
                break
        # In the unlikely event that proper pairings can't be formed,
        # Players are paired together, regardless of thier past opponents
        if matchSize*len(tries[-1]) != len(standings):
            for i in range(len(standings))[::4]:
                self.savedPairings.append( [ standings[i  ],
                                             standings[i+1],
                                             standings[i+2],
                                             standings[i+3] ] )
        else:
            self.savedPairings = tries[-1]

        return [ [ plyr.uuid for plyr in pairing ] for pairing in self.savedPairings ]

    def getPairingsEmbed( self ) -> discord.Embed:
        digest = discord.Embed( title="**Pairings for the Next Round**" )
        if len(self.savedByes) > 0:
            digest.add_field( name="**Byes**", value=", ".join( [plyr.getMention() for plyr in self.savedByes] ) )
        else:
            digest.add_field( name="**Byes**", value="There are no byes." )
        for i, pairing in enumerate( self.savedPairings ):
            digest.add_field( name=f'**Table #{i+1}:**', value=", ".join( [plyr.getMention() for plyr in pairing] ) )
        return digest


    # Note that there is not a load method. Players are added back in by the tournament when its load method is called.
    def exportToXML( self, indent: str ) -> str:
        """ Exports the queue to an XML for saving. """
        return "".join( [ f'{indent}<player name="{p.uuid}" priority="{i}"/>\n' for i, p in enumerate(self.queue) ] )



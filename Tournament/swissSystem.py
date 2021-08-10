""" This module contains the queue object that is used to create pairings in the fluidRound tournament"""
# Imports of standard libraries

# Partial imports from standard libraries
from random import shuffle

# Include typing help
from typing import List, Tuple

# External libraries

# Local modules
from .utils import *
from .player import *


class swissSystem:
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
        shuffle( digest )
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
        queue.remove(plyr)
        return f'{plyr.getMention()}, you have been removed from the pairings.'

    def readyToPair( self, threshold: int ) -> bool:
        """ Determines if there are enough people to create pairings """
        return True

    # This simply pairs the queue. Players are removed by the tournament
    def createPairings( self, matchSize: int, standings: List ) -> List:
        """ Pairs the players in the queue """
        # Standings should be in first-to-last-place order (descending score)
        standings.reverse()
        for i in range(len(standings)%matchSize):
            self.savedByes.append( standings[0] )
            del standings[0]
        shuffle( standings )
        self.savedByes = standings[:len(standings)]
        if matchSize > self.size():
            return [ ]
        size = self.size()
        tries : List = [ ]
        for _ in range( 25 ):
            tries.append( self._attemptPairing( matchSize ) )
            # Would the new queue be smaller than the match size
            if size - len(tries[-1])*matchSize < matchSize:
                break
        print( tries )
        tries.sort( key=lambda x: len(x) )
        # Since the tries have been sorted, the last one will be the one with
        # the most pairings
        return [ [ plyr.discordID for plyr in pairing ] for pairing in tries[-1] ]

    # Note that there is not a load method. Players are added back in by the tournament when its load method is called.
    def exportToXML( self, indent: str ) -> str:
        """ Exports the queue to an XML for saving. """
        return "".join( [ f'{indent}<player name="{p.uuid}" priority="{i}"/>\n' for i, p in enumerate(self.queue) ] )



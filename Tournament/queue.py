""" This module contains the queue object that is used to create pairings in the fluidRound tournament"""
# Imports of standard libraries

# Partial imports from standard libraries
from copy import deepcopy
from random import shuffle

# Include typing help
from typing import List, Tuple

# External libraries

# Local modules
from .utils import *
from .player import *


class pairingQueue:
    """ This class takes in player objects and pairs them together for match creation. """
    def __init__( self ):
        """ Constructor """
        self.queue: List[List] = [ [ ] ]

    def __str__( self ):
        """ Returns a string representation of the queue. """
        levels = [ ]
        for lvl in self.queue:
            if len(lvl) < 1:
                continue
            levels.append( ", ".join( [ plyr.getMention() for plyr in lvl ] ) )
        return "\n".join( [ f'Tier {i+1}: {lvl}' for i, lvl in levels ] )

    def size( self ) -> int:
        """ Calculates the number of people in the queue """
        return sum( len(lvl) for lvl in self.queue )

    def height( self ) -> int:
        """ Calculates the number of levels in the queue """
        return len(self.queue)

    def _isInQueue( self, plyr: player ) -> bool:
        """ Determines if a player is in the queue """
        return Union( [ (plyr in lvl) for lvl in self.queue ] )

    def _linearize( self, q: List = None ) -> List:
        """ Flattens the queue into a single list """
        if q is None:
            return [ p for p in lvl for lvl in self.queue ]
        return [ p for p in lvl for lvl in q ]

    def _delinearize( self, q: List ) -> List:
        """ Unflattens a flattened queue """
        pass

    def _shuffle( self ) -> List:
        """ Returns a copy of the current queue, but with each level shuffled """
        return [ shuffle(lvl) for lvl in deepcopy( self.queue ) ]

    def _canBePairedTogether( self, plyrOne: player, plyrTwo: player ) -> bool:
        """ Determines if two players can be paired against one another """
        # Techincally, this should be two-sided, but a one-sided check should suffice
        # I.e. if player one is in player two's list of opponents, then player
        # two should be in player one's list of opponents.
        return (plyrOne in plyrTwo.opponents)

    def _isValidGroup( self, plyrs: List ) -> bool:
        """ Determines if a group of players are all mutually valid opponents. """
        # Creates each pair of player and determines if they can be paired
        # together and logically ANDs the results
        return Intersection( [ self._canBePairedTogether(A, B) for i, A in enumerate(plyrs) for B in plyrs[i+1:] ] )

    def _attemptPairing( self, matchSize: int ) -> Tuple:
        pass

    def addPlayer( self, plyr: player ) -> str:
        """ Adds a player to the queue """
        if self._isInQueue( plyr ):
            return f'{plyr.getMention()}, you are already in the queue.'
        self.queue[0].append( plyr )
        return f'{plyr.getMention()}, you have been added to the queue.'

    def removePlayer( self, plyr: player ) -> str:
        """ Removes a player from the queue """
        for lvl in self.queue:
            if plyr in lvl:
                lvl.remove(plyr)
                return f'{plyr.getMention()}, you have been removed from the queue.'
        return f'{plyr.getMention()}, you were not in the queue.'

    def readyToPair( self, threshold: int ) -> bool:
        """ Determines if there are enough people to create pairings """
        return threshold > self.size()

    # This simply pairs the queue. Players are removed by the tournament
    def createPairings( self, matchSize: int ) -> List:
        """ Pairs the players in the queue """
        if matchSize > self.size():
            return [ ]
        tries : List = [ ]
        for _ in range( 25 ):
            tries.append( self._attemptPairing( matchSize ) )
            # Is the new queue smaller than the match size
            if len(tries[-1][1]) < matchSize:
                break
        # The possible queues are sorted by the number of matches they created
        # with the largest number last
        tries.sort( key=lambda x: len(x[0]) )
        self.queue = self._delinearize( tries[-1][1] )
        return tries[-1][0]



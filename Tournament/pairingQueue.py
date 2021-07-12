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
        return

    def __str__( self ):
        """ Returns a string representation of the queue. """
        levels = [ ]
        for lvl in self.queue:
            if len(lvl) < 1:
                continue
            levels.append( ", ".join( [ plyr.getMention() for plyr in lvl ] ) )
        return "\n".join( [ f'Tier {i+1}: {lvl}' for i, lvl in enumerate(levels) ] )

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
        return [ p for lvl in q for p in lvl ]

    def _shuffle( self ) -> List:
        """ Returns a copy of the current queue, but with each level shuffled """
        digest: List = [ ]
        for lvl in deepcopy( self.queue ):
            shuffle(lvl)
            digest.append( lvl )
        return digest

    def _trim( self ) -> None:
        """ Removes any empty list at the end of the queue (formed when players are removed) """
        # There always needs to be at least one list in the queue
        while len(self.queue) > 1 and len(self.queue[-1]) == 0:
            del self.queue[-1]
        return

    def _isValidGroup( self, plyrs: List ) -> bool:
        """ Determines if a group of players are all mutually valid opponents. """
        # Creates each pair of player and determines if they can be paired
        # together and logically ANDs the results
        return Intersection( [ A.isValidOpponent(B) for i, A in enumerate(plyrs) for B in plyrs[i+1:] ] )

    def _attemptPairing( self, matchSize: int ) -> List:
        """ Creates a potential list of pairings """
        digest: List = [ ]
        # The queue gets shuffled, each tier is sorted so that players with
        # byes are prioritized, linearized, and then reversed
        queue: List = [ ]
        for lvl in self._shuffle():
            lvl.sort( key=lambda p: p.countByes(), reverse=True )
            queue.append( lvl )
        queue = list( reversed( self._linearize( queue ) ) )
        # The pairings process can begin
        pairingFound = True
        # There has to be a more pythonic way of doing...
        while pairingFound and len(queue) >= matchSize:
            #print( "\n".join( [ str([ p.getMention() for p in pairing ]) for pairing in digest ] ) )
            pairing = [ queue[0] ]
            del queue[0]
            for plyr in queue:
                pairing.append( plyr )
                if not self._isValidGroup( pairing ):
                    del pairing[-1]
                if len(pairing) == matchSize:
                    digest.append( pairing )
                    pairingFound = True
                    break
            if pairingFound:
                for plyr in digest[-1][1:]:
                    queue.remove( plyr )

        return digest

    def bump( self ) -> None:
        """ Adds an empty list to the begin of the queue. """
        self.queue.insert( [ ], 0 )
        return

    def addPlayer( self, plyr: player, index: int = 0 ) -> str:
        """ Adds a player to the queue """
        if self._isInQueue( plyr ):
            return f'{plyr.getMention()}, you are already in the queue.'
        self.queue[index].append( plyr )
        return f'{plyr.getMention()}, you have been added to the queue.'

    def removePlayer( self, plyr: player ) -> str:
        """ Removes a player from the queue """
        for lvl in self.queue:
            if plyr in lvl:
                lvl.remove(plyr)
                self._trim()
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
        size = self.size()
        tries : List = [ ]
        for _ in range( 25 ):
            tries.append( self._attemptPairing( matchSize ) )
            # Would the new queue be smaller than the match size
            if size - len(tries[-1])*matchSize < matchSize:
                break
        tries.sort( key=lambda x: len(x) )
        return tries[-1][0]

    # Note that there is not a load method. Players are added back in by the tournament when its load method is called.
    def exportToXML( self, indent: str ) -> str:
        """ Exports the queue to an XML for saving. """
        return indent.join( [ f'<player name="{p.discordID}" priority="{i}"/>\n' for i, lvl in enumerate(self.queue) for p in lvl ] )



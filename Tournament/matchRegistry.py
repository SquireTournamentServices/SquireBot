""" This module contains the MatchRegistry class which manages the list of matches for the tournament. """

from typing import List

import discord

from match import match
from playerRegistry import PlayerRegistry
from utils import *


class MatchRegistry:
    """ Tracks, stores, and creates new matches for the tournament class. """

    def __init__( self ):
        """ The constructor. """
        self.matches: List = [ ]
        self.playerReg = None

    def __str___( self ):
        """ Returns a string representation of the registry. """
        return "The match registry doesn't have a string method yet."

    # ---------------- Accessors ----------------

    def setPlayerRegistry( self, plyrReg: PlayerRegistry ) -> None:
        """ Setter for the player registry. """
        self.playerReg = plyrReg

    # ---------------- Meta-Accessors ----------------
    # I.e. accessors for lists of matches

    def _getNextMatchNumber( self ) -> int:
        digest = 0
        for mtch in self.matches:
            if mtch.getMatchNumber() > digest:
                digest = mtch.getMatchNumber
        return digest + 1

    def getActiveMatches( self ) -> List:
        """ Returns a list of matches that have not be finalized. """
        return [ mtch for mtch in self.matches if mtch.isActive() ]

    def getCertifiedMatches( self ) -> List:
        """ Returns a list of matches that have been finalized. """
        return [ mtch for mtch in self.matches if mtch.isCertified() ]

    def getUncertifiedMatches( self ) -> List:
        """ Returns a list of matches where someone claimed victory, but are uncertified. """
        return [ mtch for mtch in self.matches if mtch.isUncertified() ]

    def getByeMatches( self ) -> List:
        """ Returns a list of matches that are byes. """
        return [ mtch for mtch in self.matches if mtch.isBye() ]

    # ---------------- Match Management ----------------

    def createMatch( self ) -> match:
        """ Creates a new match, stores it, and returns a reference to it. """
        digest = match( self._getNextMatchNumber() )
        self.matches.append( digest )
        return digest

    def _getMatchViaUUID( self, ID: str ) -> match:
        """ Find the match with the same UUID or returns None. """
        digest = None
        for mtch in self.matches:
            if ID == mtch.getUUID():
                digest = mtch
                break
        return digest

    def _getMatchViaMatchNumber( self, num: str ) -> match:
        """ Find the match with the same match number or returns None. """
        digest = None
        for mtch in self.matches:
            if num == mtch.getMatchNumber():
                digest = mtch
                break
        return digest

    def getMatch( self, ident ) -> match:
        """ Gets a match from the list of matches or returns None. """
        if isUUID( ident ):
            return self._getMatchViaUUID( ident )
        return self._getMatchViaMatchNumber( ident )

    # ---------------- Saving and Loading ----------------

    def saveMatches( self, location: str ) -> None:
        """ Saves all matches' xml files. """
        for mtch in self.matches:
            mtch.saveXML( f'{location}/matches/match_{match.getMatchNumber()}.xml' )

    def loadMatches( self, location: str ) -> None:
        """ Given a directory, saves the match files in that directory. """
        matchFiles = [ f'{location}/{f}' for f in os.listdir(location) if os.path.isfile( f'{location}/{f}' ) ]
        for matchFile in matchFiles:
            newMatch = match( -1 )
            newMatch.saveLocation = matchFile
            newMatch.loadXML( matchFile )
            newMatch.activePlayers = [ self.playerReg.getPlayer(plyr) for plyr in newMatch.activePlayers ]
            newMatch.droppedPlayers = [ self.playerReg.getPlayer(plyr) for plyr in newMatch.droppedPlayers ]
            newMatch.confirmedPlayers = [ self.playerReg.getPlayer(plyr) for plyr in newMatch.confirmedPlayers ]
            winner = self.playerReg.getPlayer( newMatch.winner )
            self.matches.append( newMatch )
            for plyr in newMatch.players:
                plyr.addMatch( newMatch )
            # TODO: The timer system should be stored here, but there should be a better method than threading
            #if not ( self.matches[-1].isCertified() or self.matches[-1].isDead() ) and not self.matches[-1].stopTimer:
            #    self.matches[-1].timer = threading.Thread( target=self._matchTimer, args=(self.matches[-1],) )
            #    self.matches[-1].timer.start( )



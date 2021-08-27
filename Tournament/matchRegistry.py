""" This module contains the MatchRegistry class which manages the list of matches for the tournament. """

from typing import List

import discord

from match import match
from utils import *


class MatchRegistry:
    """ Tracks, stores, and creates new matches for the tournament class. """

    def __init__( self ):
        """ The constructor. """
        self.matches: List = [ ]

    def __str___( self ):
        """ Returns a string representation of the registry. """
        return "The match registry doesn't have a string method yet."

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

    def _getMatchViaUUID( self, num: str ) -> match:
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

    def saveMatches( self, location: str = "" ) -> None:
        """ Saves all matches' xml files. """
        pass

    def loadMatches( self, location: str ) -> None:
        """ Given a directory, saves the match files in that directory. """
        pass



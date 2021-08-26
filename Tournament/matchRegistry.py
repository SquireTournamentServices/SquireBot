""" This module contains the MatchRegistry class which manages the list of matches for the tournament. """

import discord

from typing import List

from match import match
from utils import *


class MatchRegistry:
    """ Tracks, stores, and creates new matches for the tournament class. """

    def __init__( self ):
        """ The constructor. """
        self.matches: List = [ ]
        pass

    def __str___( self ):
        """ Returns a string representation of the registry. """
        return "The match register doesn't have a string method yet."

    # ---------------- Meta-Accessors ----------------
    # I.e. accessors for lists of matches

    def getActiveMatches( self ) -> List:
        """ Returns a list of matches that have not be finalized. """
        pass

    def getCertifiedMatches( self ) -> List:
        """ Returns a list of matches that have been finalized. """
        pass

    def getUncertifiedMatches( self ) -> List:
        """ Returns a list of matches where someone claimed victory, but are uncertified. """
        pass

    # ---------------- Match Management ----------------

    def createMatch( self ) -> match:
        """ Creates a new match, stores it, and returns a reference to it. """
        pass

    def addMatch( self, mtch: match ) -> None:
        """ Adds a player to the list of players. """
        return

    def getMatch( self, ident ) -> match:
        """ Gets a player for the list of players or returns None. """
        pass

    # ---------------- Saving and Loading ----------------

    def saveMatches( self, location: str = "" ) -> None:
        """ Saves all matches' xml files. """
        pass

    def loadMatches( self, location: str ) -> None:
        """ Given a directory, saves the match files in that directory. """
        pass



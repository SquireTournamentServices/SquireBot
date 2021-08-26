""" This module contains the PlayerRegistry class which manages the list of players for the tournament. """

import discord

from typing import List

from player import player
from utils import *


class PlayerRegistry:
    """ Tracks, stores, and creates new players for the tournament class. """

    def __init__( self ):
        """ The constructor. """
        pass

    def __str___( self ):
        """ Returns a string representation of the registry. """
        return "The player register doesn't have a string method yet."

    def getCurrentPlayer( self ) -> List:
        """ Returns a list of players that have not dropped. """
        pass

    def getActivePlayers( self ) -> List:
        """ Returns a list of players that are active. """
        pass

    def getFullyRegisteredPlayers( self ) -> List:
        """ Returns a list of players that are ready to start the tournament. """
        pass

    def getReadyPlayers( self ) -> List:
        """ Returns a list of players that have checked-in for their next game. """
        pass

    def addPlayer( self, plyr: player ) -> None:
        """ Adds a player to the list of players. """
        return

    def getPlayer( self ) -> player:
        """ Gets a player for the list of players or returns None. """
        pass

    def savePlayers( self, location: str = "" ) -> None:
        """ Saves all players' xml files. """
        pass

    def loadPlayers( self, location: str ) -> None:
        """ Given a directory, saves the player files in that directory. """
        pass


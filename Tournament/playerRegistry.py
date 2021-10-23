""" This module contains the PlayerRegistry class which manages the list of players for the tournament. """

import os
import sys

import discord

from typing import List

from .player import player
from .utils import *


class PlayerRegistry:
    """ Tracks, stores, and creates new players for the tournament class. """

    def __init__( self ):
        """ The constructor. """
        self.players: List = [ ]
        # TODO: Properties that get checked to see if a player is fully registered will go here

    def __str___( self ):
        """ Returns a string representation of the registry. """
        return "The player registry doesn't have a string method yet."

    # ---------------- Accessors ----------------

    def getPlayer( self, ident: str ) -> player:
        """ Gets a player from the list of players or returns None. """
        if isinstance( ident, int ):
            ident = str(ident)

        if ident == "" or ( not isinstance(ident, str) ):
            return None

        if isUUID( ident ):
            return self._getPlayerViaUUID( ident )
        elif ident.isnumeric():
            return self._getPlayerViaDiscordID( ident )
        else:
            return self._getPlayerViaName( ident )

    def _getPlayerViaName( self, name: str ) -> player:
        """ Gets a player from the list of players based on that player's name. """
        digest = None
        for plyr in self.players:
            if name == plyr.getName():
                digest = plyr
                break
        return digest

    def _getPlayerViaUUID( self, ID: str ) -> player:
        """ Gets a player from the list of players based on that player's UUID. """
        digest = None
        for plyr in self.players:
            if ID == plyr.getUUID():
                digest = plyr
                break
        return digest

    def _getPlayerViaDiscordID( self, ID: str ) -> player:
        """ Gets a player from the list of players based on that player's Discord id. """
        digest = None
        for plyr in self.players:
            if ID == plyr.getDiscordID():
                digest = plyr
                break
        return digest

    # ---------------- Meta-Accessors ----------------

    def getPlayers( self ) -> List:
        """ Returns a copy of the full list of players. """
        return [ plyr for plyr in self.players ]

    def getActivePlayers( self ) -> List:
        """ Returns a list of players that have not dropped or been cut. """
        return [ plyr for plyr in self.players if plyr.isActive() ]

    def getFullyRegisteredPlayers( self ) -> List:
        """ Returns a list of players that are ready to start the tournament. """
        return [ plyr for plyr in self.players if self.isFullyRegistered() ]

    # TODO: Game lfg and match check-ins will be added eventually
    def getReadyPlayers( self ) -> List:
        """ Returns a list of players that have checked-in for their next game. """
        return [ ]

    # ---------------- Player Management ----------------

    def createPlayer( self, name: str ) -> player:
        """ Adds a player to the list of players. """
        if not self.getPlayer( name ) is None:
            newPlayer = player( name )
            self.players.append( newPlayer )
            return newPlayer
        return None

    def isFullyRegistered( self, plyr: player ) -> bool:
        """ Checks to see if a plyr is fully registered. """
        # TODO: This method will use the new member to allow for dynamically defining what "fully registered" means.
        return len(plyr.decks) > 0

    # ---------------- Saving and Loading ----------------

    def savePlayers( self, location: str = "" ) -> None:
        """ Saves all players' xml files. """
        for plyr in self.players:
            plyr.saveXML( f'{location}/players/{plyr.getUUID()}.xml' )

    def loadPlayers( self, location: str ) -> None:
        """ Given a directory, saves the player files in that directory. """
        playerFiles = [ f'{location}/{f}' for f in os.listdir(location) if os.path.isfile( f'{location}/{f}' ) ]
        for playerFile in playerFiles:
            newPlayer = player( "" )
            newPlayer.saveLocation = playerFile
            newPlayer.loadXML( playerFile )
            self.players.append( newPlayer )


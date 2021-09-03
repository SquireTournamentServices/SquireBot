""" This module contains the ScoringSystem abstract class which manages the scores of players for the tournament. """

import discord

from playerRegister import PlayerRegistry
from matchRegister import MatchRegistry
from utils import *


class ScoringSystem:
    """ This class is a base class for future scoring systems. """

    def __init__( self ):
        """ The constructor. """
        pass

    def __str___( self ):
        """ Returns a string representation of the scoring system. """
        return "The scoring system doesn't have a string method yet."

    def getStandings( self ) -> List:
        """ Returns an ordered list of players and their scores. """
        pass

    def getStandingsEmbed( self ) -> List[discord.Embed]:
        """ Returns an list of enbeds containing the standings information. """
        pass

    async def updateStandingsMessage( self ) -> None:
        """ Updates the standings message(s) to be up-to-date. """
        pass


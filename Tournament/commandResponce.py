""" This module only contains the response class. """
from typing import Dict

import discord

from .exceptions import *
from .utils import *


class commandResponse:
    """ This is a simple class intended to communicate between the tournament class and the bot. """
    # The class constructor
    def __init__( self, content: str = None, embed: discord.Embed = None ):
        """ Class constructor. Content and embed can be set after or during constuction. """
        self.content = content
        self.embed   = embed

    def setContent( self, content: str ) -> None:
        """ Sents the content member sting. """
        if not isinstance( content, str ):
            return
        self.content = content

    def setEmbed( self, embed: discord.Embed ) -> None:
        """ Sents the embed member object. """
        if not isinstance( embed, discord.Embed ):
            return
        self.embed = embed

    async def send( self, messageable: discord.Messageable ):
        """ Takes a messageable object and send a message contain the stored info. """
        if not isinstance( messageable, discord.Messageable ):
            return
        await messageable.send( content=self.content, embed=self.embed )


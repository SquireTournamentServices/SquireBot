
import os
import shutil
import xml.etree.ElementTree as ET
import random
import threading
import time
import discord
import asyncio
import warnings


from typing import List, Dict, Tuple

from .tricebot import *
from .utils import *
from .match import *
from .player import *
from .deck import *
from .tournament import *
from .fluidRoundTournament import *
from .tournamentSelector import *



class guildSettings:
    def __init__( self, guild: discord.Guild ):
        self.guild   : discord.Guild = guild
        self.filename: str = f'guilds/{guild.id}'
        
        # Defaults
        # A member variable with the prefix "d_" is a default
        self.d_judgeRole     : discord.Role = discord.utils.get( guild.roles , name="Judge" )
        self.d_tournAdminRole: discord.Role = discord.utils.get( guild.roles , name="Tournament Admin" )

        self.d_pairingsChannel: discord.channel = discord.utils.get( guild.channels, name="pairings" )
        self.d_VCCatergory    : discord.CategoryChannel = discord.utils.get( guild.categories, name="Matches" )
        
        # Tournament Stuff
        self.tournaments  : list = [ ]
        self.d_tournType  : str = "Swiss"
        self.tournDefaults: dict = { }
        for prop in tournamentProperties:
            self.tournDefaults[prop] = None
        
        self.defaultNames = [ "judge-role", "tournament-admin-role", "pairings-channel", "vc-category", "tournament-type" ]

    
    # ---------------- Guild Accessors ----------------

    # Discord already defines if a guild Member is an admin in that guild.
    # This method wraps that
    def isGuildAdmin( self, user: discord.Member ) -> bool:
        return user.guild_permissions.administrator
    
    # Judges and Admins need to specify players for many commands
    # To do this, they can specify a player's display name, mention, or Discord ID
    def getMember( self, ident: str ) -> discord.Member:
        for member in self.guild.members:
            # Was a display name given?
            if ident == member.display_name:
                return member
            # Was a member's mention given?
            if get_ID_from_mention( ident ) == str(member.id):
                return member
            # Was a member's id given?
            if ident == str(member.id):
                return member
        
    
    # ---------------- Role Accessors ----------------
    def getTournAdminRole( self, tournName: str ) -> discord.Role:
        tourn = self.getTournament( tournName )
        if tourn is None:
            return None
        return tourn.tournAdminRole
    
    def getJudgeRole( self ) -> discord.Role:
        tourn = self.getTournament( tournName )
        if tourn is None:
            return None
        return tourn.judgeRole
    
    def isTournamentAdmin( self, user: discord.Member, tournName: str = None ) -> bool:
        if tournName is None:
            return self.d_tournAdminRole in user.roles
        tourn = self.getTournament( tournName )
        if tourn is None:
            return False
        return tourn.tournAdminRole in user.roles
    
    def isJudge( self, user: discord.Member, tournName: str = None ) -> bool:
        if tournName is None:
            return self.d_judgeRole in user.roles
        tourn = self.getTournament( tournName )
        if tourn is None:
            return False
        return tourn.judgeRole in user.roles
    
    def isTournamentOfficial( self, user: discord.Member, tournName: str = None ) -> bool:
        return self.isTO( user, tournName ) or self.isJudge( user, tournName )
    
    
    # ---------------- Settings and Default Methods ----------------
    
    # Updates the default settings for the guild
    def updateDefaults( self, defaults: Dict ) -> str:
        successes: list = [ ]
        failures : list = [ ]
        undefined: list = [ ]
        digest   : str  = ""

        for default in defaults:    
            if not default in self.defaultNames:
                undefined.append( default )
                continue

            if default == "judge-role":
                tmp = self.guild.get_role( get_ID_from_mention(defaults[default]) )
                if not tmp is None:
                    self.d_judgeRole = tmp
                    successes.append( default )
                else:
                    failures.append( default )
            elif default == "tournament-admin-role":
                tmp = self.guild.get_role( get_ID_from_mention(defaults[default]) )
                if not tmp is None:
                    self.d_tournAdminRole = tmp
                    successes.append( default )
                else:
                    failures.append( default )
            elif default == "pairings-channel":
                tmp = self.guild.get_channel( get_ID_from_mention(defaults[default]) )
                if not tmp is None:
                    self.d_pairingsChannel = tmp
                    successes.append( default )
                else:
                    failures.append( default )
            elif default == "vc-category":
                tmp = self.guild.get_channel( get_ID_from_mention(defaults[default]) )
                if not tmp is None:
                    self.d_VCCatergory = tmp
                    successes.append( default )
                else:
                    failures.append( default )
            elif default == "tournament-type":
                if defaults[default] in tournamentTypes:
                    self.d_tournType = defaults[default]
                    successes.append( default )
                else:
                    failures.append( default )

        if len(successes) == 0:
            digest += "No defaults were successfully updated."
        else:
            digest += f'The following default{" was" if len(successes) == 1 else "s were"} successfully updated:\n\t-'
            digest += "\n\t-".join( [ f'{d}: {defaults[d]}' for d in successes ] )
        if len(failures) > 0:
            digest += f'\n\nThere were errors in updating the following default{"" if len(failures) == 1 else "s"}:\n\t-'
            digest += "\n\t-".join( [ f'{d}: {defaults[d]}' for p in failures ] )
        if len(undefined) > 0:
            digest += f'\n\n{self.name} does not have the following default{"" if len(failures) == 1 else "s"}:\n\t-'
            digest += "\n\t-".join( [ f'{d}: {defaults[d]}' for d in undefined ] )

        return digest

    def updateTournDefaults( self ) -> str:
        pass
        
    
    # ---------------- Tournament Methods ----------------
    def _mergeProperties( self ) -> Dict:
        pass

    def createTournament( self ) -> tournament:
        pass
    
    def endTournament( self ) -> str:
        pass
    
    def currentTournaments( self ) -> List:
        pass
    
    def getTournament( self ) -> tournament:
        pass
    
   
   
    # ---------------- Saving and Loading Methods ----------------
    def save( self ) -> None:
        pass
    
    def load( self ) -> None:
        pass








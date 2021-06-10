
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
        self.tournaments : list = [ ]
        self.d_tournType : str = "Swiss"
        self.d_tournProps: dict = { }
        for prop in tournamentProperties:
            self.d_tournProps[prop] = None
        
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
        digest : str  = ""
        
        # Passing the adjusted defaults through the base fluidRoundsTournament
        filteredDefaults = fluidRoundTournament.filterProperties( { prop: defaults[prop] for prop in defaults if not (prop in self.defaultNames) } )
        
        # TODO: As more tournaments types are added, this process will need to grow
        
        # Updating properties

        if "judge-role" in defaults:
            tmp = self.guild.get_role( get_ID_from_mention(defaults["judge-role"]) )
            if not tmp is None:
                self.d_judgeRole = tmp
                filteredDefaults["successes"]["judge-role"] = defaults["judge-role"]
            else:
                filteredDefaults["failures"]["judge-role"] = defaults["judge-role"]
        if "tournament-admin-role" in defaults:
            tmp = self.guild.get_role( get_ID_from_mention(defaults["tournament-admin-role"]) )
            if not tmp is None:
                self.d_tournAdminRole = tmp
                filteredDefaults["successes"]["tournament-admin-role"] = defaults["tournament-admin-role"]
            else:
                filteredDefaults["failures"]["tournament-admin-role"] = defaults["tournament-admin-role"]
        if "pairings-channel" in defaults:
            tmp = self.guild.get_channel( get_ID_from_mention(defaults["pairings-channel"]) )
            if not tmp is None:
                self.d_pairingsChannel = tmp
                filteredDefaults["successes"]["pairings-channel"] = defaults["pairings-channel"]
            else:
                filteredDefaults["failures"]["pairings-channel"] = defaults["pairings-channel"]
        if "vc-category" in defaults:
            tmp = self.guild.get_channel( get_ID_from_mention(defaults["vc-category"]) )
            if not tmp is None:
                self.d_VCCatergory = tmp
                filteredDefaults["successes"]["vc-category"] = defaults["vc-category"]
            else:
                filteredDefaults["failures"]["vc-category"] = defaults["vc-category"]
        if "tournament-type" in defaults:
            if defaults["tournament-type"] in tournamentTypes:
                self.d_tournType = defaults["tournament-type"]
                filteredDefaults["successes"]["tournament-type"] = defaults["tournament-type"]
            else:
                filteredDefaults["failures"]["tournament-type"] = defaults["tournament-type"]
        
        for prop in filteredDefaults["successes"]:
            self.d_tournProps[prop] = filteredDefaults[prop]

        if len(filteredDefaults["successes"]) == 0:
            digest += "No defaults were successfully updated."
        else:
            digest += f'The following default{" was" if len(filteredDefaults["successes"]) == 1 else "s were"} successfully updated:\n\t-'
            digest += "\n\t-".join( [ f'{d}: {defaults[d]}' for d in filteredDefaults["successes"] ] )
        if len(filteredDefaults["failures"]) > 0:
            digest += f'\n\nThere were errors in updating the following default{"" if len(filteredDefaults["failures"]) == 1 else "s"}:\n\t-'
            digest += "\n\t-".join( [ f'{d}: {defaults[d]}' for p in filteredDefaults["failures"] ] )
        if len(filteredDefaults["undefined"]) > 0:
            digest += f'\n\n{self.name} does not have the following default{"" if len(filteredDefaults["undefined"]) == 1 else "s"}:\n\t-'
            digest += "\n\t-".join( [ f'{d}: {defaults[d]}' for d in filteredDefaults["undefined"] ] )

        return digest

    
    # ---------------- Tournament Methods ----------------
    
    # Users can set properties that are used in some tournament types, but not others
    # This filters out the unneeded properties
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








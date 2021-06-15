
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
        self.saveLoction: str = f'guilds/{guild.id}'
        
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
        
        self.eventLoop = None

        self.defaultNames = [ "judge-role", "tournament-admin-role", "pairings-channel", "vc-category", "tournament-type" ]

    # ---------------- Misc ----------------
    
    # Tournament need access to the bot's event loop.
    # This is called on bot start up
    def setEventLoop( self, loop ) -> None:
        self.eventLoop = loop
        for tourn in self.tournaments:
            tourn.loop = loop
    
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
        filteredDefaults = filterProperties( { prop: defaults[prop] for prop in defaults if not (prop in self.defaultNames) } )
        
        # TODO: As more tournaments types are added, this process will need to grow
        
        # Updating properties
        
        for prop in filteredDefaults["successes"]:
            self.d_tournProps[prop] = filteredDefaults["successes"][prop]

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

        if len(filteredDefaults["successes"]) == 0:
            digest += "No defaults were successfully updated."
        else:
            digest += f'The following default{" was" if len(filteredDefaults["successes"]) == 1 else "s were"} successfully updated:\n\t-'
            digest += "\n\t-".join( [ f'{d}: {defaults[d]}' for d in filteredDefaults["successes"] ] )
        if len(filteredDefaults["failures"]) > 0:
            digest += f'\n\nThere were errors in updating the following default{"" if len(filteredDefaults["failures"]) == 1 else "s"}:\n\t-'
            digest += "\n\t-".join( [ f'{d}: {defaults[d]}' for d in filteredDefaults["failures"] ] )
        if len(filteredDefaults["undefined"]) > 0:
            digest += f'\n\n{self.name} does not have the following default{"" if len(filteredDefaults["undefined"]) == 1 else "s"}:\n\t-'
            digest += "\n\t-".join( [ f'{d}: {defaults[d]}' for d in filteredDefaults["undefined"] ] )

        return digest

    
    # ---------------- Tournament Methods ----------------
    
    # Users can set properties that are used in some tournament types, but not others
    # This filters out the unneeded properties
    def _mergeProperties( self, overwriteProps: Dict, tourn: tournament ) -> None:
        for prop in tourn.properties:
            if not (prop in overwriteProps):
                overwriteProps[prop] = self.d_tournProps[prop]

    def createTournament( self, tournType: str, name: str, props: Dict ) -> str:
        tourn = getTournamentType( tournType, name, self.guild.name, {} )
        props = self._mergeProperties( props, tourn )
        digest = tourn.setProperties( props )
        tourn.loop = self.eventLoop
        self.tournaments.append( tourn )
        return digest
    
    # Cancels a tournament (given by name)
    # TODO: The end and cancel tournament methods should be combined
    def endTournament( self, name: str, author: str ) -> str:
        tourn = self.getTournament( name )
        digest = tourn.cancelTourn( self.d_tournAdminRole.mention, author )
        del self.tournaments[ self._indexTournament(name) ]
        return digest
        pass
    
    def currentTournaments( self ) -> List:
        return self.tournaments
    
    def getTournament( self, name: str ) -> tournament:
        digest = None
        for tourn in self.tournaments:
            if tourn.name == name:
                digest = tourn
                break
        return digest
    
    def _indexTournament( self, name: str ) -> int:
        digest = None
        for i in range(len(self.tournaments)):
            if self.tournaments[i].name == name:
                digest = i
                break
        return digest
   
   
    # ---------------- Saving and Loading Methods ----------------
    def save( self, dirName: str = "" ) -> None:
        if dirName == "":
            dirName = self.saveLocation
        else:
            self.saveLoction = dirName
        
        if not (os.path.isdir( dirName ) and os.path.exists( dirName )):
           os.mkdir( dirName )

        self.saveSettings( f'{dirName}/settings.xml' )
        self.saveTournaments( f'{dirName}/currentTournaments/' )
        
        if not (os.path.isdir( f'{dirName}/currentTournaments/' ) and os.path.exists( f'{dirName}/currentTournaments/' )):
           os.mkdir( f'{dirName}/currentTournaments/' )
        
        if not (os.path.isdir( f'{dirName}/closedTournament/' ) and os.path.exists( f'{dirName}/closedTournament/' )):
           os.mkdir( f'{dirName}/closedTournament/' )
    
    def saveSettings( self, filename: str = "" ) -> None:
        if filename == "":
            filename = f'{self.saveLocation}/settings.xml'
        digest  = "<?xml version='1.0'?>\n"
        digest += '<settings>\n'
        digest += f'\t<guild name="{self.guild.name}" id="{self.guild.id}"/>\n'
        if self.d_judgeRole is None:
            digest += f'\t<judgeRole name="None" id="None"/>\n'
        else:
            digest += f'\t<judgeRole name="{self.d_judgeRole.name}" id="{self.d_judgeRole.id}"/>\n'
        
        if self.d_tournAdminRole is None:
            digest += f'\t<tournAdminRole name="None" id="None"/>\n'
        else:
            digest += f'\t<tournAdminRole name="{self.d_tournAdminRole.name}" id="{self.d_tournAdminRole.id}"/>\n'
        
        if self.d_pairingsChannel is None:
            digest += f'\t<pairingsChannel name="None" id="None"/>\n'
        else:
            digest += f'\t<pairingsChannel name="{self.d_pairingsChannel.name}" id="{self.d_pairingsChannel.id}"/>\n'
        
        if self.d_VCCatergory is None:
            digest += f'\t<VCCatergory name="None" id="None"/>\n'
        else:
            digest += f'\t<VCCatergory name="{self.d_VCCatergory.name}" id="{self.d_VCCatergory.id}"/>\n'

        digest += f'\t<tournType default="{self.d_tournType}"/>\n'
        digest += f'\t<properties '
        for prop in self.d_tournProps:
            digest += f'{prop}="{self.d_tournProps[prop]}" '
        digest += f'/>\n'
        digest += '</settings>\n'
        
        with open( filename, 'w+' ) as xmlfile:
            xmlfile.write( toSafeXML(digest) )
    
    def saveTournaments( self, filename: str = "" ) -> None:
        if filename == "":
            filename = f'{self.saveLoction}/currentTournaments/'

        for tourn in self.tournaments:
            tourn.saveTournament()
    
    def load( self, dirName: str ) -> None:
        self.saveLoction = dirName
        self.loadSettings( f'{dirName}/settings.xml' )
        self.loadTournaments( f'{dirName}/currentTournaments' )
    
    def loadSettings( self, filename: str ) -> None:
        xmlTree = ET.parse( filename )
        root    = xmlTree.getroot()
        
        try:
            self.d_judgeRole       = self.guild.get_role( int(fromXML(root.find('judgeRole').attrib['id'])) )
        except ValueError:
            pass
        try:
            self.d_tournAdminRole  = self.guild.get_role( int(fromXML(root.find('tournAdminRole').attrib['id'])) )
        except ValueError:
            pass
        try:
            self.d_pairingsChannel = self.guild.get_channel( int(fromXML(root.find('pairingsChannel').attrib['id'])) )
        except ValueError:
            pass
        try:
            self.d_VCCatergory     = self.guild.get_channel( int(fromXML(root.find('VCCatergory').attrib['id'])) )
        except ValueError:
            pass
        
        self.d_tournType = fromXML(root.find("tournType").attrib["default"])
        
        # The filter properties method converts properties too
        self.updateDefaults( { fromXML(prop): fromXML(root.find("properties").attrib[fromXML(prop)]) for prop in root.find("properties").attrib } )
    
    def loadTournaments( self, dirName: str ) -> None:
        tournDirs: list = [ f'{dirName}/{tournName}/' for tournName in os.listdir(dirName) if os.path.isdir( f'{dirName}/{tournName}/' ) ]
        for tournDir in tournDirs:
            tourn = tournamentSelector( f'{tournDir}/tournamentType.xml', tournDir.split("/")[-2], self.guild.name, {} )
            tourn.loadTournament( tournDir )
            tourn.assignGuild( self.guild )
            self.tournaments.append( tourn )



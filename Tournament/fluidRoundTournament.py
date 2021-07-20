import os
import shutil
import xml.etree.ElementTree as ET
import random
import threading
import discord
import asyncio
import warnings

from time import sleep
from typing import List, Tuple

from .utils import *
from .tournament import tournament
from .match import match
from .player import player
from .deck import deck
from .pairingQueue import *


"""
    This is a tournament class. The bulk of data management for a tournament is handled by this class.
    It also holds certain metadata about the tournament, such as the tournament's name and host guild's name.
"""
class fluidRoundTournament(tournament):
    def __init__( self, name: str, hostGuildName: str, props: dict = { } ):     
        self.name = name.replace("\.\./", "")
        self.hostGuildName = hostGuildName
        self.format    = props["format"] if "format" in props else "Pioneer"
        
        self.guild   = None
        self.guildID = ""
        self.role    = None
        self.roleID  = ""
        self.pairingsChannel = None
        self.pairingsChannelID = ""
        
        self.infoMessageChannelID = None
        self.infoMessageID = None
        self.infoMessage = None
        
        self.regOpen      = True
        self.tournStarted = False
        self.tournEnded   = False
        self.tournCancel  = False
        
        self.loop = asyncio.new_event_loop( )
        self.fail_count = 0
        
        self.playersPerMatch   = int(props["match-size"]) if "match-size" in props else 2
        self.matchLength       = int(props["match-length"])*60 if "match-length" in props else 60*60 # Length of matches in seconds
        
        self.queue             = pairingQueue( )
        self.pairingsThreshold = self.playersPerMatch * 2 # + 3
        self.pairingWaitTime   = 5
        self.queueActivity     = [ ]
        self.highestPriority   = 0
        self.pairingsThread    = threading.Thread( target=self._launch_pairings, args=(self.pairingWaitTime,) )
        
        self.deckCount = 1

        self.players  = {}
        
        self.matches = []
        
        #Create bot class and store the game creation settings
        self.triceBotEnabled = False
        self.spectators_allowed = False
        self.spectators_need_password = False 
        self.spectators_can_chat = False 
        self.spectators_can_see_hands = False 
        self.only_registered = False
        self.player_deck_verification = False
                
        if len(props) != 0:
            self.setProperties(props)
    
    # ---------------- Property Accessors ---------------- 

    def updatePairingsThreshold( self, count: int ) -> None:
        self.pairingsThreshold = count
        if self.queue.readyToPair( self.pairingsThreshold ) and not self.pairingsThread.is_alive():
            self.pairingsThread = threading.Thread( target=self._launch_pairings, args=(self.pairingWaitTime,) )
            self.pairingsThread.start( )
    
    # ---------------- Misc ---------------- 

    # ---------------- Embed Generators ---------------- 
    def getTournamentStatusEmbed( self ) -> discord.Embed:
        digest: discord.Embed = discord.Embed( title = f'{self.name} Status' )
        NL = "\n"
        NLT = "\n\t"
        
        props = self.getProperties()
        propsText = f'{self.name} has{"" if self.isActive() else " not"} started.\n' + "\n".join( [ f'{p}: {props[p]}' for p in props if not props[p] is None ] )
        digest.add_field( name="**Settings Info.**", value=propsText )
        
        plyrsWithDecks = [ p for p in self.players if len(self.players[p].decks) > 0 ]
        plyrsActive = [ p for p in self.players if self.players[p].isActive() ]
        decksText = f'There are {len(plyrsActive)} players registered.'
        if len(plyrsWithDecks) > 0:
            decksText = decksText[:-1] + f', and {len(plyrsWithDecks)} of them have submitted decks.'
        digest.add_field( name="**Player Count**", value=decksText )
        
        queueMessage = f'There are {self.queue.size()} players in the queue.'
        queueStr  = f' The queue looks like:\n{str(self.queue)}' if self.queue.size() > 0 else ""
        if len(queueMessage) + len(queueStr) <= 1024:
            queueMessage += queueStr
        digest.add_field( name="**Queue Info.**", value=queueMessage )
        
        openMatches = [ m for m in self.matches if m.isOpen() ]
        uncertMatches = [ m for m in self.matches if m.isUncertified() ]
        matchText  = f'There are {len(openMatches)} open matches and {len(uncertMatches)} uncertified matches.'
        if len(openMatches) > 0:
            matchText += f'{NL}**Open Matches**:{NLT}{NLT.join([ "#" + str(m.matchNumber) for m in openMatches ])}'
        if len(uncertMatches) > 0:
            matchText += f'{NL}**Uncertified Matches**:{NLT}{NLT.join([ "#" + str(m.matchNumber) for m in uncertMatches ])}'
        digest.add_field( name="**Match Info.**", value=matchText )
        return digest
    
    # ---------------- Player Accessors ---------------- 
    
    # ---------------- Tournament Status ---------------- 
    self.saveOverview( )
    await self.u

    # ---------------- Player Management ---------------- 
    
    # ---------------- Match Management ---------------- 

    # ---------------- Matchmaking Queue ---------------- 
    
    # There will be a far more sofisticated pairing system in the future. Right now, the dummy version will have to do for testing
    # This is a prime canidate for adjustments when players how copies of match results.
    def addPlayerToQueue( self, plyr: int ) -> None:
        if plyr not in self.players:
            return "<@{plyr}>, you are not registered for this tournament."
        if not self.players[plyr].isActive( ):
            return "{self.players[plyr].getMention()}, you are registered but are not an active player."
        
        digest = self.queue.addPlayer( self.players[plyr] )
        self.queueActivity.append( (plyr, datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f') ) )
        if self.queue.readyToPair( self.pairingsThreshold ) and not self.pairingsThread.is_alive():
            self.pairingsThread = threading.Thread( target=self._launch_pairings, args=(self.pairingWaitTime,) )
            self.pairingsThread.start( )
        return digest
    
    async def removePlayerFromQueue( self, plyr: int ) -> None:
        if plyr not in self.players:
            return "<@{plyr}>, you are not registered for this tournament."
        self.saveOverview( )
        await self.updateInfoMessage( )
        return self.queue.removePlayer( self.players[plyr] )

    # Wrapper for self._pairQueue so that it can be ran on a seperate thread
    def _launch_pairings( self, waitTime ):
        sleep( waitTime )
        print( self.queue )
        fut_pairings = asyncio.run_coroutine_threadsafe( self._pairQueue(waitTime), self.loop )
        fut_pairings.result( )

    async def _pairQueue( self, waitTime: int ) -> None:
        startingStr = str( self.queue )
        pairings: List = self.queue.createPairings( self.playersPerMatch )
        for pairing in pairings:
            print( pairing )
            await self.addMatch( pairing )

        endStr = str( self.queue )

        self.queue.bump( )

        self.saveOverview()

        if self.queue.readyToPair( self.pairingsThreshold ) and startingStr != endStr:
            self.pairingsThread = threading.Thread( target=self._launch_pairings, args=(0,) )
            self.pairingsThread.start( )

        return

    # ---------------- XML Saving/Loading ---------------- 

    def saveTournamentType( self, filename: str = "" ) -> None:
        print( "Fluid Round tournament type being saved." )
        with open( filename, 'w+' ) as xmlfile:
            xmlfile.write( "<?xml version='1.0'?>\n<type>fluidRoundTournament</type>" )

    def saveOverview( self, filename: str = "" ) -> None:
        print( "Fluid Round Overview being saved." )
        if filename == "":
            filename = f'{self.getSaveLocation()}/overview.xml'
        digest  = "<?xml version='1.0'?>\n"
        digest += '<tournament>\n'
        digest += f'\t<name>{self.name}</name>\n'
        digest += f'\t<guild id="{self.guild.id if type(self.guild) == discord.Guild else str()}">{self.hostGuildName}</guild>\n'
        digest += f'\t<role id="{self.role.id if type(self.role) == discord.Role else str()}"/>\n'
        digest += f'\t<pairingsChannel id="{self.pairingsChannel.id}"/>\n'
        if not self.infoMessage is None:
            digest += f'\t<infoMessage channel="{self.infoMessage.channel.id}" id="{self.infoMessage.id}"/>\n'
        digest += f'\t<format>{self.format}</format>\n'
        digest += f'\t<regOpen>{self.regOpen}</regOpen>\n'
        digest += f'\t<status started="{self.tournStarted}" ended="{self.tournEnded}" canceled="{self.tournCancel}"/>\n'
        digest += f'\t<deckCount>{self.deckCount}</deckCount>\n'
        digest += f'\t<matchLength>{self.matchLength}</matchLength>\n'
        digest += f'\t<triceBotEnabled>{self.triceBotEnabled}</triceBotEnabled>\n'
        digest += f'\t<spectatorsAllowed>{self.spectators_allowed}</spectatorsAllowed>\n'
        digest += f'\t<spectatorsNeedPassword>{self.spectators_need_password}</spectatorsNeedPassword>\n'
        digest += f'\t<spectatorsCanChat>{self.spectators_can_chat}</spectatorsCanChat>\n'
        digest += f'\t<spectatorsCanSeeHands>{self.spectators_can_see_hands}</spectatorsCanSeeHands>\n'
        digest += f'\t<onlyRegistered>{self.only_registered}</onlyRegistered>\n'
        digest += f'\t<playerDeckVerification>{self.player_deck_verification}</playerDeckVerification>\n'
        digest += f'\t<queue size="{self.playersPerMatch}" threshold="{self.pairingsThreshold}">\n'
        digest += self.queue.exportToXML( "\t\t" )
        digest += f'\t</queue>\n'
        digest += f'\t<queueActivity>\n'
        for act in self.queueActivity:
            digest += f'\t\t<event player="{act[0]}" time="{act[1]}"/>\n'
        digest += f'\t</queueActivity>\n'
        digest += '</tournament>' 
        
        with open( filename, 'w+' ) as xmlfile:
            xmlfile.write( toSafeXML(digest) )
    
    def loadOverview( self, filename: str ) -> None:
        xmlTree = ET.parse( filename )
        tournRoot = xmlTree.getroot()
        self.name = fromXML(tournRoot.find( 'name' ).text)
        self.guildID   = int( fromXML(tournRoot.find( 'guild' ).attrib["id"]) )
        self.roleID    = int( fromXML(tournRoot.find( 'role' ).attrib["id"]) )
        self.pairingsChannelID = int( fromXML(tournRoot.find( 'pairingsChannel' ).attrib["id"]) )
        if not tournRoot.find( 'infoMessage' ) is None:
            self.infoMessageChannelID = int( fromXML(tournRoot.find( 'infoMessage' ).attrib["channel"]) )
            self.infoMessageID = int( fromXML(tournRoot.find( 'infoMessage' ).attrib["id"]) )

        self.format    = fromXML(tournRoot.find( 'format' ).text)
        self.deckCount = int( fromXML(tournRoot.find( 'deckCount' ).text) )

        self.regOpen      = str_to_bool( fromXML(tournRoot.find( 'regOpen' ).text ))
        self.tournStarted = str_to_bool( fromXML(tournRoot.find( 'status' ).attrib['started'] ))
        self.tournEnded   = str_to_bool( fromXML(tournRoot.find( 'status' ).attrib['ended'] ))
        self.tournCancel  = str_to_bool( fromXML(tournRoot.find( 'status' ).attrib['canceled'] ))

        self.playersPerMatch = int( fromXML(tournRoot.find( 'queue' ).attrib['size'] ))
        self.pairingsThreshold = int( fromXML(tournRoot.find( 'queue' ).attrib['threshold'] ))
        self.matchLength     = int( fromXML(tournRoot.find( 'matchLength' ).text ))
        
        self.triceBotEnabled = str_to_bool( fromXML(tournRoot.find( "triceBotEnabled" ).text ) )
        self.spectators_allowed = str_to_bool( fromXML(tournRoot.find( "spectatorsAllowed" ).text ) )
        self.spectators_need_password = str_to_bool( fromXML(tournRoot.find( "spectatorsNeedPassword" ).text ) )
        self.spectators_can_chat = str_to_bool( fromXML(tournRoot.find( "spectatorsCanChat" ).text ) )
        self.spectators_can_see_hands = str_to_bool( fromXML(tournRoot.find( "spectatorsCanSeeHands" ).text ) )
        self.only_registered = str_to_bool( fromXML(tournRoot.find( "onlyRegistered" ).text ) )
        self.player_deck_verification = str_to_bool( fromXML(tournRoot.find( "playerDeckVerification" ).text ) )
        
        acts    = tournRoot.find( 'queueActivity' ).findall( 'event' )
        for act in acts:
            self.queueActivity.append( ( fromXML( act.attrib['player'] ), fromXML(act.attrib['time'] ) ) )
        players = tournRoot.find( 'queue' ).findall( 'player' )
        for plyr in players:
            self.queue.addPlayer( self.players[int(fromXML(plyr.attrib['name']))], int(plyr.attrib['priority']) )
        if self.queue.readyToPair( self.pairingsThreshold ) and not self.pairingsThread.is_alive( ):
            self.pairingsThread = threading.Thread( target=self._launch_pairings, args=(self.pairingWaitTime,) )
            self.pairingsThread.start( )



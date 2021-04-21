import xml.etree.ElementTree as ET

import discord

from typing import List
import threading

from .utils import *


"""
    This class is designed to store information about a match and be a commonly referenced object amoungst player objects.
    It currently has the following functionities:
        - A player can be dropped from a match, so they don't have to confirm the result
        - A winner (or draw) can be record, which changes the state of the match to "uncertified"
        - Players can verify the result, which adds then to the list of confirmed players
        - Once all active players expect the reported winner have confirmed the result the match state is changed to "certified"
        - At anytime, the winner can be overwriten, but this changes the state to "uncertified", always
        - The match can be saved to an xml file
        - It can also be loaded from one, though this is done post-contruction
    There will be functionalities added, but what those look like remains to be seen.
    
    The class has the following member variables:
        - activePlayers : A list of strings (player's names) that are in the match
        - droppedPlayers: A list of strings (player's names) that dropped from the match
        - confirmedPlayers: A list of strings (player's names) that have confirmed the result
        - status: The correct status of the match, options are "open", "uncertified", and "certified"
        - winner: The winner of the match or, in the case of a draw, a string stating that the match was a draw
"""

class match:
    # The class constructor
    def __init__( self, a_players: List[str] ):
        self.saveLocation = ""

        self.matchNumber = -1

        self.activePlayers    = a_players
        self.droppedPlayers   = [ ]
        self.confirmedPlayers = [ ]
        
        self.misfortunes = { }

        self.role   = ""
        self.roleID = ""
        self.VC     = ""
        self.VC_ID  = ""

        self.status = "open"
        self.winner = ""

        self.timeExtension = 0
        self.timer     = ""
        self.startTime = getTime( )
        self.endTime   = ""
        
        self.stopTimer = False
    
    def __str__( self ):
        digest  = f'Match #{self.matchNumber}\n'
        digest += f'Active players: {", ".join(self.activePlayers)}\n'
        digest += f'Dropped players: {", ".join(self.droppedPlayers)}\n'
        digest += f'ConfirmedPlayers: {", ".join(self.confirmedPlayers)}\n'
        digest += f'Match status: {self.status}\n'
        digest += f'Match winner: {self.winner}'
        return digest
    
    def isBye( self ) -> bool:
        return self.winner == "This match is a bye."
    
    def isDraw( self ) -> bool:
        return self.winner == "This match was a draw."
    
    def isDead( self ) -> bool:
        return self.status == "dead"
    
    def isCertified( self ):
        return self.status == "certified"
    
    def getTimeElapsed( self ) -> int:
        if self.isCertified() or self.stopTimer:
            return -1
        digest = round(timeDiff( getTime(), self.startTime ) - self.timeExtension)
        if digest < 0:
            return 0
        else:
            return round(digest/60)
    
    def addMatchRole( self, a_role: discord.Role ) -> None:
        self.role = a_role
    
    def addMatchVC( self, a_VC: discord.VoiceChannel ) -> None:
        self.VC = a_VC
    
    async def killMatch( self ) -> None:
        if type( self.VC ) == discord.VoiceChannel:
            await self.VC.delete()
        if type( self.role ) == discord.Role:
            await self.role.delete()

        self.activePlayers    = [ ]
        self.droppedPlayers   = [ ]
        self.confirmedPlayers = [ ]

        self.role   = ""
        self.roleID = ""
        self.VC     = ""
        self.VC_ID  = ""

        self.winner = ""
        self.status = "dead"
        self.endTime = getTime( )
        self.stopTimer = True

 
    async def confirmMatch( self ) -> bool:
        digest  = len( self.activePlayers )  == 1
        digest |= len(self.confirmedPlayers) >= len(self.activePlayers)
        digest &= not self.isCertified( )
        if digest:
            self.status = "certified"
            self.endTime = getTime( )
            self.stopTimer = True
            if type( self.VC ) == discord.VoiceChannel:
                await self.VC.delete()
        return digest

    # Drops a player, which entains removing them from the active players
    # list and adding them to the dropped players list.
    async def dropPlayer( self, a_player: str ) -> str:
        for i in range(len(self.activePlayers)):
            if a_player == self.activePlayers[i]:
                self.droppedPlayers.append( a_player )
                del( self.activePlayers[i] )
                break
        if await self.confirmMatch( ):
            if len(self.activePlayers) == 0:
                self.winner = "This match was a draw."
            else:
                self.winner = self.activePlayers[0]
            self.confirmedPlayers.append( self.winner )
            return f'{self.role.mention}, your match has been certified. You can join the matchmaking queue again.'
        else:
            return ""
    
    def recordBye( self ) -> None:
        self.winner = "This match is a bye."
        self.endTime = getTime()
        self.stopTimer = True
        self.status = "certified"
    
    # Confirms the result for one player.
    # If all players have confirmed the result, the status of the match is status to "certified"
    async def confirmResult( self, a_player: str ) -> str:
        if self.status != "uncertified":
            return ""
        if not a_player in self.confirmedPlayers:
            self.confirmedPlayers.append( a_player )
        if await self.confirmMatch( ):
            self.stopTimer = True
            return f'{self.role.mention}, your match has been certified. You can join the matchmaking queue again.'
        else:
            return ""
    
    # Records the winner of a match and adds them to the confirmed players list.
    # An empty string is interpretted as a draw, in which case, no one is added to the confirmed players list.
    # In either case, the status of the match is changed to "uncertified"
    async def recordWinner( self, a_winner: str ) -> str:
        if a_winner == "":
            self.winner = "This match was a draw."
            self.confirmedPlayers = [ ]
        else:
            self.winner = a_winner
            self.confirmedPlayers = [ a_winner ]

        if await self.confirmMatch( ):
            return f'{self.role.mention}, your match has been certified. You can join the matchmaking queue again.'
        else:
            self.status = "uncertified"
            return ""
            

    # Saves the match to an xml file at the given location.
    def saveXML( self, a_filename: str = "" ) -> None:
        if a_filename == "":
            a_filename = self.saveLocation
        digest  = "<?xml version='1.0'?>\n"
        digest += f'<match roleID="{toSafeXML(self.role.id if type(self.role) == discord.Role else str())}" VC_ID="{toSafeXML(self.VC.id if type(self.VC) == discord.VoiceChannel else str())}">\n'
        digest += f'\t<number>{toSafeXML(self.matchNumber)}</number>\n'
        digest += f'\t<timeExtension>{toSafeXML(self.timeExtension)}</timeExtension>\n'
        digest += f'\t<stopTimer>{toSafeXML(self.stopTimer)}</stopTimer>\n'
        digest += f'\t<startTime>{toSafeXML(self.startTime)}</startTime>\n'
        digest += f'\t<endTime>{toSafeXML(self.endTime)}</endTime>\n'
        digest += f'\t<status>{toSafeXML(self.status)}</status>\n'
        digest += f'\t<winner name="{toSafeXML(self.winner)}"/>\n'
        digest += '\t<activePlayers>\n'
        for player in self.activePlayers:
            digest += f'\t\t<player name="{toSafeXML(player)}"/>\n'
        digest += '\t</activePlayers>\n'
        digest += '\t<droppedPlayers>\n'
        for player in self.droppedPlayers:
            digest += f'\t\t<player name="{toSafeXML(player)}"/>\n'
        digest += '\t</droppedPlayers>\n'
        digest += '\t<confirmedPlayers>\n'
        for player in self.confirmedPlayers:
            digest += f'\t\t<player name="{toSafeXML(player)}"/>\n'
        digest += '\t</confirmedPlayers>\n'
        digest += '</match>'
        with open( a_filename, "w" ) as savefile:
            savefile.write( digest )
    
    # Loads a match from an xml file saved with this class
    def loadXML( self, a_filename: str ) -> None:
        self.saveLocation = a_filename
        xmlTree = ET.parse( a_filename )
        matchRoot = xmlTree.getroot()
        self.roleID = fromXML(matchRoot.attrib["roleID"])
        if self.roleID != "":
            self.roleID = int( fromXML( self.roleID ) )
        self.VC_ID = matchRoot.attrib["VC_ID"]
        if self.VC_ID != "":
            self.VC_ID = int( fromXML( self.VC_ID ) )
        self.matchNumber = int( fromXML( matchRoot.find( "number" ).text ) )
        self.stopTimer = str_to_bool( fromXML( matchRoot.find("stopTimer").text ) )
        self.startTime = matchRoot.find( fromXML( "startTime" ).text )
        self.endTime = matchRoot.find( fromXML( "endTime" ).text )
        self.status = matchRoot.find( fromXML( "status" ).text )
        self.winner = matchRoot.find( fromXML( "winner" ).attrib["name"] )
        for player in matchRoot.find("activePlayers"):
            self.activePlayers.append( fromXML( player.attrib["name"] ) )
        for player in matchRoot.find("droppedPlayers"):
            self.droppedPlayers.append( fromXML( player.attrib["name"] ) )
        for player in matchRoot.find("confirmedPlayers"):
            self.confirmedPlayers.append( fromXML( player.attrib["name"] ) )


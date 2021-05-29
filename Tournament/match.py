import xml.etree.ElementTree as ET

import discord

from typing import List, Dict
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
    def __init__( self, a_players: List[str]):
        self.saveLocation = ""

        self.matchNumber = -1

        self.activePlayers    = a_players
        self.droppedPlayers   = [ ]
        self.confirmedPlayers = [ ]
        
        self.misfortunes = { }

        self.role   = None
        self.roleID = ""
        self.VC     = ""
        self.VC_ID  = ""

        self.status = "open"
        self.winner = ""

        self.matchLength   = 60*60 # Time is in seconds
        self.timeExtension = 0
        self.timer     = ""
        self.startTime = getTime( )        
        self.endTime   = ""
        
        # Only changed if it is a trice match
        self.triceMatch = False
        self.playerDeckVerification = False
        self.gameID = -1
        self.replayURL = ""
        
        self.sentOneMinWarning  = False
        self.sentFiveMinWarning = False
        self.sentFinalWarning   = False
        
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
    
    def getTimeLeft( self ) -> int:
        if self.isCertified() or self.stopTimer:
            return -1
        return self.matchLength - round(self.getTimeElapsed()) + self.timeExtension
        
    def getTimeElapsed( self ) -> float:
        if self.isCertified() or self.stopTimer:
            return -1
        return timeDiff( getTime(), self.startTime )
    
    def giveTimeExtension( self, t: int ) -> None:
        if self.isCertified() or self.stopTimer:
            return None
        timeLeft = self.getTimeLeft()
        if timeLeft + t > 300 and self.sentFiveMinWarning:
            self.sentFiveMinWarning = False
        if timeLeft + t >  60 and self.sentOneMinWarning:
            self.sentOneMinWarning = False
        self.timeExtension += t
        
    
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
    
    def getMention( self ):
        if type(self.role) == discord.Role:
            return self.role.mention
        return f'Match #{self.matchNumber}'
 
    async def confirmMatch( self ) -> bool:
        digest  = len( self.activePlayers    ) == 1
        digest |= len( self.confirmedPlayers ) >= len( self.activePlayers )
        digest &= not self.isCertified( )
        if digest:
            self.status = "certified"
            self.endTime = getTime( )
            self.stopTimer = True
            if type( self.VC ) == discord.VoiceChannel:
                await self.VC.delete()
        return digest

    def recordBye( self ) -> None:
        self.winner = "This match is a bye."
        self.endTime = getTime()
        self.stopTimer = True
        self.status = "certified"
    
    # Confirms the result for one player.
    # If all players have confirmed the result, the status of the match is status to "certified"
    async def confirmResult( self, a_player: str ) -> str:
        if self.status != "uncertified":
            return f'a result for match #{self.matchNumber} has not been recorded.'
        if not a_player in self.confirmedPlayers:
            self.confirmedPlayers.append( a_player )
        if await self.confirmMatch( ):
            self.stopTimer = True
            return f'{self.getMention()}, your match has been certified. You can join the matchmaking queue again.'
        else:
            return f'you have confirmed the result of match #{self.matchNumber}.'
    
    # Combines previous methods into a single method.  A player and "win",
    # "loss", or "draw" is specified and the result for that player is
    # recorded.  Messages and the announcements for the bot to send are made
    # here.  It is intended that any derived class use this method to handle
    # the recording on results in order to provide a single interface for the
    # tournament classes to use
    async def recordResult( self, plyr: str, result: str ) -> Dict[str, str]:
        digest = { "message": "" }
        if self.isCertified():
            digest["message"] = f'Match #{self.matchNumber} is already certified. Talk to a tournament official to change the result of this match.'
            return digest
            
        if "win" == result or "winner" == result:
            self.winner = plyr
            self.confirmedPlayers = [ plyr ]
            digest["message"] = f'<@{plyr}> has recorded themself as the winner of match #{self.matchNumber}. {self.getMention()}, please confirm with "!confirm-result".'
        elif "draw" == result:
            self.winner = "This match is a draw."
            self.confirmedPlayers = [ plyr ]
            digest["message"] = f'<@{plyr}> has recorded match #{self.matchNumber} as a draw. {self.getMention()}, please confirm with "!confirm-result".'
        elif "loss" == result or "loser" == result:
            self.droppedPlayers.append( plyr )
            del( self.activePlayers[ self.activePlayers.index(plyr) ] )
            digest["message"] = f'<@{plyr}>, you have been recorded as losing match #{self.matchNumber}. You will not be able to join the queue until this match is finished, but you will not need to confirm the result.'
        else:
            digest["message"] = f'You have given an invalid result. The possible match results are "win", "draw", and "loss".'
        
        if await self.confirmMatch( ):
            if len(self.activePlayers) == 0:
                self.winner = "This match was a draw."
            elif len(self.activePlayers) == 1:
                self.winner = self.activePlayers[0]
                self.confirmedPlayers.append( self.winner )
            digest["announcement"] = f'{self.getMention()}, your match has been certified. You can join the matchmaking queue again.'
        else:
            self.status = "uncertified"
        
        return digest
    
    async def recordResultAdmin( self, plyr: str, result: str ) -> Dict[str, str]:
        digest = { "message": "" }
        
        if "win" == result or "winner" == result:
            self.winner = plyr
            digest["announcement"] = f'{self.getMention()}, <@{plyr}> has been recorded as the winner of this match.'
            if not self.isCertified( ):
                self.confirmedPlayers = [ ]
                digest["announcement"] += ' Please confirm with "!confirm-result"'
            else:
                digest["announcement"] += ' There is no need to re-confirm the result.'
            digest["message"] = f'<@{plyr}> has recorded as the winner of match #{self.matchNumber}.'
        elif "draw" == result:
            self.winner = "This match is a draw."
            digest["announcement"] = f'{self.getMention()}, this match has been recorded as a draw.'
            if not self.isCertified( ):
                self.confirmedPlayers = [ ]
                digest["announcement"] += ' Please confirm with "!confirm-result"'
            else:
                digest["announcement"] += ' There is no need to re-confirm the result.'
            digest["message"] = f'Match #{self.matchNumber} has been recorded as a draw.'
        elif "loss" == result or "loser" == result:
            self.droppedPlayers.append( plyr )
            del( self.activePlayers[ self.activePlayers.index(plyr) ] )
            digest["announcement"] = f'<@{plyr}>, you have been recorded as losing match #{self.matchNumber}. You will not be able to join the queue until this match is finished, but you will not need to confirm the result.'
            digest["message"] = f'<@{plyr}> has recorded as a loser of match #{self.matchNumber}.'
        else:
            digest["message"] = f'You have given an invalid result. The possible match results are "win", "draw", and "loss".'
        
        if await self.confirmMatch( ):
            if len(self.activePlayers) == 0:
                self.winner = "This match was a draw."
            elif len(self.activePlayers) == 1:
                self.winner = self.activePlayers[0]
                self.confirmedPlayers.append( self.winner )
            digest["announcement"] += f'\n\n{self.getMention()}, your match has been certified. You can join the matchmaking queue again.'
        elif not self.isCertified( ):
            self.status = "uncertified"
        
        return digest

    # Saves the match to an xml file at the given location.
    def saveXML( self, a_filename: str = "" ) -> None:
        if a_filename == "":
            a_filename = self.saveLocation
        digest  = "<?xml version='1.0'?>\n"
        digest += f'<match roleID="{self.role.id if type(self.role) == discord.Role else str()}" VC_ID="{self.VC.id if type(self.VC) == discord.VoiceChannel else str()}">\n'
        digest += f'\t<number>{self.matchNumber}</number>\n'
        digest += f'\t<matchLength>{self.matchLength}</matchLength>\n'
        digest += f'\t<timeExtension>{self.timeExtension}</timeExtension>\n'
        digest += f'\t<stopTimer>{self.stopTimer}</stopTimer>\n'
        digest += f'\t<startTime>{self.startTime}</startTime>\n'
        digest += f'\t<endTime>{self.endTime}</endTime>\n'
        digest += f'\t<sentWarnings oneMin="{self.sentOneMinWarning}" fiveMin="{self.sentFiveMinWarning}" final="{self.sentFinalWarning}"/>\n'
        digest += f'\t<status>{self.status}</status>\n'
        digest += f'\t<triceMatch>{self.triceMatch}</triceMatch>\n'
        digest += f'\t<playerDeckVerification>{self.playerDeckVerification}</playerDeckVerification>\n'
        digest += f'\t<gameID>{self.gameID}</gameID>\n'
        digest += f'\t<replayURL>{self.replayURL}</replayURL>\n'
        digest += f'\t<winner name="{self.winner}"/>\n'
        digest += '\t<activePlayers>\n'
        for player in self.activePlayers:
            digest += f'\t\t<player name="{player}"/>\n'
        digest += '\t</activePlayers>\n'
        digest += '\t<droppedPlayers>\n'
        for player in self.droppedPlayers:
            digest += f'\t\t<player name="{player}"/>\n'
        digest += '\t</droppedPlayers>\n'
        digest += '\t<confirmedPlayers>\n'
        for player in self.confirmedPlayers:
            digest += f'\t\t<player name="{player}"/>\n'
        digest += '\t</confirmedPlayers>\n'
        digest += '</match>'
        with open( a_filename, "w+" ) as savefile:
            savefile.write( toSafeXML(digest) )
    
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
        self.matchNumber   = int( fromXML( matchRoot.find( "number" ).text ) )
        self.timeExtension = int( fromXML( matchRoot.find("timeExtension").text ) )
        self.matchLength   = int( fromXML( matchRoot.find( "matchLength" ).text ) )
        self.stopTimer = str_to_bool( fromXML( matchRoot.find("stopTimer").text ) )
        self.startTime = fromXML( matchRoot.find( "startTime") .text )
        self.endTime = fromXML( matchRoot.find( "endTime" ).text )
        self.status = fromXML( matchRoot.find( "status" ).text )                
        self.triceMatch = str_to_bool( fromXML( matchRoot.find(  "triceMatch" ).text ) )
        self.playerDeckVerification = str_to_bool( fromXML ( matchRoot.find( "playerDeckVerification" ).text ) )
        self.gameID = int( fromXML( matchRoot.find( "gameID" ).text ) )
        self.replayURL = fromXML( matchRoot.find( "replayURL" ).text )
        self.sentOneMinWarning  = str_to_bool( fromXML( matchRoot.find( "sentWarnings" ).attrib["oneMin" ] ) )
        self.sentFiveMinWarning = str_to_bool( fromXML( matchRoot.find( "sentWarnings" ).attrib["fiveMin"] ) )
        self.sentFinalWarning   = str_to_bool( fromXML( matchRoot.find( "sentWarnings" ).attrib["final"  ] ) )
        self.winner = fromXML( matchRoot.find( "winner" ).attrib["name"] )
        if self.winner != "":
            self.winner = int(self.winner)
        for player in matchRoot.find("activePlayers"):
            self.activePlayers.append( int( fromXML( player.attrib["name"] ) ) )
        for player in matchRoot.find("droppedPlayers"):
            self.droppedPlayers.append( int( fromXML( player.attrib["name"] ) ) )
        for player in matchRoot.find("confirmedPlayers"):
            self.confirmedPlayers.append( int( fromXML( player.attrib["name"] ) ) )


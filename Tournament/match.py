import xml.etree.ElementTree as ET
import uuid

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
        self.uuid = str( uuid.uuid4() )
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
        self.textChannel = ""
        self.textChannel_ID = ""

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
        digest += f'Active players: {", ".join([ p.getMention() for p in self.activePlayers ])}\n'
        digest += f'Dropped players: {", ".join([ p.getMention() for p in self.droppedPlayers ])}\n'
        digest += f'ConfirmedPlayers: {", ".join([ p.getMention() for p in self.confirmedPlayers ])}\n'
        digest += f'Match status: {self.status}\n'
        # TODO: Make a winnerToStr method
        if isinstance(self.winner, player):
            digest += f'Match winner: {self.winner.getMention()}>'
        else:
            digest += f'Match winner: self.winner>'
        return digest

    def isOpen( self ) -> bool:
        return self.status == "open"

    def isUncertified( self ) -> bool:
        return self.status == "uncertified"

    def isBye( self ) -> bool:
        return self.winner == "This match is a bye."

    def isDraw( self ) -> bool:
        return self.winner == "This match is a draw."

    def isDead( self ) -> bool:
        return self.status == "dead"

    def isCertified( self ):
        return self.status == "certified"

    def getUUID( self ) -> str:
        """ Returns the unique idenifying ID string of the match. """
        return self.uuid

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

    def addmatchTextChannel( self, a_TC: discord.TextChannel ) -> None:
        self.textChannel = a_TC

    def addMatchVC( self, a_VC: discord.VoiceChannel ) -> None:
        self.VC = a_VC

    async def killMatch( self ) -> None:
        if type( self.VC ) == discord.VoiceChannel:
            await self.VC.delete(reason="Match killed")
        if type( self.textChannel ) == discord.TextChannel:
            await self.textChannel.delete(reason="Match killed")
        if type( self.role ) == discord.Role:
            await self.role.delete(reason="Match killed")

        self.activePlayers    = [ ]
        self.droppedPlayers   = [ ]
        self.confirmedPlayers = [ ]

        self.role   = ""
        self.roleID = ""
        self.VC     = ""
        self.VC_ID  = ""
        self.textChannel = ""
        self.textChannel_ID = ""

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
                await self.VC.delete(reason="Match result confirmed")
            if type( self.textChannel ) == discord.TextChannel:
                await self.textChannel.delete(reason="Match result confirmed")
        return digest

    def recordBye( self ) -> None:
        self.winner = "This match is a bye."
        self.endTime = getTime()
        self.stopTimer = True
        self.status = "certified"

    # Confirms the result for one player.
    # If all players have confirmed the result, the status of the match is status to "certified"
    async def confirmResult( self, a_player: "player" ) -> str:
        digest = { }
        if self.status != "uncertified":
            digest["message"] = f'{a_player.getMention()}, a result of match #{self.matchNumber} has not been recorded.'
        elif a_player in self.confirmedPlayers:
            digest["message"] = f'{a_player.getMention()}, you have already confirmed the result of match #{self.matchNumber}.'
        else:
            self.confirmedPlayers.append( a_player )
            digest["message"] = f'{a_player.getMention()}, your confirmation has been logged.'
            if await self.confirmMatch( ):
                self.stopTimer = True
                digest["announcement"] = f'{self.getMention()}, your match has been certified. You can join the matchmaking queue again.'

        return digest

    async def confirmResultAdmin( self, a_player: "player", mention: str ) -> str:
        digest = { }
        if not (a_player in self.activePlayers or a_player in self.droppedPlayers):
            digest["message"] = f'{mention}, there is no player {a_player!r} in match #{self.matchNumber}.'
        elif a_player in self.confirmedPlayers:
            digest["message"] = f'{mention}, {a_player.getMention()} has already confirmed the result of match #{self.matchNumber}.'
        elif a_player in self.droppedPlayers:
            digest["message"] = f'{mention}, {a_player.getMention()} has already drop from the match #{self.matchNumber}.'
        else:
            self.confirmedPlayers.append( a_player )
            digest["message"] = f'{mention}, you have logged the confirmation of {a_player.getMention()}.'
            if await self.confirmMatch( ):
                self.stopTimer = True
                digest["announcement"] = f'{self.getMention()}, your match has been certified. You can join the matchmaking queue again.'

        return digest

    # Combines previous methods into a single method.  A player and "win",
    # "loss", or "draw" is specified and the result for that player is
    # recorded.  Messages and the announcements for the bot to send are made
    # here.  It is intended that any derived class use this method to handle
    # the recording on results in order to provide a single interface for the
    # tournament classes to use
    async def recordResult( self, plyr: "player", result: str ) -> Dict[str, str]:
        digest = { "message": "" }
        if self.isCertified():
            digest["message"] = f'Match #{self.matchNumber} is already certified. Talk to a tournament official to change the result of this match.'
            return digest

        if "win" == result or "winner" == result:
            self.winner = plyr
            self.confirmedPlayers = [ plyr ]
            digest["message"] = f'{plyr.getMention()} has recorded themself as the winner of match #{self.matchNumber}. {self.getMention()}, please confirm with "!confirm-result".'
        elif "draw" == result:
            self.winner = "This match is a draw."
            self.confirmedPlayers = [ plyr ]
            digest["message"] = f'{plyr.getMention()} has recorded match #{self.matchNumber} as a draw. {self.getMention()}, please confirm with "!confirm-result".'
        elif "loss" == result or "loser" == result:
            self.droppedPlayers.append( plyr )
            self.activePlayers.remove( plyr )
            digest["message"] = f'{plyr.getMention()}, you have been recorded as losing match #{self.matchNumber}. You will not be able to join the queue until this match is finished, but you will not need to confirm the result.'
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

    async def recordResultAdmin( self, plyr: "player", result: str, mention: str ) -> Dict[str, str]:
        digest = { "message": "" }

        if not (plyr in self.activePlayers or plyr in self.droppedPlayers):
            digest["message"] = f'{mention}, there is no player {plyr!r} in match #{self.matchNumber}.'
            return digest

        # TODO: Each of these pieces should probably be its own method
        if "win" == result or "winner" == result:
            self.winner = plyr
            digest["announcement"] = f'{self.getMention()}, {plyr.getMention()} has been recorded as the winner of this match.'
            if not self.isCertified( ):
                self.confirmedPlayers = [ plyr ]
                digest["announcement"] += ' Please confirm with "!confirm-result"'
            else:
                digest["announcement"] += ' There is no need to re-confirm the result.'
            digest["message"] = f'{mention}, {plyr.getMention()} has recorded as the winner of match #{self.matchNumber}.'
        elif "draw" == result:
            self.winner = "This match is a draw."
            digest["announcement"] = f'{self.getMention()}, this match has been recorded as a draw.'
            if not self.isCertified( ):
                self.confirmedPlayers = [ plyr ]
                digest["announcement"] += ' Please confirm with "!confirm-result"'
            else:
                digest["announcement"] += ' There is no need to re-confirm the result.'
            digest["message"] = f'{mention}, match #{self.matchNumber} has been recorded as a draw.'
        elif "loss" == result or "loser" == result:
            # TODO: A player that double-drops can cause issues
            self.droppedPlayers.append( plyr )
            self.activePlayers.remove( plyr )
            digest["announcement"] = f'{plyr.getMention()}, you have been recorded as losing match #{self.matchNumber}. You will not be able to join the queue until this match is finished, but you will not need to confirm the result.'
            digest["message"] = f'{mention}, {plyr.getMention()} has recorded as a loser of match #{self.matchNumber}.'
        else:
            digest["message"] = f'{mention}, you have given an invalid result. The possible match results are "win", "draw", and "loss".'

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
        digest += f'<match roleID="{self.role.id if type(self.role) == discord.Role else str()}" VC_ID="{self.VC.id if type(self.VC) == discord.VoiceChannel else str()}" text_channel_ID="{self.textChannel.id if type(self.textChannel) == discord.TextChannel else str()}">\n'
        digest += f'\t<uuid>{self.uuid}</uuid>'
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
        digest += f'\t<replayURL>{toSafeXML(self.replayURL)}</replayURL>\n'
        if isinstance(self.winner, player):
            digest += f'\t<winner name="{self.winner.getUUID()}"/>\n'
        else:
            digest += f'\t<winner name="{self.winner}"/>\n'
        digest += '\t<activePlayers>\n'
        for plyr in self.activePlayers:
            digest += f'\t\t<player name="{plyr.getUUID()}"/>\n'
        digest += '\t</activePlayers>\n'
        digest += '\t<droppedPlayers>\n'
        for plyr in self.droppedPlayers:
            digest += f'\t\t<player name="{plyr.getUUID()}"/>\n'
        digest += '\t</droppedPlayers>\n'
        digest += '\t<confirmedPlayers>\n'
        for plyr in self.confirmedPlayers:
            digest += f'\t\t<player name="{plyr.getUUID()}"/>\n'
        digest += '\t</confirmedPlayers>\n'
        digest += '</match>'
        with open( a_filename, "w+" ) as savefile:
            savefile.write( digest )

    # Loads a match from an xml file saved with this class
    def loadXML( self, a_filename: str ) -> None:
        self.saveLocation = a_filename
        xmlTree = ET.parse( a_filename )
        matchRoot = xmlTree.getroot()
        self.roleID = fromXML(matchRoot.attrib["roleID"])
        self.uuid = fromXML(matchRoot.find( 'uuid' ).text)
        if self.roleID != "":
            self.roleID = int( fromXML( self.roleID ) )
        self.VC_ID = matchRoot.attrib["VC_ID"]
        if self.VC_ID != "":
            self.VC_ID = int( fromXML( self.VC_ID ) )
        self.textChannel_ID = matchRoot.attrib["text_channel_ID"]
        if self.textChannel_ID != "":
            self.textChannel_ID = int( fromXML( self.textChannel_ID ) )
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
        if self.winner != "" and not ( "a draw" in self.winner ) and not self.isBye():
            self.winner = self.winner
        for player in matchRoot.find("activePlayers"):
            self.activePlayers.append( fromXML( player.attrib["name"] ) )
        for player in matchRoot.find("droppedPlayers"):
            self.droppedPlayers.append( fromXML( player.attrib["name"] ) )
        for player in matchRoot.find("confirmedPlayers"):
            self.confirmedPlayers.append( fromXML( player.attrib["name"] ) )


from .player import player

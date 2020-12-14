import os
import xml.etree.ElementTree as ET

from typing import List


from .tournamentUtils import *
from .match import match
from .player import player
from .deck import deck


class tournament:
    def __init__( self, a_tournName: str, a_hostGuildName: str, a_format: str = "EDH" ):
        self.tournName = a_tournName
        self.hostGuildName = a_hostGuildName
        self.format    = a_format
        
        self.regOpen      = True
        self.tournStarted = False
        self.tournEnded   = False
        self.tournCancel  = False
        
        self.playersPerMatch = 2
        self.playerQueue = []

        self.activePlayers  = {}
        self.droppedPlayers = {}
        
        self.uniqueMatches = []
        self.openMatches   = {}
        self.uncertMatches = {}
        self.closedMatches = []
    
    def saveTournament( self, a_dirName: str ) -> None:
        self.saveMatches( a_dirName )
        self.savePlayers( a_dirName )
        self.saveOverview( f'{a_dirName}/overview.xml' )
    
    def saveOverview( self, a_filename ):
        digest  = "<?xml version='1.0'?>\n"
        digest += '<tournament>\n'
        digest += f'\t<name>{self.tournName}</name>\n'
        digest += f'\t<hostGuildName>{self.hostGuildName}</hostGuildName>\n'
        digest += f'\t<format>{self.format}</format>\n'
        digest += f'\t<regOpen>{self.regOpen}</regOpen>\n'
        digest += f'\t<status started="{self.tournStarted}" ended="{self.tournEnded}" canceled="{self.tournCancel}"/>\n'
        digest += f'\t<queue size="{self.playersPerMatch}">\n'
        for player in self.playerQueue:
            digest += f'\t\t<player name="{player}"/>\n'
        digest += f'\t</queue>\n'
        digest += '</tournament>'
        
        with open( a_filename, 'w' ) as xmlFile:
            xmlFile.write( digest )
    
    def savePlayers( self, a_dirName: str ) -> None:
        if not (os.path.isdir( f'{a_dirName}/players/' ) and os.path.exists( f'{a_dirName}/players/' )):
           os.mkdir( f'{a_dirName}/players/' ) 

        for player in self.activePlayers:
            self.activePlayers[player].saveXML( f'{a_dirName}/players/{self.activePlayers[player].playerName}.xml' )
        for player in self.droppedPlayers:
            self.activePlayers[player].saveXML( f'{a_dirName}/players/{self.activePlayers[player].playerName}.xml' )
        

    def saveMatches( self, a_dirName: str ) -> None:
        if not (os.path.isdir( f'{a_dirName}/matches/' ) and os.path.exists( f'{a_dirName}/matches/' )):
           os.mkdir( f'{a_dirName}/matches/' ) 

        for i in range(len(self.openMatches)):
            self.openMatchesmatch.saveXML( f'{a_dirName}/matches/openMatch-{i}.xml' )
        for i in range(len(self.uncertMatches)):
            match.saveXML( f'{a_dirName}/matches/uncertMatch-{i}.xml' )
        for i in range(len(self.closedMatches)):
            match.saveXML( f'{a_dirName}/matches/closedMatch-{i}.xml' )
        
    def loadTournament( self, a_dirName: str ) -> None:
        self.loadOverview( f'{a_dirName}/overview.xml' )
        self.loadPlayers( f'{a_dirName}/players/' )
        self.loadMatches( f'{a_dirName}/matches/' )
    
    def loadOverview( self, a_filename: str ) -> None:
        xmlTree = ET.parse( a_filename )
        tournRoot = xmlTree.getroot() 
        self.tournName = tournRoot.find( 'name' ).text
        self.hostGuildName = tournRoot.find( 'hostGuildName' ).text
        self.format    = tournRoot.find( 'format' ).text

        self.regOpen      = str_to_bool( tournRoot.find( 'regOpen' ).text )
        self.tournStarted = str_to_bool( tournRoot.find( 'status' ).attrib['started'] )
        self.tournEnded   = str_to_bool( tournRoot.find( 'status' ).attrib['ended'] )
        self.tournCancel  = str_to_bool( tournRoot.find( 'status' ).attrib['canceled'] )

        self.playersPerMatch = int( tournRoot.find( 'queue' ).attrib['size'] )
        for player in tournRoot.find( 'queue' ).findall( 'player' ):
            self.playerQueue.append( player.attrib['name'] )
    
    def loadPlayers( self, a_dirName: str ) -> None:
        playerFiles = [ f'{a_dirName}/{f}' for f in os.listdir(a_dirName) if os.path.isfile( f'{a_dirName}/{f}' ) ]
        for playerFile in playerFiles:
            newPlayer = player( "" )
            newPlayer.loadXML( playerFile )
            if newPlayer.status == "active":
                self.activePlayers[newPlayer.playerName]  = newPlayer
            else:
                self.droppedPlayers[newPlayer.playerName] = newPlayer
    
    def loadMatches( self, a_dirName: str ) -> None:
        matchFiles = [ f'{a_dirName}/{f}' for f in os.listdir(a_dirName) if os.path.isfile( f'{a_dirName}/{f}' ) ]
        emptyMatch = match( [] )
        for matchFile in matchFiles:
            newMatch = match( [] )
            newMatch.loadXML( matchFile )
            for aPlayer in newMatch.activePlayers:
                if aPlayer in self.activePlayers:
                    self.activePlayers[aPlayer].matches.append( emptyMatch )
                    self.activePlayers[aPlayer].matches[-1] = newMatch
                elif aPlayer in self.droppedPlayers:
                    self.droppedPlayers[aPlayer].matches.append( emptyMatch )
                    self.droppedPlayers[aPlayer].matches[-1] = newMatch
            for dPlayer in newMatch.droppedPlayers:
                if dPlayer in self.activePlayers:
                    self.activePlayers[dPlayer].matches.append( emptyMatch )
                    self.activePlayers[dPlayer].matches[-1] = newMatch
                elif dPlayer in self.droppedPlayers:
                    self.droppedPlayers[dPlayer].matches.append( emptyMatch )
                    self.droppedPlayers[dPlayer].matches[-1] = newMatch
            self.uniqueMatches.append( emptyMatch )
            self.uniqueMatches[-1] = newMatch
            if status == "open":
                for aPlayer in newMatch.activePlayers:
                    self.openMatches[aPlayer] = newMatch
            elif status == "uncertified":
                for aPlayer in newMatch.activePlayers:
                    self.uncertMatches[aPlayer] = newMatch
            elif status == "closed":
                self.closedMatches.append( emptyMatch )
                self.closedMatches[-1] = newMatch
        

    def setRegStatus( self, a_status: bool ) -> str:
        if not ( self.tournEnded or self.tournCancel ):
            self.regOpen = a_status
            return ""
        elif self.tournEnded:
            return "This tournament has already ended. As such, registeration can't be opened."
        elif self.tournCancel:
            return "This tournament has been cancelled. As such, registeration can't be opened."
    
    def startTourn( self ) -> str:
        if not (self.tournStarted or self.tournEnded or self.tournCancel):
            self.tournStarted = True
            self.regOpen = False
            return ""
        elif self.tournEnded:
            return "This tournament has already ended. As such, it can't be started."
        elif self.tournCancel:
            return "This tournament has been cancelled. As such, it can't be started."
    
    def endTourn( self ) -> str:
        if not self.tournStarted:
            return "The tournament has not started. As such, it can't be ended; however, it can be cancelled. Please use the cancel command if that's what you intended to do."
        else:
            self.tournEnded = False
    
    def cancelTourn( self ) -> str:
        self.tournCancel = True
        return "This tournament has been canceled."
    
    def addPlayer( self, a_discordUser ) -> str:
        if self.tournCancel:
            return "Sorry but this tournament has been cancelled. If you believe this to be incorrect, please contact the tournament officials."
        if self.tournEnded:
            return "Sorry, but this tournament has already ended. If you believe this to be incorrect, please contact the tournament officials."
        if self.regOpen:
            self.activePlayers[a_discordUser.name] = player( a_discordUser )
            return ""
        else:
            return "Sorry, registeration for this tournament isn't open currently."
    
    # There will be a far more sofisticated pairing system in the future. Right now, the dummy version will have to do for testing
    # This is a prime canidate for adjustments when players how copies of match results.
    def addPlayerToQueue( self, a_player: str ) -> None:
        if a_player in self.playerQueue:
            return "You are already in the matchmaking queue."
        if a_player in self.droppedPlayers:
            return "It appears that you have been dropped from the tournament. If you think this is an error, please contact tournament officials."
        if not a_player in self.activePlayers:
            return "It appears that you are not registered for this tournament. If you think this is an error, please contact tournament officials."
        if a_player in self.openMatches:
            return "It appears you are already in a match. Please either finish your match or drop from it before starting a new one. If you think this is an error, please contact tournament officials."
        if a_player in self.uncertMatches:
            return "It would appear that you have an uncertified match. Please certify the result before starting a new match."
        
        self.playerQueue.append(a_player)
        if len(self.playerQueue) >= self.playersPerMatch:
            self.addMatch( self.playerQueue[0:self.playersPerMatch + 1] )
        for i in range(self.playersPerMatch):
            del( self.playerQueue[0] )

    
    def addMatch( self, a_players: List[str] ) -> None:
        emptyMatch = match( [] )
        newMatch   = match( a_players )
        self.uniqueMatches.append( emptyMatch )
        self.uniqueMatches[-1] = newMatch
        for player in a_players:
            self.activePlayers[player].matches.append( emptyMatch )
            self.activePlayers[player].matches[-1] = newMatch
            self.openMatches[player] = newMatch 
    
    def playerMatchDrop( self, a_player: str ) -> None:
        if a_player in self.openMatches:
            self.openMatches[a_player].playerDrop( a_player )
            self.activePlayers[a_player].addMatchResult( "loss" )
            if len( self.openMatches[a_player].activePlayers) == 1:
                l_match = self.openMatches[a_player]
                self.closedMatches.append( l_match )
                del( self.openMatches[l_match.activePlayers[0]] )
            del( self.openMatches[a_player] )
    
    def playerTournDrop( self, a_player: str ) -> None:
        self.playerMatchDrop( a_player )
        if a_player in self.activePlayers:
            self.droppedPlayers[a_player] = self.activePlayers[a_player]
            del( self.activePlayers[a_player] )
    
    def playerVerifyResult( self, a_player: str ) -> None:
        if a_player in self.uncertMatches:
            l_match = self.uncertMatches[a_player]
            del( self.uncertMatches[a_player] )
            matchClosed = True
            for player in l_match.activePlayers:
                matchClosed &= not player in self.uncertMatches
            if matchClosed:
                self.closedMatches.append( l_match )
                
    
    def recordMatchWin( self, a_winner: str ) -> None:
        l_match = self.openMatches[a_winner]
        l_match.recordWinner( a_winner )
        for player in l_match.activePlayers:
            if player == a_winner:
                self.activePlayers[player].addMatchResult( "win" )
            else:
                self.activePlayers[player].addMatchResult( "loss" )
                self.uncertMatches[player] = l_match
            del( self.openMatches[player] )
    
    def recordMatchDraw( self, a_player: str ) -> None:
        l_match = self.openMatches[ a_player ]
        l_match.recordWinner( "" )
        for player in l_match.activePlayers:
            self.activePlayers[player].addMatchResult( "draw" )
            if player != a_player:
                self.uncertMatches[player] = l_match
            del( self.openMatches[player] )




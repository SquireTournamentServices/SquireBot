


from tournamentUtils import *
from match import match
from player import player
from deck import deck


class tournament:
    def __init__( self, a_tournName: str, a_hostGuild: str, a_format: str = "EDH" ):
        self.tournName = a_tournName
        self.hostGuild = a_hostGuild
        self.format    = a_format
        
        self.regOpen = True
        self.tournStarted = False
        self.tournEnded   = False
        self.tournCancel  = False
        
        self.playersPerMatch = 2
        self.playerQueue = []

        self.activePlayers  = {}
        self.droppedPlayers = {}
        
        self.openMatches   = {}
        self.uncertMatches = {}
        self.closedMatches = []
    

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
    
    def addPlayer( self, a_playerName: str = "", a_displayName: str = "" ) -> str:
        if self.tournCancel:
            return "Sorry but this tournament has been cancelled. If you believe this to be incorrect, please contact the tournament officials."
        if self.tournEnded:
            return "Sorry, but this tournament has already ended. If you believe this to be incorrect, please contact the tournament officials."
        if self.regOpen:
            self.activePlayers[a_playerName] = player( a_playerName, a_displayName )
            return ""
        else:
            return "Sorry, registeration for this tournament isn't open currently."
    
    def getPlayer( self, a_playerName: str ) -> player:
        if a_playerName in self.activePlayers:
            return self.activePlayers[a_playerName]
        else:
            return player()
    
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
            self.addMatch( self.playerQueue[0:self.playersPerMatch + 1]
        for i in range(self.playersPerMatch):
            del( self.playerQueue[0] )

    
    def addMatch( self, a_players: list[str] ) -> None:
        for player in a_players:
            self.openMatches[player] = match( a_players )
        
    
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




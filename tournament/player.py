

from .tournamentUtils import *
from .deck import deck



class player:
    def __init__( self, a_playerName: str = "", a_displayName: str = "" ):
        self.playerName   = a_playerName
        if a_displayName == "":
            self.displayName  = a_playerName
        else:
            self.displayName  = a_displayName
        self.decks        = { }
        self.matchResults = [ ]
    
    def addDeck( self, a_commander: str = "", a_decklist: str = "" ) -> None:
        self.decks[a_commander] = deck( a_decklist )
        
    def addMatchResult( self, a_result: str ) -> None:
        self.matchResults.append( a_result )
    
    def getMatchPoints( self ) -> int:
        return len( [ 1 for result in self.matchResults if result == "win" ] )



from typing import List



class match:
    def __init__( self, a_players: List[str] ):
        self.activePlayers  = a_players
        self.droppedPlayers = [ ]
        self.confirmedPlayers = [ ]
        self.status = "open"
        self.winner = ""
    
    def dropPlayer( self, a_player: str ) -> None:
        if not a_player in self.activePlayers:
            return
        self.droppedPlayers.append( a_player )
        for i in range(len(self.activePlayers)):
            if a_player == self.activePlayers[i]:
                del( self.activePlayers[i] )
    
    def confirmResult( self, a_player: str ) -> None:
        if not self.status == "uncertified":
            return
        if not a_player in self.confirmedPlayers:
            self.confirmedPlayers.append( a_player )
        if len(self.confirmedPlayers) == len(self.activePlayers):
            self.status == "certified"
    
    def recordWinner( self, a_winner: str ) -> None:
        if a_winner == "":
            self.winner = "This match was a draw."
        else:
            self.winner = a_winner
            self.confirmedPlayers = [ winner ]
        self.status = "uncertified"







class match:
    def __init__( self, a_players: list[str] ):
        self.activePlayers  = a_players
        self.droppedPlayers = []
        
        self.winner = ""
    
    def playerDrop( self, a_player: str ):
        self.droppedPlayers.append( a_player )
        for i in range(len(self.activePlayers)):
            if a_player == self.activePlayers[i]:
                del( self.activePlayers[i] )
    
    # True = Open, False = Closed
    def getStatus( self ) -> bool:
        return self.winner == ""
    
    def recordWinner( self, a_winner: str ):
        if a_winner == "":
            self.winner = "This match was a draw."
        else:
            self.winner = a_winner



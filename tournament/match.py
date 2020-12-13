import xml.etree.ElementTree as ET


from typing import List



class match:
    def __init__( self, a_players: List[str] ):
        self.activePlayers  = a_players
        self.droppedPlayers = [ ]
        self.confirmedPlayers = [ ]
        self.status = "open"
        self.winner = ""
    
    def saveXML( self, a_filename: str ) -> None:
        digest  = "<?xml version='1.0'?>\n"
        digest += '<match>\n'
        digest += f'\t<status>{self.status}</status>\n'
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
        with open( a_filename, "w" ) as savefile:
            savefile.write( digest )
    
    def loadXML( self, a_filename: str ) -> None:
        xmlTree = ET.parse( a_filename )
        matchRoot = xmlTree.getroot()
        self.status = matchRoot.find( "status" ).text
        self.winner = matchRoot.find( "winner" ).attrib["name"]
        for player in matchRoot.find("activePlayers"):
            print( player.attrib )
            self.activePlayers.append( player.attrib["name"] )
        for player in matchRoot.find("droppedPlayers"):
            self.droppedPlayers.append( player.attrib["name"] )
        for player in matchRoot.find("confirmedPlayers"):
            self.confirmedPlayers.append( player.attrib["name"] )
    
    def dropPlayer( self, a_player: str ) -> None:
        if not a_player in self.activePlayers:
            return
        self.droppedPlayers.append( a_player )
        for i in range(len(self.activePlayers)):
            if a_player == self.activePlayers[i]:
                del( self.activePlayers[i] )
                return
    
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



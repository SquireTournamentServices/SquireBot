import xml.etree.ElementTree as ET


from typing import List


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
    def __init__( self, a_players: List[str], a_num: int = 0 ):
        self.activePlayers  = a_players
        self.droppedPlayers = [ ]
        self.confirmedPlayers = [ ]
        self.matchMention = ""
        self.matchNumber  = a_num
        self.status = "open"
        self.winner = ""
    
    def __str__( self ):
        return f'Match number {self.matchNum} is {self.status}{". The winner is " + self.winner if self.status == "certified" else ""}. '
    
    # Saves the match to an xml file at the given location.
    def saveXML( self, a_filename: str ) -> None:
        digest  = "<?xml version='1.0'?>\n"
        digest += '<match number="{self.matchNumber}">\n'
        digest += f'\t<status>{self.status}</status>\n'
        digest += f'\t<mention>"{self.matchMention}</mention>\n'
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
    
    # Loads a match from an xml file saved with this class
    def loadXML( self, a_filename: str ) -> None:
        xmlTree = ET.parse( a_filename )
        matchRoot = xmlTree.getroot()
        self.matchNumber = int( matchRoot.attrib["number"] )
        self.status = matchRoot.find( "status" ).text
        self.matchMention = matchRoot.find( 'mention' ).text
        self.winner = matchRoot.find( "winner" ).attrib["name"]
        for player in matchRoot.find("activePlayers"):
            print( player.attrib )
            self.activePlayers.append( player.attrib["name"] )
        for player in matchRoot.find("droppedPlayers"):
            self.droppedPlayers.append( player.attrib["name"] )
        for player in matchRoot.find("confirmedPlayers"):
            self.confirmedPlayers.append( player.attrib["name"] )
    
    def addMatchMention( self, a_mention: str ) -> None:
        self.matchMention = a_mention
    
    # Drops a player, which entains removing them from the active players
    # list and adding them to the dropped players list.
    def dropPlayer( self, a_player: str ) -> None:
        for i in range(len(self.activePlayers)):
            if a_player == self.activePlayers[i]:
                del( self.activePlayers[i] )
                self.droppedPlayers.append( a_player )
                return
    
    # Confirms the result for one player.
    # If all players have confirmed the result, the status of the match is status to "certified"
    def confirmResult( self, a_player: str ) -> None:
        if not self.status == "uncertified":
            return
        if not a_player in self.confirmedPlayers:
            self.confirmedPlayers.append( a_player )
        if len(self.confirmedPlayers) == len(self.activePlayers):
            self.status == "certified"
    
    # Records the winner of a match and adds them to the confirmed players list.
    # An empty string is interpretted as a draw, in which case, no one is added to the confirmed players list.
    # In either case, the status of the match is changed to "uncertified"
    def recordWinner( self, a_winner: str ) -> None:
        if a_winner == "":
            self.winner = "This match was a draw."
        else:
            self.winner = a_winner
            self.confirmedPlayers = [ winner ]
        self.status = "uncertified"



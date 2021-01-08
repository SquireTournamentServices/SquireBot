import xml.etree.ElementTree as ET

from .tournamentUtils import *
from .deck import deck
from .match import match


"""
    This class manages players.
    The class currently has the following functionalities:
        - Decks can be added to the list of decks
        - The player's number of wins can be calculated
        - A discord user can be added, though a player doesn't have one by default
        - The player's status is tracked and can be updated (i.e if they are active or have dropped)
        - An xml file can be created which stores the overview of the player and their decks but not their matches.
        - The player can load an xml file after construction
    There is one functionality that the player can have but can't be codified in this class.
    Ideally, each player stores references to match object instead of copies.
    In order to do this, an empty match has to be added and then overwritten by the desired match object.
    Doing this allows each player to have an up-to-date list of match objects at all times, but requires this to be kept up-to-date
    externally instead of in the class.
    In the future, functionalities might be added to update matches, but that remains to be seen.
    
    The class has the following member variables:
        - playerName: The name of the player
        - status: A string that states if the player is active or has dropped
        - decks: A dict that index-s deck objects with their identifier (deck.ident)
        - matches: A list of matches that the player is associated with
        - discordUser: A copy of the player's associated discord user object
"""

class player:
    # The class constructor
    def __init__( self, a_playerName: str = "" ):
        self.discordUser = ""
        self.discordName = ""
        self.playerName  = a_playerName
        self.triceName   = ""
        self.status  = "active"
        self.decks   = { }
        self.matches = [ ]
    
    def __str__( self ):
        newLine = "\n\t- "
        digest  = f'Player Name: {self.playerName}\n'
        digest += f'Disord Nickname: {self.discordUser.display_name}\n'
        digest += f'Cockatrice Username: {self.triceName}\n'
        digest += f'Status: {self.status}\n'
        digest += f'Decks:{newLine}{newLine.join( [ self.decks[deck] for deck in self.decks ] )}\n'
        digest += f'Matches:{newLine}{newLine.join( self.matches )}'
        return digest
    
    def pairingString( self ):
        digest  = f'Player Name: {self.discordUser.mention}\n'
        if self.triceName != "":
            digest += f'Cockatrice Username: {self.triceName}\n'
        counter = 0
        for deck in self.decks:
            counter += 1
            digest += f'Deck {counter}: {self.decks[deck].deckHash}'
        return digest
    
    # Adds a copy of a discord user object
    def addDiscordUser( self, a_discordUser ) -> None:
        self.discordUser = a_discordUser
    
    # Updates the status of the player
    def updateStatus( self, a_status: str ) -> None:
        self.status = a_status
    
    # Saves the overview of the player and their deck(s)
    # Matches aren't saved with the player. They are save seperately.
    # The tournament object loads match objects and then associates each player with their match(es)
    def saveXML( self, a_filename: str = "" ) -> None:
        if a_filename == "":
            a_filename = self.discordUser.display_name + '.xml'
        digest  = "<?xml version='1.0'?>\n"
        digest += '<player>\n'
        digest += f'\t<name>{self.playerName}</name>\n'
        if self.discordUser != "":
            digest += f'\t<discordName>{self.discordUser.display_name}</discordName>\n'
        digest += f'\t<status>{self.status}</status>\n'
        for ident in self.decks:
            digest += self.decks[ident].exportXMLString( '\t' )
        digest += '</player>'
        with open( a_filename, 'w' ) as xmlFile:
            xmlFile.write( digest )
    
    # Loads an xml file saved with the class after construction
    def loadXML( self, a_filename: str ) -> None:
        xmlTree = ET.parse( a_filename )
        self.playerName = xmlTree.getroot().find( 'name' ).text
        self.discordName = xmlTree.getroot().find( 'discordName' ).text
        self.status = xmlTree.getroot().find( "status" ).text
        for deckTag in xmlTree.getroot().findall('deck'):
            print( deckTag.attrib )
            print( deckTag.attrib['ident'] )
            self.decks[deckTag.attrib['ident']] = deck()
            self.decks[deckTag.attrib['ident']].importFromETree( deckTag )
    
    # Addes a deck to the list of decks
    def addDeck( self, a_ident: str = "", a_decklist: str = "" ) -> None:
        self.decks[a_ident] = deck( a_ident, a_decklist )
    
    # Tallies the number of matches that the player is in, has won, and have been certified.
    def getMatchPoints( self ) -> int:
        return len( [ 1 for match in self.matches if match.status == 'certified' and match.winner == self.playerName ] )



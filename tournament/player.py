import xml.etree.ElementTree as ET

from .tournamentUtils import *
from .deck import deck
from .match import match



class player:
    def __init__( self, a_discordUser ):
        self.discordUser = a_discordUser
        self.playerName  = a_discordUser.name if a_discordUser != "" else ""
        self.status  = "active"
        self.decks   = { }
        self.matches = [ ]
    
    def saveXML( self, a_filename: str = "" ) -> None:
        if a_filename == "":
            a_filename = self.discordUser.name + '.xml'
        digest  = "<?xml version='1.0'?>\n"
        digest += '<player>\n'
        digest += f'\t<name>"{self.discordUser.name}"</name>\n'
        digest += f'\t<status>"{self.status}"</status>\n'
        for commander in self.decks:
            digest += self.decks[commander].exportXMLString( '\t' )
        digest += '</player>'
        with open( a_filename, 'w' ) as xmlFile:
            xmlFile.write( digest )
    
    def loadXML( self, a_filename: str ) -> None:
        xmlTree = ET.parse( a_filename )
        self.playerName = xmlTree.getroot().find( 'name' ).text
        self.status = xmlTree.getroot.find( "status" ).text
        for deckTag in xmlTree.getroot().findall('deck'):
            print( deckTag.attrib )
            print( deckTag.attrib['commander'] )
            self.decks[deckTag.attrib['commander']] = deck()
            self.decks[deckTag.attrib['commander']].importFromETree( deckTag )
    
    def addDeck( self, a_commander: str = "", a_decklist: str = "" ) -> None:
        self.decks[a_commander] = deck( a_commander, a_decklist )
    
    def getMatchPoints( self ) -> int:
        return len( [ 1 for match in self.matches if match.status == 'certified' and match.winner == discordUser.name ] )



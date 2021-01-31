import xml.etree.ElementTree as ET

from typing import List

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
        - name: The name of the player
        - status: A string that states if the player is active or has dropped
        - decks: A dict that index-s deck objects with their identifier (deck.ident)
        - matches: A list of matches that the player is associated with
        - discordUser: A copy of the player's associated discord user object
"""

class player:
    # The class constructor
    def __init__( self, a_name: str = "" ):
        self.discordUser = ""
        self.discordID   = ""
        self.name  = a_name
        self.triceName   = ""
        self.status  = "active"
        self.decks   = { }
        self.matches = [ ]
        self.opponents = [ ]
    
    def __str__( self ):
        newLine = "\n\t- "
        digest  = f'Player Name: {self.name}\n'
        digest += f'Disord Nickname: {self.discordUser.display_name}\n'
        digest += f'Cockatrice Username: {self.triceName}\n'
        digest += f'Status: {self.status}\n'
        digest += f'Decks:{newLine}{newLine.join( [ str(self.decks[ident]) for ident in self.decks ] )}\n'
        digest += f'Matches:{newLine}{newLine.join( [ str(mtch) for mtch in self.matches ] )}'
        return digest
    
    def __eq__( self, other: 'player' ):
        if type(other) != player:
            return False
        digest  = ( self.name == other.name )
        digest &= ( self.discordID == other.discordID )
        return digest
    
    def isValidOpponent( self, a_plyr: 'player' ) -> bool:
        if self.name in a_plyr.opponents:
            return False
        if a_plyr.name in self.opponents:
            return False
        return True
    
    def areValidOpponents( self, a_plyrs: List['player'] ) -> bool:
        for plyr in a_plyrs:
            if not self.isValidOpponent( plyr ):
                return False
        return True
    
    def pairingString( self ):
        digest  = f'Player Name: {self.discordUser.mention}\n'
        if self.triceName != "":
            digest += f'Cockatrice Username: {self.triceName}\n'
        counter = 0
        for deck in self.decks:
            counter += 1
            digest += f'Deck {counter}: {self.decks[deck].deckHash}\n'
        return digest
    
    # Adds a copy of a discord user object
    def addDiscordUser( self, a_discordUser ) -> None:
        self.discordUser = a_discordUser
    
    # Updates the status of the player
    def updateStatus( self, a_status: str ) -> None:
        self.status = a_status
    
    def hasOpenMatch( self ) -> bool:
        digest = False
        for match in self.matches:
            digest |= not match.isCertified( )
        return digest
    
    def getMatch( self, a_matchNum: int ) -> match:
        for mtch in self.matches:
            if mtch.matchNumber == a_matchNum:
                return mtch
        return match( [] )
    
    # Find the index of the not certified match closest to the end of the match array
    # Returns 1 if no open matches exist; otherwise, returns a negative index
    def findOpenMatchIndex( self ) -> int:
        if not self.hasOpenMatch( ):
            # print( f'No open matches found. Returning one.' )
            return 1
        digest = -1
        while self.matches[digest].status == "certified":
            digest -= 1
        # print( f'An open match was found. Returning {digest}.' )
        return digest

    def findOpenMatch( self ) -> match:
        index = self.findOpenMatchIndex( )
        if index == 1:
            # print( f'The reported index was one. Returning an empty match.' )
            return match( [] )
        # print( f'The reported index was not one. Returning an the correct match.' )
        return self.matches[index]
    
    def findOpenMatchNumber( self ) -> int:
        index = self.findOpenMatchIndex( )
        if index == 1:
            return -1
        return self.matches[index].matchNumber
    
    async def drop( self ) -> None:
        self.status = "dropped"
        for match in self.matches:
            if match.status != "certified":
                await match.dropPlayer( self.name )
    
    async def certifyResult( self ) -> str:
        index = self.findOpenMatchIndex( )
        if index == 1:
            return ""
        return await self.matches[index].confirmResult( self.name )
    
    async def recordWin( self ) -> str:
        index = self.findOpenMatchIndex( )
        if index == 1:
            return ""
        return await self.matches[index].recordWinner( self.name )
    
    async def recordDraw( self ) -> str:
        index = self.findOpenMatchIndex( )
        if index == 1:
            return ""
        await self.matches[index].recordWinner( "" )
        return await self.matches[index].confirmResult( self.name )
            
    # Addes a deck to the list of decks
    def addDeck( self, a_ident: str = "", a_decklist: str = "" ) -> None:
        self.decks[a_ident] = deck( a_ident, a_decklist )
    
    def getDeckIdent( self, a_ident: str = "" ) -> str:
        if a_ident in self.decks:
            return a_ident
        digest = ""
        for ident in self.decks:
            if a_ident == self.decks[ident].deckHash:
                digest = ident
                break
        return digest
    
    # Tallies the number of matches that the player is in, has won, and have been certified.
    def getMatchPoints( self ) -> int:
        digest = 0
        certMatches = [ mtch for mtch in self.matches if mtch.isCertified( ) ]
        for mtch in certMatches:
            if mtch.winner == self.name:
                digest += 3
            elif "a draw" in mtch.winner.lower():
                digest += 1
        return digest
    
    # Calculates the percentage of game the player has won
    def getMatchWinPercentage( self ) -> float:
        certMatches = [ mtch for mtch in self.matches if mtch.isCertified( ) ]
        if len( certMatches ) == 0:
            return 0.0
        return len( [ 1 for mtch in certMatches if mtch.winner == self.name ] )/len( certMatches )
    
    def getNumberOfWins( self ) -> int:
        return sum( [ 1 if mtch.winner == self.name else 0 for mtch in self.matches if mtch.isCertified( ) ] )
    
    # Saves the overview of the player and their deck(s)
    # Matches aren't saved with the player. They are save seperately.
    # The tournament object loads match objects and then associates each player with their match(es)
    def saveXML( self, a_filename: str = "" ) -> None:
        if a_filename == "":
            a_filename = self.discordUser.name + '.xml'
        digest  = "<?xml version='1.0'?>\n"
        digest += '<player>\n'
        digest += f'\t<name>{self.name}</name>\n'
        digest += f'\t<discord id="{self.discordUser.id if type(self.discordUser) == discord.Member else str()}"/>\n'
        digest += f'\t<status>{self.status}</status>\n'
        for ident in self.decks:
            digest += self.decks[ident].exportXMLString( '\t' )
        digest += '</player>'
        with open( a_filename, 'w' ) as xmlFile:
            xmlFile.write( digest )
    
    # Loads an xml file saved with the class after construction
    def loadXML( self, a_filename: str ) -> None:
        xmlTree = ET.parse( a_filename )
        self.name = xmlTree.getroot().find( 'name' ).text
        self.discordID  = xmlTree.getroot().find( 'discord' ).attrib['id']
        if self.discordID != "":
            self.discordID = int( self.discordID )
        self.status = xmlTree.getroot().find( "status" ).text
        for deckTag in xmlTree.getroot().findall('deck'):
            # print( deckTag.attrib )
            # print( deckTag.attrib['ident'] )
            self.decks[deckTag.attrib['ident']] = deck()
            self.decks[deckTag.attrib['ident']].importFromETree( deckTag )
    


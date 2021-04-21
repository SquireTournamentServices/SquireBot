import hashlib
import string
import xml.etree.ElementTree as ET


from typing import List


from .utils import *


"""
    This class manages a deck.
    It currently has the following functionalities.
        - Parses both annotated and nonannotated Cocktrice decklists (not .cod files, though)
        - Stores and updates a decklist and deckhash
        - Creates a string that can be added to an xml file, but can not create its own xml file
        - Imports a deck from an ElementTree created from its xml string output
    There are no current plans to add additional functionalities.
    
    The class has the following member variables:
        - deckHash: an int that holds the deck's Cocktrice deckhash
        - ident: an identifier given on creation (usually the commander)
        - decklist: the string given on construction
        - cards: a list of strings for card names with the prefix "SB:" if a card is in the sideboard
"""

class deck:
    # Class constructor
    def __init__( self, a_ident: str = "", a_decklist: str = "" ):
        self.deckHash  = 0
        self.ident = a_ident
        self.decklist = a_decklist
        if self.decklist == "":
            self.cards = [ ]
        else:
            self.cards = self.parseAnnotatedTriceDecklist( ) if "\n//" in self.decklist else self.parseNonAnnotatedTriceDecklist( )
        self.updateDeckHash()
    
    def __str__( self ):
        return f'{self.ident}: {self.deckHash}'
    
    # Functions for exporting a decklist to a xml without creating an xml file.
    # Since decks are contained in the player object, exporting an xml string is more helpful
    def exportXMLString( self, a_indent: str = "" ) -> str:
        lineStart = f'\n{toSafeXML(a_indent)}\t'
        digest = f'{a_indent}<deck ident="{toSafeXML(self.ident)}">' 
        for card in self.cards:
            digest += f'{lineStart}<card name="{toSafeXML(card)}"/>'
        digest += f'\n{toSafeXML(a_indent)}</deck>\n'
        return digest
    
    def importFromETree( self, a_tree: ET ) -> None:
        self.ident = fromXML( a_tree.attrib["ident"] )
        for card in a_tree.iter( "card" ):
            self.cards.append( fromXML( card.attrib['name'] ) )
        self.updateDeckHash()
    
    # Converts a semicolon-delineated deck string into a hash.
    # This deck-hasher is built to spoof how Cockatrice creates a deckhash.
    # A large portion of the logic in the first for loop is there to track what
    # cards are sideboard card since Cockatrice handles the naming of those differently.
    # When creating the modified list of cards, there are three cases:
    #   - The card is a sideboard card, in which case that card will look like "SB:" + card_name.lower() for each copy needed
    #       - Ex: "SB: 2 Izzet Charm" -> [ "SB:izzet charm", "SB:izzet charm" ]
    #   - The card doesn't have a number associated with it, in which case we process a single copy
    #       - Ex: "Izzet Charm" -> [ "izzet charm" ]
    #   - The card has a number associated with it, so we store that many copies
    #       - Ex: "1 Izzet Charm" -> [ "izzet charm" ]
    def updateDeckHash( self ) -> None:
        l_cards = []
        for card in self.cards:
            if not "SB:" in card:
                try:
                    int( card[0] )
                    card = card.split(" ", 1)
                except:
                    card = [ card ]
                if len( card ) == 1:
                    number = 1
                    name   = card[0].strip().lower()
                else:
                    number = int( card[0].strip() )
                    name   = card[1].strip().lower()
                for i in range(number):
                    l_cards.append( name )
            else:
                card = card.split(" ", 2)
                number = int( card[1].strip() )
                name   = card[0] + card[2].strip().lower()
                for i in range(number):
                    l_cards.append( name )

        l_cards.sort()
        newHash = hashlib.sha1()
        newHash.update( ";".join(l_cards).encode("utf-8"))
        hashed_deck = newHash.digest()
        hashed_deck = (
            (hashed_deck[0] << 32)
            + (hashed_deck[1] << 24)
            + (hashed_deck[2] << 16)
            + (hashed_deck[3] << 8)
            + (hashed_deck[4])
        )
        processed_hash = number_to_base(hashed_deck, 32)
        self.deckHash = "".join([conv_dict[i] for i in processed_hash])
        while len(self.deckHash) < 8:
            self.deckHash = "0" + self.deckHash

    # Parses a nonannotated decklist from Cockatrice into a list of cards. 
    # A nonannotated, Cockatrice decklist has a double space between the main and side boards.
    # In order to compute the correct hash, all sideboard cards need the "SB: " prefix, which this adds.
    def parseNonAnnotatedTriceDecklist( self ) -> List[str]:
        digest = []
        prefix = ""
        for line in self.decklist.strip().split("\n"):
            line = line.strip()
            if line == "":
                prefix = "SB: "
            else:
                digest.append(prefix + line)
        return digest

    # Parses an annotated decklist from Cockatrice into a list of cards. 
    # Unlike the nonannotated decklist, all sideboard cards have to correct prefix.
    # As such, we can grab all the line that aren't whitespace nor start with "//"
    def parseAnnotatedTriceDecklist( self ) -> List[str]:
        return [ line for line in self.decklist.strip().split("\n") if line.strip() != "" and line[0:2] != "//" ]
        
    


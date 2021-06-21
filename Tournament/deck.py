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
        - cards: a list of strings for card names with the prefix "SB:"
                 if a card is in the sideboard
"""

import hashlib
import xml.etree.ElementTree as ET
import json
import re
import requests
import traceback
from typing import List

from .utils import *

# Constant compiled regexes
moxFieldLinkRegex = re.compile('\s*(https?:\/\/)?(www\.)?moxfield\.com\/decks\/([a-zA-Z0-9-]{22})\s*', re.M | re.I)
tappedoutLinkRegex = re.compile('\s*(https?:\/\/)?tappedout\.net\/mtg-decks\/([a-z0-9-]*)\/?\s*', re.M | re.I)
mtgGoldFishLinkRegex = re.compile('\s*(https?:\/\/)?(www\.)?mtggoldfish\.com\/deck\/([0-9]{7})(#[a-zA-Z]*)?\s*', re.M | re.I)
cockatriceDeckRegex = re.compile('\s*<\?xml version="1\.0" encoding="UTF-8"\?>\s*<cockatrice_deck version="1">\s*<deckname>[^<]*<\/deckname>\s*<comments>[^<]*<\/comments>\s*(\s*<zone name="[^<"]+"\s*>\s*([\s]*<card number="[0-9]+" *name="[^<"]+"\s*\/>\s*)*<\/zone>\s*)+\s*<\/cockatrice_deck>\s*', re.M | re.I)

deckRegex = re.compile("(\s*[0-9]+ [a-zA-Z 0-9,.'-]*\r?\n?)+", re.M)

def isValidCodFile(deckData: str) -> bool:
    return None != re.fullmatch(cockatriceDeckRegex, deckData)
    
def isMoxFieldLink(decklist: str) -> bool:
    return None != re.fullmatch(moxFieldLinkRegex, decklist)

def isMtgGoldfishLink(decklist: str) -> bool:
    return None != re.fullmatch(mtgGoldFishLinkRegex, decklist)
    
def isTappedOutLink(decklist: str) -> bool:
    return None != re.fullmatch(tappedoutLinkRegex, decklist)

class deck:       
    """
    The class is this module
    """
    # Class constructor
    def __init__ ( self, ident: str = "", decklist: str = "" ):
        self.deckHash  = 0
        self.ident = ident
        self.cards = [ ]
        self.decklist = ""
        
        # Check input type
        if isValidCodFile(decklist):
            self._loadFromCodFile(decklist)
        
        # Deck scraping
        elif isMoxFieldLink(decklist):
            self._loadMoxFieldDeck(decklist)
        elif isMtgGoldfishLink(decklist):
            self._loadMtgGoldfishDeck(decklist)
        elif isTappedOutLink(decklist):
            self._loadTappedOutDeck(decklist)
        else:
            self.decklist = decklist
            if self.decklist == "":
                self.cards = [ ]
            else:
                self.cards = self.parseAnnotatedTriceDecklist( ) if "\n//" in self.decklist else \
                            self.parseNonAnnotatedTriceDecklist( )
        self.updateDeckHash()

    def __str__( self ):
        return f'{self.ident}: {self.deckHash}'

    def _loadMtgGoldfishDeck(self, deckURL: str):
        if isMtgGoldfishLink(deckURL):
            regex_match = re.fullmatch(mtgGoldFishLinkRegex, deckURL)
            https, www, deck_id, anchor = regex_match.groups()
            
            url = f"https://www.mtggoldfish.com/deck/download/{deck_id}"
            
            self.decklist = requests.get(url, timeout=7.0, data="", verify=True).text
            self.cards = self.parseAnnotatedTriceDecklist( ) if "\n//" in self.decklist else \
                            self.parseNonAnnotatedTriceDecklist( )                        

    def _loadTappedOutDeck(self, deckURL: str):
        if isTappedOutLink(deckURL):
            regex_match = re.fullmatch(tappedoutLinkRegex, deckURL)
            https, deck_id = regex_match.groups()
            
            url = f"https://tappedout.net/mtg-decks/{deck_id}/?fmt=txt"
            
            self.decklist = requests.get(url, timeout=7.0, data="", verify=True).text
            self.cards = self.parseAnnotatedTriceDecklist( ) if "\n//" in self.decklist else \
                            self.parseNonAnnotatedTriceDecklist( )

    def _loadMoxFieldDeck(self, deckURL: str):
        if isMoxFieldLink(deckURL):
            self.decklist = ""
            regex_match = re.fullmatch(moxFieldLinkRegex, deckURL)
            https, www, deck_id = regex_match.groups()
            
            url = f"https://api.moxfield.com/v2/decks/all/{deck_id}"
            
            resp = requests.get(url, timeout=7.0, data="", verify=True).text
            deck_data = json.loads(resp)
            
            main = deck_data["main"]
            self.decklist += f'1 {str(main["name"])}\n'
                
            main_board = deck_data["mainboard"]
            for card_name in main_board:
                # Add card to decklist
                card = main_board[card_name]
                self.decklist += f'{str(card["quantity"])} {str(card_name)}\n'
                
            side_board = deck_data["sideboard"]            
            for card_name in side_board:
                # Add card to decklist
                card = side_board[card_name]
                self.decklist += f'SB: {str(card["quantity"])} {str(card_name)}\n'
                            
            self.cards = self.parseAnnotatedTriceDecklist()

    def _loadFromCodFile(self, fileData: str):
        # Check if the file is valid
        if isValidCodFile(fileData):
            # Init deck object
            self.decklist = ""
            
            # Extract deck and return object
            dck = ET.fromstring(fileData)
            
            # self.ident = fromXML(dck.find("deckname").text)
            zones = dck.findall("zone")
            for zone in zones:
                zonecards = zone.findall("card")
                for card in zonecards:
                    number = int(card.attrib['number'])
                    cardname = fromXML(card.attrib['name'])
                    cardnameLower = cardname.lower()
                    
                    # Add card to decklist
                    if zone.attrib['name'] == "side":
                        self.decklist += "SB: "
                    self.decklist += f'{number} {cardname}\n'
            
            # Update hash
            self.cards = self.parseNonAnnotatedTriceDecklist()
        else:
            # Error case
            return None

    def exportXMLString( self, indent: str = "" ) -> str:
        """
        Function for exporting a decklist to a xml without creating an xml file.
        Since decks are contained in the player object, exporting an xml string is more helpful
        """
        lineStart = f'\n{indent}\t'
        digest = f'{indent}<deck ident="{self.ident}">'
        for card in self.cards:
            digest += f'{lineStart}<card name="{card}"/>'
        digest += f'\n{indent}</deck>\n'
        return digest

    def importFromETree( self, tree: ET ) -> None:
        """ Function for importing a decklist from an element tree """
        self.ident = fromXML( tree.attrib["ident"] )
        for card in tree.iter( "card" ):
            self.cards.append( fromXML( card.attrib['name'] ) )
        self.updateDeckHash()

    def updateDeckHash( self ) -> None:
        """
        Converts a semicolon-delineated deck string into a hash.
        This deck-hasher is built to spoof how Cockatrice creates a deckhash.
        A large portion of the logic in the first for loop is there to track what
        cards are sideboard card since Cockatrice handles the naming of those differently.
        When creating the modified list of cards, there are three cases:
        - The card is a sideboard card, in which case that card will look like "SB:" + card.lower()
            - Ex: "SB: 2 Izzet Charm" -> [ "SB:izzet charm", "SB:izzet charm" ]
        - The card doesn't have a number associated with it, in which case we process a single copy
            - Ex: "Izzet Charm" -> [ "izzet charm" ]
        - The card has a number associated with it, so we store that many copies
            - Ex: "1 Izzet Charm" -> [ "izzet charm" ]
        """
        if "" != self.decklist and re.fullmatch(deckRegex, self.decklist) is None:
            raise SyntaxError(f"Error deck list is not in the correct form {self.decklist}.")
        
        cards = []
        for card in self.cards:
            if not "SB:" in card:
                try:
                    int( card[0] )
                    card = card.split(" ", 1)
                except IndexError:
                    card = [ card ]
                if len( card ) == 1:
                    number = 1
                    name   = card[0].strip().lower()
                else:
                    number = int( card[0].strip() )
                    name   = card[1].strip().lower()
                for i in range(number):
                    cards.append( name )
            else:
                card = card.split(" ", 2)
                number = int( card[1].strip() )
                name   = card[0] + card[2].strip().lower()
                for i in range(number):
                    cards.append( name )

        cards.sort()
        newHash = hashlib.sha1()
        newHash.update( ";".join(cards).encode("utf-8"))
        hashedDeck = newHash.digest()
        hashedDeck = (
            (hashedDeck[0] << 32)
            + (hashedDeck[1] << 24)
            + (hashedDeck[2] << 16)
            + (hashedDeck[3] << 8)
            + (hashedDeck[4])
        )
        processedHash = numberToBase(hashedDeck, 32)
        self.deckHash = "".join([convDict[i] for i in processedHash])
        while len(self.deckHash) < 8:
            self.deckHash = "0" + self.deckHash

    def parseNonAnnotatedTriceDecklist( self ) -> List[str]:
        """
        Parses a nonannotated decklist from Cockatrice into a list of cards.  A
        nonannotated, Cockatrice decklist has a double space between the main and
        side boards.  In order to compute the correct hash, all sideboard cards
        need the "SB: " prefix, which this adds.
        """
        digest = []
        prefix = ""
        for line in self.decklist.strip().split("\n"):
            line = line.strip()
            if line == "":
                prefix = "SB: "
            else:
                digest.append(prefix + line)
        return digest

    def parseAnnotatedTriceDecklist( self ) -> List[str]:
        """
        Parses an annotated decklist from Cockatrice into a list of cards.
        Unlike the nonannotated decklist, all sideboard cards have to correct prefix.
        As such, we can grab all the line that aren't whitespace nor start with "//"
        """
        return [ line for line in self.decklist.strip().split("\n") \
                       if line.strip() != "" and line[0:2] != "//" ]




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
from .exceptions import *
from .cardDB import *

# Constant compiled regexes
cardsDB = initCardDB()
moxFieldLinkRegex = re.compile('\s*(https?:\/\/)?(www\.)?moxfield\.com\/decks\/([a-z_A-Z0-9-]+)\s*', re.M | re.I)
tappedoutLinkRegex = re.compile('\s*(https?:\/\/)?tappedout\.net\/mtg-decks\/([a-z0-9-]*)\/?\s*', re.M | re.I)
mtgGoldFishLinkRegex = re.compile('\s*(https?:\/\/)?(www\.)?mtggoldfish\.com\/deck\/([0-9]{7})(#[a-zA-Z]*)?\s*', re.M | re.I)
cockatriceDeckRegex = re.compile('\s*<\?xml version="1\.0" encoding="UTF-8"\?>\s*<cockatrice_deck version="1">\s*<deckname>[^<]*<\/deckname>\s*<comments>[^<]*<\/comments>\s*(\s*<zone name="[^<"]+"\s*>\s*([\s]*<card number="[0-9]+" *name="[^<"]+"\s*\/>\s*)*<\/zone>\s*)+\s*<\/cockatrice_deck>\s*', re.M | re.I)

deckRegex = re.compile("(\s*[0-9]+ [\/a-zA-Z 0-9,.'-]+\r*\n*)+", re.M)

def isValidCodFile(deckData: str) -> bool:
    return cockatriceDeckRegex.search(deckData)

def isMoxFieldLink(decklist: str) -> bool:
    return moxFieldLinkRegex.search(decklist)

def isMtgGoldfishLink(decklist: str) -> bool:
    return mtgGoldFishLinkRegex.search(decklist)

def isTappedOutLink(decklist: str) -> bool:
    return tappedoutLinkRegex.search(decklist)

class deck:
    """
    The class is this module
    """
    # More specifically this checks to make sure that each line of a decklist is correct
    validDecklistRegex = re.compile( "^(sb: )?[0-9]+[x]? [^\n]+$", re.I )

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

        # Normal decklist
        else:
            if not self.validateDecklist( decklist ):
                raise DecklistError( f'Error in passed-in decklist.' )
            self.decklist = decklist
            if self.decklist == "":
                self.cards = [ ]
            else:
                self.cards = self.parseAnnotatedTriceDecklist( ) if "\n//" in self.decklist else \
                            self.parseNonAnnotatedTriceDecklist( )

        self.updateDeckHash()

    def __str__( self ):
        return f'{self.ident}: {self.deckHash}'

    def validateDecklist( self, decklist: str ) -> bool:
        """ A(n almost) static method that determines if a decklist will cause problems"""
        for card in decklist.strip().split("\n"):
            if card == "":
                continue
            print( card )
            if not self.validDecklistRegex.search( card ):
                return False
        return True

    def _loadMtgGoldfishDeck(deckURL: str):
        regex_match = mtgGoldFishLinkRegex.fullmatch(deckURL)
        https, www, deck_id, anchor = regex_match.groups()

        url = f"https://www.mtggoldfish.com/deck/download/{deck_id}"

        self.decklist = requests.get(url, timeout=7.0, data="", verify=True).text
        if not self.validateDecklist( self.decklist ):
            raise DeckRetrievalError( f'Error while retrieving a deck from {url}' )

        self.cards = self.parseAnnotatedTriceDecklist( ) if "\n//" in self.decklist else \
                     self.parseNonAnnotatedTriceDecklist( )

    def _loadTappedOutDeck(self, deckURL: str):
        regex_match = tappedoutLinkRegex.fullmatch(deckURL)
        https, deck_id = regex_match.groups()

        url = f"https://tappedout.net/mtg-decks/{deck_id}/?fmt=txt"

        decklist = requests.get(url, timeout=7.0, data="", verify=True).text

        # Sort out sideboard
        boards = decklist.split("Sideboard:")
        mainboard = boards[0]

        sideboard = []
        sideboard_list = ""
        if len(boards) > 1:
            sideboard_list = "\n".join( [ card for card in boards[1].split("\n") if (not card.isspace()) and card != "" ] )

        if not self.validateDecklist( mainboard + sideboard_list ):
            raise DeckRetrievalError( f'Error while retrieving a deck from {url}' )

        self.decklist = mainboard + sideboard_list
        self.cards = self.parseAnnotatedTriceDecklist( ) if "\n//" in self.decklist else \
            self.parseNonAnnotatedTriceDecklist( )

    def _loadMoxFieldDeck(self, deckURL: str):
        self.decklist = ""
        regex_match = moxFieldLinkRegex.fullmatch(deckURL)
        https, www, deck_id = regex_match.groups()

        url = f"https://api.moxfield.com/v2/decks/all/{deck_id}"

        resp = requests.get(url, timeout=7.0, data="", verify=True).text
        deck_data = json.loads(resp)
        
        main = deck_data["commanders"]
        for commander in main:
            self.decklist += f'1 {main[commander]["card"]["name"]}\n'
        
        main_board = deck_data["mainboard"]
        for card_name in main_board:
            # Add card to decklist
            card = main_board[card_name]
            self.decklist += f'{card["quantity"]} {card_name}\n'
            side_board = deck_data["sideboard"]
            for card_name in side_board:
                # Add card to decklist
                card = side_board[card_name]
                self.decklist += f'SB: {card["quantity"]} {card_name}\n'

        if not self.validateDecklist( self.decklist ):
            raise DeckRetrievalError( f'Error while retrieving a deck from {url}' )

        self.cards = self.parseAnnotatedTriceDecklist()

    def _loadFromCodFile(self, fileData: str):
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

        if not self.validateDecklist( self.decklist ):
            raise CodFileError( f'Malformed card/quantity while parsing cod file.' )

        # Update hash
        self.cards = self.parseNonAnnotatedTriceDecklist()

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
        if "" != self.decklist and not deckRegex.search(self.decklist):
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
                    name   = cardsDB.getCard(card[0]).strip().lower()
                else:
                    number = int( card[0].strip() )
                    name   = cardsDB.getCard(card[1]).strip().lower()
                for i in range(number):
                    cards.append( name )
            else:
                card = card.split(" ", 2)
                number = int( card[1].strip() )
                name   = card[0] + cardsDB.getCard(card[2]).strip().lower()
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




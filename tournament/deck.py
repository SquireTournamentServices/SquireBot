import hashlib
import string
import xml.etree.ElementTree as ET


from typing import List


from .tournamentUtils import *


class deck:
    def __init__( self, a_commander: str = "", a_decklist: str = "" ):
        self.deckHash  = ""
        self.commander = a_commander
        if a_decklist == "":
            self.cards = [ ]
        else:
            self.cards = self.parseAnnotatedTriceDecklist( a_decklist ) if "\n//" in a_decklist else self.parseNonAnnotatedTriceDecklist( a_decklist )
        self.updateDeckHash()
    
    def exportXMLString( self, a_indent: str = "" ) -> str:
        lineStart = f'\n{a_indent}\t'
        digest = f'{a_indent}<deck commander="{self.commander}">' 
        for card in self.cards:
            digest += f'{lineStart}<card name="{card}"/>'
        digest += f'\n{a_indent}</deck>\n'
        return digest
    
    def importFromETree( self, a_tree: ET ) -> None:
        for card in a_tree.iter( "card" ):
            self.cards.append( card.attrib['name'] )
        self.updateDeckHash()
    
    # Converts a semicolon-delineated deck string into a hash.
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

    def parseNonAnnotatedTriceDecklist( self, a_decklist: str) -> List[str]:
        digest = []
        prefix = ""
        for line in a_decklist.strip().split("\n"):
            line = line.strip()
            if line == "":
                prefix = "SB: "
            else:
                digest.append(prefix + line)
        print( digest )
        return digest

    def parseAnnotatedTriceDecklist( self, a_decklist: str ) -> List[str]:
        return [ line for line in a_decklist.strip().split("\n") if line.strip() != "" and line[0:2] != "//" ]
        
    


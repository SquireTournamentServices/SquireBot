import hashlib
import string



conv_dict = {
    int(c, 32): c for c in (string.digits + string.ascii_lowercase)[:32]
}  # convert from integer to base32hex symbols

def number_to_base(n, b):
    """Converts a number in base 10 to base b"""
    if n == 0:
        return [0]
    digits = []
    while n:
        digits.append(int(n % b))
        n //= b
    return digits[::-1]


class deck:
    def __init__( self, a_decklist = "" ):
        self.cards = self.parseAnnotatedTriceDecklist( a_decklist )
        self.ownerName = ""
        self.deckHash  = ""
        self.updateDeckHash()
        
    def saveDeck( a_filename = "" ):
        if a_filename == "":
            a_filename = ownerName + "-deck"
        deckfile = open( a_filename, "w" )
        deckfile.write( "\n".join( self.cards ) )
        deckfile.close()
    
    def loadDeck( a_filename ):
        deckfile = open( a_filename, "r" )
        self.cards = deckfile.read().strip().split("\n")
        self.updateDeckHash()
    
    # Converts a semicolon-delineated deck string into a hash.
    def updateDeckHash( self ):
        l_cards = []
        for card in self.cards:
            number = int( card.split(" ", 1)[0].strip() )
            name   = card.split(" ", 1)[1].strip().lower()
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

    def parseAnnotatedTriceDecklist( self, a_decklist ):
        return [ line for line in a_decklist.strip().split("\n") if line.strip() != "" and line[0:2] != "//" ]
        
    


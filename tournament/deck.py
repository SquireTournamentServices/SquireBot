


class deck:
    def __init__( self, a_decklist = "" ):
        self.cards = parseAnnotatedTriceDecklist( a_decklist )
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
    
    def updateDeckHash():

    def parseAnnotatedTriceDecklist( a_decklist ):
        return [ line for line in a_decklist.strip().split("\n") if line.strip() != "" and line[0:2] != "//" ]
        
    


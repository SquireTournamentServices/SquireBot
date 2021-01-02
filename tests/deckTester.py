from deck import deck

f = open("tmp", "r")
decklist = f.read().strip()
f.close()

newDeck = deck( decklist )
print( newDeck.deckHash )



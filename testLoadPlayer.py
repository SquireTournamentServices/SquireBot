from tournament.player import player
from tournament.deck import deck


p1 = player("")
p1.loadXML( "tester.xml" )
print(p1.decks)
print(p1.decks["Elsha of the Infinite"].deckHash)



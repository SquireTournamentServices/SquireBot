import cardDB
import time
import os

#@profile
def test():
    # Assert cockatrice name converter works
    c = cardDB.card("a // b", "flip")
    assert(c.name == "a")

    c = cardDB.card("a // b", "modal_dfc")
    assert(c.name == "a")

    c = cardDB.card("a // b", "transform")
    assert(c.name == "a")

    # Test downloading the cards
    try:
        os.remove("AllPrintings.json")
    except FileNotFoundError as e:
        print(e)
    cards = cardDB.cardDB()
    length = len(cards.cards)
    assert(length > 0)

    # Test load from cache
    cards = cardDB.cardDB()
    assert(len(cards.cards) == length)

if __name__ == '__main__':
    test()

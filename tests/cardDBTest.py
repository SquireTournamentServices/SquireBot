import time
import os
from test import *
from Tournament import *

class CardDBTest(TestCase):
    def __init__(self):
        self.testName = "Tournament/cardDB.py"

    def test(self):
        types = ["Instant"]
        
        # Assert cockatrice name converter works
        c = card("a // b", "flip", types)
        assert(c.name == "a")

        c = card("a // b", "modal_dfc", types)
        assert(c.name == "a")

        c = card("a // b", "transform", types)
        assert(c.name == "a")

        # Test downloading the cards
        try:
            os.remove("AllPrintings.json")
        except FileNotFoundError as e:
            print(e)
            
        cards = cardDB()
        length = len(cards.cards)
        assert(length > 0)

        # Test load from cache
        cards = cardDB()
        assert(len(cards.cards) == length)
        
        return True

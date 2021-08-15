from Tournament import *
from test import *

class DeckTests(TestCase):
    def __init__(self):
        self.testName = "Tournament/deck.py"

    def test(self):
        subTests = []
        
        subTests.append(MoxfieldTest())
        subTests.append(CodFileTest())
        subTests.append(TappedOutTest())
        subTests.append(MtgGoldfishTest())
        subTests.append(BaseCaseTest())
        
        testRunner = TestRunner(subTests)
        
        print("[DECK TEST]: Running sub tests...")
        return testRunner.executeTests()
    
class MoxfieldTest(TestCase):
    def __init__(self):
        self.testName = "Tournament/deck.py moxfield tests"
        
    def test(self):
        return True

class CodFileTest(TestCase):
    def __init__(self):
        self.testName = "Tournament/deck.py .cod file tests"
        
    def test(self):
        return True

class TappedOutTest(TestCase):
    def __init__(self):
        self.testName = "Tournament/deck.py tappedout tests"
        
    def test(self):
        return True

class MtgGoldfishTest(TestCase):
    def __init__(self):
        self.testName = "Tournament/deck.py mtgoldfish tests"
        
    def test(self):
        return True
    
class BaseCaseTest(TestCase):
    def __init__(self):
        self.testName = "Tournament/deck.py base case tests"
        
    def test(self):
        deckname = "test-deck"
        deckhash = "u1i483i6"
        
        # Sample format
        decklist1 = """1 Mana Crypt
2 Mana Drain
SB: 1 Mana Vault
SB: 2 White Mana Battery"""

        testdeck = deck(deckname, decklist1)
        assert(testdeck.deckHash == deckhash)
        assert(testdeck.ident == deckname)

        # Cockatrice export non-annotated
        decklist2 = """1 Mana Crypt
2 Mana Drain

1 Mana Vault
2 White Mana Battery"""

        testdeck = deck(deckname, decklist2)
        assert(testdeck.deckHash == deckhash)
        assert(testdeck.ident == deckname)

        # Cockatrice export annotated
        decklist3 = """// 3 Maindeck
// 1 Artifact
1 Mana Crypt

// 2 Instant
2 Mana Drain


// 3 Sideboard
// 3 Artifact
SB: 1 Mana Vault
SB: 2 White Mana Battery"""
        testdeck = deck(deckname, decklist3)
        assert(testdeck.deckHash == deckhash)
        assert(testdeck.ident == deckname)
        
        # Test that deck.py does the cardb lookup
        decklist4 = """2 Glasspool Mimic // Glasspool Shore
SB: 2 Wandering Archaic // Explore the Vastlands"""
        testdeck = deck(deckname, decklist4)
        assert(testdeck.deckHash == "h3jg66ua")
        assert(testdeck.ident == deckname)
        
        return True

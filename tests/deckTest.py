import os
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
        subTests.append(ExistingDataTest())
        
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
        decklists = []
        decklists.append("""<?xml version="1.0" encoding="UTF-8"?>
<cockatrice_deck version="1">
    <deckname></deckname>
    <comments></comments>
    <zone name="main">
        <card number="1" name="Paradoxical Outcome"/>
        <card number="1" name="Acquire"/>
        <card number="1" name="Tale's End"/>
        <card number="1" name="Dramatic Reversal"/>
        <card number="1" name="Bribery"/>
        <card number="1" name="Turnabout"/>
        <card number="1" name="Laboratory Maniac"/>
        <card number="1" name="Jace, Ingenious Mind-Mage"/>
        <card number="1" name="Vedalken Aethermage"/>
        <card number="1" name="Meishin, the Mind Cage"/>
        <card number="1" name="Disruptive Pitmage"/>
        <card number="1" name="Graceful Adept"/>
        <card number="1" name="Docent of Perfection"/>
        <card number="1" name="Teferi, Mage of Zhalfir"/>
        <card number="1" name="Spellbook"/>
        <card number="1" name="Voidmage Prodigy"/>
        <card number="1" name="Bazaar Trademage"/>
        <card number="1" name="Knowledge Pool"/>
        <card number="1" name="Sage's Dousing"/>
        <card number="1" name="Crookclaw Transmuter"/>
        <card number="1" name="Echo Mage"/>
        <card number="1" name="Merfolk Trickster"/>
        <card number="1" name="Vodalian Mage"/>
        <card number="1" name="Venser, Shaper Savant"/>
        <card number="1" name="Naban, Dean of Iteration"/>
        <card number="1" name="Flood of Tears"/>
        <card number="1" name="Sol Ring"/>
        <card number="1" name="Brine Seer"/>
        <card number="1" name="Thalakos Dreamsower"/>
        <card number="1" name="Diviner's Wand"/>
        <card number="1" name="Jace, Cunning Castaway"/>
        <card number="1" name="Narset, Parter of Veils"/>
        <card number="1" name="Jace, the Living Guildpact"/>
        <card number="1" name="Wayfarer's Bauble"/>
        <card number="1" name="Juntu Stakes"/>
        <card number="1" name="Eye of the Storm"/>
        <card number="1" name="Brainstorm"/>
        <card number="1" name="Summary Dismissal"/>
        <card number="1" name="Misdirection"/>
        <card number="1" name="Willbender"/>
        <card number="1" name="Mystic Sanctuary"/>
        <card number="1" name="Mind Stone"/>
        <card number="1" name="Mirrormade"/>
        <card number="1" name="Opt"/>
        <card number="1" name="Corrupted Conscience"/>
        <card number="1" name="Daring Apprentice"/>
        <card number="1" name="Portal Mage"/>
        <card number="1" name="Time Stop"/>
        <card number="1" name="Hisoka, Minamo Sensei"/>
        <card number="1" name="Containment Membrane"/>
        <card number="1" name="Silumgar Spell-Eater"/>
        <card number="1" name="Thassa's Oracle"/>
        <card number="1" name="Kheru Spellsnatcher"/>
        <card number="1" name="Disruptive Student"/>
        <card number="1" name="Treasure Mage"/>
        <card number="1" name="Jace Beleren"/>
        <card number="1" name="Ponder"/>
        <card number="1" name="Kasmina, Enigmatic Mentor"/>
        <card number="1" name="Folio of Fancies"/>
        <card number="1" name="Jace, Architect of Thought"/>
        <card number="1" name="Aether Spellbomb"/>
        <card number="35" name="Island"/>
        <card number="1" name="Boompile"/>
        <card number="1" name="Glamerdye"/>
        <card number="1" name="Pondering Mage"/>
    </zone>
    <zone name="side">
        <card number="1" name="Azami, Lady of Scrolls"/>
    </zone>
</cockatrice_deck>
""")
        
        decklists.append("""<?xml version="1.0" encoding="UTF-8"?>
<cockatrice_deck version="1">
    <deckname></deckname>
    <comments></comments>
    <zone name="main">
        <card number="1" name="Braids, Conjurer Adept"/>
        <card number="1" name="Mana Crypt"/>
        <card number="1" name="Mana Vault"/>
        <card number="1" name="Basalt Monolith"/>
        <card number="1" name="Grim Monolith"/>
        <card number="1" name="Sol Ring"/>
        <card number="1" name="Fellwar Stone"/>
        <card number="1" name="Arcane Signet"/>
        <card number="1" name="Command Tower"/>
        <card number="15" name="Island"/>
        <card number="15" name="Snow-Covered Island"/>
        <card number="1" name="Gemstone Caverns"/>
        <card number="1" name="Scorched Ruins"/>
        <card number="1" name="Scroll Rack"/>
        <card number="1" name="Sensei's Divining Top"/>
        <card number="1" name="It That Betrays"/>
        <card number="1" name="Pathrazer of Ulamog"/>
        <card number="1" name="Breaker of Armies"/>
        <card number="1" name="Eldrazi Conscription"/>
        <card number="1" name="Ulamog's Crusher"/>
        <card number="1" name="Bane of Bala Ged"/>
        <card number="1" name="Clock of Omens"/>
        <card number="1" name="Narset, Parter of Veils"/>
        <card number="1" name="Teferi, Master of Time"/>
        <card number="1" name="Teferi's Ageless Insight"/>
        <card number="1" name="Alhammarret's Archive"/>
        <card number="1" name="Mox Tantalite"/>
        <card number="1" name="Mox Amber"/>
        <card number="1" name="Mox Opal"/>
        <card number="1" name="Chrome Mox"/>
        <card number="1" name="Field of Ruin"/>
        <card number="1" name="Maze of Ith"/>
        <card number="1" name="Consecrated Sphinx"/>
        <card number="1" name="Psychic Possession"/>
        <card number="1" name="Cyclonic Rift"/>
        <card number="1" name="Evacuation"/>
        <card number="1" name="Grafdigger's Cage"/>
        <card number="1" name="Voltaic Key"/>
        <card number="1" name="Manifold Key"/>
        <card number="1" name="Gruul Keyrune"/>
        <card number="1" name="Thran Dynamo"/>
    </zone>
</cockatrice_deck>
""")
        
        deckhashes = ["of0gdhk3", "unoq8n8l"]
        
        assert(len(decklists) == len(deckhashes))
        for i in range(0, len(decklists)):
            testdeck = deck("testdeck", decklists[i])
            if(testdeck.deckHash != deckhashes[i]):
                print(f"Error with cockatrice file decklist {decklists[i]}. Hash is {testdeck.deckHash} expecting {deckhashes[i]}. Decklist: '''{testdeck.decklist}'''")
                return False        
        return True

class TappedOutTest(TestCase):
    def __init__(self):
        self.testName = "Tournament/deck.py tappedout tests"
        
    def test(self):
        decklinks = ["https://tappedout.net/mtg-decks/all-hail-west-theros-summer-bloom-copy/", "https://tappedout.net/mtg-decks/dungeon-master-sefris/"]
        deckhashes = ["mmpirkak", "fng10fmj"]
        
        assert(len(decklinks) == len(deckhashes))
        for i in range(0, len(decklinks)):
            try:
                testdeck = deck("testdeck", decklinks[i])
                if(testdeck.deckHash != deckhashes[i]):
                    print(f"Error with tappedout decklist {decklinks[i]}. Hash is {testdeck.deckHash} expecting {deckhashes[i]}. Decklist: '''{testdeck.decklist}'''")
                    return False
            except Exception as e:
                print(f"Error with tappedout decklist ({e}). Decklist: {decklinks[i]}")
        return True

class MtgGoldfishTest(TestCase):
    def __init__(self):
        self.testName = "Tournament/deck.py mtgoldfish tests (top 6 from summer bloom 2021)"
        
    def test(self):
        # Top six from summer bloom 2021
        decklinks = ["https://www.moxfield.com/decks/otJGTVMYLE2Tu7dY2eCf3A", "https://www.moxfield.com/decks/BcN9es_OAUaArNr9Yb6-bQ", "https://www.moxfield.com/decks/YlXoO8U2N0qZq7mLrhDqtA", "https://www.moxfield.com/decks/jPilLqEhgk2t1li2haDpCQ", "https://www.moxfield.com/decks/qW5f_UJGBUOxSyhx0sY_Mw", "https://www.moxfield.com/decks/iNtkQTBHW0es9Z_PpE2InA"]
        deckhashes = ["t7rdfct8", "kinva7iq", "s44prtc8", "0sbns7o2", "qvb0eogv", "i0p34cdo"]
        
        assert(len(decklinks) == len(deckhashes))
        for i in range(0, len(decklinks)):
            testdeck = deck("testdeck", decklinks[i])
            if(testdeck.deckHash != deckhashes[i]):
                print(f"Error with moxfield decklist {decklinks[i]}. Hash is {testdeck.deckHash} expecting {deckhashes[i]}. Decklist: '''{testdeck.decklist}'''")
                return False        
        return True

class ExistingDataTest(TestCase):
    def __init__(self):
        self.testName = "Tournament/deck.py test existing data (summer bloom 2021 decks) for hash regression"
    
    def test(self):
        path = f"{os.getcwd()}/test-data-decks"
        for filename in os.listdir(path):
            with open(os.path.join(path, filename), 'r') as f:
                decklist = f.read()
                try:
                    testdeck = deck(filename, decklist)
                except Exception as e:
                    # Catch exception
                    print(f"Error with deck with expected hash {filename} has the wrong hash. Decklist '''{decklist}'''.")
                    raise e
                
                if filename != testdeck.deckHash:
                    print(f"Error with deck with expected hash {filename} has the wrong hash. Decklist '''{decklist}'''. Actual hash: {testdeck.deckHash} Cards: {testdeck.cards}")
                    return False
                    
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

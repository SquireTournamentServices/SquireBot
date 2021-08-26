""" These are tests for the player class. """


import sys
import os

projectBaseDir = os.path.dirname(os.path.realpath(__file__)) + "/../../"

sys.path.insert( 0, projectBaseDir + 'Tournament')
sys.path.insert( 0, projectBaseDir )

from Tournament import player

import unittest



class TestPlayerGeneral( unittest.IsolatedAsyncioTestCase ):
    """ """
    def setUp( self ) -> None:
        """ Creates a player called 'Test Player'. """
        self.player = player( "Test Player" )

    def tearDown( self ) -> None:
        """ Does nothing since players don't have shared data. """
        return

    def test_get_name( self ) -> None:
        """ """
        pass

    def test_drop( self ) -> None:
        """ """
        pass

    def test_pairing_string( self ) -> None:
        """ """
        pass

    def test_add_opponent( self ) -> None:
        """ """
        pass

    def test_remove_opponent( self ) -> None:
        """ """
        pass

    def test_save_and_load( self ) -> None:
        """ Tests if the save and loading features work properly. """
        self.player.triceName = "Test & Play"
        with open( "test-deck-one.txt", "r" ) as decklist:
            self.player.addDeck( "Deck One", decklist.read() )
        with open( "test-deck-two.txt", "r" ) as decklist:
            self.player.addDeck( "Deck Two", decklist.read() )
        with open( "test-deck-three.txt", "r" ) as decklist:
            self.player.addDeck( "Deck Three", decklist.read() )
        with open( "test-deck-four.txt", "r" ) as decklist:
            self.player.addDeck( "Deck Four", decklist.read() )
        with open( "test-deck-five.txt", "r" ) as decklist:
            self.player.addDeck( "Deck Five", decklist.read() )
        with open( "test-deck-six.txt", "r" ) as decklist:
            self.player.addDeck( "Deck Six", decklist.read() )
        self.player.saveXML( )
        newPlayer = player( "" )
        newPlayer.loadXML( self.player.saveLocation )
        self.assertEqual( self.player, newPlayer )


class TestPlayerDecks( unittest.IsolatedAsyncioTestCase ):
    def setUp( self ) -> None:
        """ Creates a player called 'Test Player'. """
        self.player = player( "Test Player" )

    def tearDown( self ) -> None:
        """ Does nothing since players don't have shared data. """
        return

    def test_add_deck( self ) -> None:
        """ Adds several decks """
        with open( "test-deck-one.txt", "r" ) as decklist:
            deck_list = decklist.read()
            self.player.addDeck( "Deck One", deck_list )
            self.assertTrue( len(self.player.decks) == 1 )
            self.assertTrue( "Deck One" in self.player.decks )
        with open( "test-deck-two.txt", "r" ) as decklist:
            deck_list = decklist.read()
            self.player.addDeck( "Deck Two", deck_list )
            self.assertTrue( len(self.player.decks) == 2 )
            self.assertTrue( "Deck Two" in self.player.decks )
        oldDeck = self.player.decks["Deck One"]
        self.player.addDeck( "Deck One", "1 Empty Deck" )
        self.assertNotEqual( self.player.decks["Deck One"], oldDeck )
        self.assertTrue( len(self.player.decks) == 2 )

    async def test_remove_deck( self ) -> None:
        """ Adds and then removes some decks """
        with open( "test-deck-one.txt", "r" ) as decklist:
            deck_list = decklist.read()
            self.player.addDeck( "Deck One", deck_list )
            self.assertTrue( len(self.player.decks) == 1 )
            self.assertTrue( "Deck One" in self.player.decks )
        with open( "test-deck-two.txt", "r" ) as decklist:
            deck_list = decklist.read()
            self.player.addDeck( "Deck Two", deck_list )
            self.assertTrue( len(self.player.decks) == 2 )
            self.assertTrue( "Deck Two" in self.player.decks )
        with open( "test-deck-three.txt", "r" ) as decklist:
            deck_list = decklist.read()
            self.player.addDeck( "Deck Three", deck_list )
            self.assertTrue( len(self.player.decks) == 3 )
            self.assertTrue( "Deck Three" in self.player.decks )
        await self.player.removeDeck( "Deck Two" )
        self.assertTrue( len(self.player.decks) == 2 )
        self.assertFalse( "Deck Two" in self.player.decks )
        await self.player.removeDeck( "Deck One" )
        self.assertTrue( len(self.player.decks) == 1 )
        self.assertFalse( "Deck One" in self.player.decks )

    def test_deck_embed_one( self ) -> None:
        """ This test is simply to check if errors occur. """
        with open( "test-deck-one.txt", "r" ) as decklist:
            deck_list = decklist.read()
            self.player.addDeck( "Deck One", deck_list )
            self.assertTrue( len(self.player.decks) == 1 )
            self.assertTrue( "Deck One" in self.player.decks )
        embed = self.player.getDeckEmbed( "Deck One" )

    def test_deck_embed_two( self ) -> None:
        """ This test is simply to check if errors occur. """
        with open( "test-deck-two.txt", "r" ) as decklist:
            deck_list = decklist.read()
            self.player.addDeck( "Deck Two", deck_list )
            self.assertTrue( len(self.player.decks) == 1 )
            self.assertTrue( "Deck Two" in self.player.decks )
        embed = self.player.getDeckEmbed( "Deck Two" )

    def test_deck_embed_three( self ) -> None:
        """ This test is simply to check if errors occur. """
        with open( "test-deck-three.txt", "r" ) as decklist:
            deck_list = decklist.read()
            self.player.addDeck( "Deck Three", deck_list )
            self.assertTrue( len(self.player.decks) == 1 )
            self.assertTrue( "Deck Three" in self.player.decks )
        embed = self.player.getDeckEmbed( "Deck Three" )

    def test_deck_embed_four( self ) -> None:
        """ This test is simply to check if errors occur. """
        with open( "test-deck-four.txt", "r" ) as decklist:
            deck_list = decklist.read()
            self.player.addDeck( "Deck Four", deck_list )
            self.assertTrue( len(self.player.decks) == 1 )
            self.assertTrue( "Deck Four" in self.player.decks )
        embed = self.player.getDeckEmbed( "Deck Four" )

    def test_deck_embed_five( self ) -> None:
        """ This test is simply to check if errors occur. """
        with open( "test-deck-five.txt", "r" ) as decklist:
            deck_list = decklist.read()
            self.player.addDeck( "Deck Five", deck_list )
            self.assertTrue( len(self.player.decks) == 1 )
            self.assertTrue( "Deck Five" in self.player.decks )
        embed = self.player.getDeckEmbed( "Deck Five" )

    def test_deck_embed_six( self ) -> None:
        """ This test is simply to check if errors occur. """
        with open( "test-deck-six.txt", "r" ) as decklist:
            deck_list = decklist.read()
            self.player.addDeck( "Deck Six", deck_list )
            self.assertTrue( len(self.player.decks) == 1 )
            self.assertTrue( "Deck Six" in self.player.decks )
        embed = self.player.getDeckEmbed( "Deck Six" )


class TestPlayerMatches( unittest.IsolatedAsyncioTestCase ):
    def setUp( self ) -> None:
        """ Creates a player called 'Test Player'. """
        self.player = player( "Test Player" )

    def tearDown( self ) -> None:
        """ Does nothing since players don't have shared data. """
        return

    def test_add_match( self ) -> None:
        """ """
        pass

    def test_remove_match( self ) -> None:
        """ """
        pass

    def test_record_win( self ) -> None:
        """ """
        pass

    def test_record_draw( self ) -> None:
        """ """
        pass

    def test_confirm_result( self ) -> None:
        """ """
        pass

    def test_get_match( self ) -> None:
        """ """
        pass

    def test_find_open_match( self ) -> None:
        """ """
        pass

    def test_find_open_match_index( self ) -> None:
        """ """
        pass

    def test_find_open_match_number( self ) -> None:
        """ """
        pass

    def test_has_open_match( self ) -> None:
        """ """
        pass


unittest.main()

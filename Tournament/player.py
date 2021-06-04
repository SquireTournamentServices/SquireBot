import xml.etree.ElementTree as ET

from typing import List

from .utils import *
from .deck import deck
from .match import match


"""
    This class manages players.
    The class currently has the following functionalities:
        - Decks can be added to the list of decks
        - The player's number of wins can be calculated
        - A discord user can be added, though a player doesn't have one by default
        - The player's status is tracked and can be updated (i.e if they are active or have dropped)
        - An xml file can be created which stores the overview of the player and their decks but not their matches.
        - The player can load an xml file after construction
    There is one functionality that the player can have but can't be codified in this class.
    Ideally, each player stores references to match object instead of copies.
    In order to do this, an empty match has to be added and then overwritten by the desired match object.
    Doing this allows each player to have an up-to-date list of match objects at all times, but requires this to be kept up-to-date
    externally instead of in the class.
    In the future, functionalities might be added to update matches, but that remains to be seen.
    
    The class has the following member variables:
        - name: The name of the player
        - status: A string that states if the player is active or has dropped
        - decks: A dict that index-s deck objects with their identifier (deck.ident)
        - matches: A list of matches that the player is associated with
        - discordUser: A copy of the player's associated discord user object
"""

class player:
    # The class constructor
    def __init__( self, name: str = "", discordID: str = "" ):
        self.saveLocation = f'{name}.xml'
        self.discordUser = ""
        self.discordID = discordID
        self.name = name
        self.triceName = ""
        self.status  = "active"
        self.decks   = { }
        self.matches = [ ]
        self.opponents = set( )
    
    def __str__( self ):
        newLine = "\n\t- "
        digest  = f'Player Name: {self.name}\n'
        digest += f'Disord Nickname: {self.discordUser.display_name}\n'
        digest += f'Cockatrice Username: {self.triceName}\n'
        digest += f'Status: {self.status}\n'
        digest += f'Decks:{newLine}{newLine.join( [ str(self.decks[ident]) for ident in self.decks ] )}\n'
        digest += f'Matches:{newLine}{newLine.join( [ str(mtch) for mtch in self.matches ] )}'
        return digest
    
    def __eq__( self, other: 'player' ):
        if type(other) != player:
            return False
        digest  = ( self.name == other.name )
        digest &= ( self.discordID == other.discordID )
        return digest
    
    def isActive( self ):
        return self.status == "active"
    
    def isValidOpponent( self, a_plyr: 'player' ) -> bool:
        if self.name in a_plyr.opponents:
            return False
        if a_plyr.name in self.opponents:
            return False
        return True
    
    def areValidOpponents( self, a_plyrs: List['player'] ) -> bool:
        for plyr in a_plyrs:
            if not self.isValidOpponent( plyr ):
                return False
        return True
    
    def getMention( self ):
        if type(self.discordUser) == discord.User or type(self.discordUser) == discord.Member:
            return self.discordUser.mention
        return f'<@{self.discordID}>'
    
    def getDisplayName( self ):
        if type(self.discordUser) == discord.User or type(self.discordUser) == discord.Member:
            return self.discordUser.display_name
        else:
            return "\u200b" # Widthless whitespace char to prevent Embed issues
    
    async def getDeckEmbed( self, a_deckname: str ) -> discord.Embed:
        digest = discord.Embed()
        
        fields = [ "" ]
        for card in self.decks[a_deckname].cards:
            if len(fields[-1]) + len(card) > 1023:
                fields.append( "" )
            fields[-1] += card + "\n"
        
        digest.add_field( name=f'{a_deckname}: {self.decks[a_deckname].deckHash}', value=fields[0], inline=False )
        
        for f in fields[1:]:
            digest.add_field( name="\u200b", value=f, inline=False )
        
        return digest
    
    def pairingString( self ):
        digest = "\u200b\u200b"
        if self.triceName != "":
            digest += f'Cockatrice Username: {self.triceName}\n'
        counter = 0
        for deck in self.decks:
            counter += 1
            digest += f'Deck #{counter}: {self.decks[deck].deckHash}\n'
        return digest[:-1] # Trim the extra new line char
    
    # Adds a copy of a discord user object
    def addDiscordUser( self, a_discordUser ) -> None:
        self.discordUser = a_discordUser
    
    # Updates the status of the player
    def updateStatus( self, a_status: str ) -> None:
        self.status = a_status
    
    def hasOpenMatch( self ) -> bool:
        digest = False
        for mtch in self.matches:
            digest |= not mtch.isCertified( )
        return digest
    
    def removeOpponent( self, a_plyr ) -> None:
        if a_plyr in self.opponents:
            self.opponents.remove( a_plyr )
    
    async def removeMatch( self, a_matchNum: int ) -> None:
        index = -1
        for i in range(len(self.matches)):
            if self.matches[i].matchNumber == a_matchNum:
                index = i
                break
        if index == -1:
            return
        for plyr in self.matches[i].activePlayers:
            self.removeOpponent( plyr )
        for plyr in self.matches[i].droppedPlayers:
            self.removeOpponent( plyr )
        del( self.matches[i] )
        self.saveXML( )
    
    def addMatch( self, a_mtch: match ) -> None:
        self.matches.append( a_mtch )
        for plyr in a_mtch.activePlayers:
            if plyr == self.name:
                continue
            self.opponents.add( plyr )
        for plyr in a_mtch.droppedPlayers:
            if plyr == self.name:
                continue
            self.opponents.add( plyr )
    
    def getMatch( self, a_matchNum: int ) -> match:
        for mtch in self.matches:
            if mtch.matchNumber == a_matchNum:
                return mtch
        return match( [] )
    
    # Find the index of the not certified match closest to the end of the match array
    # Returns 1 if no open matches exist; otherwise, returns a negative index
    def findOpenMatchIndex( self ) -> int:
        if not self.hasOpenMatch( ):
            return 1
        digest = -1
        while self.matches[digest].isCertified() and abs(digest) <= len(self.matches):
            digest -= 1
        return digest

    def findOpenMatch( self ) -> match:
        index = self.findOpenMatchIndex( )
        if index == 1:
            # print( f'The reported index was one. Returning an empty match.' )
            return match( [] )
        # print( f'The reported index was not one. Returning an the correct match.' )
        return self.matches[index]
    
    def findOpenMatchNumber( self ) -> int:
        index = self.findOpenMatchIndex( )
        if index == 1:
            return -1
        return self.matches[index].matchNumber
    
    async def drop( self ) -> None:
        self.status = "dropped"
        digest = []
        for match in self.matches:
            if match.status != "certified":
                await match.dropPlayer( self.name )
    
    async def confirmResult( self ) -> str:
        index = self.findOpenMatchIndex( )
        if index == 1:
            return f'you are not in any open matches.'
        return await self.matches[index].confirmResult( self.name )
    
    async def recordWin( self ) -> str:
        index = self.findOpenMatchIndex( )
        if index == 1:
            return ""
        return await self.matches[index].recordResult( self.name, "win" )
    
    async def recordDraw( self ) -> str:
        index = self.findOpenMatchIndex( )
        if index == 1:
            return ""
        digest  = await self.matches[index].recordResult(  self.name, "draw" )
        digest += await self.matches[index].confirmResult( self.name )
        return digest
            
    # Addes a deck to the list of decks
    def addDeck( self, a_ident: str = "", a_decklist: str = "" ) -> None:
        # Removes an deck instead of overwriting it to keep self.decks in chrono order
        if a_ident in self.decks: 
            del( self.decks[a_ident] )
        self.decks[a_ident] = deck( a_ident, a_decklist )
    
    # A coroutine that returns a string for use in the generallized verification commands
    # An author is needed only when admin run the command
    async def removeDeckCoro( self, a_ident: str, author: str = "" ) -> str:
        del( self.decks[a_ident] )
        self.saveXML( )
        if author != "":
            await self.discordUser.send( content=f'Your deck {a_ident} has been removed by tournament admin.' )
            return f'{author}, the deck {a_ident} has been removed from {self.discordUser.mention}.' 
        return f'{self.discordUser.mention}, your decklist whose name or deck hash was "{a_ident}" has been deleted.'
    
    def getDeckIdent( self, ident: str = "" ) -> str:
        if ident in self.decks:
            return ident
        for name in self.decks:
            if ident == self.decks[name].deckHash:
                return name
        return ""
    
    def getCertMatches( self, withBye: bool=True ):
        digest = [ ]
        for mtch in self.matches:
            if not withBye and mtch.isBye():
                continue
            if mtch.isCertified():
                digest.append( mtch )
        return digest
    
    # Tallies the number of matches that the player is in, has won, and have been certified.
    def getMatchPoints( self, withBye: bool=True ) -> float:
        digest = 0
        certMatches = self.getCertMatches( withBye )
        for mtch in certMatches:
            if mtch.winner == self.name:
                digest += 3 #4
            elif mtch.isDraw():
                digest += 1 #0.5
            elif withBye and mtch.isBye():
                digest += 1
            else:
                digest += 0 #-2.25
        return digest
    
    # Calculates the percentage of game the player has won
    def getMatchWinPercentage( self, withBye: bool=True ) -> float:
        certMatches = self.getCertMatches( withBye )
        if len( certMatches ) == 0:
            return 0.0
        digest = self.getNumberOfWins( )/( len(certMatches)*1.0 )
        #digest = self.getMatchPoints( withBye )/( len(certMatches)*4. )
        return digest #if digest >= 1./3 else 1./3
    
    def getNumberOfWins( self ) -> int:
        return sum( [ 1 if mtch.winner == self.name else 0 for mtch in self.matches if mtch.isCertified( ) ] )
    
    # Saves the overview of the player and their deck(s)
    # Matches aren't saved with the player. They are save seperately.
    # The tournament object loads match objects and then associates each player with their match(es)
    def saveXML( self, a_filename: str = "" ) -> None:
        if a_filename == "":
            a_filename = self.saveLocation
        digest  = "<?xml version='1.0'?>\n"
        digest += '<player>\n'
        digest += f'\t<name>{toSafeXML(self.name)}</name>\n'
        digest += f'\t<triceName>{toSafeXML(self.triceName)}</triceName>\n'
        digest += f'\t<discord id="{toSafeXML(self.discordUser.id if type(self.discordUser) == discord.Member else str())}"/>\n'
        digest += f'\t<status>{toSafeXML(self.status)}</status>\n'
        for ident in self.decks:
            digest += self.decks[ident].exportXMLString( '\t' )
        digest += '</player>'
        with open( a_filename, 'w+' ) as xmlFile:
            xmlFile.write( digest )
    
    # Loads an xml file saved with the class after construction
    def loadXML( self, a_filename: str ) -> None:
        xmlTree = ET.parse( a_filename )
        self.saveLocation = a_filename
        self.name = fromXML(xmlTree.getroot().find( 'name' ).text)
        self.triceName = fromXML(xmlTree.getroot().find( 'triceName' ).text)
        if self.triceName == None:
            self.triceName = ""
        self.discordID  = fromXML(xmlTree.getroot().find( 'discord' ).attrib['id'])
        if self.discordID != "":
            self.discordID = int( self.discordID )
        self.status = fromXML(xmlTree.getroot().find( "status" ).text)
        for deckTag in xmlTree.getroot().findall('deck'):
            self.decks[deckTag.attrib['ident']] = deck()
            self.decks[deckTag.attrib['ident']].importFromETree( deckTag )
    


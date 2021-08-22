import os
import shutil
import threading
import time
from time import sleep
import asyncio
import warnings
import xml.etree.ElementTree as ET
import uuid
from typing import List, Dict, Tuple

import discord
from dotenv import load_dotenv

from .tricebot import TriceBot
from .commandResponse import commandResponse
from .utils import *
from .player import player
from .match import match
from .deck import *


load_dotenv()
# Trice bot auth token must be the same as in config.conf for the tricebot
# is whitespace sensitive
TRICE_BOT_AUTH_TOKEN = os.getenv('TRICE_BOT_AUTH_TOKEN')
# This is the external URL of the tricebot for replay downloads, this is different
# to the apiURL which is a loopback address or internal IP address allowing for
# nginx or similar to be setup.
EXTERN_URL = os.getenv('EXTERN_URL')
API_URL = os.getenv('API_URL')

#init trice bot object
trice_bot = TriceBot(TRICE_BOT_AUTH_TOKEN, apiURL=API_URL, externURL=EXTERN_URL)


"""
    This is the base tournament class. The other tournament classes are derived
    from this class.  Unlike the standard model of derived classes, the base
    tournament class needs to have to same public methods that its derived
    classes have.  Public method that a dervived class adds needs to also add
    that method to the base class and have it return a string stating that:
      - f'{self.name} does not have this method defined'
    Or something akin to that.
"""
class tournament:
    properties: list = [ "format", "deck-count", "match-length",
                         "match-size", "pairings-channel", "standings-channel",
                         "tricebot-enabled", "spectators-allowed", "spectators-need-password",
                         "spectators-can-chat", "spectators-can-see-hands",
                         "only-registered", "player-deck-verification" ]
    # The tournament base class is not meant to be constructed, but this
    # constructor acts as a guide for the minimum a constructor needs
    def __init__( self, name: str, hostGuildName: str, props: dict = { } ):
        self.uuid = str( uuid.uuid4() )
        self.name: str = name.replace("../", "")
        self.hostGuildName = hostGuildName
        self.format    = props["format"] if "format" in props else "Pioneer"

        self.guild   = None
        self.guildID = ""
        self.role    = None
        self.roleID  = ""
        self.pairingsChannel = None
        self.pairingsChannelID = ""

        self.infoMessageChannelID = None
        self.infoMessageID = None
        self.infoMessage = None

        self.regOpen      = True
        self.tournStarted = False
        self.tournEnded   = False
        self.tournCancel  = False

        self.loop = asyncio.new_event_loop( )
        self.fail_count = 0

        self.playersPerMatch = int(props["match-size"]) if "match-size" in props else 2
        self.matchLength     = int(props["match-length"])*60 if "match-length" in props else 60*60 # Length of matches in seconds

        self.deckCount = 1

        self.players: List = [ ]

        self.matches: List = [ ]

        #Create bot class and store the game creation settings
        self.triceBotEnabled = False
        self.spectators_allowed = False
        self.spectators_need_password = False
        self.spectators_can_chat = False
        self.spectators_can_see_hands = False
        self.only_registered = False
        self.player_deck_verification = False

        if len(props) != 0:
            self.setProperties(props, save=False)

    def getSaveLocation( self ) -> str:
        digest: str = ""
        if self.isDead():
            digest = f'guilds/{self.guild.id}/closedTournaments/{self.name}/'
        else:
            digest = f'guilds/{self.guild.id}/currentTournaments/{self.name}/'
        return digest

    def isPlanned( self ) -> bool:
        return not ( self.tournStarted or self.tournEnded or self.tournCancel )

    def isActive( self ) -> bool:
        return self.tournStarted and not ( self.tournEnded or self.tournCancel )

    def isDead( self ) -> bool:
        return self.tournEnded or self.tournCancel

    # ---------------- Universally Defined Methods ----------------

    async def addDiscordGuild( self, guild: discord.Guild ) -> str:
        self.guild = guild
        self.hostGuildName = guild.name
        self.guildID = self.guild.id
        self.role = await guild.create_role( name=f'{self.name} Player' )
        print( self.role, type(self.role), self.role is discord.Role )
        self.roleID = self.role.id
        self.pairingsChannel = discord.utils.get( guild.channels, name="match-pairings" )
        self.pairingsChannelID = self.pairingsChannel.id

    async def assignGuild( self, guild: discord.Guild ) -> str:
        print( f'The guild "{guild}" is being assigned to {self.name}.' )
        print( f'There are {len(self.players)} players in this tournament!\n' )
        self.guild = guild
        self.guildID = guild.id
        self.hostGuildName = guild.name
        self.pairingsChannel = guild.get_channel( self.pairingsChannelID )
        infoChannel = None
        if isinstance(self.infoMessageChannelID, int):
            infoChannel = self.guild.get_channel( self.infoMessageChannelID )
        if (not infoChannel is None) and isinstance(self.infoMessageID, int):
            self.infoMessage = await infoChannel.fetch_message( self.infoMessageID )
        if self.pairingsChannel is None:
            self.pairingsChannel = discord.utils.get( guild.channels, name="match-pairings" )
        if self.roleID != "":
            self.role = guild.get_role( self.roleID )
        for player in self.players:
            ID = player.getDiscordID()
            if ID != "":
                player.addDiscordUser( self.guild.get_member( ID ) )
        for mtch in self.matches:
            if mtch.roleID != "":
                mtch.addMatchRole( guild.get_role( mtch.roleID ) )
            if mtch.VC_ID != "":
                mtch.addMatchVC( guild.get_channel( mtch.VC_ID ) )

    async def updateInfoMessage( self ) -> None:
        if self.infoMessage is None:
            return
        await self.infoMessage.edit( embed = self.getTournamentStatusEmbed() )
        return

    def getPlayerByDiscordID( self, ID: int ) -> player:
        """ Gets a player by their Discord ID. """
        for plyr in self.players:
            if ID == plyr.discordID:
                return plyr
        return None

    def getPlayerByName( self, name: str ) -> player:
        """ Gets a player by their name. """
        for plyr in self.players:
            if name == plyr.name:
                return plyr
        return None

    def getPlayerByUUID( self, uuid: str ) -> player:
        """ Gets a player by their UUID (likely won't be used). """
        for plyr in self.players:
            if uuid == plyr.uuid:
                return plyr
        return None

    def getPlayer( self, identifier: str ) -> player:
        identifier = str( identifier )
        for plyr in self.players:
            if identifier == str(plyr.discordID):
                return plyr
            if identifier == plyr.name:
                return plyr
            if identifier == plyr.uuid:
                return plyr
        return None

    # ---------------- Property Accessors ----------------

    # Each tournament type needs a static method that will filter out valid properties
    # This used throughout the tournament and when adding server defaults
    def filterProperties( guild: discord.Guild, props: Dict ) -> Dict:
        digest: dict = { "successes": dict(), "failures": dict(), "undefined": dict() }
        for prop in props:
            props[prop] = str(props[prop])

            # Valid numbers here are strickly positive
            # And yes, this is safe. The second expression isn't evaluated if the first is false
            isValidNumber = props[prop].isnumeric() and int(props[prop]) > 0

            # Check for empty strings
            if props[prop] == "":
                pass
            elif prop == "format":
                # Not really sure what TODO here
                digest["successes"][prop] = props[prop]
            elif prop == "deck-count":
                if isValidNumber:
                    digest["successes"][prop] = int(props[prop])
                else:
                    digest["failures"][prop] = props[prop]
            elif prop == "match-length":
                # The length of a match needs to be an int
                if isValidNumber:
                    digest["successes"][prop] = int(props[prop]) * 60
                else:
                    digest["failures"][prop] = props[prop]
            elif prop == "match-size":
                # The number of people in a match needs to be an int
                if isValidNumber:
                    digest["successes"][prop] = int(props[prop])
                else:
                    digest["failures"][prop] = props[prop]
            elif prop == "pairings-channel":
                # The pairings channel properties should be an ID, which is an int
                # Also, the guild should have a channel whose ID is the given ID
                channelID = get_ID_from_mention( props[prop] )
                if channelID.isnumeric() and not (guild.get_channel( int(channelID) ) is None):
                    digest["successes"][prop] = guild.get_channel( int(channelID) )
                else:
                    digest["failures"][prop] = props[prop]
            elif prop == "standings-channel":
                # The standings channel properties should be an ID, which is an int
                # Also, the guild should have a channel whose ID is the given ID
                channelID = get_ID_from_mention( props[prop] )
                if channelID.isnumeric() and not (guild.get_channel( int(channelID) ) is None):
                    digest["successes"][prop] = guild.get_channel( int(channelID) )
                else:
                    digest["failures"][prop] = props[prop]
            elif prop == "tricebot-enabled":
                # This needs to be a bool
                if not ( str_to_bool(props[prop]) is None ):
                    digest["successes"][prop] = str_to_bool(props[prop])
                else:
                    digest["failures"][prop] = props[prop]
            elif prop == "spectators-allowed":
                # This needs to be a bool
                if not ( str_to_bool(props[prop]) is None ):
                    digest["successes"][prop] = str_to_bool(props[prop])
                else:
                    digest["failures"][prop] = props[prop]
            elif prop == "spectators-need-password":
                # This needs to be a bool
                if not ( str_to_bool(props[prop]) is None ):
                    digest["successes"][prop] = str_to_bool(props[prop])
                else:
                    digest["failures"][prop] = props[prop]
            elif prop == "spectators-can-chat":
                # This needs to be a bool
                if not ( str_to_bool(props[prop]) is None ):
                    digest["successes"][prop] = str_to_bool(props[prop])
                else:
                    digest["failures"][prop] = props[prop]
            elif prop == "spectators-can-see-hands":
                # This needs to be a bool
                if not ( str_to_bool(props[prop]) is None ):
                    digest["successes"][prop] = str_to_bool(props[prop])
                else:
                    digest["failures"][prop] = props[prop]
            elif prop == "only-registered":
                # This needs to be a bool
                if not ( str_to_bool(props[prop]) is None ):
                    digest["successes"][prop] = str_to_bool(props[prop])
                else:
                    digest["failures"][prop] = props[prop]
            elif prop == "player-deck-verification":
                # This needs to be a bool
                if not ( str_to_bool(props[prop]) is None ):
                    digest["successes"][prop] = str_to_bool(props[prop])
                else:
                    digest["failures"][prop] = props[prop]
            else:
                digest["undefined"][prop] = props[prop]

        return digest

    def getProperties( self ) -> Dict:
        digest: dict = { }
        digest["format"] = self.format
        digest["deck-count"] = self.deckCount
        digest["match-length"] = f'{int(self.matchLength/60)} min.'
        digest["match-size"] = self.playersPerMatch
        digest["pairings-channel"] = None if self.pairingsChannel is None else f'<#{self.pairingsChannel.id}>'
        digest["tricebot-enabled"] = self.triceBotEnabled if self.triceBotEnabled else None
        digest["spectators-allowed"] = self.spectators_allowed if self.spectators_allowed else None
        digest["spectators-need-password"] = self.spectators_need_password if self.spectators_need_password else None
        digest["spectators-can-chat"] = self.spectators_can_chat if self.spectators_can_chat else None
        digest["spectators-can-see-hands"] = self.spectators_can_see_hands if self.spectators_can_see_hands else None
        digest["only-registered"] = self.only_registered if self.only_registered else None
        digest["player-deck-verification"] = self.player_deck_verification if self.player_deck_verification else None
        return digest

    # Sets properties that can be changed directly by users
    # TODO: Consider a properies member instead of individual members (fixme)
    def setProperties( self, props: Dict, save: bool = False ) -> str:
        digest: str = ""

        if len(props) == 0:
            return digest

        filteredProps = tournament.filterProperties( self.guild, props )
        for prop in filteredProps["successes"]:
            if prop == "format":
                self.format = filteredProps["successes"][prop]
            elif prop == "deck-count":
                self.deckCount = filteredProps["successes"][prop]
            elif prop == "match-length":
                self.matchLength = filteredProps["successes"][prop]
            elif prop == "match-size":
                self.playersPerMatch = filteredProps["successes"][prop]
            elif prop == "pairings-channel":
                self.pairingsChannel = filteredProps["successes"][prop]
                self.pairingsChannelID = filteredProps["successes"][prop].id
            elif prop == "tricebot-enabled":
                self.triceBotEnabled = filteredProps["successes"][prop]
            elif prop == "spectators-allowed":
                self.spectators_allowed = filteredProps["successes"][prop]
            elif prop == "spectators-need-password":
                self.spectators_need_password = filteredProps["successes"][prop]
            elif prop == "spectators-can-chat":
                self.spectators_can_chat = filteredProps["successes"][prop]
            elif prop == "spectators-can-see-hands":
                self.spectators_can_see_hands = filteredProps["successes"][prop]
            elif prop == "only-registered":
                self.only_registered = filteredProps["successes"][prop]
            elif prop == "player-deck-verification":
                self.player_deck_verification = filteredProps["successes"][prop]

        if len(filteredProps["successes"]) == 0:
            digest += "No properties were successfully updated."
        else:
            digest += f'The following propert{"y was" if len(filteredProps["successes"]) == 1 else "ies were"} successfully updated:\n\t-'
            digest += "\n\t-".join( [ f'{p}: {props[p]}' for p in filteredProps["successes"] ] )
        if len(filteredProps["failures"]) > 0:
            digest += f'\n\nThere were errors in updating the following propert{"y was" if len(filteredProps["failures"]) == 1 else "ies"}:\n\t-'
            digest += "\n\t-".join( [ f'{p}: {props[p]}' for p in filteredProps["failures"] ] )
        if len(filteredProps["undefined"]) > 0:
            digest += f'\n\n{self.name} does not have the following propert{"y" if len(filteredProps["undefined"]) == 1 else "ies"}:\n\t-'
            digest += "\n\t-".join( [ f'{p}: {props[p]}' for p in filteredProps["undefined"] ] )
        
        if save:
            self.saveOverview( )

        return digest

    def updatePairingsThreshold( self, count: int ) -> str:
        return f'There is no pairings threshold is not defined for {self.name}'

    def getMatch( self, matchNum: int ) -> match:
        if matchNum > len(self.matches) + 1:
            return match( [] )
        if self.matches[matchNum - 1].matchNumber == matchNum:
            return self.matches[matchNum - 1]
        for mtch in self.matches:
            if mtch.matchNumber == matchNum:
                return mtch

    # ---------------- Misc ----------------

    # TODO: There should be a calculator class for this when more flexible
    # scoring systems are added
    def getStandings( self ) -> List[List]:
        rough = [ ]
        for plyr in self.players:
            if not plyr.isActive( ):
                continue
            if len(plyr.matches) == 0:
                continue
            # Match Points
            points = plyr.getMatchPoints()
            # Match Win Percentage
            MWP = plyr.getMatchWinPercentage( withBye=False )
            # Opponent Match Win Percentage
            OWP = 0.0
            if len(plyr.opponents) > 0:
                wins  = sum( [ opp.getNumberOfWins( ) for opp in plyr.opponents ] )
                games = sum( [len(opp.getCertMatches( withBye=False )) for opp in plyr.opponents] )
                if games != 0:
                    OWP = wins/games
                #OWP = sum( [ self.getPlayer(opp).getMatchWinPercentage( withBye=False ) for opp in plyr.opponents ] )/len(plyr.opponents)
            rough.append( (points, MWP, OWP, plyr) )

        # sort() is stable, so relate order similar elements is preserved
        rough.sort( key= lambda x: x[2], reverse=True )
        rough.sort( key= lambda x: x[1], reverse=True )
        rough.sort( key= lambda x: x[0], reverse=True )

        # Place, Player object, Points, MWP, OWP
        digest =  [ [ i+1 for i in range(len(rough))], \
                    [ i[3] for i in rough ], \
                    [ i[0] for i in rough ], \
                    [ i[1]*100 for i in rough ], \
                    [ i[2]*100 for i in rough ] ]

        return digest


    # ---------------- Embed Generators ----------------
    def getTournamentStatusEmbed( self ) -> discord.Embed:
        digest: discord.Embed = discord.Embed( title = f'{self.name} Status' )
        NL = "\n"
        NLT = "\n\t"

        props = self.getProperties()
        propsText = f'{self.name} has{"" if self.isActive() else " not"} started.\n' + "\n".join( [ f'{p}: {props[p]}' for p in props if not props[p] is None ] )
        digest.add_field( name="**Settings Info.**", value=propsText )

        plyrsWithDecks = [ p for p in self.players if len(p.decks) > 0 ]
        plyrsActive = [ p for p in self.players if p.isActive() ]
        decksText = f'There are {len(plyrsActive)} players registered.'
        if len(plyrsWithDecks) > 0:
            decksText = decksText[:-1] + f', and {len(plyrsWithDecks)} of them have submitted decks.'
        digest.add_field( name="**Player Count**", value=decksText )

        openMatches = [ m for m in self.matches if m.isOpen() ]
        uncertMatches = [ m for m in self.matches if m.isUncertified() ]
        matchText  = f'There are {len(openMatches)} open matches and {len(uncertMatches)} uncertified matches.'
        if len(openMatches) > 0:
            matchText += f'{NL}**Open Matches**:{NLT}{NLT.join([ "#" + str(m.matchNumber) for m in openMatches ])}'
        if len(uncertMatches) > 0:
            matchText += f'{NL}**Uncertified Matches**:{NLT}{NLT.join([ "#" + str(m.matchNumber) for m in uncertMatches ])}'
        digest.add_field( name="**Match Info.**", value=matchText )
        return digest

    def getPlayerProfileEmbed( self, plyr: str, mention: str ) -> discord.Embed:
        digest = commandResponse( )
        Plyr = self.getPlayer( plyr )
        if Plyr is None:
            digest.setContent( f'{mention}, {plyr!r} is not a player in {self.name}.' )
        else:
            embed = discord.Embed()
            bioInfo: str = f'Discord Name: {Plyr.getMention()}\n'
            discordID = Plyr.getDiscordID()
            if not discordID is None:
                bioInfo += f'Discord ID: {discordID}\n'
            if Plyr.triceName != "":
                bioInfo += f'Cockatrice Name: {Plyr.triceName}\n'
            bioInfo += f'Reg. Status: {"Registered" if Plyr.isActive() else "Dropped"}'
            embed.add_field( name="Biographic Info:", value=bioInfo )
            deckPairs = [ f'{d}: {Plyr.decks[d].deckHash}' for d in Plyr.decks ]
            embed.add_field( name="Decks:", value=("\u200b" + "\n".join(deckPairs)) )
            for mtch in Plyr.matches:
                players = mtch.activePlayers + mtch.droppedPlayers
                status = f'Status: {mtch.status}'
                if isinstance(mtch.winner, player):
                    winner = f'Winner: {Plyr.getMention()}'
                else:
                    winner = f'Winner: {mtch.winner}'
                Plyrs = [ player.getMention() for player in players if player != Plyr ]
                oppens = "Opponents: " + ", ".join( Plyrs )
                embed.add_field( name=f'Match #{mtch.matchNumber}', value=f'{status}\n{winner}\n{oppens}' )
            digest.setEmbed( embed )

        return digest

    async def getDeckEmbed( self, plyr: int, deckIdent: str, mention: str = "" ):
        digest = commandResponse( )
        Plyr = self.getPlayer( plyr )
        if Plyr is None:
            digest.setContent( f'{mention}, {plyr!r} is not registered for {self.name}.' )
        else:
            deckName = Plyr.getDeckIdent( deckIdent )
            if deckName == "":
                digest.setContent( f'{mention}, {Plyr.getMention()} does not have a deck whose name or hash is {deckIdent!r}.' )
            else:
                digest.setEmbed( Plyr.getDeckEmbed( deckName ) )

        return digest

    def getMatchEmbed( self, mtch: int ):
        digest = discord.Embed( )
        Match = self.matches[mtch]
        digest.add_field( name="Status", value=Match.status )
        digest.add_field( name="Active Players", value="\u200b" + ", ".join( [ plyr.getMention() for plyr in Match.activePlayers ] ) )
        if len(Match.droppedPlayers) != 0:
            digest.add_field( name="Dropped Players", value=", ".join( [ plyr.getMention() for plyr in Match.droppedPlayers ] ) )
        if not ( Match.isCertified() or Match.stopTimer ):
            t = round(Match.getTimeLeft( ) / 60)
            digest.add_field( name="Time Remaining", value=f'{t if t > 0 else 0} minutes' )
        if Match.winner != "":
            if isinstance(Match.winner, player):
                digest.add_field( name="Winner", value=Match.winner.getMention() )
            else:
                digest.add_field( name="Winner", value=Match.winner )
        if len(Match.confirmedPlayers) != 0:
            digest.add_field( name="Confirmed Players", value=", ".join( [ plyr.getMention() for plyr in Match.confirmedPlayers ] ) )

        if Match.triceMatch:
            digest.add_field( name="Tricebot Match", value = f'Replay at: {Match.replayURL}\nPlayer deck verification is {"enabled" if Match.playerDeckVerification else "disabled "}' )

        return digest

    # ---------------- Player Accessors ----------------
    def setPlayerTriceName( self, plyr: str, name: str ) -> str:
        Plyr = self.getPlayer( plyr )
        if Plyr is None:
            return f'you are not registered for {self.name}. Use the !register {self.name} to register for this tournament.'
        if not Plyr.isActive():
            return f'you are registered by are not an active player in {self.name}. If you believe this is an error, contact tournament staff.'
        self.getPlayer(plyr).triceName = name
        self.getPlayer(plyr).saveXML( )
        return f'Your cockatrice name was set to {name} successfully.'

    async def addDeck( self, plyr: str, deckName: str, decklist: str ) -> str:
        Plyr = self.getPlayer( plyr )
        if not self.regOpen:
            return f'registration for {self.name} is closed, so you cannot submit a deck. If you believe this is an error, contact tournament staff.'
        if Plyr is None:
            return f'you are not registered for {self.name}. Use the !register {self.name} to register for this tournament.'
        if not Plyr.isActive():
            return f'you are registered by are not an active player in {self.name}. If you believe this is an error, contact tournament staff.'
        Plyr.addDeck( deckName, decklist )
        Plyr.saveXML( )
        deckHash = self.getPlayer(plyr).decks[deckName].deckHash

        message = f'your deck has been successfully registered in {self.name}. Your deck name is "{deckName}", and the deck hash is "{deckHash}". Make sure it matches your deck hash in Cockatrice. You can see your decklist by using !decklist "{deckName}" or !decklist {deckHash}.'
        if isMoxFieldLink(decklist) or isTappedOutLink(decklist) or isMtgGoldfishLink(decklist):
            message += f'\nPlease be aware that this website treats your commander as if it were in your mainboard.'
        await self.updateInfoMessage( )
        return message

    async def addDeckAdmin( self, plyr: str, deckName: str, decklist: str, mention: str ) -> str:
        """ Adds a deck to player from the admin's interface. """
        digest = commandResponse( )
        Plyr = self.getPlayer( plyr )
        if Plyr is None:
            digest.setContent( f'{mention}, {plyr!r} is not registered for {self.name}. Use the !admin-register {self.name} {plyr!r} to register them.' )
        elif not Plyr.isActive():
            digest.setContent( f'{mention}, {plyr} is not an active in {self.name}.' )
        else:
            Plyr.addDeck( deckName, decklist )
            Plyr.saveXML( )
            deckHash = Plyr.decks[deckName].deckHash
            await Plyr.sendMessage( content = f'A decklist has been submitted for {self.name} on your behalf. The name of the deck is "{deckName}" and the deck hash is "{deckHash}". Use the command "!decklist {deckName}" to see the list. Please contact tournament staff if there is an error.' )
            await self.updateInfoMessage( )
            digest.setContent( f'{mention}, you have submitted a decklist for {plyr}. The deck hash is {deckHash}.' )

        return digest

    async def removeDeck( self, plyr: int, deckName: str = "", author: str = "" ) -> commandResponse:
        digest = commandResponse( )
        Plyr = self.getPlayer( plyr )
        if Plyr is None:
            digest.setContent( f'<@{plyr}>, you are not registered for {self.name}.' )
        elif not Plyr.isActive():
            digest.setContent( f'<@{plyr}>, you are not an active player in {self.name}.' )
        else:
            digest.setContent( await Plyr.removeDeck( deckName ) )
            await self.updateInfoMessage()

        return digest

    async def removeDeckAdmin( self, plyr: int, deckName: str, mention: str) -> commandResponse:
        digest = commandResponse( )
        Plyr = self.getPlayer( plyr )
        if Plyr is None:
            digest.setContent( f'{mention}, {plyr!r} is not registered for {self.name}.' )
        elif not Plyr.isActive():
            digest.setContent( f'{mention}, {Plyr.getMention()} is not an active player in {self.name}.' )
        else:
            digest.setContent( await Plyr.removeDeckAdmin( deckName, mention ) )
            await self.updateInfoMessage()

        return digest


    # ---------------- Tournament Status ----------------

    def setRegStatus( self, status: bool ) -> str:
        if not ( self.tournEnded or self.tournCancel ):
            self.regOpen = status
            return ""
        elif self.tournEnded:
            return "This tournament has already ended. As such, registeration can't be opened."
        elif self.tournCancel:
            return "This tournament has been cancelled. As such, registeration can't be opened."

    def startTourn( self ) -> str:
        if not (self.tournStarted or self.tournEnded or self.tournCancel):
            self.tournStarted = True
            self.regOpen = False
            return ""
        elif self.tournEnded:
            return "This tournament has already ended. As such, it can't be started."
        elif self.tournCancel:
            return "This tournament has been cancelled. As such, it can't be started."

    async def purgeTourn( self ) -> None:
        for match in self.matches:
            match.stopTimer = True
            if type( match.VC ) == discord.VoiceChannel:
                try:
                    await match.VC.delete( )
                except:
                    pass
            if type( match.role ) == discord.Role:
                try:
                    await match.role.delete( )
                except:
                    pass
        if type( self.role ) == discord.Role:
            try:
                await self.role.delete( )
            except:
                pass

    async def endTourn( self, adminMention: str = "", author: str = "" ) -> str:
        if not self.tournStarted:
            return f'{self.name} has not started, so it cannot be ended. However, it can be cancelled.'
        await self.purgeTourn( )
        self.tournEnded = False
        self.saveTournament( f'closedTournaments/{self.name}' )
        if os.path.isdir( f'currentTournaments/{self.name}' ):
            shutil.rmtree( f'currentTournaments/{self.name}' )
        await self.updateInfoMessage()
        return f'{adminMention}, {self.name} has been closed by {author}.'

    async def cancelTourn( self, adminMention: str = "", author: str = "") -> str:
        await self.purgeTourn( )
        oldLocation = self.getSaveLocation()
        self.tournCancel = True
        self.saveTournament( )
        if os.path.isdir( oldLocation ):
            shutil.rmtree( oldLocation )
        await self.updateInfoMessage()
        return f'{adminMention}, {self.name} has been cancelled by {author}.'

    # ---------------- Player Management ----------------

    async def prunePlayers( self, ctx ) -> str:
        digest = commandResponse( )
        await ctx.send( f'Pruning players starting. This may take some time...' )
        for plyr in self.players:
            # TODO: This needs to be generalized. Not all tournament require a deck. There will also be a check-in feature eventually.
            # This should check if the player is ready to play.
            if len(plyr.decks) == 0:
                await self.dropPlayer( plyr.name )
                await ctx.send( f'{plyr.getMention()} has been pruned.' )
                await plyr.sendMessage( content=f'You did not complete registration for {self.name}, so you have been dropped by tournament staff. If you believe this is an error, contact them immediately.' )
                plyr.saveXML( )
        await self.updateInfoMessage( )
        digest.setContent( f'All players that did not submit a deck have been pruned.' )
        return digest

    async def addPlayer( self, discordUser ) -> str:
        if not self.regOpen:
            return f'{discordUser.mention}, registration for the tounament is closed. If you believe this to be incorrect, please contact the tournament staff.'
        if self.tournCancel:
            return f'{discordUser.mention}, this tournament has been cancelled. If you believe this to be incorrect, please contact the tournament staff.'
        if self.tournEnded:
            return f'{discordUser.mention}, this tournament has already ended. If you believe this to be incorrect, please contact the tournament staff.'
        RE = ""
        plyr = self.getPlayer( str(discordUser.id) )
        if ( not plyr is None ) and plyr.isActive( ):
            return f'{plyr.getMention()}, you are already an active player in {self.name}.'
        elif not plyr is None:
            plyr.activate()
            RE = "re-"
        else:
            plyr = player( discordUser.display_name, discordUser.id )
            self.players.append( plyr )

        plyr.saveLocation = f'{self.getSaveLocation()}/players/{plyr.uuid}.xml'
        plyr.addDiscordUser( discordUser )
        await plyr.addRole( self.role )
        plyr.saveXML( )
        await self.updateInfoMessage( )
        return f'{discordUser.mention}, you have been {RE}registered in {self.name}!'

    async def addPlayerAdmin( self, discordUser, mention: str ) -> str:
        digest = commandResponse( )
        RE = ""
        plyr = self.getPlayer( discordUser.id )
        if ( not plyr is None ) and plyr.isActive( ):
            digest.setContent( f'{mention}, {plyr.getMention()} is already an active player in {self.name}.' )
            return digest
        elif not plyr is None:
            plyr.activate()
            RE = "re-"
        else:
            plyr = player( discordUser.display_name, discordUser.id )
            self.players.append( plyr )

        plyr.saveLocation = f'{self.getSaveLocation()}/players/{toSafeXML(plyr.uuid)}.xml'
        plyr.addDiscordUser( discordUser )
        await plyr.addRole( self.role )
        plyr.saveXML( )
        await plyr.sendMessage( content=f'You have been registered for {self.name} by tournament staff!' )
        await self.updateInfoMessage( )
        digest.setContent( f'{mention}, you have {RE}registered {plyr.getMention()} for {self.name}.' )
        return digest

    async def addDummyPlayer( self, playerName, mention: str ) -> str:
        """ Adds a player without a discord user object to the tournament. """
        digest = commandResponse( )
        plyr = self.getPlayer( playerName )
        RE = ""
        if ( not plyr is None ) and plyr.isActive( ):
            digest.setContent( f'{mention}, {plyr.getMention()} is already an active player in {self.name}.' )
        elif not plyr is None:
            plyr.activate()
            RE = "re-"
        else:
            plyr = player( playerName, None )
            self.players.append( plyr )

        plyr.saveLocation = f'{self.getSaveLocation()}/players/{playerName}.xml'
        plyr.saveXML( )
        digest.setContent( f'{mention}, {plyr.getMention()} has been {RE}registered for {self.name}.' )
        await self.updateInfoMessage( )
        return digest

    async def dropPlayer( self, plyr: str ) -> commandResponse:
        Plyr = self.getPlayer( plyr )
        digest = commandResponse( )
        if Plyr is None:
            digest.setContent( f'<@{plyr}>, you are not registered for {self.name}.' )
        elif not Plyr.isActive():
            digest.setContent( f'{Plyr.getMention()}, you are not an active player in {self.name}.' )
        else:
            await Plyr.removeRole( self.role )
            await Plyr.drop( )
            Plyr.saveXML()
            digest.setContent( f'<@{plyr}>, you have been dropped from {self.name}.' )
            await self.removePlayerFromQueue( plyr )

        return digest

    async def dropPlayerAdmin( self, plyr: str, mention: str ) -> Dict:
        digest = commandResponse( )
        Plyr = self.getPlayer( plyr )
        if Plyr is None:
            digest.setContent( f'{mention}, {plyr!r} is not registered for {self.name}.' )
        elif not Plyr.isActive():
            digest.setContent( f'{mention}, {Plyr.getMention()} is not an active player in {self.name}.' )
        else:
            # TODO: Dropping a player should remove the role
            await Plyr.removeRole( self.role )
            await Plyr.drop( )
            Plyr.saveXML()
            await self.removePlayerFromQueue( Plyr )
            await self.updateInfoMessage( )
            await Plyr.sendMessage( content=f'You have been dropped from {self.name} on {self.guild.name} by tournament staff. If you believe this is an error, check with them.' )
            digest.setContent( f'{mention}, {Plyr.getMention()} has been dropped from {self.name}.' )

        return digest

    async def playerConfirmResult( self, plyr: str ) -> commandResponse:
        digest = commandResponse( )
        Plyr = self.getPlayer( plyr )
        if Plyr is None:
            digest.setContent( f'<@{plyr}>, you are not registered for {self.name}.' )
        elif not Plyr.isActive( ):
            digest.setContent( f'{Plyr.getMention()}, you are not an active player in {self.name}.' )
        elif not Plyr.hasOpenMatch( ):
            digest.setContent( f'{Plyr.getMention()}, the results of all your matches are certified.' )
        else:
            mtch = Plyr.findOpenMatch( )
            message = await mtch.confirmResult( Plyr )
            if "announcement" in message:
                await self.pairingsChannel.send( message["announcement"] )
                digest.setContent( message["message"] )
            await self.updateInfoMessage( )
            mtch.saveXML( )

        return digest

    async def playerConfirmResultAdmin( self, plyr: str, matchNum: int, mention: str ) -> commandResponse:
        digest = commandResponse( )
        Plyr = self.getPlayer( plyr )
        if Plyr is None:
            digest.setContent( f'{mention}, there is not a player by {plyr!r} registered for {self.name}.' )
        elif not Plyr.isActive( ):
            digest.setContent( f'{mention}, {Plyr.getMention()} is not an active player in {self.name}.' )
        elif not Plyr.hasOpenMatch( ):
            digest.setContent( f'{mention}, all the matches that {Plyr.getMention()} is a part of are certified.' )
        else:
            # TODO: This should use the getMatch method
            message = await self.matches[matchNum - 1].confirmResultAdmin( Plyr, mention )
            digest.setContent( message["message"] )
            self.matches[matchNum - 1].saveXML( )
            await self.updateInfoMessage( )
            if "announcement" in message:
                await self.pairingsChannel.send( content=message["announcement"] )

        return digest

    async def recordMatchResult( self, plyr: str, result: str ) -> commandResponse:
        digest = commandResponse( )
        Plyr = self.getPlayer( plyr )
        if Plyr is None:
            digest.setContent( f'<@{plyr}>, you are not registered for {self.name}.' )
        elif not Plyr.isActive( ):
            digest.setContent( f'<@{plyr}>, you are not an active player in {self.name}.' )
        elif not Plyr.hasOpenMatch( ):
            digest.setContent( f'<@{plyr}>, the results of all your matches are certified.' )
        else:
            mtch = Plyr.findOpenMatch( )
            message = await mtch.recordResult( Plyr, result )
            digest.setContent( message["message"] )
            mtch.saveXML( )
            await self.updateInfoMessage( )
            if "announcement" in message:
                await self.pairingsChannel.send( content=message["announcement"] )

        return digest

    async def recordMatchResultAdmin( self, plyr: str, result: str, matchNum: int, mention: str ) -> commandResponse:
        digest = commandResponse( )
        Plyr = self.getPlayer( plyr )
        if Plyr is None:
            digest.setContent( f'{mention}, there is not a player by {plyr!r} registered for {self.name}.' )
        elif not Plyr.isActive( ):
            digest.setContent( f'{mention}, {Plyr.getMention()} is not an active player in {self.name}.' )
        elif not Plyr.hasOpenMatch( ):
            digest.setContent( f'{mention}, all the matches that {Plyr.getMention()} is a part of are certified.' )
        else:
            # TODO: This should use the getMatch method
            message = await self.matches[matchNum - 1].recordResultAdmin( Plyr, result, mention )
            digest.setContent( message["message"] )
            self.matches[matchNum - 1].saveXML( )
            await self.updateInfoMessage( )
            if "announcement" in message:
                await self.pairingsChannel.send( content=message["announcement"] )

        return digest

    async def pruneDecks( self, ctx ) -> str:
        digest = commandResponse( )
        await ctx.send( f'Pruning decks starting. This may take some time...' )
        for plyr in self.players:
            deckIdents = [ ident for ident in plyr.decks ]
            while len( plyr.decks ) > self.deckCount:
                del( plyr.decks[deckIdents[0]] )
                await ctx.send( f'The deck {deckIdents[0]!r} belonging to {plyr.getMention()} has been pruned.' )
                await plyr.sendMessage( content=f'You submitted too many decks for {self.name}, so your deck {deckIdents[0]!r} has been pruned by tournament staff.' )
                del( deckIdents[0] )
            plyr.saveXML( )
        await self.updateInfoMessage()
        digest.setContent( f'Decks have been pruned. All players have at most {self.deckCount} deck{"" if self.deckCount == 1 else "s"}.' )
        return digest

    # ---------------- Match Management ----------------
    async def _sendMatchWarning( self, msg: str ) -> None:
        await self.pairingsChannel.send( content=msg )

    def _launch_match_warning( self, msg: str ) -> None:
        if self.loop.is_running( ):
            fut_send = asyncio.run_coroutine_threadsafe( self._sendMatchWarning(msg), self.loop )
            fut_send.result( )
        else:
            self.loop.run_until_complete( self._sendMatchWarning(msg) )

    def _matchTimer( self, mtch: match, t: int = -1 ) -> None:
        if t == -1:
            t = self.matchLength

        while mtch.getTimeLeft() > 0 and not mtch.stopTimer:
            sleep( 1 )
            if mtch.getTimeLeft() <= 60 and not mtch.sentOneMinWarning and not mtch.stopTimer:
                    task = threading.Thread( target=self._launch_match_warning, args=(f'{mtch.getMention()}, you have one minute left in your match.',) )
                    task.start( )
                    mtch.sentOneMinWarning = True
                    mtch.saveXML( )
            elif mtch.getTimeLeft() <= 300 and not mtch.sentFiveMinWarning and not mtch.stopTimer:
                    task = threading.Thread( target=self._launch_match_warning, args=(f'{mtch.getMention()}, you have five minutes left in your match.',) )
                    task.start( )
                    mtch.sentFiveMinWarning = True
                    mtch.saveXML( )

        if not mtch.stopTimer and not mtch.sentFinalWarning:
            task = threading.Thread( target=self._launch_match_warning, args=(f'{mtch.getMention()}, time in your match is up!!',) )
            task.start( )
            task.join( )
            mtch.sentFinalWarning = True
        mtch.saveXML( )

    async def addMatch( self, plyrs: List ) -> None:
        print( "Creating a new match." )
        newMatch = match( plyrs )
        self.matches.append( newMatch )
        newMatch.matchNumber = len(self.matches)
        newMatch.matchLength = self.matchLength
        newMatch.saveLocation = f'{self.getSaveLocation()}/matches/match_{newMatch.matchNumber}.xml'
        newMatch.timer = threading.Thread( target=self._matchTimer, args=(newMatch,) )
        # TODO: Why is this being checked...
        if isinstance( self.guild, discord.Guild ):
            matchRole = await self.guild.create_role( name=f'Match {newMatch.matchNumber}' )
            overwrites = { self.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                           getAdminRole(self.guild): discord.PermissionOverwrite(read_messages=True),
                           getJudgeRole(self.guild): discord.PermissionOverwrite(read_messages=True),
                           matchRole: discord.PermissionOverwrite(read_messages=True) }
            matchCategory = discord.utils.get( self.guild.categories, name="Matches" )
            if len(matchCategory.channels) >= 50:
                matchCategory = category=discord.utils.get( self.guild.categories, name="More Matches" )

            game_name: str = f'{self.name} Match {newMatch.matchNumber}'

            newMatch.VC    = await matchCategory.create_voice_channel( name=game_name, overwrites=overwrites )
            newMatch.role  = matchRole

            message = f'\n{matchRole.mention} of {self.name}, you have been paired. A voice channel has been created for you. Below is information about your opponents.\n'
            embed   = discord.Embed( )

            if self.triceBotEnabled:
                #This causes the replay to get saved into a folder
                game_name: str = f'{self.name}/Match {newMatch.matchNumber}'

                #Try to create the game
                creation_success: bool = False
                replay_download_link: str = ""
                game_id: int = -1
                tries: int = 0
                max_tries: int = 3

                game_password: str = "game-" + str(newMatch.matchNumber)

                playerNames = []
                deckHashes = []
                if self.player_deck_verification:
                    for plyr in plyrs:
                        name = self.getPlayer(plyr).triceName
                        if name == "" or name is None:
                            name = "*"
                        playerNames.append(name)
                        deckHashes.append( [dck.deckHash for dck in self.getPlayer(plyr).decks.values()] )

                #Try up to three times
                while not creation_success and tries < max_tries:
                    game_made = trice_bot.createGame(game_name, game_password, len(plyrs), self.spectators_allowed, self.spectators_need_password, self.spectators_can_chat, self.spectators_can_see_hands, self.only_registered, self.player_deck_verification, playerNames, deckHashes)

                    creation_success = game_made.success
                    replay_download_link = trice_bot.getDownloadLink(game_made.replayName)
                    game_id = game_made.gameID
                    tries += 1

                if creation_success:
                    #Game was made
                    newMatch.triceMatch = True
                    newMatch.gameID = game_id
                    newMatch.replayURL = replay_download_link

                    if self.player_deck_verification:
                        newMatch.playerDeckVerification = True

                    message += f'A cockatrice game was automatically made for you it is called {game_name}'
                    message += f' and has a password of "`{game_password}`"\n'

                    #TODO: move replay download link? (fixme)
                    message += f'Replay download link {replay_download_link} (available on game end).\n'
                else:
                    #Game was not made due to an error with tricebot
                    message += f"A cockatrice game was not automatically made for you. The status of tricebot can be found here: {EXTERN_URL}/status.\n"

        for plyr in plyrs:
            # TODO: This should be unready player
            await self.removePlayerFromQueue( plyr )
            plyr.matches.append( newMatch )
            for p in plyrs:
                plyr.addOpponent( p )
            if type( self.guild ) == discord.Guild:
                await plyr.addRole( matchRole )
                embed.add_field( name=plyr.getDisplayName(), value=plyr.pairingString() )

        for plyr in plyrs:
            plyr.saveXML()

        if type( self.guild ) is discord.Guild:
            await self.pairingsChannel.send( content=message, embed=embed )

        newMatch.timer.start()
        newMatch.saveXML()
        await self.updateInfoMessage()

    # See tricebot.py for retun details
    # copy pasta of them is here. accurate as of 25/04/21

    #  1 if success
    #  0 auth token is bad or error404 or network issue
    # -1 if player not found
    # -2 if an unknown error occurred
    def kickTricePlayer(self, a_matchNum, playerName):
        match = self.matches[a_matchNum - 1]
        return trice_bot.kickPlayer(match.gameID, playerName)

    async def addBye( self, plyr: str, mention: str ) -> None:
        digest = commandResponse( )
        Plyr = self.getPlayer( plyr )
        if Plyr is None:
            digest.setContent( f'{mention}, {plyr!r} is not registered for {self.name}.' )
        elif not Plyr.isActive():
            digest.setContent( f'{mention}, {Plyr.getMention()} is not an active player in {self.name}.' )
        elif Plyr.hasOpenMatch( ):
            digest.setContent( f'{mention}, {Plyr.getMention()} has a open match that needs certified before they can be given a bye.' )
        else:
            await self.removePlayerFromQueue( Plyr )
            newMatch = match( [ Plyr ] )
            newMatch.matchNumber = len(self.matches)
            newMatch.saveLocation = f'{self.getSaveLocation()}/matches/match_{newMatch.matchNumber}.xml'
            newMatch.recordBye( )
            self.matches.append( newMatch )
            Plyr.matches.append( newMatch )
            newMatch.saveXML( )
            Plyr.saveXML( )
            await self.updateInfoMessage( )
            await Plyr.sendMessage( f'You have been given a bye from tournament staff of {self.name}.' )
            digest.setContent( f'{mention}, {Plyr.getMention()} has been given a bye.' )

        return digest

    async def removeMatch( self, matchNum: int, author: str = "" ) -> str:
        digest = commandResponse( )
        if self.matches[matchNum - 1] != matchNum:
            self.matches.sort( key=lambda x: x.matchNumber )

        # TODO: This is one of several places where player references in matches would be very helpful
        for plyr in self.matches[matchNum - 1].activePlayers:
            Plyr = self.getPlayer( plyr )
            await Plyr.removeMatch( matchNum )
            await Plyr.sendMessage( content=f'You were a particpant in match #{matchNum} in the tournament {self.name}. This match has been removed by tournament staff. If you think this is an error, contact them.' )
        for plyr in self.matches[matchNum - 1].droppedPlayers:
            Plyr = self.getPlayer( plyr )
            await Plyr.removeMatch( matchNum )
            await Plyr.sendMessage( content=f'You were a particpant in match #{matchNum} in the tournament {self.name} on the server {self.hostGuildName}. This match has been removed by tournament staff. If you think this is an error, contact them.' )

        await self.matches[matchNum - 1].killMatch( )
        self.matches[matchNum - 1].saveXML( )

        await self.updateInfoMessage()
        digest.setContent( f'{author}, match #{matchNum} has been removed.' )
        return digest


    # ---------------- Matchmaking Queue Methods ----------------

    # There will be a far more sofisticated pairing system in the future. Right now, the dummy version will have to do for testing
    # This is a prime canidate for adjustments when players how copies of match results.
    def addPlayerToQueue( self, plyr: str ) -> str:
        return f'{self.name} does not have a matchmaking queue.'

    async def removePlayerFromQueue( self, plyr: str ) -> str:
        return f'{self.name} does not have a matchmaking queue.'


    # ---------------- XML Saving/Loading ----------------
    # Most of these are also universally defined, but are for a particular purpose

    def saveTournament( self, dirName: str = "" ) -> None:
        dirName = dirName.replace("../", "")
        #Check on folder creation, event though input should be safe
        if dirName == "":
            dirName = self.getSaveLocation()
        if not (os.path.isdir( f'{dirName}' ) and os.path.exists( f'{dirName}' )):
            os.mkdir( f'{dirName}' )
        self.saveTournamentType( f'{dirName}/tournamentType.xml' )
        self.saveOverview( f'{dirName}/overview.xml' )
        self.saveMatches( dirName )
        self.savePlayers( dirName )

    def saveTournamentType( self, filename: str = "" ):
        print( "No tournament type being saved." )
        return None

    def _getInnerXMLString( self ) -> str:
        digest  = f'\t<uuid>{self.uuid}</uuid>'
        digest += f'\t<name>{self.name}</name>\n'
        digest += f'\t<guild id="{self.guild.id}">{self.hostGuildName}</guild>\n'
        digest += f'\t<role id="{self.role.id}"/>\n'
        digest += f'\t<pairingsChannel id="{self.pairingsChannel.id}"/>\n'
        if not self.infoMessage is None:
            digest += f'\t<infoMessage channel="{self.infoMessage.channel.id}" id="{self.infoMessage.id}"/>\n'
        digest += f'\t<format>{self.format}</format>\n'
        digest += f'\t<regOpen>{self.regOpen}</regOpen>\n'
        digest += f'\t<status started="{self.tournStarted}" ended="{self.tournEnded}" canceled="{self.tournCancel}"/>\n'
        digest += f'\t<deckCount>{self.deckCount}</deckCount>\n'
        digest += f'\t<matchSize>{self.playersPerMatch}</matchSize>\n'
        digest += f'\t<matchLength>{self.matchLength}</matchLength>\n'
        digest += f'\t<triceBotEnabled>{self.triceBotEnabled}</triceBotEnabled>\n'
        digest += f'\t<spectatorsAllowed>{self.spectators_allowed}</spectatorsAllowed>\n'
        digest += f'\t<spectatorsNeedPassword>{self.spectators_need_password}</spectatorsNeedPassword>\n'
        digest += f'\t<spectatorsCanChat>{self.spectators_can_chat}</spectatorsCanChat>\n'
        digest += f'\t<spectatorsCanSeeHands>{self.spectators_can_see_hands}</spectatorsCanSeeHands>\n'
        digest += f'\t<onlyRegistered>{self.only_registered}</onlyRegistered>\n'
        digest += f'\t<playerDeckVerification>{self.player_deck_verification}</playerDeckVerification>\n'
        return digest

    def saveOverview( self, filename: str = "" ) -> None:
        if filename == "":
            filename = f'{self.getSaveLocation()}overview.xml'
        with open( filename, 'w' ) as xmlfile:
            xmlfile.write( "<?xml version='1.0'?>\n" )
            xmlfile.write( "<tournament>\n" )
            xmlfile.write( toSafeXML(self._getInnerXMLString()) )
            xmlfile.write( "</tournament>" )

    def savePlayers( self, dirName: str = "" ) -> None:
        if dirName == "":
            dirName = self.getSaveLocation()
        if not (os.path.isdir( f'{dirName}/players/' ) and os.path.exists( f'{dirName}/players/' )):
           os.mkdir( f'{dirName}/players/' )

        for player in self.players:
            player.saveXML( f'{dirName}/players/{toPathSafe(player.uuid)}.xml' )

    def saveMatches( self, dirName: str = "" ) -> None:
        if dirName == "":
           dirName = self.getSaveLocation()
        if not (os.path.isdir( f'{dirName}/matches/' ) and os.path.exists( f'{dirName}/matches/' )):
           os.mkdir( f'{dirName}/matches/' )

        for match in self.matches:
            match.saveXML( f'{dirName}/matches/match_{match.matchNumber}.xml' )

    def loadTournament( self, dirName: str ) -> None:
        self.loadPlayers( f'{dirName}/players/' )
        self.loadOverview( f'{dirName}/overview.xml' )
        self.loadMatches( f'{dirName}/matches/' )

    def loadOverview( self, filename: str ) -> None:
        xmlTree = ET.parse( filename )
        tournRoot = xmlTree.getroot()
        self.uuid = fromXML(tournRoot.find( 'uuid' ).text)
        self.name = fromXML(tournRoot.find( 'name' ).text)
        self.guildID   = int( fromXML(tournRoot.find( 'guild' ).attrib["id"]) )
        self.roleID    = int( fromXML(tournRoot.find( 'role' ).attrib["id"]) )
        self.pairingsChannelID = int( fromXML(tournRoot.find( 'pairingsChannel' ).attrib["id"]) )
        if not tournRoot.find( 'infoMessage' ) is None:
            self.infoMessageChannelID = int( fromXML(tournRoot.find( 'infoMessage' ).attrib["channel"]) )
            self.infoMessageID = int( fromXML(tournRoot.find( 'infoMessage' ).attrib["id"]) )

        self.format    = fromXML(tournRoot.find( 'format' ).text)
        self.deckCount = int( fromXML(tournRoot.find( 'deckCount' ).text) )

        self.playersPerMatch = int( fromXML(tournRoot.find("matchSize").text) )
        self.matchLength     = int( fromXML(tournRoot.find("matchLength").text) )

        self.regOpen      = str_to_bool( fromXML(tournRoot.find( 'regOpen' ).text ))
        self.tournStarted = str_to_bool( fromXML(tournRoot.find( 'status' ).attrib['started'] ))
        self.tournEnded   = str_to_bool( fromXML(tournRoot.find( 'status' ).attrib['ended'] ))
        self.tournCancel  = str_to_bool( fromXML(tournRoot.find( 'status' ).attrib['canceled'] ))

        self.triceBotEnabled = str_to_bool( fromXML(tournRoot.find( "triceBotEnabled" ).text ) )
        self.spectators_allowed = str_to_bool( fromXML(tournRoot.find( "spectatorsAllowed" ).text ) )
        self.spectators_need_password = str_to_bool( fromXML(tournRoot.find( "spectatorsNeedPassword" ).text ) )
        self.spectators_can_chat = str_to_bool( fromXML(tournRoot.find( "spectatorsCanChat" ).text ) )
        self.spectators_can_see_hands = str_to_bool( fromXML(tournRoot.find( "spectatorsCanSeeHands" ).text ) )
        self.only_registered = str_to_bool( fromXML(tournRoot.find( "onlyRegistered" ).text ) )
        self.player_deck_verification = str_to_bool( fromXML(tournRoot.find( "playerDeckVerification" ).text ) )

    def loadPlayers( self, dirName: str ) -> None:
        playerFiles = [ f'{dirName}/{f}' for f in os.listdir(dirName) if os.path.isfile( f'{dirName}/{f}' ) ]
        for playerFile in playerFiles:
            print( playerFile )
            newPlayer = player( "" )
            newPlayer.loadXML( playerFile )
            self.players.append( newPlayer )

    def loadMatches( self, dirName: str ) -> None:
        matchFiles = [ f'{dirName}/{f}' for f in os.listdir(dirName) if os.path.isfile( f'{dirName}/{f}' ) ]
        for matchFile in matchFiles:
            newMatch = match( [] )
            newMatch.saveLocation = matchFile
            newMatch.loadXML( matchFile )
            newMatch.activePlayers = [ self.getPlayer(plyr) for plyr in newMatch.activePlayers ]
            newMatch.droppedPlayers = [ self.getPlayer(plyr) for plyr in newMatch.droppedPlayers ]
            newMatch.confirmedPlayers = [ self.getPlayer(plyr) for plyr in newMatch.confirmedPlayers ]
            winner = self.getPlayer( newMatch.winner )
            if isinstance( winner, player ):
                newMatch.winner = winner
            self.matches.append( newMatch )
            for aPlayer in newMatch.activePlayers:
                aPlayer.addMatch( newMatch )
            for dPlayer in newMatch.droppedPlayers:
                dPlayer.addMatch( newMatch )
            if not ( self.matches[-1].isCertified() or self.matches[-1].isDead() ) and not self.matches[-1].stopTimer:
                self.matches[-1].timer = threading.Thread( target=self._matchTimer, args=(self.matches[-1],) )
                self.matches[-1].timer.start( )
        self.matches.sort( key= lambda x: x.matchNumber )
        for plyr in self.players:
            plyr.matches.sort( key= lambda x: x.matchNumber )



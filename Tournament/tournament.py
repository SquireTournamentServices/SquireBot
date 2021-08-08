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
from .utils import *
from .match import match
from .player import player
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

        self.matches = []

        #Create bot class and store the game creation settings
        self.triceBotEnabled = False
        self.spectators_allowed = False
        self.spectators_need_password = False
        self.spectators_can_chat = False
        self.spectators_can_see_hands = False
        self.only_registered = False
        self.player_deck_verification = False

        if len(props) != 0:
            self.setProperties(props)

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

    def getPlayer( self, identifier ) -> player:
        for plyr in self.players:
            if identifier == plyr.discordID:
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
    def setProperties( self, props: Dict ) -> str:
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
                wins  = sum( [ self.getPlayer(opp).getNumberOfWins( ) for opp in plyr.opponents ] )
                games = sum( [len(self.getPlayer(opp).getCertMatches( withBye=False )) for opp in plyr.opponents] )
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

    def getPlayerProfileEmbed( self, plyr: int ) -> discord.Embed:
        Player = self.getPlayer( plyr )
        digest = discord.Embed()
        bioInfo: str = f'Discord Name: {Player.getMention()}\n'
        discordID = Player.getDiscordID()
        if not discordID is None:
            bioInfo += f'Discord ID: {discordID}\n'
        if Player.triceName != "":
            bioInfo += f'Cockatrice Name: {Player.triceName}\n'
        bioInfo += f'Reg. Status: {"Registered" if Player.isActive() else "Dropped"}'
        digest.add_field( name="Biographic Info:", value=bioInfo )
        deckPairs = [ f'{d}: {Player.decks[d].deckHash}' for d in Player.decks ]
        digest.add_field( name="Decks:", value=("\u200b" + "\n".join(deckPairs)) )
        for mtch in Player.matches:
            players = mtch.activePlayers + mtch.droppedPlayers
            status = f'Status: {mtch.status}'
            if mtch.winner in self.players:
                winner = f'Winner: {self.getPlayer(mtch.winner).getMention()}'
            else:
                winner = f'Winner: {mtch.winner if mtch.winner else "N/A"}'
            oppens = "Opponents: " + ", ".join( [ f'<@{player}>' for player in players if player != plyr ] )
            digest.add_field( name=f'Match #{mtch.matchNumber}', value=f'{status}\n{winner}\n{oppens}' )
        return digest

    def getMatchEmbed( self, mtch: int ):
        digest = discord.Embed( )
        Match = self.matches[mtch]
        digest.add_field( name="Status", value=Match.status )
        digest.add_field( name="Active Players", value="\u200b" + ", ".join( [ self.getPlayer(plyr).getMention() for plyr in Match.activePlayers ] ) )
        if len(Match.droppedPlayers) != 0:
            digest.add_field( name="Dropped Players", value=", ".join( [ self.getPlayer(plyr).getMention() for plyr in Match.droppedPlayers ] ) )
        if not ( Match.isCertified() or Match.stopTimer ):
            t = round(Match.getTimeLeft( ) / 60) 
            digest.add_field( name="Time Remaining", value=f'{t if t > 0 else 0} minutes' )
        if Match.winner != "":
            if Match.winner in self.players:
                digest.add_field( name="Winner", value=self.getPlayer(Match.winner).getMention() )
            else:
                digest.add_field( name="Winner", value=Match.winner )
        if len(Match.confirmedPlayers) != 0:
            digest.add_field( name="Confirmed Players", value=", ".join( [ self.getPlayer(plyr).getMention() for plyr in Match.confirmedPlayers ] ) )

        if Match.triceMatch:
            digest.add_field( name="Tricebot Match", value = f'Replay at: {Match.replayURL}\nPlayer deck verification is {"enabled" if Match.playerDeckVerification else "disabled "}' )

        return digest

    # ---------------- Player Accessors ----------------
    def setPlayerTriceName( self, plyr: str, name: str ) -> str:
        if not plyr in self.players:
            return f'you are not registered for {self.name}. Use the !register {self.name} to register for this tournament.'
        if not self.getPlayer(plyr).isActive():
            return f'you are registered by are not an active player in {self.name}. If you believe this is an error, contact tournament staff.'
        self.getPlayer(plyr).triceName = name
        self.getPlayer(plyr).saveXML( )
        return f'Your cockatrice name was set to {name} successfully.'

    async def addDeck( self, plyr: str, deckName: str, decklist: str ) -> str:
        if not plyr in self.players:
            return f'you are not registered for {self.name}. Use the !register {self.name} to register for this tournament.'
        if not self.getPlayer(plyr).isActive():
            return f'you are registered by are not an active player in {self.name}. If you believe this is an error, contact tournament staff.'
        if not self.regOpen:
            return f'registration for {self.name} is closed, so you cannot submit a deck. If you believe this is an error, contact tournament staff.'
        self.getPlayer(plyr).addDeck( deckName, decklist )
        self.getPlayer(plyr).saveXML( )
        deckHash = self.getPlayer(plyr).decks[deckName].deckHash

        if isMoxFieldLink(decklist) or isTappedOutLink(decklist) or isMtgGoldfishLink(decklist):
            message += f'\nPlease be aware that this website treats your commander as if it were in your mainboard.'
        return message

    async def addDeckAdmin( self, plyr: str, deckName: str, decklist: str ) -> str:
        if not plyr in self.players:
            return f'{plyr!r} is not registered for {self.name}. Use the !admin-register {self.name} {plyr!r} to register them.'
        if not self.getPlayer(plyr).isActive():
            return f'{plyr!r} is not an active in {self.name}.'
        self.getPlayer(plyr).addDeck( deckName, decklist )
        self.getPlayer(plyr).saveXML( )
        deckHash = self.getPlayer(plyr).decks[deckName].deckHash

        await self.getPlayer(plyr).sendMessage( content = f'A decklist has been submitted for {self.name} on your behalf. The name of the deck is "{deckName}" and the deck hash is "{deckHash}". Use the command "!decklist {deckName}" to see the list. Please contact tournament staff if there is an error.' )
        return f'you have submitted a decklist for {self.getPlayer(plyr).getMention()}. The deck hash is {deckHash}.'
        message = f'your deck has been successfully registered in {self.name}. Your deck name is "{deckName}", and the deck hash is "{deckHash}". Make sure it matches your deck hash in Cockatrice. You can see your decklist by using !decklist "{deckName}" or !decklist {deckHash}.'

        if isMoxFieldLink(decklist) or isTappedOutLink(decklist) or isMtgGoldfishLink(decklist):
            message += f'\nPlease be aware that this website treats your commander as if it were in your mainboard.'
        return message

    async def removeDeck( self, plyr: int, deckName: str = "", author: str = "" ) -> str:
        if not plyr in self.players:
            return f'<@{plyr}>, you are not registered for {self.name}. Use !register {self.name} to register for this tournament.'
        if not self.getPlayer(plyr).isActive():
            return f'<@{plyr}>, you are registered by are not an active player in {self.name}. If you believe this is an error, contact tournament staff.'

        digest = await self.getPlayer(plyr).removeDeck( deckName, author )
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
        await ctx.send( f'Pruning players starting... now!' )
        for plyr in self.players:
            if len(plyr.decks) == 0:
                await self.dropPlayer( plyr )
                await ctx.send( f'{plyr.getMention()} has been pruned.' )
                await plyr.sendMessage( content=f'You have been dropped from the tournament {self.name} on {ctx.guild.name} by tournament staff for not submitting a deck. If you believe this is an error, contact them immediately.' )
                plyr.saveXML( )
        return f'All players that did not submit a deck have been pruned.'

    async def addPlayer( self, discordUser, admin=False ) -> str:
        if not admin and self.tournCancel:
            return "this tournament has been cancelled. If you believe this to be incorrect, please contact the tournament staff."
        if not admin and self.tournEnded:
            return "this tournament has already ended. If you believe this to be incorrect, please contact the tournament staff."
        if not ( admin or self.regOpen ):
            return "registration for the tounament is closed. If you believe this to be incorrect, please contact the tournament staff."
        RE = ""
        discordID = discordUser.id
        if discordID in self.players:
            self.getPlayer(discordID).activate()
            RE = "re-"
        else:
            newPlayer = player( discordUser.display_name, discordID )
            self.players.append( newPlayer )

        self.getPlayer(discordID).saveLocation = f'{self.getSaveLocation()}/players/{discordID}.xml'
        self.getPlayer(discordID).addDiscordUser( discordUser )
        await self.getPlayer(discordID).addRole( self.role )
        self.getPlayer(discordID).saveXML( )
        if admin:
            await self.getPlayer(discordID).sendMessage( content=f'You have been registered for {self.name}!' )
            return f'you have {RE}registered {self.getPlayer(discordID).getMention()} for {self.name}.'
        return f'you have been {RE}registered in {self.name}!'

    async def addDummyPlayer( self, playerName ) -> str:
        digest: dict = { "text": "", "embed": None }
        RE = ""
        if playerName in self.players:
            self.getPlayer(playerName).activate()
            RE = "re-"
        else:
            self.players.append( player( playerName, None ) )

        self.getPlayer(playerName).saveLocation = f'{self.getSaveLocation()}/players/{playerName}.xml'
        self.getPlayer(playerName).saveXML( )
        digest["text"] = f'{self.getPlayer(playerName).getMention()} has been {RE}registered for {self.name}.'
        await self.updateInfoMessage( )
        return digest

    async def dropPlayer( self, plyr: str, author: str = "" ) -> None:
        if not isinstance(plyr, player):
            plyr = self.getPlayer( plyr )
        try:
            await plyr.removeRole( self.role )
        except AttributeError as e:
            pass # This is thrown when the discord object is None
        await plyr.drop( )
        plyr.saveXML()
        message = await self.removePlayerFromQueue( plyr )
        
        # The player was dropped by an admin, so two messages need to be sent
        # TODO: The admin half of this command needs to be its own method
        if author != "":
            await self.getPlayer(plyr).sendMessage( content=f'You have been dropped from {self.name} on {self.guild.name} by tournament staff. If you believe this is an error, check with them.' )
            return f'{author}, {self.getPlayer(plyr).getMention()} has been dropped from the tournament.'
        return message

    async def playerConfirmResult( self, plyr: str, matchNum: int, admin: bool = False ) -> None:
        if not plyr in self.players:
            return f'you are not registered in {self.name}.'
        message = await self.matches[matchNum - 1].confirmResult( plyr )
        if message != "":
            await self.pairingsChannel.send( message )
            return f'you have certified the result of match #{matchNum} on behalf of {plyr}.' if admin else f'your confirmation has been logged.'
        if admin:
            await self.players.sendMessage( content=f'The result for match #{matchNum} in {self.name} has been confirmed on your behalf by tournament staff.' )
        return message

    async def recordMatchResult( self, plyr: str, result: str, matchNum: int, admin: bool = False ) -> str:
        if admin:
            message = await self.matches[matchNum - 1].recordResultAdmin( plyr, result )
        else:
            message = await self.matches[matchNum - 1].recordResult( plyr, result )

        if "announcement" in message:
            await self.pairingsChannel.send( content=message["announcement"] )
        return message["message"]

    async def pruneDecks( self, ctx ) -> str:
        await ctx.send( f'Pruning decks starting... now!' )
        for plyr in self.players:
            deckIdents = [ ident for ident in plyr.decks ]
            while len( plyr.decks ) > self.deckCount:
                del( plyr.decks[deckIdents[0]] )
                await ctx.send( f'The deck {deckIdents[0]} belonging to {plyr.getMention()} has been pruned.' )
                await plyr.sendMessage( content=f'Your deck {deckIdents[0]} has been pruned from the tournament {self.name} on {ctx.guild.name} by tournament staff.' )
                del( deckIdents[0] )
            plyr.saveXML( )
        await self.updateInfoMessage()
        return f'Decks have been pruned. All players have at most {self.deckCount} deck{"" if self.deckCount == 1 else "s"}.'

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
        for plyr in plyrs:
            self.queueActivity.append( (plyr, getTime() ) )
        newMatch = match( plyrs )
        self.matches.append( newMatch )
        newMatch.matchNumber = len(self.matches)
        newMatch.matchLength = self.matchLength
        newMatch.saveLocation = f'{self.getSaveLocation()}/matches/match_{newMatch.matchNumber}.xml'
        if isinstance( self.guild, discord.Guild ):
            matchRole = await self.guild.create_role( name=f'Match {newMatch.matchNumber}' )
            overwrites = { self.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                           gAdminRole(self.guild): discord.PermissionOverwrite(read_messages=True),
                           getJudgeRole(self.guild): discord.PermissionOverwrite(read_messages=True),
                           matchRole: discord.PermissionOverwrite(read_messages=True) }
            matchCategory = discord.utils.get( self.guild.categories, name="Matches" )
            if len(matchCategory.channels) >= 50:
                matchCategory = category=discord.utils.get( self.guild.categories, name="More Matches" )

            game_name: str = f'{self.name} Match {newMatch.matchNumber}'

            newMatch.VC    = await matchCategory.create_voice_channel( name=game_name, overwrites=overwrites )
            newMatch.role  = matchRole
            newMatch.timer = threading.Thread( target=self._matchTimer, args=(newMatch,) )

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

                    message += f'A cockatrice game was automatically made for you it is called {game_name }'
                    message += f' and has a password of `"{game_password}"`\n'

                    #TODO: move replay download link? (fixme)
                    message += f'Replay download link {replay_download_link} (available on game end).\n'
                else:
                    #Game was not made
                    message += "A cockatrice game was not automatically made for you.\n"

        for plyr in plyrs:
            # TODO: This should be unready player
            await self.removePlayerFromQueue( plyr )
            self.getPlayer(plyr).matches.append( newMatch )
            for p in plyrs:
                self.getPlayer(plyr).addOpponent( p )
            if type( self.guild ) == discord.Guild:
                self.getPlayer(plyr).saveXML()
                await self.getPlayer(plyr).addRole( matchRole )
                embed.add_field( name=self.getPlayer(plyr).getDisplayName(), value=self.getPlayer(plyr).pairingString() )

        if type( self.guild ) is discord.Guild:
            await self.pairingsChannel.send( content=message, embed=embed )

        newMatch.timer.start( )
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

    async def addBye( self, plyr: str ) -> None:
        await self.removePlayerFromQueue( plyr )
        newMatch = match( [ plyr ] )
        self.matches.append( newMatch )
        newMatch.matchNumber = len(self.matches)
        newMatch.saveLocation = f'{self.getSaveLocation()}/matches/match_{newMatch.matchNumber}.xml'
        newMatch.recordBye( )
        self.getPlayer(plyr).matches.append( newMatch )
        newMatch.saveXML( )

    async def removeMatch( self, matchNum: int, author: str = "" ) -> str:
        if self.matches[matchNum - 1] != matchNum:
            self.matches.sort( key=lambda x: x.matchNumber )

        for plyr in self.matches[matchNum - 1].activePlayers:
            await self.getPlayer(plyr).removeMatch( matchNum )
            await self.getPlayer(plyr).sendMessage( content=f'You were a particpant in match #{matchNum} in the tournament {self.name} on the server {self.hostGuildName}. This match has been removed by tournament staff. If you think this is an error, contact them.' )
        for plyr in self.matches[matchNum - 1].droppedPlayers:
            await self.getPlayer(plyr).removeMatch( matchNum )
            await self.getPlayer(plyr).sendMessage( content=f'You were a particpant in match #{matchNum} in the tournament {self.name} on the server {self.hostGuildName}. This match has been removed by tournament staff. If you think this is an error, contact them.' )

        await self.matches[matchNum - 1].killMatch( )
        self.matches[matchNum - 1].saveXML( )

        await self.updateInfoMessage()
        return f'{author}, match #{matchNum} has been removed.'


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

    def saveOverview( self, filename: str = "" ):
        print( "No overview being saved." )
        return None

    def savePlayers( self, dirName: str = "" ) -> None:
        if dirName == "":
            dirName = self.getSaveLocation()
        if not (os.path.isdir( f'{dirName}/players/' ) and os.path.exists( f'{dirName}/players/' )):
           os.mkdir( f'{dirName}/players/' )

        for player in self.players:
            player.saveXML( f'{dirName}/players/{toPathSafe(player.name)}.xml' )

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
        return None

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
            self.matches.append( newMatch )
            for aPlayer in newMatch.activePlayers:
                if aPlayer in self.players:
                    self.getPlayer(aPlayer).addMatch( newMatch )
            for dPlayer in newMatch.droppedPlayers:
                if dPlayer in self.players:
                    self.getPlayer(dPlayer).addMatch( newMatch )
            if not ( self.matches[-1].isCertified() or self.matches[-1].isDead() ) and not self.matches[-1].stopTimer:
                self.matches[-1].timer = threading.Thread( target=self._matchTimer, args=(self.matches[-1],) )
                self.matches[-1].timer.start( )
        self.matches.sort( key= lambda x: x.matchNumber )
        for plyr in self.players:
            plyr.matches.sort( key= lambda x: x.matchNumber )



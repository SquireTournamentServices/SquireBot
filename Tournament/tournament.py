import os
import shutil
import xml.etree.ElementTree as ET
import random
import threading
import time
import discord
import asyncio
import warnings

from typing import List, Dict, Tuple

from .tricebot import TriceBot
from .utils import *
from .match import match
from .player import player
from .deck import deck

from dotenv import load_dotenv

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
    # The tournament base class is not meant to be constructed, but this
    # constructor acts as a guide for the minimum a constructor needs
    def __init__( self, name: str, hostGuildName: str, props: dict = { } ):     
        self.name = name.replace("\.\./", "")
        self.hostGuildName = hostGuildName
        self.format    = props["format"] if "format" in props else "Pioneer"
        
        self.saveLocation = f'currentTournaments/{self.name}'

        self.guild   = None
        self.guildID = ""
        self.role    = None
        self.roleID  = ""
        self.pairingsChannel = None
        self.pairingsChannelID = ""
        
        self.regOpen      = True
        self.tournStarted = False
        self.tournEnded   = False
        self.tournCancel  = False
        
        self.loop = asyncio.new_event_loop( )
        self.fail_count = 0
        
        self.playersPerMatch = 2
        self.matchLength     = 60*60 # Length of matches in seconds
        
        self.deckCount = 1

        self.players  = {}
        
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
    
    def assignGuild( self, guild: discord.Guild ) -> str:
        print( f'The guild "{guild}" is being assigned to {self.name}.' )
        print( f'There are {len(self.players)} players in this tournament!\n' )
        self.guild = guild
        self.guildID = guild.id
        self.hostGuildName = guild.name
        self.pairingsChannel = guild.get_channel( self.pairingsChannelID )
        if self.pairingsChannel is None:
            self.pairingsChannel = discord.utils.get( guild.channels, name="match-pairings" )
        if self.roleID != "":
            self.role = guild.get_role( self.roleID )
        for player in self.players:
            ID = self.players[player].discordID
            if ID != "":
                self.players[player].addDiscordUser( self.guild.get_member( ID ) )
        for mtch in self.matches:
            if mtch.roleID != "":
                mtch.addMatchRole( guild.get_role( mtch.roleID ) )
            if mtch.VC_ID != "":
                mtch.addMatchVC( guild.get_channel( mtch.VC_ID ) )


    # ---------------- Property Accessors ---------------- 
    
    def setProperties( self, props: Dict ) -> str:
        successes = [ ]
        failures  = [ ]
        undefined = [ ]
        for prop in props:
            props[prop] = str(props[prop])
            
            # This flag is True if the value is a number and greater than 0
            isValidNumber = props[prop].isnumeric()
            if isValidNumber:
                number = int(props[prop])
                isValidNumber = number > 0
                
            # Check for empty strings
            if props[prop] == "":                
                successes.append( prop )
            elif prop == "format":
                # Not really sure what TODO here
                self.format = props[prop]
                successes.append( prop )
            elif prop == "deck-count":
                if isValidNumber:
                    self.deckCount = number
                    successes.append( prop )
                else:
                    failures.append( prop )
            elif prop == "match-length":
                # The length of a match needs to be an int
                if isValidNumber:
                    self.matchLength = number * 60
                    successes.append( prop )
                else:
                    failures.append( prop )
            elif prop == "match-size":
                # The number of people in a match needs to be an int
                if isValidNumber:
                    self.playersPerMatch = number
                    successes.append( prop )
                else:
                    failures.append( prop )
            elif prop == "pairings-channel":
                # The pairings channel properties should be an ID, which is an int
                # Also, the guild should have a channel whose ID is the given ID
                channelID = discordID_from_mention( props[prop] )
                if channelID.isnumeric() and not (self.guild.get_channel( int(channelID) ) is None):
                    self.pairingsChannel = self.guild.get_channel( int(channelID) )
                    self.pairingsChannelID = self.pairingsChannel.id
                    successes.append( prop )
                else:
                    failures.append( prop )
            elif prop == "tricebot-enabled":
                # This needs to be a bool
                if not ( str_to_bool(props[prop]) is None ): 
                    self.triceBotEnabled = str_to_bool(props[prop])
                    successes.append( prop )
                else:
                    failures.append( prop )
            elif prop == "spectators-allowed":
                # This needs to be a bool
                if not ( str_to_bool(props[prop]) is None ): 
                    self.spectators_allowed = str_to_bool(props[prop])
                    successes.append( prop )
                else:
                    failures.append( prop )
            elif prop == "spectators-need-password":
                # This needs to be a bool
                if not ( str_to_bool(props[prop]) is None ): 
                    self.spectators_need_password = str_to_bool(props[prop])
                    successes.append( prop )
                else:
                    failures.append( prop )
            elif prop == "spectators-can-chat":
                # This needs to be a bool
                if not ( str_to_bool(props[prop]) is None ): 
                    self.spectators_can_chat = str_to_bool(props[prop])
                    successes.append( prop )
                else:
                    failures.append( prop )
            elif prop == "spectators-can-see-hands":
                # This needs to be a bool
                if not ( str_to_bool(props[prop]) is None ): 
                    self.spectators_can_see_hands = str_to_bool(props[prop])
                    successes.append( prop )
                else:
                    failures.append( prop )
            elif prop == "only-registered":
                # This needs to be a bool
                if not ( str_to_bool(props[prop]) is None ): 
                    self.only_registered = str_to_bool(props[prop])
                    successes.append( prop )
                else:
                    failures.append( prop )
            elif prop == "player-deck-verification":                
                # This needs to be a bool
                if not ( str_to_bool(props[prop]) is None ): 
                    self.player_deck_verification = str_to_bool(props[prop])
                    successes.append( prop )
                else:
                    failures.append( prop )
            else:
                undefined.append( prop )
        digest = ""
        if len(successes) == 0:
            digest += "No properties were successfully updated."
        else:
            digest += f'The following propert{"y was" if len(successes) == 1 else "ies were"} successfully updated:\n\t-'
            digest += "\n\t-".join( [ f'{p}: {props[p]}' for p in successes ] )
        if len(failures) > 0:
            digest += f'\n\nThere were errors in updating the following propert{"y was" if len(failures) == 1 else "ies"}:\n\t-'
            digest += "\n\t-".join( [ f'{p}: {props[p]}' for p in failures ] )
        if len(undefined) > 0:
            digest += f'\n\n{self.name} does not have the following propert{"y" if len(failures) == 1 else "ies"}:\n\t-'
            digest += "\n\t-".join( [ f'{p}: {props[p]}' for p in undefined ] )

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
    
    def getStandings( self ) -> List[List]:
        rough = [ ]
        for plyr in self.players.values():
            if not plyr.isActive( ):
                continue
            if plyr.discordUser is None:
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
                wins  = sum( [ self.players[opp].getNumberOfWins( ) for opp in plyr.opponents ] )
                games = sum( [len(self.players[opp].getCertMatches( withBye=False )) for opp in plyr.opponents] )
                if games != 0:
                    OWP = wins/games
                #OWP = sum( [ self.players[opp].getMatchWinPercentage( withBye=False ) for opp in plyr.opponents ] )/len(plyr.opponents)
            rough.append( (points, MWP, OWP, plyr.discordUser.display_name) )
        
        # sort() is stable, so relate order similar elements is preserved
        rough.sort( key= lambda x: x[2], reverse=True )
        rough.sort( key= lambda x: x[1], reverse=True )
        rough.sort( key= lambda x: x[0], reverse=True )
        
        # Place, Player name, Points, MWP, OWP
        digest =  [ [ i+1 for i in range(len(rough))], \
                    [ i[3] for i in rough ], \
                    [ i[0] for i in rough ], \
                    [ i[1]*100 for i in rough ], \
                    [ i[2]*100 for i in rough ] ]

        return digest


    # ---------------- Embed Generators ---------------- 
    def getPlayerProfileEmbed( self, plyr: int ) -> discord.Embed:
        digest = discord.Embed()
        deckPairs = [ f'{d}: {self.players[plyr].decks[d].deckHash}' for d in self.players[plyr].decks ]
        digest.add_field( name="Decks:", value=("\u200b" + "\n".join(deckPairs)) )
        for mtch in self.players[plyr].matches:
            players = mtch.activePlayers + mtch.droppedPlayers
            status = f'Status: {mtch.status}'
            if mtch.winner in self.players:
                winner = f'Winner: {self.players[mtch.winner].getMention()}'
            else:
                winner = f'Winner: {mtch.winner if mtch.winner else "N/A"}'
            oppens = "Opponents: " + ", ".join( [ self.players[plyr].discordUser.mention for plyr in players if plyr != plyr ] )
            digest.add_field( name=f'Match #{mtch.matchNumber}', value=f'{status}\n{winner}\n{oppens}' )
        return digest

    def getMatchEmbed( self, mtch: int ):
        digest = discord.Embed( )
        Match = self.matches[mtch] 
        digest.add_field( name="Status", value=Match.status )
        digest.add_field( name="Active Players", value="\u200b" + ", ".join( [ self.players[plyr].getMention() for plyr in Match.activePlayers ] ) )
        if len(Match.droppedPlayers) != 0:
            digest.add_field( name="Dropped Players", value=", ".join( [ self.players[plyr].getMention() for plyr in Match.droppedPlayers ] ) )
        if not ( Match.isCertified() or Match.stopTimer ):
            t = Match.getTimeElapsed()
            if t > self.matchLength/60:
                digest.add_field( name="Time Remaining", value=f'0 minutes' )
            else:
                digest.add_field( name="Time Remaining", value=f'{round(self.matchLength/60 - t)} minutes' )
        if Match.winner != "":
            if Match.winner in self.players:
                digest.add_field( name="Winner", value=self.players[Match.winner].discordUser.mention )
            else:
                digest.add_field( name="Winner", value=Match.winner )
        if len(Match.confirmedPlayers) != 0:
            digest.add_field( name="Confirmed Players", value=", ".join( [ self.players[plyr].getMention() for plyr in Match.confirmedPlayers ] ) )
            
        if Match.triceMatch:
            digest.add_field( name="Tricebot Match", value = f'Replay at: {Match.replayURL}' )
            
        return digest
    
    # ---------------- Player Accessors ---------------- 
    def setPlayerTriceName( self, plyr: str, name: str ) -> str:
        if not plyr in self.players:
            return f'you are not registered for {self.name}. Use the !register {self.name} to register for this tournament.'
        if not self.players[plyr].isActive():
            return f'you are registered by are not an active player in {self.name}. If you believe this is an error, contact tournament staff.'
        self.players[plyr].triceName = name
        self.players[plyr].saveXML( )
        return f'Your cockatrice name was set to {name} successfully.'
    
    def addDeck( self, plyr: str, deckName: str, decklist: str, admin: bool = False ) -> str:
        if not plyr in self.players:
            return f'you are not registered for {self.name}. Use the !register {self.name} to register for this tournament.'
        if not self.players[plyr].isActive():
            return f'you are registered by are not an active player in {self.name}. If you believe this is an error, contact tournament staff.'
        if not ( admin or self.regOpen ):
            return f'registration for {self.name} is closed, so you can not submit a deck. If you believe this is an error, contact tournament staff.'
        self.players[plyr].addDeck( deckName, decklist )
        self.players[plyr].saveXML( )
        deckHash = self.players[plyr].decks[deckName].deckHash
        if admin:
            self.players[plyr].discordUser.send( content = f'A decklist has been submitted for {tourn} on your behalf. The name of the deck is "{deckName}" and the deck hash is "{deckHash}". Use the command "!decklist {deckName}" to see the list. Please contact tournament staff if there is an error.' ) 
            return f'you have submitted a decklist for {plyr}. The deck hash is {deckHash}.'
        return f'your deck has been successfully registered in {self.name}. Your deck name is "{deckName}", and the deck hash is "{deckHash}". Make sure it matches your deck hash in Cockatrice. You can see your decklist by using !decklist "{deckName}" or !decklist {deckHash}.'
        
    
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
            return f'{self.name} has not started, so it can not be ended. However, it can be cancelled.'
        await self.purgeTourn( )
        self.tournEnded = False
        self.saveTournament( f'closedTournaments/{self.name}' )
        if os.path.isdir( f'currentTournaments/{self.name}' ): 
            shutil.rmtree( f'currentTournaments/{self.name}' )
        return f'{adminMention}, {self.name} has been closed by {author}.'
    
    async def cancelTourn( self, adminMention: str = "", author: str = "") -> str:
        await self.purgeTourn( )
        self.tournCancel = True
        self.saveTournament( f'closedTournaments/{self.name}' )
        if os.path.isdir( f'currentTournaments/{self.name}' ): 
            shutil.rmtree( f'currentTournaments/{self.name}' )
        return f'{adminMention}, {self.name} has been cancelled by {author}.'
    
    # ---------------- Player Management ---------------- 

    async def prunePlayers( self, ctx ) -> str:
        await ctx.send( f'Pruning players starting... now!' )
        for plyr in self.players:
            if len(self.players[plyr].decks) == 0:
                await self.dropPlayer( plyr ) 
                await ctx.send( f'{self.players[plyr].getMention()} has been pruned.' )
                await self.players[plyr].discordUser.send( content=f'You have been dropped from the tournament {self.name} on {ctx.guild.name} by tournament staff for not submitting a deck. If you believe this is an error, contact them immediately.' )
                self.players[plyr].saveXML( )
        return f'All players that did not submit a deck have been pruned.'
    
    async def addPlayer( self, discordUser, admin=False ) -> str:
        if not admin and self.tournCancel:
            return "this tournament has been cancelled. If you believe this to be incorrect, please contact the tournament staff."
        if not admin and self.tournEnded:
            return "this tournament has already ended. If you believe this to be incorrect, please contact the tournament staff."
        if not ( admin or self.regOpen ):
            return "registration for the tounament is closed. If you believe this to be incorrect, please contact the tournament staff."
        RE = ""
        if discordUser.id in self.players:
            self.players[discordUser.id].status = "active"
            RE = "re-"
        else:
            self.players[discordUser.id] = player( discordUser.display_name, discordUser.id )

        self.players[discordUser.id].saveLocation = f'{self.saveLocation}/players/{toPathSafe(discordUser.display_name)}.xml'
        self.players[discordUser.id].addDiscordUser( discordUser )
        await self.players[discordUser.id].discordUser.add_roles( self.role )
        self.players[discordUser.id].saveXML( )
        if admin:
            await discordUser.send( content=f'You have been registered for {self.name}!' )  
            return f'you have {RE}registered {discordUser.mention} for {self.name}'
        return f'you have been {RE}registered in {self.name}!'

    async def dropPlayer( self, plyr: str, author: str = "" ) -> None:
        await self.players[plyr].discordUser.remove_roles( self.role )
        await self.players[plyr].drop( )
        self.players[plyr].saveXML()
        if author != "":
            await self.players[plyr].discordUser.send( content=f'You have been dropped from {self.name} on {self.guild.name} by tournament staff. If you believe this is an error, check with them.' )
            return f'{author}, {self.players[plyr].discordUser.mention} has been dropped from the tournament.'
        return f'{self.players[plyr].discordUser.mention}, you have been dropped from {self.name}.'
    
    async def playerConfirmResult( self, plyr: str, matchNum: int, admin: bool = False ) -> None:
        if not plyr in self.players:
            return f'you are not registered in {self.name}.'
        message = await self.matches[matchNum - 1].confirmResult( plyr )
        if message != "":
            await self.pairingsChannel.send( message )
            return f'you have certified the result of match #{matchNum} on behalf of {plyr}.' if admin else f'your confirmation has been logged.'
        if admin:
            await self.players.discordUser.send( f'The result for match #{matchNum} in {self.name} has been confirmed on your behalf by tournament staff.' )
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
        for plyr in self.players.values():
            deckIdents = [ ident for ident in plyr.decks ]
            while len( plyr.decks ) > self.deckCount:
                del( plyr.decks[deckIdents[0]] )
                await ctx.send( f'The deck {deckIdents[0]} belonging to {plyr.discordUser.mention} has been pruned.' )
                await plyr.discordUser.send( content=f'Your deck {deckIdents[0]} has been pruned from the tournament {self.name} on {ctx.guild.name} by tournament staff.' )
                del( deckIdents[0] )
            plyr.saveXML( )
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
            time.sleep( 1 )
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
    
    async def addMatch( self, plyrs: List[str] ) -> None:
        for plyr in plyrs:
            self.queueActivity.append( (plyr, getTime() ) )
        newMatch = match( plyrs )
        self.matches.append( newMatch )
        newMatch.matchNumber = len(self.matches)
        newMatch.matchLength = self.matchLength
        newMatch.saveLocation = f'{self.saveLocation}/matches/match_{newMatch.matchNumber}.xml'
        if type( self.guild ) == discord.Guild:
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
                        name = self.players[plyr].triceName
                        if name == "":
                            name = "*"
                        playerNames.append(name)
                        deckHashes.append( [dck.deckHash for dck in self.players[plyr].decks.values()] )

                #Try up to three times
                while not creation_success and tries < max_tries:
                    playerNames = []
                    deckHashes = []
                    i: int = 0
                    if self.player_deck_verification:
                        for plyr in plyrs:
                            name = self.players[plyr].triceName
                            if name == "" or name == None:
                            if name == "":
                                name = "*"
                            playerNames.append(name)
                            deckHashes.append([])
                            for deck in self.players[plyr].decks:
                                deckHashes[i].append(self.players[plyr].decks[deck].deckHash)
                            i+=1
                    
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
                
                    #TODO: move replay download link?
                    message += f'Replay download link {replay_download_link} (available on game end).\n'
                else:
                    #Game was not made
                    message += "A cockatrice game was not automatically made for you.\n"

        for plyr in plyrs:
            self.removePlayerFromQueue( plyr )
            self.players[plyr].matches.append( newMatch )
            for p in plyrs:
                if p != plyr:
                    self.players[plyr].opponents.append( p )
            if type( self.guild ) == discord.Guild:
                self.players[plyr].saveXML()
                await self.players[plyr].discordUser.add_roles( matchRole )
                embed.add_field( name=self.players[plyr].getDisplayName(), value=self.players[plyr].pairingString() )
        
        if type( self.guild ) is discord.Guild:
            await self.pairingsChannel.send( content=message, embed=embed )
            
        newMatch.timer.start( )
        newMatch.saveXML()
    
    # See tricebot.py for retun details
    # copy pasta of them is here. accurate as of 25/04/21
    
    #  1 if success
    #  0 auth token is bad or error404 or network issue
    # -1 if player not found
    # -2 if an unknown error occurred
    def kickTricePlayer(self, a_matchNum, playerName):
        match = self.matches[a_matchNum - 1]
        return trice_bot.kickPlayer(match.gameID, playerName)
    
    def addBye( self, plyr: str ) -> None:
        self.removePlayerFromQueue( plyr )
        newMatch = match( [ plyr ] )
        self.matches.append( newMatch )
        newMatch.matchNumber = len(self.matches)
        newMatch.saveLocation = f'{self.saveLocation}/matches/match_{newMatch.matchNumber}.xml'
        newMatch.recordBye( )
        self.players[plyr].matches.append( newMatch )
        newMatch.saveXML( )
    
    async def removeMatch( self, matchNum: int, author: str = "" ) -> str:
        if self.matches[matchNum - 1] != matchNum:
            self.matches.sort( key=lambda x: x.matchNumber )

        for plyr in self.matches[matchNum - 1].activePlayers:
            await self.players[plyr].removeMatch( matchNum )
            await self.players[plyr].discordUser.send( content=f'You were a particpant in match #{matchNum} in the tournament {self.name} on the server {self.hostGuildName}. This match has been removed by tournament staff. If you think this is an error, contact them.' )
        for plyr in self.matches[matchNum - 1].droppedPlayers:
            await self.players[plyr].removeMatch( matchNum )
            await self.players[plyr].discordUser.send( content=f'You were a particpant in match #{matchNum} in the tournament {self.name} on the server {self.hostGuildName}. This match has been removed by tournament staff. If you think this is an error, contact them.' )

        await self.matches[matchNum - 1].killMatch( )
        self.matches[matchNum - 1].saveXML( )
        
        return f'{author}, match #{matchNum} has been removed.'
    
    
    # ---------------- Matchmaking Queue Methods ---------------- 
    
    # There will be a far more sofisticated pairing system in the future. Right now, the dummy version will have to do for testing
    # This is a prime canidate for adjustments when players how copies of match results.
    def addPlayerToQueue( self, plyr: str ) -> str:
        return f'{self.name} does not have a matchmaking queue.'
    
    def removePlayerFromQueue( self, plyr: str ) -> str:
        return f'{self.name} does not have a matchmaking queue.'


    # ---------------- XML Saving/Loading ---------------- 
    # Most of these are also universally defined, but are for a particular purpose

    def saveTournament( self, dirName: str = "" ) -> None:        
        dirName = dirName.replace("\.\./", "") 
        #Check on folder creation, event though input should be safe
        if dirName == "":
            dirName = self.saveLocation
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
            dirName = self.saveLocation
        if not (os.path.isdir( f'{dirName}/players/' ) and os.path.exists( f'{dirName}/players/' )):
           os.mkdir( f'{dirName}/players/' ) 

        for player in self.players:
            self.players[player].saveXML( f'{dirName}/players/{toPathSafe(self.players[player].name)}.xml' )

    def saveMatches( self, dirName: str = "" ) -> None:
        if dirName == "":
            dirName = self.saveLocation
        if not (os.path.isdir( f'{dirName}/matches/' ) and os.path.exists( f'{dirName}/matches/' )):
           os.mkdir( f'{dirName}/matches/' ) 

        for match in self.matches:
            match.saveXML( f'{dirName}/matches/match_{match.matchNumber}.xml' )
        
    def loadTournament( self, dirName: str ) -> None:
        self.saveLocation = dirName
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
            newPlayer.saveLocation = playerFile
            newPlayer.loadXML( playerFile )
            self.players[newPlayer.discordID] = newPlayer
        print( list(self.players.keys()) )
    
    def loadMatches( self, dirName: str ) -> None:
        matchFiles = [ f'{dirName}/{f}' for f in os.listdir(dirName) if os.path.isfile( f'{dirName}/{f}' ) ]
        for matchFile in matchFiles:
            newMatch = match( [] )
            newMatch.saveLocation = matchFile
            newMatch.loadXML( matchFile )
            self.matches.append( newMatch )
            for aPlayer in newMatch.activePlayers:
                if aPlayer in self.players:
                    self.players[aPlayer].addMatch( newMatch )
            for dPlayer in newMatch.droppedPlayers:
                if dPlayer in self.players:
                    self.players[dPlayer].addMatch( newMatch )
            if not ( self.matches[-1].isCertified() or self.matches[-1].isDead() ) and not self.matches[-1].stopTimer:
                self.matches[-1].timer = threading.Thread( target=self._matchTimer, args=(self.matches[-1],) )
                self.matches[-1].timer.start( )
        self.matches.sort( key= lambda x: x.matchNumber )
        for plyr in self.players.values():
            plyr.matches.sort( key= lambda x: x.matchNumber )



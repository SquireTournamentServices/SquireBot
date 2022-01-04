import os
import shutil
import copy
import math
import asyncio
import xml.etree.ElementTree as ET
from Tournament import *
from test import *


class TournamentTest(TestCase):
    def __init__(self):
        self.testName = "Tournament/*Tournament.py"

    def test(self):
        subTests = []
        subTests.append(FluidRoundTournamentTest())
        subTests.append(SwissTournamentTest())

        tests = TestRunner(subTests)
        print("[TOURNAMENT TEST]: Running tournament unit tests.")
        status = tests.executeTests()
        print(
            f"[TOURNAMENT TEST]: {len(tests.passedTests)}/{len(tests.testCases)} sub-tests passed"
        )

        return status


# Code for all sub tests
TOURN_MATCH_SIZE = 4
TOURN_PLAYERS = TOURN_MATCH_SIZE * 100
TOURN_NAME = "test-tourn"
GUILD_NAME = "test-guild"
SAVE_LOCATION = f"{os.getcwd()}/guilds/1/currentTournaments/{TOURN_NAME}"


def assertEq(a, b, testDesc):
    status = a == b
    if not status:
        print(f"[ASSERT EQUALS]: {testDesc}")
    return status


def assertEqList(a, b, testDesc):
    a.sort()
    b.sort()
    status = len(a) == len(b)

    if status:
        for i in range(0, len(a)):
            status &= a[i] == b[i]

    if not status:
        print(a[i])
        print(b[i])
        print(f"[ASSERT EQUALS]: {testDesc}")
    return status


# discordId = 0
def getID():
    # discordId += 1
    # return discordId
    return 1


class DiscordDud:
    def __init__(self):
        self.id = getID()


class DiscordDudChannel(DiscordDud):
    pass


class DiscordMessageDud(DiscordDud):
    def __init__(self):
        self.id = getID()
        self.channel = DiscordDudChannel()

    async def edit(self, embed):
        pass


class DiscordPlayerDud(DiscordDud):
    def __init__(self, name, id):
        self.display_name = name
        self.id = id
        self.mention = f"<@{id}>"


async def addplayers(tournament):
    for i in range(0, TOURN_PLAYERS):
        await tournament.addPlayer(DiscordPlayerDud(f"player {i}", i))


def testTournamentSaveLoad(tournament) -> bool:
    try:
        shutil.rmtree(SAVE_LOCATION)
    except Exception as e:
        pass
    path = SAVE_LOCATION.split("/")
    for i in range(1, len(path)):
        try:
            os.mkdir("/".join(path[0 : i + 1]))
        except Exception as e:
            print(e)
    os.mkdir(f"{SAVE_LOCATION}/players")
    os.mkdir(f"{SAVE_LOCATION}/matches")

    # Add fake discord objects to fool the save/load commands
    tournament.pairingsChannel = DiscordDudChannel()
    tournament.infoMessage = DiscordMessageDud()
    tournament.guild = DiscordDud()
    tournament.role = DiscordDud()

    # Add players
    loop = asyncio.get_event_loop()
    loop.run_until_complete(addplayers(tournament))

    # Add matches
    matchCount = TOURN_PLAYERS / TOURN_MATCH_SIZE
    for i in range(0, math.floor(matchCount)):
        players = []
        for j in range(0, TOURN_MATCH_SIZE):
            players.append(tournament.players[j])
        loop = asyncio.get_event_loop()
        loop.run_until_complete(tournament.addMatch(players))

    # Save tournament then load tournament
    tournament.saveTournament(SAVE_LOCATION)

    # Load the tournament and check that the two objects have the same data
    tournType = ET.parse(f"{SAVE_LOCATION}/tournamentType.xml").getroot().text
    tournamentLoaded = getTournamentType(tournType, TOURN_NAME, GUILD_NAME, dict())
    tournamentLoaded.loadTournament(f"{SAVE_LOCATION}")

    # Assert tournament properties are equal
    testStatus = assertEq(type(tournamentLoaded), type(tournament), "Tournament type")
    testStatus &= assertEq(tournamentLoaded.uuid, tournament.uuid, "Tournament uuid")
    testStatus &= assertEq(tournamentLoaded.name, tournament.name, "Tournament name")
    testStatus &= assertEq(
        tournamentLoaded.hostGuildName,
        tournament.hostGuildName,
        "Tournament hostGuildName",
    )
    testStatus &= assertEq(
        tournamentLoaded.guildID, tournament.guild.id, "Tournament guildID"
    )
    testStatus &= assertEq(
        tournamentLoaded.roleID, tournament.role.id, "Tournament roleID"
    )
    testStatus &= assertEq(
        tournamentLoaded.pairingsChannelID,
        tournament.pairingsChannel.id,
        "Tournament pairingsChannelID",
    )
    # testStatus &= assertEq(tournamentLoaded.infoMessageChannelID, tournament.infoMessageChannelID, "Tournament infoMessageChannelID")
    testStatus &= assertEq(
        tournamentLoaded.infoMessageID,
        tournament.infoMessage.id,
        "Tournament infoMessageID",
    )
    testStatus &= assertEq(
        tournamentLoaded.regOpen, tournament.regOpen, "Tournament regOpen"
    )
    testStatus &= assertEq(
        tournamentLoaded.tournStarted,
        tournament.tournStarted,
        "Tournament tournStarted",
    )
    testStatus &= assertEq(
        tournamentLoaded.tournEnded, tournament.tournEnded, "Tournament tournEnded"
    )
    testStatus &= assertEq(
        tournamentLoaded.tournCancel, tournament.tournCancel, "Tournament tournCancel"
    )
    testStatus &= assertEq(
        tournamentLoaded.format, tournament.format, "Tournament format"
    )
    testStatus &= assertEq(
        tournamentLoaded.playersPerMatch,
        tournament.playersPerMatch,
        "Tournament playersPerMatch",
    )
    testStatus &= assertEq(
        tournamentLoaded.matchLength, tournament.matchLength, "Tournament matchLength"
    )
    testStatus &= assertEq(
        tournamentLoaded.deckCount, tournament.deckCount, "Tournament deckCount"
    )
    testStatus &= assertEqList(
        tournamentLoaded.players, tournament.players, "Tournament players"
    )
    testStatus &= assertEqList(
        tournamentLoaded.matches, tournament.matches, "Tournament matches"
    )
    testStatus &= assertEq(
        tournamentLoaded.triceBotEnabled,
        tournament.triceBotEnabled,
        "Tournament triceBotEnabled",
    )
    testStatus &= assertEq(
        tournamentLoaded.spectators_allowed,
        tournament.spectators_allowed,
        "Tournament spectators_allowed",
    )
    testStatus &= assertEq(
        tournamentLoaded.spectators_need_password,
        tournament.spectators_need_password,
        "Tournament spectators_need_password",
    )
    testStatus &= assertEq(
        tournamentLoaded.spectators_can_chat,
        tournament.spectators_can_chat,
        "Tournament spectators_can_chat",
    )
    testStatus &= assertEq(
        tournamentLoaded.spectators_can_see_hands,
        tournament.spectators_can_see_hands,
        "Tournament spectators_can_see_hands",
    )
    testStatus &= assertEq(
        tournamentLoaded.only_registered,
        tournament.only_registered,
        "Tournament only_registered",
    )
    testStatus &= assertEq(
        tournamentLoaded.player_deck_verification,
        tournament.player_deck_verification,
        "Tournament player_deck_verification",
    )

    return testStatus


class FluidRoundTournamentTest(TestCase):
    def __init__(self):
        self.testName = "Tournament/fluidRoundTournament.py"

    def test(self):
        t = fluidRoundTournament(TOURN_NAME, GUILD_NAME, dict())
        return testTournamentSaveLoad(t)


class SwissTournamentTest(TestCase):
    def __init__(self):
        self.testName = "Tournament/swissTournament.py"

    def test(self):
        t = swissTournament(TOURN_NAME, GUILD_NAME, dict())
        return testTournamentSaveLoad(t)

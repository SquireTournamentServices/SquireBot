import os
import sys
import shutil
import copy
import math
import asyncio
import xml.etree.ElementTree as ET

projectBaseDir = os.path.dirname(os.path.realpath(__file__)) + "/../"

sys.path.insert( 0, projectBaseDir + 'Tournament')
sys.path.insert( 0, projectBaseDir )

from Tournament import *
from test import *

# Code for all sub tests
TOURN_MATCH_SIZE = 4
TOURN_PLAYERS = TOURN_MATCH_SIZE * 100
TOURN_NAME = "test-tourn"
GUILD_NAME = "test-guild"
SAVE_LOCATION = f"{os.getcwd()}/guilds/1/currentTournaments/{TOURN_NAME}"

def main():
    tourn = fluidRoundTournament( TOURN_NAME, GUILD_NAME, {"match-size": 4} )
    print( f'Tournament Created: There are {tourn.playersPerMatch} player per match.' )
    for i in range(20):
        plyr = tourn.playerReg.createPlayer( f'Player {i}')
        tourn.queue.addPlayer( plyr )
    print( "Players Added" )
    for pairing in tourn.queue.createPairings( 4 ):
        print( pairing )
    print( f'There are {tourn.matchReg.getMatchCount()} matches.' )

if __name__ == "__main__":
    main()

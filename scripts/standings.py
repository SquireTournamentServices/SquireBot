import sys
import os

projectBaseDir = os.path.dirname(os.path.realpath(__file__)) + "/../"

sys.path.insert( 0, projectBaseDir + 'Tournament')
sys.path.insert( 0, projectBaseDir )

from Tournament import *


tournDir = sys.argv[1]

if tournDir[-1] == "/":
    tournDir = tournDir[:-1]

tourn = tournamentSelector( f'{tournDir}/tournamentType.xml', f'{tournDir}', "PWP" )
tourn.loadTournament( f'{tournDir}' )

for s in tourn.getStandings():
    print( s )

exit()


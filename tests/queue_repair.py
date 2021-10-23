import os
import sys
import asyncio

projectBaseDir = os.path.dirname(os.path.realpath(__file__)) + "/../"

sys.path.insert( 0, projectBaseDir + 'Tournament')
sys.path.insert( 0, projectBaseDir )

from Tournament import pairingQueue, matchRegistry, playerRegistry

playerReg = playerRegistry.PlayerRegistry()
matchReg  = matchRegistry.MatchRegistry()
matchReg.setPlayerRegistry( playerReg )
queue = pairingQueue()

for i in range(40):
    plyr = playerReg.createPlayer( f'Player {i+1}' )
    if not plyr is None:
        queue.addPlayer( plyr )

async def pair( ):
    pairings = queue.createPairings( 4 )
    for p in pairings:
        print( p )
        p = [ playerReg.getPlayer(plyr) for plyr in p ]
        mtch = matchReg.createMatch( )
        for plyr in p:
            mtch.addPlayer( plyr )
        await mtch.recordResult( p[0], "win" )
        for plyr in p[1:]:
            await mtch.confirmResult( plyr )
        print( mtch )

def main( ):
    loop = asyncio.new_event_loop()
    print( "\nPairing once\n" )
    loop.run_until_complete( pair() )
    for plyr in playerReg.players:
        print( f'{plyr.getName()}: {[p.getName() for p in plyr.opponents]}' )
    print( "\nPairing again\n" )
    loop.run_until_complete( pair() )
    for plyr in playerReg.players:
        print( f'{plyr.getName()}: {[p.getName() for p in plyr.opponents]}' )
    print( "\nPairing again\n" )
    loop.run_until_complete( pair() )
    for plyr in playerReg.players:
        print( f'{plyr.getName()}: {[p.getName() for p in plyr.opponents]}' )
    print( "\nPairing again\n" )
    loop.run_until_complete( pair() )
    for plyr in playerReg.players:
        print( f'{plyr.getName()}: {[p.getName() for p in plyr.opponents]}' )

if __name__ == "__main__":
    main( )

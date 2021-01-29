import sys
import os
import statistics
import threading
import time

from decimal import Decimal
from numpy.random import normal

import xml.etree.ElementTree as ET

projectBaseDir = os.path.dirname(os.path.realpath(__file__)) + "/../"

sys.path.insert( 0, projectBaseDir + 'Tournament')
sys.path.insert( 0, projectBaseDir )

from Tournament import *



# To speed up the tourn sim
timeRatio = 1/600
# The string that indicates that a player wants to LFG
lfgKey    = "@!766808531109281802"

# The number of players to simulate
plyrCount = 200
# The length of the pairings (in seconds)
roundTime = 6*60*60*timeRatio

# The mean and std. dev. of game times (in seconds)
gameTimeAvg = 55*60
gameTimeDev = 15*60
# The mean and std. dev. of requeue times (in seconds)
queueWaitAvg = 1*60
queueWaitDev = 0.5*60


def splitTime( time: str ) -> float:
    time = [ float(t) for t in time.split(" ")[1].split(":") ]
    return 60*60*time[0] + 60*time[1] + time[2]

def timeDifference( t_1: str, t_2: str ) -> float:
    return abs( splitTime( t_1 ) - splitTime( t_2 ) )

def format_e(n):
    a = '%E' % n
    return a.split('E')[0].rstrip('0').rstrip('.') + 'E' + a.split('E')[1]   

def cleanMatch( a_mtch ):
    waitTime = normal( loc=gameTimeAvg, scale=gameTimeDev )*timeRatio
    matchTimes.append( waitTime )
    time.sleep( waitTime )
    a_mtch.winner = a_mtch.activePlayers[0]
    a_mtch.status = "certified"
    requeueTimes = [ abs(normal( loc=queueWaitAvg, scale=queueWaitDev )*timeRatio) for _ in range(4) ]
    requeueTimes.sort( )
    requeueTimes[3] -= requeueTimes[2]
    requeueTimes[2] -= requeueTimes[1]
    requeueTimes[1] -= requeueTimes[0]
    for i in range(4):
        time.sleep( requeueTimes[i] )
        tourn.addPlayerToQueue( a_mtch.activePlayers[i] )



players = [ f'Player {i}' for i in range(plyrCount) ]


tourn = tournament( "Tourn Sim", "N/A" )
tourn.pairingWaitTime *= timeRatio
for plyr in players:
    tourn.activePlayers[plyr] = player( plyr )
for plyr in players:
    tourn.addPlayerToQueue( plyr )

matchTimes = [ ]
totalTime = 0
index     = 0
threads = [ ]

while totalTime < roundTime:
    time.sleep( tourn.pairingWaitTime )
    while index < len(tourn.matches):
        threads.append( threading.Thread( target=cleanMatch, args=(tourn.matches[index],) ) )
        threads[-1].start()
        index += 1
    totalTime += tourn.pairingWaitTime

for t in threads:
    t.join( )


tourn.pairingsThread.join()
tourn.loop.stop()

# -------------------------------------------------------
# The tournament simulation is done. We now have to
# process the queue activity to find the average wait time
# -------------------------------------------------------

times = [ ]
players = { }

print( tourn.queueActivity[0] )
# The queue active is a list of tuples containing the player's name and the time that they entered the queue
for act in tourn.queueActivity:
    if not act[0] in players:
        players[act[0]] = act[1]
    else:
        times.append( timeDifference( act[1], players[act[0]] )/timeRatio )
        print( format_e( Decimal(times[-1]) ) )
        del( players[act[0]] )

print( tourn.getStandings() )

print( f'There were {tourn.fail_count} threading failures.' )
times.sort()
print( f'The average wait time is: {statistics.mean( times )} seconds' )
print( f'The median wait time is: {statistics.median( times )} seconds' )
print( f'The longest wait time is: {times[-1]} seconds' )
print( f'The highest priority level is: {tourn.highestPriority}' )
matchTimes.sort()
print( f'The number of matches is: {len(tourn.matches)}' )
print( f'The average time is: {statistics.mean( matchTimes )/timeRatio} seconds' )
print( f'The median time is: {statistics.median( matchTimes )/timeRatio} seconds' )
print( f'The longest time is: {matchTimes[-1]/timeRatio} seconds' )



with open( "queueActivity.txt", "w" ) as f:
    for act in tourn.queueActivity:
        f.write( f'{act[0]}, {act[1]}\n' )



tourn.saveMatches( "./tester" )







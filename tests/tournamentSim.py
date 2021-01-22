import sys
import os
import statistics

from decimal import Decimal
import xml.etree.ElementTree as ET

projectBaseDir = os.path.dirname(os.path.realpath(__file__)) + "/../"

sys.path.insert( 0, projectBaseDir + 'Tournament')
sys.path.insert( 0, projectBaseDir )

from Tournament import *

# To speed up the tourn sim
timeRatio = 1/600
# The string that indicates that a player wants to LFG
lfgKey    = "@!766808531109281802"

def splitTime( time: str ) -> float:
    time = [ float(t) for t in time.split(" ")[1].split(":") ]
    return 24*60*time[0] + 60*time[1] + time[2]

def timeDifference( t_1: str, t_2: str ) -> float:
    return abs( splitTime( t_1 ) - splitTime( t_2 ) )

def format_e(n):
    a = '%E' % n
    return a.split('E')[0].rstrip('0').rstrip('.') + 'E' + a.split('E')[1]   


lfgData = ET.parse( "./matchmakingTestData.xml" ).getroot( )
messages = lfgData.findall( "message" )

players = [ ]
for msg in messages:
    if msg.attrib["author"] not in players:
        players.append( msg.attrib["author"] )

print( f'There are {len(players)} players about to be registered.' )

tourn = tournament( "Tourn Sim", "N/A" )
tourn.pairingWaitTime *= timeRatio
for plyr in players:
    tourn.activePlayers[plyr] = player( plyr )

print( f'There are {len(tourn.activePlayers)} players registered.' )

for i in range(len(messages[:-1])):
    print( f'Next message in {timeDifference( messages[i].attrib["time"], messages[i+1].attrib["time"] )*timeRatio} seconds' )

#time.sleep( 60 )

for i in range(len(messages[:-1])):
    plyr = tourn.activePlayers[messages[i].attrib["author"]]
    if plyr.hasOpenMatch():
        plyr.findOpenMatch().winner = plyr.name
        plyr.findOpenMatch().status = "certified"
    if lfgKey in messages[i].text:
        tourn.addPlayerToQueue( plyr.name )
        print( f'Added player to queue. Current queue size is {sum([len(lvl) for lvl in tourn.queue])}.' )
    t = timeDifference( messages[i].attrib["time"], messages[i+1].attrib["time"] )*timeRatio
    if t > 1.0:
        t = 1.0
    print( f'Next message in {t} seconds' )
    time.sleep( t )


tourn.pairingsThread.join()

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

times.sort()
print( f'The average wait time is: {statistics.mean( times )} seconds' )
print( f'The median wait time is: {statistics.median( times )} seconds' )
print( f'The longest wait time is: {times[-1]} seconds' )
print( f'The highest priority level is: {tourn.highestPriority}' )


with open( "queueActivity.txt", "w" ) as f:
    for act in tourn.queueActivity:
        f.write( f'{act[0]}, {act[1]}\n' )



tourn.saveMatches( "./tester" )







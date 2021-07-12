#! /usr/bin/python3
import os
import sys

projectBaseDir = os.path.dirname(os.path.realpath(__file__)) + "/../"

sys.path.insert( 0, projectBaseDir + 'Tournament')
sys.path.insert( 0, projectBaseDir )

from Tournament import *

queue = pairingQueue( )

players = [ player(i, f'[{i}]') for i in range(50) ]

for p in players:
    queue.addPlayer( p )

print( queue )

pairings = queue.createPairings( 4 )

for p in pairings:
    print( ", ".join( [ plyr.getMention() for plyr in p ] ) )




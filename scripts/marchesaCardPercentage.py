#! /usr/bin/python3

import sys
import os
import time

from decimal import Decimal

import xml.etree.ElementTree as ET

projectBaseDir = os.path.dirname(os.path.realpath(__file__)) + "/../"

sys.path.insert( 0, projectBaseDir + 'Tournament')
sys.path.insert( 0, projectBaseDir )

from Tournament import *


marchesa = fluidRoundTournament("Marchesa", "Monarch")
marchesa.loadTournament( "Marchesa" )

cards = list(  )
count = dict( )
countPerPlayer = dict( )

totalDeckCount = 0

for p in marchesa.players.values():
    firstDeck = True
    for d in p.decks.values():
        if len(d.cards) < 10:
            continue
        totalDeckCount += 1
        for c in d.cards:
            if "SB:" in c:
                c = c.split(" ", 1)[-1]
            c = c.split(" ", 1)[-1].strip().lower()
            if not c in countPerPlayer:
                countPerPlayer[c] = 1
            elif firstDeck:
                countPerPlayer[c] += 1
            if not c in cards:
                count[c] = 0
                cards.append(c)
            count[c] += 1
        firstDeck = False

print( cards )

cardCount = totalDeckCount * 100
playersWithDecks = len( [p for p in marchesa.players.values() if len(p.decks) > 0 ] )

cards.sort( )
cards.sort( key=lambda c: count[c], reverse=True )

for c in cards:
    print( f'{c}: {count[c]}' )

with open("cardData.csv", "w") as output:
    output.write( f'There were {totalDeckCount} decks submitted by {playersWithDecks} players.\n' )
    output.write( f'Card Name, Total Count, Percentage, Number of Players with Card, Percentage\n' )
    for c in cards:
        output.write( f'{c.replace(",", "")}, {count[c]}, {trunk(count[c]/totalDeckCount)}, {countPerPlayer[c]}, {trunk(countPerPlayer[c]/playersWithDecks)}\n' )



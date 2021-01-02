import sys
import os

projectBaseDir = os.path.dirname(os.path.realpath(__file__)) + "/../"

sys.path.insert( 0, projectBaseDir + 'Tournament')
sys.path.insert( 0, projectBaseDir )

from Tournament import *


newMatch = match( [ "Johnny", "Jill" ] )

matchArr = [ ]
matchArr.append( newMatch )
print( matchArr[-1].activePlayers )
newMatch.activePlayers.append( "Spike" )
print( matchArr[-1].activePlayers )

newTourn = tournament( "tester", "Testing Grounds" )
newTourn.activePlayers["Johny"] = player( "Johny" ) 
newTourn.activePlayers["Jill" ] = player( "Jill"  ) 
newTourn.activePlayers["Timmy"] = player( "Timmy" ) 
newTourn.activePlayers["Tammy"] = player( "Tammy" ) 
newTourn.activePlayers["Spike"] = player( "Spike" ) 

newTourn.playersPerMatch = 5

newTourn.addPlayerToQueue( "Johny" )
newTourn.addPlayerToQueue( "Jill"  )
newTourn.addPlayerToQueue( "Timmy" )
newTourn.addPlayerToQueue( "Tammy" )
newTourn.addPlayerToQueue( "Spike" )

print( newTourn.uniqueMatches[-1] )
print( newTourn.activePlayers["Timmy"].matches[-1] )
print( newTourn.activePlayers["Tammy"].matches[-1] )
print( "" )

newTourn.playerMatchDrop( "Timmy" ) 

print( newTourn.uniqueMatches[-1] )
print( newTourn.activePlayers["Timmy"].matches[-1] )
print( newTourn.activePlayers["Tammy"].matches[-1] )
print( "" )

newTourn.recordMatchWin( "Spike" )

print( newTourn.uniqueMatches[-1] )
print( newTourn.uncertMatches["Tammy"] )
print( newTourn.activePlayers["Timmy"].matches[-1] )
print( newTourn.activePlayers["Tammy"].matches[-1] )
print( "" )

newTourn.playerCertifyResult( "Johny" )

print( newTourn.uniqueMatches[-1] )
print( newTourn.uncertMatches["Tammy"] )
print( newTourn.activePlayers["Timmy"].matches[-1] )
print( newTourn.activePlayers["Tammy"].matches[-1] )
print( "" )

newTourn.recordMatchDraw( "Jill"  )

print( newTourn.uniqueMatches[-1] )
print( newTourn.activePlayers["Timmy"].matches[-1] )
print( newTourn.activePlayers["Tammy"].matches[-1] )
print( "" )

newTourn.playerCertifyResult( "Johny" )
newTourn.playerCertifyResult( "Tammy" )
newTourn.playerCertifyResult( "Spike" )

print( newTourn.uniqueMatches[-1] )
print( newTourn.activePlayers["Timmy"].matches[-1] )
print( newTourn.activePlayers["Tammy"].matches[-1] )
print( "" )













from tournament.tournament import tournament
from tournament.player import player
from tournament.match import match
from tournament.deck import deck
from tournament.tournamentUtils import *


tournDir = "openTournaments/tester/"

dummyTourn = tournament( "tester", "Testing Grounds" )

dummyTourn.activePlayers["Timmy"] = player( "" )
dummyTourn.activePlayers["Timmy"].playerName = "Timmy"
dummyTourn.activePlayers["Timmy"].addDeck( "Elsha", "1 Elsha of the Infinite" )
dummyTourn.activePlayers["Tammy"] = player( "" )
dummyTourn.activePlayers["Tammy"].playerName = "Tammy"
dummyTourn.activePlayers["Tammy"].addDeck( "Elsha", "1 Elsha of the Infinite" )

dummyTourn.activePlayers["Johnny"] = player( "" )
dummyTourn.activePlayers["Johnny"].playerName = "Johnny"
dummyTourn.activePlayers["Johnny"].addDeck( "Elsha", "1 Elsha of the Infinite" )
dummyTourn.activePlayers["Jill"] = player( "" )
dummyTourn.activePlayers["Jill"].playerName = "Jill"
dummyTourn.activePlayers["Jill"].addDeck( "Elsha", "1 Elsha of the Infinite" )

dummyTourn.activePlayers["Spike"] = player( "" )
dummyTourn.activePlayers["Spike"].playerName = "Spike"
dummyTourn.activePlayers["Spike"].addDeck( "Elsha", "1 Elsha of the Infinite" )


dummyTourn.addPlayerToQueue( "Timmy" )
dummyTourn.addPlayerToQueue( "Tammy" )
dummyTourn.addPlayerToQueue( "Johnny" )
dummyTourn.addPlayerToQueue( "Jill" )
dummyTourn.addPlayerToQueue( "Spike" )




dummyTourn.saveTournament( tournDir )


otherTourn = tournament( "", "" )
otherTourn.loadTournament( tournDir )

print( "This is from the saved tournament:" )
print( dummyTourn.tournName )
print( dummyTourn.hostGuildName )
print( dummyTourn.format    )
print( dummyTourn.regOpen      )
print( dummyTourn.tournStarted )
print( dummyTourn.tournEnded   )
print( dummyTourn.tournCancel  )
print( dummyTourn.playersPerMatch )
print( dummyTourn.playerQueue )
print( dummyTourn.activePlayers )
print( dummyTourn.droppedPlayers )
print( "" )
print( "This is from the loaded tournament:" )
print( otherTourn.tournName )
print( otherTourn.hostGuildName )
print( otherTourn.format    )
print( otherTourn.regOpen      )
print( otherTourn.tournStarted )
print( otherTourn.tournEnded   )
print( otherTourn.tournCancel  )
print( otherTourn.playersPerMatch )
print( otherTourn.playerQueue )
print( otherTourn.activePlayers )
print( otherTourn.droppedPlayers )

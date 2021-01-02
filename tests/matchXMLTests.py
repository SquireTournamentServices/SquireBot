from match import match


m1 = match( [] )
m1.activePlayers.append( "Johnny" )
m1.activePlayers.append( "Jill" )
m1.activePlayers.append( "Tammy" )
m1.activePlayers.append( "Timmy" )
m1.activePlayers.append( "Spike" )

m1.dropPlayer( "Johnny" )

m1.saveXML( "matchTester.xml" )

m2 = match( [] )
m2.loadXML( "matchTester.xml" )
print( "This is m1:" )
print( m1.status )
print( m1.winner )
print( m1.activePlayers )
print( m1.droppedPlayers )
print( m1.confirmedPlayers )
print( "This is m2:" )
print( m2.status )
print( m2.winner )
print( m2.activePlayers )
print( m2.droppedPlayers )
print( m2.confirmedPlayers )





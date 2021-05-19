import os
import xml.etree.ElementTree as ET


from .tournament import *
from .fluidRoundTournament import *


tournamentTypes = [ "fluidRoundTournament" ]

def getTournamentType( tournType: str, tournName: str = "", guildName: str = "" ):
    if tournType == "fluidRoundTournament":
        return fluidRoundTournament( tournName, guildName )
    else:
        return None
    

def tournamentSelector( typeFile: str, tournName: str = "", guildName: str = "" ):
    tournType = ET.parse( typeFile ).getroot().text
    if tournType == "fluidRoundTournament":
        return fluidRoundTournament( tournName, guildName )
    else:
        raise NotImplementedError( f'{tournType} is not a supported tournament type' )




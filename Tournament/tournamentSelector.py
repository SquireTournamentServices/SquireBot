import os
import xml.etree.ElementTree as ET


from .tournament import *
from .fluidRoundTournament import *


tournamentTypes = [ "fluidRoundTournament" ]

def getTournamentType( tournType: str, tournName: str = "", guildName: str = "", tournProps: dict = { } ):
    tournType = tournType.strip().lower()
    t = None
    if tournType == "fluidroundtournament":
        t = fluidRoundTournament( tournName, guildName, tournProps )
    
    return t
    

def tournamentSelector( typeFile: str, tournName: str = "", guildName: str = "", tournProps: dict = { } ):
    tournType = ET.parse( typeFile ).getroot().text
    digest = getTournamentType( tournType, tournName, guildName, tournProps )
    if digest is None:
        raise NotImplementedError( f'{tournType} is not a supported tournament type' )
    return digest




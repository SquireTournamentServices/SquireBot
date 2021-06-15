import os
import xml.etree.ElementTree as ET


from .tournament import *
from .fluidRoundTournament import *


tournamentTypes = [ "fluidRoundTournament" ]

def getTournamentType( tournType: str, tournName: str = "", guildName: str = "", tournProps: dict = { } ):
    tournType = tournType.strip().lower()
    digest = None
    if tournType == "fluidroundtournament":
        digest = fluidRoundTournament( tournName, guildName, tournProps )
    
    return digest
    

def tournamentSelector( typeFile: str, tournName: str = "", guildName: str = "", tournProps: dict = { } ):
    tournType = ET.parse( typeFile ).getroot().text
    digest = getTournamentType( tournType, tournName, guildName, tournProps )
    if digest is None:
        raise NotImplementedError( f'{tournType} is not a supported tournament type' )
    return digest


def filterProperties( props: Dict ) -> Dict:
    """Tracks a dict of potential tournament properties and converts to ensure they're 'level'"""
    digest: dict = { "successes": dict(), "failures": dict(), "undefined": dict() } 

    # A list of filtered dicts of properties of the form { "successes": dict(), "failures": dict(), "undefined": dict() }
    filteredDefaults: list = [ ]
    
    # Passing the adjusted defaults through the base fluidRoundsTournament
    filteredDefaults.append( fluidRoundTournament.filterProperties( props ) )
     
    # TODO: As more tournaments types are added, this process will need to grow
    
    # Combine the filtered values into the return value
    # If a property fails due to one tournament, but successed from another,
    # that property is a failure.  This *shouldn't* happen, though.
    for prop in props:
        isFailure = False
        isSuccess = False
        for propSet in filteredDefaults:
            if prop in propSet["failures"]:
                isFailure = True
                break
            if prop in propSet["successes"]:
                isSuccess = True
        if isFailure:
            digest["failures"][prop] = props[prop]
        elif isSuccess:
            digest["successes"][prop] = propSet["successes"][prop]
        else:
            digest["undefined"][prop] = props[prop]
    
    return digest
        
        





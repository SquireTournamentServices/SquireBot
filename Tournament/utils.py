""" This modules contains various methods and consts for SquireBot """
import string
import re

from typing import Dict, List
from datetime import datetime

import discord


convDict = {
    int(c, 32): c for c in (string.digits + string.ascii_lowercase)[:32]
}  # convert from integer to base32hex symbols

TFORM = "%Y-%m-%d %H:%M:%S.%f"

def numberToBase(n: int, b: int) -> int:
    """Converts a number in base 10 to base b"""
    if n == 0:
        return [0]
    digits = []
    while n:
        digits.append(int(n % b))
        n //= b
    return digits[::-1]

def str_to_bool( newBool: str ) -> bool:
    """ Converts str to bool, return None if neither """
    newBool = newBool.lower()
    if newBool in [ "t", "true", "1" ]:
        return True
    elif newBool in [ "f", "false", "0" ]:
        return False

    return None

def trunk( score ) -> str:
    """ Trunkates doubles to 2 decimal places """
    if not isinstance(score, str):
        score = str(score)
    score = score.split(".")
    if len(score) > 1:
        score[1] = score[1][:2]
    return ".".join(score)

def getTime( ) -> str:
    return datetime.utcnow().strftime(TFORM)

def Union( vals: List ) -> bool:
    """ Applies a logical OR to a list of bools """
    digest = vals[0]
    for val in vals[1:]:
        digest |= val
    return digest

def Intersection( vals: List ) -> bool:
    """ Applies a logical AND to a list of bools """
    digest = vals[0]
    for val in vals[1:]:
        digest &= val
    return digest

# Finds the difference (in second) between two times given by getTime()
def timeDiff( tOne: str, tTwo: str ) -> float:
    """ Gets the difference between two times in TFORM """
    diff = datetime.strptime( tOne, TFORM ) - datetime.strptime( tTwo, TFORM )
    digest = diff.days*24*60*60 + diff.seconds + diff.microseconds*10**-6
    return abs(digest)

def getAdminRole( duild: discord.Guild ):
    """ TODO: Soon to be depricated method """
    ret = ""
    for role in duild.roles:
        if str(role).lower() == "tournament admin":
            ret = role
            break
    return ret

def getJudgeRole( duild: discord.Guild ):
    """ TODO: Soon to be depricated method """
    digest = ""
    for role in duild.roles:
        if str(role).lower() == "judge":
            digest = role
            break
    return digest

def get_ID_from_mention( mention: str ) -> str:
    """ Gets a Discord ID from a Discord mention string """
    if mention is None:
        return None
    return re.sub( r"<@[^0-9]?([0-9]+)>", r"\1", mention )

def getPrimaryType( types: List[str] ) -> str:
    if   "Creature" in types:
        return "Creature"
    elif "Land" in types:
        return "Land"
    elif "Artifact" in types:
        return "Artifact"
    elif "Enchantment" in types:
        return "Enchantment"
    elif "Instant" in types:
        return "Instant"
    elif "Sorcery" in types:
        return "Sorcery"
    elif "Planeswalker" in types:
        return "Planeswalker"
    else:
        return types[0]

# Takes in any number of arguments (likely from a command call) and returns a dict
# The keys of the dict are tournament properties (other key/value pairs are discarded)
# The delimiter between properties and values is an equal sign.
#   - example input: match-size= 1 hello = foo bar tricebot-enabled = true Format =EDH
#             output: { "match-size": "1", "hello", "foo bar" "tricebot-enabled": "true", "format": "EDH"}
def generatePropsDict( *args ) -> Dict:
    """ Converts a user-input group of properties to a dict """
    args: list = [ segment.strip().lower() for segment in " ".join(args).split("=") ]
    digest: dict = { }
    pastSegement: list = [ args[0] ]
    for i in range(1,len(args)):
        segment = args[i].rsplit( " " )
        digest[pastSegement[-1].strip()] = segment[0].strip()
        pastSegement = segment
    toDelete = [ ]
    return digest


problemChars = { '"': "&quot",
                 "'": "&apos",
                 "<": "&lt",
                 ">": "&gt",
                 "&": "&amp"
               }

def isPathSafeName(name: str) -> bool:
    """ Checks to see if a name can be a file/dir """
    digest = ("~" in name) or ("/" in name)
    for char in problemChars:
        digest |= (char in name)
    return digest

def toPathSafe(name: str) -> bool:
    """ Changes a name to be a safe file/dir name """
    #bad chars are xml chars, "~", and "../" as it is a directory buggerer
    digest = name.replace("~", "_").replace("/", "_")
    for char in problemChars:
        digest = digest.replace(char, "_")
    return digest

def toSafeXML( inputXML: str ) -> str:
    """ Adds XML escape chars where needed """
    if inputXML is None:
        return "" # Check for None
    digest = str(inputXML)
    for char in problemChars:
        digest.replace(char, problemChars[char])
    return digest

def fromXML( inputXML: str ) -> str:
    """ Expands XML escape chars (because the XML library doesn't) """
    digest = str(inputXML)
    for char in problemChars:
        digest.replace(problemChars[char], char)
    return digest


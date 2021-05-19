import string
import discord

from datetime import datetime


conv_dict = {
    int(c, 32): c for c in (string.digits + string.ascii_lowercase)[:32]
}  # convert from integer to base32hex symbols

t_form = "%Y-%m-%d %H:%M:%S.%f"

def number_to_base(n: int, b: int) -> int:
    """Converts a number in base 10 to base b"""
    if n == 0:
        return [0]
    digits = []
    while n:
        digits.append(int(n % b))
        n //= b
    return digits[::-1]

def str_to_bool( s: str ) -> bool:
    s = s.lower()
    if s == "t" or s == "true":
        return True
    return False

def trunk( score ) -> str:
    if type(score) != str:
        score = str(score)
    score = score.split(".")
    if len(score) > 1:
        score[1] = score[1][:2]
    return ".".join(score) 

def getTime( ) -> str:
    return datetime.utcnow().strftime(t_form)

# Finds the difference (in second) between two times given by getTime()
def timeDiff( t_1: str, t_2: str ) -> float:
    t_diff = datetime.strptime( t_1, t_form ) - datetime.strptime( t_2, t_form ) 
    digest = t_diff.days*24*60*60 + t_diff.seconds + t_diff.microseconds*10**-6
    return abs(digest)

#def getUserIdent( a_user: discord.Member ) -> str:
#    l_name = a_user.name.replace("/", "_").replace("\"", "_").replace("\'", "_")
#    return f'{l_name}#{a_user.discriminator}'

def getAdminRole( a_guild: discord.Guild ):
    ret = ""
    for role in a_guild.roles:
        if str(role).lower() == "tournament admin":
            ret = role
            break
    return ret

def getJudgeRole( a_guild: discord.Guild ):
    digest = ""
    for role in a_guild.roles:
        if str(role).lower() == "judge":
            digest = role
            break
    return digest

problem_chars = { '"': "&quot",
                  "'": "&apos",
                  "<": "&lt",
                  ">": "&gt",
                  "&": "&amp"
                }

def isPathSafeName(name: str) -> bool:
    #bad chars are xml chars, "~", and "../" as it is a directory buggerer
    digest = ("~" in name) or ("/" in name)
    for c in problem_chars:
        digest |= (c in name)
    return digest

def toPathSafe(name: str) -> bool:
    #bad chars are xml chars, "~", and "../" as it is a directory buggerer
    digest = name.replace("~", "_").replace("/", "_")
    for c in problem_chars:
        digest = digest.replace(c, "_")
    return digest

def toSafeXML( input_XML: str ) -> str:
    digest = str(input_XML)
    for c in problem_chars:
        digest.replace(c, problem_chars[c])
    return digest

#Shouldn't be needed as the reader should expand XML escaped chars but has to be as the xml library is dumb
def fromXML( input_XML: str ) -> str:
    digest = str(input_XML)
    for c in problem_chars:
        digest.replace(problem_chars[c], c)
    return digest


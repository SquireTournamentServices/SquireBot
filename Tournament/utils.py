import string
import discord

from datetime import datetime


conv_dict = {
    int(c, 32): c for c in (string.digits + string.ascii_lowercase)[:32]
}  # convert from integer to base32hex symbols

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
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')

# Finds the difference (in second) between two times given by getTime()
def timeDiff( t_1: str, t_2: str ) -> float:
    t_1 = t_1.split(" ")
    t_2 = t_2.split(" ")
    digest = 0
    if t_1[0] != t_2[0]:
        t_1[0] = datetime.strptime(t_1[0], '%Y-%m-%d')
        t_2[0] = datetime.strptime(t_2[0], '%Y-%m-%d')
        digest += 60*60*24*( abs((t_2[0] - t_1[0]).days) + 1 )
    t_1[1] = t_1[1].split(":")
    t_2[1] = t_2[1].split(":")
    t = [ abs( float(t_2[1][i]) - float(t_1[1][i]) ) for i in range(len(t_1[1])) ]
    digest += 60*60*t[0] + 60*t[1] + t[2]
    return digest

def getUserIdent( a_user: discord.Member ) -> str:
    l_name = a_user.name.replace("/", "_").replace("\"", "_").replace("\'", "_")
    return f'{l_name}#{a_user.discriminator}'

def getAdminRole( a_guild: discord.Guild ):
    ret = ""
    for role in a_guild.roles:
        if str(role).lower() == "tournament admin":
            ret = role
            break
    return ret



import string
import discord


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



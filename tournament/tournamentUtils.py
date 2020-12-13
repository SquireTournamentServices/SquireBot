import string


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


class UID:
    currentID = [0]
        
    def getNewID( self ):
        ret = self.currentID[0]
        self.currentID[0] += 1
        return ret




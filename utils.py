

def get_signed_int(x):
    """
    Returns a signed integer from the byte
    :param x:  Byte
    """
    if (x & 0x80) >> 7 == 1:
        return -((x-1) ^ 0xff)
    else:
        return x

def to_signed_binary(x):
    """
    Converts the signed integer to a 2s-complement byte.
    """
    if x > 0:
        return x & 0xff
    elif x < 0:
        return ((-x) ^ 0xff) + 1
    else:
        return 0



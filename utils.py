

def byte_to_signed_int(x):
    """
    Returns a signed integer from the byte
    :param x:  Byte
    """
    if (x & 0x80) >> 7 == 1:
        return -((x-1) ^ 0xff)
    else:
        return x

def int_to_signed_byte(x):
    """
    Converts the signed integer to a 2s-complement byte.
    """
    if x > 0:
        return x & 0xff
    elif x < 0:
        return ((-x) ^ 0xff) + 1
    else:
        return 0

def word_to_signed_int(x):
    """
    returns a signed integer from the word (2-bytes)
    :param x: two-bytes to convert to a signed number
    """
    pass


def is_negative(b):
    """Returns True if the given byte represents a negative number.
    """
    return ((b >> 7) & 0x1) == 1


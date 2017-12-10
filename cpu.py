from collections import namedtuple


class InvalidFlagException(Exception):
    def __init__(self, flag):
        self._msg = "{0}: Invalid condition flag.".format(flag)

    def __repr__(self):
        return self._msg


class Flags:
    """
    Condition flags for 8080 are
    Bit     Name              Use
    0       carry             1 if carry out of high bit or borrow from high bit
    1       <unused>          Always one
    2       parity            1 if number of one bits is even, 0 otherwise
    3       <unused>          Always zero
    4       auxiliary carry   1 if carry out of bit 3 or borrow from 4th bit
    5       <unused>          Always zero
    6       zero              1 of operation resulted in zero
    7       sign              Set to most significant bit of result (bit 7)
    """
    CARRY = 0
    PARITY = 2
    AUX_CARRY = 3
    ZERO = 6
    SIGN = 7

    def __init__(self):
        self.flags = 2  # the second bit is always 1
        self._valid_bits = (Flags.CARRY, Flags.PARITY,
                            Flags.AUX_CARRY, Flags.ZERO,
                            Flags.SIGN)

    def set(self, bit):
        """
        Sets (to one) the given condition flag
        :param bit:  Bit (defined by ConditionFlags constants) to set
        :return:
        :raises InvalidFlagException: if an invalid flag is given
        """
        if bit not in self._valid_bits:
            raise InvalidFlagException(bit)
        self._set_flag(bit)

    def clear(self, bit):
        """
        Clears (sets to zero) the given condition flag
        :param bit:  Bit (defined by ConditionFlags constants) to set
        :return:
        :raises InvalidFlagException: if an invalid flag is given
        """
        if bit not in self._valid_bits:
            raise InvalidFlagException (bit)
        self._clear_flag(bit)

    def __getitem__(self, key):
        """
        Used to get the value (0 or 1) of the given bit
        :param key:
        :return: value of given flag
        """
        if type(key) != int:
            raise TypeError("Expected bit-number of flag")
        if key not in self._valid_bits:
            raise IndexError(key)

        return (self.flags & 2 ** key) >> key

    def _set_flag(self, bit):
        """
        Set condition flag bit.
        :param bit: the flag to set
        :return:
        """
        self.flags |= 2**bit

    def _clear_flag(self, bit):
        """
        Set flag to zero
        :param bit:  bit to clear
        :return:
        """
        self.flags &= ~ 2**bit


class InvalidPairException(Exception):
    pass


RegisterPair = namedtuple("RegisterPair", ["hi", "lo"])


class Registers:
    """
    Encapsulates registers and provides easy access to them.
    """
    A = 0
    B = 1
    C = 2
    D = 3
    E = 4
    H = 5
    L = 6

    def __init__(self):
        self._registers = [0, 0, 0, 0, 0, 0, 0]
        self._pairs = { Registers.H: RegisterPair(Registers.H, Registers.L),
                        Registers.B: RegisterPair(Registers.B, Registers.C),
                        Registers.D: RegisterPair(Registers.D, Registers.E)}

    def __getitem__(self, reg):
        """
        Returns the value of the given register
        :param reg:
        :return:
        """
        if type(reg) != int:
            raise TypeError("Expected register number")
        if reg < Registers.A or reg > Registers.L:
            raise IndexError(reg)
        return self._registers[reg]

    def __setitem__(self, reg, val):
        if type(reg) != int:
            raise TypeError("Expected register number")
        if reg < Registers.A or reg > Registers.L:
            raise IndexError(reg)
        self._registers[reg] = val

    def get_address_from_pair(self, register):
        """
        Calculate an address from the given register pair.

        The first register of the pair is the most significant byte of the address.

        :param register: Register number that defines the pair.  Valid values: B, D, H
        :return: address calculated from two registers
        :raises: InvalidPairException if the register argument is invalid
        """
        if register not in self._pairs:
            raise InvalidPairException()
        pair = self._pairs[register]
        hi = self._registers[pair.hi]
        lo = self._registers[pair.lo]
        return (hi << 8) | lo

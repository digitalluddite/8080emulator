from unittest import TestCase

from cpu import Registers, InvalidPairException


class TestRegisters(TestCase):
    def setUp(self):
        self.reg = Registers()

    def test_get_address_from_pair(self):
        for hi,lo in ((Registers.B, Registers.C),
                      (Registers.D, Registers.E),
                      (Registers.H, Registers.L)):
            self.reg[hi] = 0x20
            self.reg[lo] = 0x10
            self.assertTrue(self.reg.get_address_from_pair(hi) == 0x2010)

        with self.assertRaises(InvalidPairException):
            for reg in (Registers.A, Registers.C, Registers.E, Registers.L):
                self.reg.get_address_from_pair(reg)


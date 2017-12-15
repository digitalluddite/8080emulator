from unittest import TestCase

from cpu import Flags


class TestConditionFlags(TestCase):
    def setUp(self):
        self.flags = Flags()
        self.bits = (Flags.CARRY, Flags.SIGN,
                     Flags.ZERO, Flags.AUX_CARRY,
                     Flags.PARITY)

    def test_set(self):
        for b in self.bits:
            self.flags.set(b)
            self.assertTrue(self.flags[b] == 1)

    def test_clear(self):
        self.flags.flags = 255
        for b in self.bits:
            self.flags.clear(b)
            self.assertTrue(self.flags[b] == 0)

    def test_calculate_parity(self):
        for b, res in [(0x00, 1), (0x01, 0), (0x02, 0), (0x03, 1), (0xe3, 0), (0xf3, 1)]: # 0xe3 == 1110 0011
            self.flags.calculate_parity(b)
            self.assertTrue(self.flags[Flags.PARITY] == res, f'Incorrect parity for {b}: expected {res}')

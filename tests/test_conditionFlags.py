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

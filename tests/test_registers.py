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

    def test_get_register_from_opcode(self):
        instructions = [0x40, 0x41, 0x42, 0x43, 0x4a, 0x4e, 0x7c, 0x65]
        expected_registers = [(Registers.B, Registers.B),
                              (Registers.B, Registers.C),
                              (Registers.B, Registers.D),
                              (Registers.B, Registers.E),
                              (Registers.C, Registers.D),
                              (Registers.C, Registers.M),
                              (Registers.A, Registers.H),
                              (Registers.H, Registers.L)]
        for i in range(8):
            code = instructions[i]
            expected_src = expected_registers[i][0]
            expected_dst = expected_registers[i][1]
            self.assertTrue(Registers.get_register_from_opcode(code, 3) == expected_src)
            self.assertTrue(Registers.get_register_from_opcode(code, 0) == expected_dst)
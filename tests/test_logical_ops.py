from unittest import TestCase
import logging

from machine import Machine8080
from cpu import Registers, Flags

class LogicalOpsTests(TestCase):
    def setUp(self):
        self.machine = Machine8080()
        self.machine.load("rom")
        logging.basicConfig(level=logging.DEBUG)

    def _test_flag(self, flag, name, expected):
        """Checks that the carry bit val is equal to expected.
        """
        self.assertEqual(self.machine._flags[flag], expected,
                        f'{name} not equal to {expected}')

    def set_flags(self, flags):
        """ Sets the given flags
        :param flags: iterable of (flag, value) tuples
        """
        for f,v in flags:
            self.set_flag(f,v)

    def set_register(self, reg, val):
        self.machine._registers[reg] = val

    def set_flag(self, flag, val):
        if val == 0:
            self.machine._flags.clear(flag)
        else:
            self.machine._flags.set(flag)
        
    def test_ana(self):
        """Logical AND.  
        Carry bit is cleared, zero, sign, and parity are affected

        Intel manual from Sept '75 says the AC bit is affected as 
        well, but not how it's affected

            1111 0011
        AND 0011 1111
            0011 0011 (0x33)
        """
        self.machine._flags.set(Flags.CARRY)
        # Verify ANA performs correct operation with each register  (Skip ANA M since it's memory)
        tests = [(0xa0, Registers.B, 0x33), (0xa1, Registers.C, 0x33), 
                 (0xa2, Registers.D, 0x33), (0xa3, Registers.E, 0x33), 
                 (0xa4, Registers.H, 0x33), (0xa5, Registers.L, 0x33),
                 (0xa7, Registers.A, 0x3f)]

        for opcode, reg, res in tests:
            self.machine._registers[Registers.A] = 0xf3
            self.machine._registers[reg] = 0x3f
            self.machine.ana(opcode)
            self.assertEqual(self.machine._registers[Registers.A], res,
                            f'Result of ANA (opcode: {opcode:02X}) {self.machine._registers[Registers.A]:02X} not {res:02X}')
            self._test_flag(Flags.CARRY, "Carry", 0)

        # test memory ANA opcode 0xa6
        self.machine.write_memory(0x5599, 0x33)
        self.machine._registers[Registers.H] = 0x55
        self.machine._registers[Registers.L] = 0x99
        self.machine._registers[Registers.A] = 0x3f
        self.machine.ana(0xa6)
        self.assertEqual(self.machine._registers[Registers.A], 0x33,
                        f'result of ANA M = {self.machine._registers[Registers.A]}, not 0x33')
        self._test_flag(Flags.CARRY, "Carry", 0)

        # verify CARRY flag is cleared
        self.machine._flags.set(Flags.CARRY)
        self.assertEqual(self.machine._flags[Flags.CARRY], 1, "Carry flag isn't set when it should be!")
        self.machine._registers[Registers.B] = 1
        self.machine._registers[Registers.A] = 3
        self.machine.ana(0xa0) # 0xa0 = ANA B
        self.assertEqual(self.machine._flags[Flags.CARRY], 0, "Carry flag isn't reset after ANA")

        # verify ZERO flag is set appropriately
        self.machine._flags.clear(Flags.ZERO)
        self.machine._registers[Registers.C] = 2
        self.machine._registers[Registers.A] = 6
        self.machine.ana(0xa1)
        self._test_flag(Flags.ZERO, "Zero", 0)

        # verify Zero flag is set
        self.machine._registers[Registers.C] = 0
        self.machine.ana(0xa1)
        self._test_flag(Flags.ZERO, "Zero", 1)

        # verify parity
        self.machine._flags.clear(Flags.PARITY)
        self.machine._registers[Registers.A] = 0x33  # 0011 0011
        self.machine._registers[Registers.D] = 0xf1  # 1111 0001  => 0011 0001  Parity should be 0
        self.machine.ana(0xa2)
        self._test_flag(Flags.PARITY, "Parity", 0)

        self.machine._registers[Registers.A] = 0x33  # 0011 0011
        self.machine._registers[Registers.D] = 0xf3  # 1111 0011  => 0011 0011  Parity should be 1
        self.machine.ana(0xa2)
        self._test_flag(Flags.PARITY, "Parity", 1)

        # verify sign
        # 1011 1100
        # 1001 0111  => 1001 0100
        self.machine._flags.clear(Flags.SIGN)
        self.machine._registers[Registers.D] = 0xbd
        self.machine._registers[Registers.A] = 0x97
        self.machine.ana(0xa2)
        self._test_flag(Flags.SIGN, "Sign", 1)

        self.machine._flags.set(Flags.SIGN)
        self.machine._registers[Registers.D] = 0x3d
        self.machine._registers[Registers.A] = 0x97
        self.machine.ana(0xa2)
        self._test_flag(Flags.SIGN, "Sign", 0)

    def test_ani(self):
        """Logical AND the immediate byte with the accumulator
        CY and AC are cleared
        Other flags set appropriately
        """
        pass

    def test_xra(self):
        """
        Exclusive-OR the register (or memory) specified in the opcode

        Carry and AC bits are cleared.
        Zero, sign, parity, auxiliary carry?

        The reference manual states that the carry bit is reset but doesn't say anything
        about the aux. carry bit.  The XRI instruction (xor immediate) does NOT affect
        the aux carry.  So I wonder if it was a mistake by the manual writers to include
        it here.  I've seen other mistakes in the document.

        (Modern Intel references state that the aux carry is undefined for this instruction)

        A different Intel 8080 Manual, from Sept. '75, says this instruction clears the AC flag
        """
        # test correct behavior with registers
        # Register = 0x5C  0101 1100
        # Accum.   = 0x78  0111 1000  XOR = 0010 0100
        tests = [(0xa8, Registers.B), (0xa9, Registers.C), (0xaa, Registers.D),
                 (0xab, Registers.E), (0xac, Registers.H), (0xad, Registers.L)]
        for op, reg in tests:
            self.machine._flags.set(Flags.CARRY)
            self.machine._flags.set(Flags.AUX_CARRY)
            self.machine._flags.clear(Flags.ZERO)

            self.machine._registers[reg] = 0x5C
            self.machine._registers[Registers.A] = 0x78
            self.machine._flags.set(Flags.CARRY)
            self.machine.xra(op)
            self.assertEqual(self.machine._registers[Registers.A], 0x24,
                            f'XRA ({op:02X}) expected 0x24 got {self.machine._registers[Registers.A]:02X}')

            self._test_flag(Flags.CARRY, "Carry", 0)
            self._test_flag(Flags.AUX_CARRY, "Aux.Carry", 0)
            self._test_flag(Flags.ZERO, "Zero", 0)

        # A ^ A = 0
        self.machine._flags.set(Flags.CARRY)
        self.machine._flags.set(Flags.AUX_CARRY)
        self.machine.xra(0xaf)
        self.assertEqual(self.machine._registers[Registers.A], 0,
                        f'A ^ A = {self.machine._registers[Registers.A]}')
        self._test_flag(Flags.CARRY, "Carry", 0)
        self._test_flag(Flags.AUX_CARRY, "Aux. Carry", 0)
        self._test_flag(Flags.ZERO, "Zero", 1)

        # test correct behavior with memory
        self.machine.write_memory(0x72aa, 0x5c)
        self.machine._registers[Registers.H] = 0x72
        self.machine._registers[Registers.L] = 0xaa
        self.machine._registers[Registers.A] = 0x78
        self.machine._flags.set(Flags.CARRY)
        self.machine._flags.set(Flags.AUX_CARRY)
        self.machine.xra(0xae)
        self.assertEqual(self.machine._registers[Registers.A], 0x24,
                        f'XRA M expected 0x24 got {self.machine._registers[Registers.A]:02X}')
        self._test_flag(Flags.CARRY, "Carry", 0)
        self._test_flag(Flags.AUX_CARRY, "Aux. Carry", 0)

        # test sign bit is set/cleared
        # 0110 0100
        # 0010 1111 => 0100 1011
        self.machine._flags.set(Flags.SIGN)
        self.machine._registers[Registers.B] = 0x64
        self.machine._registers[Registers.A] = 0x2f
        self.machine.xra(0xa8)
        self._test_flag(Flags.SIGN, "Sign", 0)

        self.machine._registers[Registers.A] = 0xcf
        self.machine.xra(0xa8)
        self._test_flag(Flags.SIGN, "Sign", 1)

        # test parity bit is set/cleared
        self.set_flag(Flags.PARITY, 0)
        # 0110 1100
        # 1001 1111  => 1111 0011
        self.set_register(Registers.B, 0x6c)
        self.set_register(Registers.A, 0x9f)
        self.machine.xra(0xa8)
        self._test_flag(Flags.PARITY, "Parity", 1)

        # 1111 0011
        # 0111 0011  => 1000 0000
        self.set_register(Registers.B, 0xF3)
        self.set_register(Registers.A, 0x73)
        self.machine.xra(0xa8)
        self._test_flag(Flags.PARITY, "Parity", 0)

    def test_xri(self):
        """
        xor second byte of instruction is xor'd with accumulator

        Carry and AC is cleared
        Zero, Sign, Parity set appropriately

        :param opcode:
        :param operands:
        :return:
        """
        self.set_flags([(Flags.CARRY, 1), (Flags.AUX_CARRY, 1), (Flags.ZERO, 1),
                        (Flags.PARITY, 1), (Flags.SIGN, 0)])
        self.set_register(Registers.A, 0x4b) # 0100 1011
        self.machine.xri(0xee, (0x98,))      # 1001 1000 => 1101 0011
        self.assertEqual(self.machine._registers[Registers.A], 0xd3)
        self._test_flag(Flags.CARRY, "Carry", 0)
        self._test_flag(Flags.AUX_CARRY, "Aux Carry", 0)
        self._test_flag(Flags.ZERO, "Zero", 0)
        self._test_flag(Flags.PARITY, "Parity", 0)
        self._test_flag(Flags.SIGN, "Sign", 1)

        self.machine.xri(0xee, (0xd3,))
        self.assertEqual(self.machine._registers[Registers.A], 0)
        self._test_flag(Flags.ZERO, "Zero", 1)
        self._test_flag(Flags.PARITY, "Parity", 1)
        self._test_flag(Flags.SIGN, "Sign", 0)

    def test_ora(self):
        # 1101 0110
        # 0100 1000  => 1101 1110
        tests = [(0xb0, Registers.B, 0xde), (0xb1, Registers.C, 0xde), (0xb2, Registers.D, 0xde),
                 (0xb3, Registers.E, 0xde), (0xb4, Registers.H, 0xde), (0xb5, Registers.L, 0xde),
                 (0xb7, Registers.A, 0x48)]
        for op, reg, expected in tests:
            self.set_flags([(Flags.CARRY, 1), (Flags.AUX_CARRY, 1), (Flags.ZERO, 1),
                            (Flags.PARITY, 0), (Flags.SIGN, 0)])
            self.set_register(reg, 0xd6)
            self.set_register(Registers.A, 0x48)
            self.machine.ora(op)
            self.assertEqual(self.machine._registers[Registers.A], expected,
                             f'Register {reg} OR A didn\'t produce {expected}')
            self._test_flag(Flags.CARRY, "Carry", 0)
            self._test_flag(Flags.AUX_CARRY, "AUX Carry", 0)
            self._test_flag(Flags.ZERO, "ZERO", 0)
            self._test_flag(Flags.PARITY, "Parity", 1)
            self._test_flag(Flags.SIGN, "Sign", 1 if reg != Registers.A else 0)

        self.set_register(Registers.H, 0x33)
        self.set_register(Registers.L, 0xa7)
        # 0011 0011
        # 0100 0000 => 0111 0011
        self.machine.write_memory(0x33a7, 0x33)
        self.set_flag(Flags.PARITY, 1)
        self.set_flag(Flags.SIGN, 1)
        self.set_register(Registers.A, 0x40)
        self.machine.ora(0xb6)
        self.assertEqual(self.machine._registers[Registers.A], 0x73)
        self._test_flag(Flags.PARITY, "Parity", 0)
        self._test_flag(Flags.SIGN, "Sign", 0)

        self.set_flag(Flags.ZERO, 0)
        self.set_register(Registers.D, 0x00)
        self.set_register(Registers.A, 0x00)
        self.machine.ora(0xb2)
        self.assertEqual(self.machine._registers[Registers.A], 0x00)
        self._test_flag(Flags.ZERO, "Zero", 1)

    def test_ori(self):
        opcode = 0xf6
        self.set_flags([(Flags.CARRY, 1), (Flags.AUX_CARRY, 1), (Flags.ZERO, 1),
                        (Flags.SIGN, 0), (Flags.PARITY, 1)])
        #  1001 1100
        #  0100 1111  => 1101 1111
        self.set_register(Registers.A, 0x4f)
        self.machine.ori(opcode, (0x9c,))
        self.assertEqual(self.machine._registers[Registers.A], 0xdf)
        self._test_flag(Flags.CARRY, "CARRY", 0)
        self._test_flag(Flags.AUX_CARRY, "AUX CARRY", 0)
        self._test_flag(Flags.PARITY, "PARITY", 0)
        self._test_flag(Flags.ZERO, "ZERO", 0)
        self._test_flag(Flags.SIGN, "Sign", 1)

        # 0110 1100
        # 0000 1111
        self.set_register(Registers.A, 0x0f)
        self.machine.ori(opcode, (0x6c,))
        self._test_flag(Flags.PARITY, "PARITY", 1)
        self._test_flag(Flags.SIGN, "Sign", 0)
        self._test_flag(Flags.ZERO, "ZERO", 0)

        self.set_register(Registers.A, 0x00)
        self.machine.ori(opcode, (0x00,))
        self._test_flag(Flags.ZERO, "ZERO", 1)


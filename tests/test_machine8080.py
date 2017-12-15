from unittest import TestCase
import logging

from machine import Machine8080
from machine import OutOfMemoryException
from cpu import Registers, Flags


class TestMachine8080(TestCase):
    def setUp(self):
        self.machine = Machine8080()
        self.machine.load("rom")
        logging.basicConfig(level=logging.INFO)

    def test_read_memory(self):
        membytes = self.machine.read_memory(0, 10)
        self.assertTrue(len(membytes) == 10)
        with self.assertRaises(OutOfMemoryException):
            self.machine.read_memory(0xfff0, 100)
        membytes = self.machine.read_memory(0, 4)
        self.assertTrue(membytes == [0x00, 0x00, 0x00, 0xc3])

    def test_mov(self):
        self.machine._registers[Registers.A] = 0x10
        self.machine._registers[Registers.B] = 0x33
        self.machine.mov(0x47)  # MOV B, A
        self.assertTrue(self.machine._registers[Registers.A] == 0x10)
        self.assertTrue(self.machine._registers[Registers.B] == 0x10)  # make sure source doesn't change

        self.machine.write_memory(0xff00, 0xAA)
        self.machine._registers[Registers.H] = 0xff
        self.machine._registers[Registers.L] = 0x00
        self.machine.mov(0x7e)
        self.assertTrue(self.machine._registers[Registers.A] == 0xAA)

    def test_stax(self):
        self.assertFalse(self.machine.read_memory(0x1000, 1)[0] == 0xAA)  # make sure it's not what we're setting
        self.machine._registers[Registers.A] = 0xAA
        self.machine._registers[Registers.B] = 0x10
        self.machine._registers[Registers.C] = 0x00
        self.machine.stax(0x02)
        self.assertTrue(self.machine.read_memory(0x1000, 1)[0] == 0xAA)

        self.assertFalse(self.machine.read_memory(0x01FF, 1)[0] == 0xAA)  # make sure it's not what we're setting
        self.machine._registers[Registers.A] = 0xAA
        self.machine._registers[Registers.D] = 0x01
        self.machine._registers[Registers.E] = 0xFF
        self.machine.stax(0x12)
        self.assertTrue(self.machine.read_memory(0x01FF, 1)[0] == 0xAA)

    def test_ldax(self):
        self.assertTrue(self.machine._registers[Registers.A] == 0x00)
        self.machine.write_memory(0xFF17, 0x45)
        self.machine._registers[Registers.B] = 0xFF
        self.machine._registers[Registers.C] = 0x17
        self.machine.ldax(0x0a)
        self.assertTrue(self.machine._registers[Registers.A] == 0x45)

        self.machine.write_memory(0x17FF, 0x2C)
        self.machine._registers[Registers.D] = 0x17
        self.machine._registers[Registers.E] = 0xFF
        self.machine.ldax(0x1a)
        self.assertTrue(self.machine._registers[Registers.A] == 0x2c)

    def test_pchl(self):
        self.machine._registers[Registers.H] = 0x54
        self.machine._registers[Registers.L] = 0x32
        self.machine.pchl(0xe9)
        self.assertTrue(self.machine._pc == 0x5432)

    def test_jmp(self):
        for lo,hi in [ (0x32, 0x23), (0x44, 0xff), (0x12, 0x43)]:
            self.machine.jmp(0xc3, (lo, hi))
            self.assertTrue(self.machine._pc == ((hi << 8) | lo))

    def _test_condjump_set(self, opcode, flag, bitname):
        """
        Tests if the program jumps when the given flag is set
        :param opcode:
        :param flag:
        :param msg:
        :return:
        """
        self.machine._flags.clear(flag)
        self.machine._pc = 0
        self.machine.conditional_jmp(opcode, (0x22, 0x44))
        self.assertFalse(self.machine._pc == 0x4422, f'{bitname} bit 0 should not have jumped')
        self.machine._flags.set(flag)
        self.machine.conditional_jmp(opcode, (0x22, 0x44))
        self.assertTrue(self.machine._pc == 0x4422, f'{bitname} bit 1 should have jumped')

    def _test_condjump_clear(self, opcode, flag, bitname):
        """
        Tests if the program jumps when the given flag is set
        :param opcode:
        :param flag:
        :param msg:
        :return:
        """
        self.machine._flags.set(flag)
        self.machine._pc = 0
        self.machine.conditional_jmp(opcode, (0x22, 0x44))
        self.assertFalse(self.machine._pc == 0x4422, f'{bitname} bit 1 should not have jumped')
        self.machine._flags.clear(flag)
        self.machine.conditional_jmp(opcode, (0x22, 0x44))
        self.assertTrue(self.machine._pc == 0x4422, f'{bitname} bit 0 should have jumped')

    def test_jc(self):
        self._test_condjump_set(0xda, Flags.CARRY, "CARRY")

    def test_jnc(self):
        self._test_condjump_clear(0xd2, Flags.CARRY, "CARRY")

    def test_jz(self):
        self._test_condjump_set(0xca, Flags.ZERO, "ZERO")

    def test_jnz(self):
        self._test_condjump_clear(0xc2, Flags.ZERO, "ZERO")

    def test_jm(self):
        self._test_condjump_set(0xfa, Flags.SIGN, "SIGN")

    def test_jp(self):
        self._test_condjump_clear(0xf2, Flags.SIGN, "SIGN")

    def test_jpe(self):
        self._test_condjump_set(0xea, Flags.PARITY, "PARITY")

    def test_jpo(self):
        self._test_condjump_clear(0xe2, Flags.PARITY, "PARITY")

    def _test_flag(self, flag, name, expected):
        """Checks that the carry bit val is equal to expected.
        """
        self.assertTrue(self.machine._flags[flag] == expected,
                        f'{name} not equal to {expected}')

    def test_ana(self):
        """Logical AND.  Carry bit is cleared, zero, sign, and parity are affected

        Intel manual from Sept '75 says the AC bit is affected as well, but not how it's affected

            1111 0011
        AND 0011 1111
            0011 0011 (0x33)
        """
        self.machine._flags.set(Flags.CARRY)
        # Verify ANA performs correct operation with each register  (Skip ANA M since it's memory)
        tests = [(0xa0, Registers.B, 0x33), (0xa1, Registers.C, 0x33), (0xa2, Registers.D, 0x33),
                 (0xa3, Registers.E, 0x33), (0xa4, Registers.H, 0x33), (0xa5, Registers.L, 0x33),
                 (0xa7, Registers.A, 0x3f)]
        for opcode, reg, res in tests:
            self.machine._registers[Registers.A] = 0xf3
            self.machine._registers[reg] = 0x3f
            self.machine.ana(opcode)
            self.assertTrue(self.machine._registers[Registers.A] == res,
                            f'Result of ANA (opcode: {opcode:02X}) {self.machine._registers[Registers.A]:02X} not {res:02X}')
            self._test_flag(Flags.CARRY, "Carry", 0)

        # test memory ANA opcode 0xa6
        self.machine.write_memory(0x5599, 0x33)
        self.machine._registers[Registers.H] = 0x55
        self.machine._registers[Registers.L] = 0x99
        self.machine._registers[Registers.A] = 0x3f
        self.machine.ana(0xa6)
        self.assertTrue(self.machine._registers[Registers.A] == 0x33,
                        f'result of ANA M = {self.machine._registers[Registers.A]}, not 0x33')
        self._test_flag(Flags.CARRY, "Carry", 0)

        # verify CARRY flag is cleared
        self.machine._flags.set(Flags.CARRY)
        self.assertTrue(self.machine._flags[Flags.CARRY] == 1, "Carry flag isn't set when it should be!")
        self.machine._registers[Registers.B] = 1
        self.machine._registers[Registers.A] = 3
        self.machine.ana(0xa0) # 0xa0 = ANA B
        self.assertTrue(self.machine._flags[Flags.CARRY] == 0, "Carry flag isn't reset after ANA")

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

    def set_flag(self, flag, val):
        if val == 0:
            self.machine._flags.clear(flag)
        else:
            self.machine._flags.set(flag)

    def set_register(self, reg, val):
        self.machine._registers[reg] = val

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
        self.assertTrue(self.machine._registers[Registers.A] == 0,
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
        self.assertTrue(self.machine._registers[Registers.A] == 0x24,
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

    def test_mvi(self):
        """Moves byte in operand into the given register or memory location

        2-byte instruction
        """
        tests = [(0x06, Registers.B, 0x87), (0x0e, Registers.C, 0x23), (0x16, Registers.D, 0x12),
                 (0x1e, Registers.E, 0xf2), (0x26, Registers.H, 0xa2), (0x2e, Registers.L, 0xee),
                 (0x3d, Registers.A, 0xd9)]
        for op, reg, val in tests:
            self.machine.mvi(op, (val,))
            self.assertEqual(self.machine._registers[reg], val, f'Register {reg} does not equal {val}')

        # 0x36 - opcode for MVI M
        self.set_register(Registers.H, 0x34)
        self.set_register(Registers.L, 0xaa)
        self.machine.mvi(0x36, (0xed,))
        self.assertEqual(self.machine.read_memory(0x34aa, 1)[0], 0xed,
                          f'Memory address 0x34aa does not contain 0xed')

    def test_lxi(self):
        """Moves two bytes into low and hi parts of register pair or stack pointer

        <opcode> <lo> <hi>
        """
        for op, lo,hi in [(0x01, Registers.C, Registers.B), (0x11, Registers.E, Registers.D),
                          (0x21, Registers.L, Registers.H)]:
            self.machine.lxi(op, (0xef, 0x12))
            self.assertEqual(self.machine._registers[lo], 0xef, f'lo byte of {op:02X} not correct')
            self.assertEqual(self.machine._registers[hi], 0x12, f'hi byte of {op:02X} not correct')

        # test SP
        self.machine.lxi(0x31, (0x12, 0xef))
        self.assertEqual(self.machine._sp, 0xef12)

    def test_lda(self):
        """Set data in memory location to accumulator
        """
        self.machine.write_memory(0x1122, 0xaa)
        self.machine.lda(0x3a, (0x22, 0x11))
        self.assertEqual(self.machine._registers[Registers.A], 0xaa, f'Accumulator not set from memory.')

    def test_sta(self):
        """
        Contents of the accumulator are stored in the address
        :return:
        """
        self.set_register(Registers.A, 0x3f)
        self.machine.sta(0x32, (0xab, 0x12))
        val, *_ = self.machine.read_memory(0x12ab, 1)
        self.assertEqual(val, self.machine._registers[Registers.A], f'Memory not set with STA command')

    def test_lhld(self):
        self.machine.write_memory(0x2233, 0x34)
        self.machine.write_memory(0x2234, 0xaf)
        self.machine.lhld(0x2a, (0x33, 0x22))

        self.assertEqual(self.machine._registers[Registers.L], 0x34, f'L register didn\'t get 0x34')
        self.assertEqual(self.machine._registers[Registers.H], 0xaf, f'H register didn\'t get 0xaf')
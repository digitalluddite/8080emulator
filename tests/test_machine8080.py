from unittest import TestCase
import logging

from machine import Machine8080
from machine import OutOfMemoryException, HaltException
from cpu import Registers, Flags


class TestMachine8080(TestCase):
    def setUp(self):
        self.machine = Machine8080()
        self.machine.load("rom")
        logging.basicConfig(level=logging.DEBUG)

    def test_read_memory(self):
        membytes = self.machine.read_memory(0, 10)
        self.assertEqual(len(membytes), 10)
        with self.assertRaises(OutOfMemoryException):
            self.machine.read_memory(0xfff0, 100)
        membytes = self.machine.read_memory(0, 4)
        self.assertEqual(membytes, [0x00, 0x00, 0x00, 0xc3])

    def test_mov(self):
        self.machine._registers[Registers.A] = 0x10
        self.machine._registers[Registers.B] = 0x33
        self.machine.mov(0x47)  # MOV B, A
        self.assertEqual(self.machine._registers[Registers.A], 0x10)
        self.assertEqual(self.machine._registers[Registers.B], 0x10)  

        self.machine.write_memory(0xff00, 0xAA)
        self.machine._registers[Registers.H] = 0xff
        self.machine._registers[Registers.L] = 0x00
        self.machine.mov(0x7e)
        self.assertEqual(self.machine._registers[Registers.A], 0xAA)

    def test_stax(self):
        self.assertNotEqual(self.machine.read_memory(0x1000, 1)[0], 0xAA)  
        self.machine._registers[Registers.A] = 0xAA
        self.machine._registers[Registers.B] = 0x10
        self.machine._registers[Registers.C] = 0x00
        self.machine.stax(0x02)
        self.assertEqual(self.machine.read_memory(0x1000, 1)[0], 0xAA)


        self.assertNotEqual(self.machine.read_memory(0x01FF, 1)[0], 0xAA)  
        self.machine._registers[Registers.A] = 0xAA
        self.machine._registers[Registers.D] = 0x01
        self.machine._registers[Registers.E] = 0xFF
        self.machine.stax(0x12)
        self.assertEqual(self.machine.read_memory(0x01FF, 1)[0], 0xAA)

    def test_ldax(self):
        self.assertEqual(self.machine._registers[Registers.A], 0x00)
        self.machine.write_memory(0xFF17, 0x45)
        self.machine._registers[Registers.B] = 0xFF
        self.machine._registers[Registers.C] = 0x17
        self.machine.ldax(0x0a)
        self.assertEqual(self.machine._registers[Registers.A], 0x45)

        self.machine.write_memory(0x17FF, 0x2C)
        self.machine._registers[Registers.D] = 0x17
        self.machine._registers[Registers.E] = 0xFF
        self.machine.ldax(0x1a)
        self.assertEqual(self.machine._registers[Registers.A], 0x2c)

    def test_pchl(self):
        self.machine._registers[Registers.H] = 0x54
        self.machine._registers[Registers.L] = 0x32
        self.machine.pchl(0xe9)
        self.assertEqual(self.machine._pc, 0x5432)

    def test_jmp(self):
        for lo,hi in [ (0x32, 0x23), (0x44, 0xff), (0x12, 0x43)]:
            self.machine.jmp(0xc3, (lo, hi))
            self.assertEqual(self.machine._pc, ((hi << 8) | lo))

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

        self.assertNotEqual(self.machine._pc, 0x4422, f'{bitname} bit 0 should not have jumped')
        self.machine._flags.set(flag)
        self.machine.conditional_jmp(opcode, (0x22, 0x44))
        self.assertEqual(self.machine._pc, 0x4422, f'{bitname} bit 1 should have jumped')

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

        self.assertNotEqual(self.machine._pc, 0x4422, f'{bitname} bit 1 should not have jumped')
        self.machine._flags.clear(flag)
        self.machine.conditional_jmp(opcode, (0x22, 0x44))
        self.assertEqual(self.machine._pc, 0x4422, f'{bitname} bit 0 should have jumped')

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
        self.assertEqual(self.machine._flags[flag], expected,
                        f'{name} not equal to {expected}')

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
        tests = [(0xa0, Registers.B, 0x33), (0xa1, Registers.C, 0x33), (0xa2, Registers.D, 0x33),
                 (0xa3, Registers.E, 0x33), (0xa4, Registers.H, 0x33), (0xa5, Registers.L, 0x33),
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

    def set_flag(self, flag, val):
        if val == 0:
            self.machine._flags.clear(flag)
        else:
            self.machine._flags.set(flag)

    def set_flags(self, flags):
        """ Sets the given flags
        :param flags: iterable of (flag, value) tuples
        """
        for f,v in flags:
            self.set_flag(f,v)

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

    def test_shld(self):
        self.set_register(Registers.L, 0x9a)
        self.set_register(Registers.H, 0xe1)
        self.machine.shld(0x22, (0xee, 0x54))
        l, h = self.machine.read_memory(0x54ee, 2)
        self.assertEqual(l, 0x9a, 'First memory byte not 0x9a')
        self.assertEqual(h, 0xe1, 'Second memory byte not 0xe1')

    def test_xchg(self):
        self.set_register(Registers.H, 0x12)
        self.set_register(Registers.L, 0x55)
        self.set_register(Registers.D, 0x54)
        self.set_register(Registers.E, 0xae)
        self.machine.xchg(0xeb)
        self.assertEqual(self.machine._registers[Registers.D], 0x12)
        self.assertEqual(self.machine._registers[Registers.E], 0x55)
        self.assertEqual(self.machine._registers[Registers.H], 0x54)
        self.assertEqual(self.machine._registers[Registers.L], 0xae)

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

    def test_call(self):
        """
        Invoke a function
        ((SP)-1) <- PCH
        ((SP)-2) <- PCL
        (SP) <- (SP)-2
        (PC) <- (operands[1])(operands[0])
        """
        self.machine._sp = 0xa000
        self.machine._pc = 0x88AB
        self.machine.call(0xcd, (0xFF, 0x78))
        self.assertEqual(self.machine._sp, 0xa000-2,
                        f'Stack Pointer not correct after call {self.machine._sp:02X}')
        self.assertEqual(self.machine._pc, 0x78FF, 'Program counter not set correctly')
        lo, hi = self.machine.read_memory(self.machine._sp, 2)
        self.assertEqual(hi, 0x88, f'Invalid stack HI {hi:02X} not 0x88')
        self.assertEqual(lo, 0xab, f'Invalid stack LO {lo:02X} not 0xab')

    def test_ret(self):
        """
        (PCL) <- (SP)
        (PCH) <- (SP)+1
        (SP) <- (SP)+2
        """
        self.machine.write_memory(0x6666, 0x98)
        self.machine.write_memory(0x6667, 0x9A)
        self.machine._sp = 0x6666
        self.machine.ret(0xc9)
        self.assertEqual(self.machine._pc, 0x9a98)
        self.assertEqual(self.machine._sp, 0x6668)

    def test_call_ret(self):
        self.machine._sp = 0x1122
        self.machine._pc = 0x8899
        self.machine.call(0xcd, (0xab, 0xcd))
        self.assertEqual(self.machine._pc, 0xcdab)
        self.assertEqual(self.machine._sp, 0x1120)
        self.machine.ret(0xc9)
        self.assertEqual(self.machine._pc, 0x8899)
        self.assertEqual(self.machine._sp, 0x1122)

    def test_cmc(self):
        self.set_flag(Flags.CARRY, 0)
        opcode = 0x3f
        self.machine.cmc(opcode)
        self._test_flag(Flags.CARRY, "Carry", 1)
        self.machine.cmc(opcode)
        self._test_flag(Flags.CARRY, "Carry", 0)

    def test_stc(self):
        self.set_flag(Flags.CARRY, 0)
        self.machine.stc()
        self._test_flag(Flags.CARRY, "Carry", 1)
        self.machine.stc()
        self._test_flag(Flags.CARRY, "Carry", 1)

    def test_cma(self):
        self.set_register(Registers.A, 0x14) # 0001 0100  => 1110 1011
        self.machine.cma()
        self.assertEqual(self.machine._registers[Registers.A], 0xEB,
                         f'REG A = {self.machine._registers[Registers.A]:02X} not 0xEB')
        self.machine.cma()
        self.assertEqual(self.machine._registers[Registers.A], 0x14)
        self.set_register(Registers.A, 0x00)
        self.machine.cma()
        self.assertEqual(self.machine._registers[Registers.A], 0xff)
        self.machine.cma()
        self.assertEqual(self.machine._registers[Registers.A], 0x00)

    def test_conditional_call(self):
        """
        Instruction format 11CCC100

        NZ -- 000  (not zero)
        Z  -- 001  (zero)
        NC -- 010  (no carry)
        C  -- 011  (carry)
        PO -- 100  (parity odd)
        PE -- 101  (parity even)
        P  -- 110  (positive)
        M  -- 111  (negative/minus)

        if CCC:
            ((SP) - 1) <-  PCH
            ((SP) - 2) <-  PCL
            (SP) <- (SP) - 2
            (PC) <- (operands[1])(operands[0])

        :param opcode:
        :param operands:
        """
        #  Tests:  (opcode, Flag, flag-val)...
        tests = [(0xc4, Flags.ZERO, 0), (0xcc, Flags.ZERO, 1),
                 (0xd4, Flags.CARRY, 0), (0xdc, Flags.CARRY, 1),
                 (0xe4, Flags.PARITY, 0), (0xec, Flags.PARITY, 1),
                 (0xf4, Flags.SIGN, 0), (0xfc, Flags.SIGN, 1)]
        for op, flag, val in tests:
            # turn off expected flag, make sure the call doesn't execute
            if val == 0:
                self.set_flag(flag,1)
            else:
                self.set_flag(flag,0)
            self.machine._sp = 0x4444
            self.machine._pc = 0x6666
            self.machine.conditional_call(op, (0x22, 0xaa))
            self.assertEqual(self.machine._pc, 0x6666)
            self.assertEqual(self.machine._sp, 0x4444)
            # turn on flag and verify conditional jump works
            self.set_flag(flag, val)
            self.machine.conditional_call(op, (0x22, 0xaa))
            self.assertEqual(self.machine._sp, 0x4442)
            self.assertEqual(self.machine._pc, 0xaa22)

    def test_push_pair(self):
        """
        ((SP) - 1) <- (rh)
        ((SP) - 2)  <- (rl)
        (SP)       <- (SP) - 2
        :return:
        """
        for op, pair in [(0xc5, 0), (0xd5, 1), (0xe5, 2)]:
            hi, lo = self.machine._registers.get_pairs(pair)
            self.set_register(hi, 0x33)
            self.set_register(lo, 0xef)
            self.machine._sp = 0x4444
            self.machine.push_pair(op)
            self.assertEqual(self.machine._sp, 0x4442)
            bl, bh = self.machine.read_memory(self.machine._sp, 2)
            self.assertEqual(bl, 0xef)
            self.assertEqual(bh, 0x33)

    def test_conditional_ret(self):
        tests = [(0xc0, Flags.ZERO, 0), (0xc8, Flags.ZERO, 1),
                 (0xd0, Flags.CARRY, 0), (0xd8, Flags.CARRY, 1),
                 (0xe0, Flags.PARITY, 0), (0xe8, Flags.PARITY, 1),
                 (0xf0, Flags.SIGN, 0), (0xf8, Flags.SIGN, 1)]
        for op, flag, val in tests:
            # set flag opposite to expected, verify return doesn't happen
            if val == 0:
                self.set_flag(flag, 1)
            else:
                self.set_flag(flag, 0)
            self.machine._sp = 0x1122
            self.machine._pc = 0x0001
            self.set_register(Registers.B, 0x22)
            self.set_register(Registers.C, 0xab)
            self.machine.push_pair(0xc5)  # push B,C register pair
            self.machine.conditional_ret(op)
            self.assertNotEqual(self.machine._sp, 0x1122)
            self.assertEqual(self.machine._pc, 0x0001)  # PC doesn't change

            # set flag to expected value and try again
            self.set_flag(flag, val)
            self.machine.conditional_ret(op)
            self.assertEqual(self.machine._sp, 0x1122)
            self.assertEqual(self.machine._pc, 0x22ab)

    def tests_push_psw(self):
        self.machine._registers[Registers.A] = 0x2f
        self.set_flag(Flags.PARITY, 1)
        self.set_flag(Flags.ZERO, 1)
        self.machine._sp = 0x2345
        self.machine.push_psw()
        f, a = self.machine.read_memory(self.machine._sp, 2)
        self.assertEqual(self.machine._flags.flags, f)
        self.assertEqual(self.machine._registers[Registers.A], a)

        self.set_flag(Flags.PARITY, 0)
        self.machine.push_psw()
        f, a = self.machine.read_memory(self.machine._sp, 2)
        self.assertEqual(self.machine._flags.flags, f)
        self.assertEqual(self.machine._registers[Registers.A], a)

    def test_pop_pair(self):
        base = 0x0000
        expected = []
        self.machine._sp = 0x2000
        tests = [(0xc1, 0xc5, 0), (0xd1, 0xd5, 1), (0xe1, 0xe5, 2)]
        for op,push_op, pair in tests:
            hi,lo = self.machine._registers.get_pairs(pair)
            self.set_register(hi, base+1)
            self.set_register(lo, base+2)
            expected.append((base+1, base+2))
            self.machine.push_pair(push_op)
            base += 2

        for op, _, pair in tests[::-1]:
            hi, lo = self.machine._registers.get_pairs(pair)
            self.machine.pop_pair(op)
            exhi, exlo = expected.pop()
            self.assertEqual(self.machine._registers[hi], exhi)
            self.assertEqual(self.machine._registers[lo], exlo)

    def test_pop_psw(self):
        self.set_register(Registers.A, 0x3e)
        self.set_flag(Flags.CARRY, 1)
        self.set_flag(Flags.SIGN, 1)
        self.machine._sp = 0x3333
        self.machine.push_psw()
        self.set_flag(Flags.CARRY, 0)
        self.set_flag(Flags.SIGN, 0)
        self.set_register(Registers.A, 0)
        self.machine.pop_psw()
        self._test_flag(Flags.CARRY, "Carry", 1)
        self._test_flag(Flags.SIGN, "Sign", 1)
        self.assertEqual(self.machine._registers[Registers.A], 0x3e)

    def test_xthl(self):
        self.machine._sp = 0x5555
        i = 0
        for b in [0x11, 0x44, 0xa0, 0xe3]:
            self.machine.write_memory(self.machine._sp + i, b)
            i += 1
        self.set_register(Registers.H, 0xf0)
        self.set_register(Registers.L, 0xe3)
        self.machine.xthl()

        l, h = self.machine.read_memory(self.machine._sp, 2)
        self.assertEqual(l, 0xe3)
        self.assertEqual(h, 0xf0)
        self.assertEqual(self.machine._registers[Registers.H], 0x44)
        self.assertEqual(self.machine._registers[Registers.L], 0x11)

    def test_sphl(self):
        self.machine._sp = 0x0000
        self.set_register(Registers.H, 0x5e)
        self.set_register(Registers.L, 0xa1)
        self.machine.sphl()
        self.assertEqual(self.machine._sp, 0x5ea1)

    def test_halt(self):
        with self.assertRaises(HaltException):
            self.machine.halt()

    def test_rlc(self):
        self.set_flag(Flags.CARRY, 0)
        self.set_register(Registers.A, 1)
        for x in range(1,9):
            self.machine.rlc()
            if x == 8:
                test_val = 1
                carry = 1
            else:
                test_val = 1 << x
                carry = 0
            self.assertEqual(self.machine._registers[Registers.A], test_val)
            self.assertEqual(self.machine._flags[Flags.CARRY], carry)

    def test_ral(self):
        """Rotate left through cary bit

        Carry goes to A0, A7 goes to carry, everything else shifts left
        """
        self.set_flag(Flags.CARRY, 0)
        self.set_register(Registers.A, 0x81)  # 1000 0001
        self.machine.ral()  # expected, CY = 1, 0000 0010
        self._test_flag(Flags.CARRY, "CARRY", 1)
        self.assertEqual(self.machine._registers[Registers.A], 0x02)

        self.machine.ral() # CY = 0, 0000 0101
        self._test_flag(Flags.CARRY, "CARRY", 0)
        self.assertEqual(self.machine._registers[Registers.A], 0x05)

    def test_rrc(self):
        """
        Rotate right
        (An-1) <- (An); (A7) <- (A0)
        (CY) <- (A0)
        :param args:
        """
        self.machine._flags[Flags.CARRY] = 0
        self.set_register(Registers.A, 0x41)  # 0100 0001
        self.machine.rrc() # 1010 0000 CY = 1
        self._test_flag(Flags.CARRY, "Carry", 1)
        self.assertEqual(self.machine._registers[Registers.A], 0xa0)

        self.machine.rrc() # 0101 0000 CY = 0
        self._test_flag(Flags.CARRY, "Carry", 0)
        self.assertEqual(self.machine._registers[Registers.A], 0x50)

    def test_rar(self):
        """
        An <- An+1
        CY <- A0
        A7 <- CY
        """
        self.machine._flags[Flags.CARRY] = 1
        self.machine._registers[Registers.A] = 0x42 # 0100 0010
        self.machine.rar()  # carry should be 0, A = 1010 0001
        self._test_flag(Flags.CARRY, "Carry", 0)
        self.assertEqual(self.machine._registers[Registers.A], 0xa1)

        self.machine.rar() # CY = 1, A = 0101 0000
        self._test_flag(Flags.CARRY, "Carry", 1)
        self.assertEqual(self.machine._registers[Registers.A], 0x50)

    def _clear_flags(self):
        for f in [Flags.CARRY, Flags.AUX_CARRY, Flags.SIGN, Flags.PARITY, Flags.ZERO]:
            self.machine._flags.clear(f)

    def _set_flags(self):
        for f in [Flags.CARRY, Flags.AUX_CARRY, Flags.SIGN, Flags.PARITY, Flags.ZERO]:
            self.machine._flags.set(f)

    def test_cmp(self):
        """
        Instruction format: 10111SSS

        Contents of register (or memory) is subtracted from A.
        Accumulator remains unchanged.  Condition flags are set.

        Z flag is set if (A) == SSS; CY is set if A < SSS
        """
        self.machine._registers[Registers.A] = 0x59 # 0101 1001 (89)
        self.machine._registers[Registers.B] = 0x80 # 1000 0000 (-128)
        self.machine.cmp(0xb8)  # 0xd9  1101 1001
        self._test_flag(Flags.CARRY, "Carry", 0)
        self._test_flag(Flags.ZERO, "Zero", 0)
        self._test_flag(Flags.SIGN, "Sign", 0)
        self._test_flag(Flags.PARITY, "Parity", 0)
        self._test_flag(Flags.AUX_CARRY, "Aux Carry", 0)
        self.assertEqual(self.machine._registers[Registers.A], 0x59)

        self._clear_flags()
        self.machine._registers[Registers.C] = 0x4a # 0100 1010  # I assume AC will be set
        self.machine.cmp(0xb9)  # 0000 1111
        self._test_flag(Flags.CARRY, "Carry", 0)
        self._test_flag(Flags.AUX_CARRY, "Aux Carry", 1)

        self._clear_flags()
        self.machine._registers[Registers.D] = 0x60  # 0110 0000
        self.machine.cmp(0xda)
        self._test_flag(Flags.CARRY, "Carry", 1)
        self._test_flag(Flags.AUX_CARRY, "Aux Carry", 0)
        self._test_flag(Flags.SIGN, "Sign", 1)

        self._clear_flags()
        self.machine.cmp(0xbf)  # 0x81 1000 0001
        self._test_flag(Flags.ZERO, "Zero", 1)
        self._test_flag(Flags.PARITY, "Parity", 1)

    def test_inx(self):
        tests = [(0x03, Registers.B, Registers.C), (0x13, Registers.D, Registers.E),
                 (0x23, Registers.H, Registers.L)]
        for op, hi, lo in tests:
            self.set_register(hi, 0x44)
            self.set_register(lo, 0xab)
            self._clear_flags()
            self.machine.inx(op)
            self.assertEqual(self.machine._registers[hi], 0x44) 
            self.assertEqual(self.machine._registers[lo], 0xac) 
            self.assertEqual(self.machine._flags.flags, 0x2) # bit 1 is always one

        self.set_register(Registers.B, 0x44)
        self.set_register(Registers.C, 0xff)
        self.machine.inx(0x03)
        self.assertEqual(self.machine._registers[Registers.B], 0x45)
        self.assertEqual(self.machine._registers[Registers.C], 0x00)
        
        self.machine._sp = 0x5678
        self.machine.inx(0x33)  # opcode for SP "pair"
        self.assertEqual(self.machine._sp, 0x5679)
        self.machine._sp = 0xffff
        self.machine.inx(0x33)
        self.assertEqual(self.machine._sp, 0x0000)

    def test_dcx(self):
        tests = [(0x0b, Registers.B, Registers.C), (0x1b, Registers.D, Registers.E),
                 (0x2b, Registers.H, Registers.L)]
        for op, hi, lo in tests:
            self.set_register(hi, 0x23)
            self.set_register(lo, 0x00)
            self._clear_flags()
            self.machine.dcx(op)
            self.assertEqual(self.machine._flags.flags, 0x02)
            self.assertEqual(self.machine._registers[hi], 0x22)
            self.assertEqual(self.machine._registers[lo], 0xff)

        self.set_register(Registers.H, 0x00)
        self.set_register(Registers.L, 0x00)
        self.machine.dcx(0x2b)
        self.assertEqual(self.machine._registers[Registers.H], 0xff) 
        self.assertEqual(self.machine._registers[Registers.L], 0xff) 

        self.machine._sp = 0x1111
        self.machine.dcx(0x3b)
        self.assertEqual(self.machine._sp, 0x1110)
        self.machine._sp = 0x0000
        self.machine.dcx(0x3b)
        self.assertEqual(self.machine._sp, 0xffff)

    def test_inr(self):
        """
        (R) <- (R) + 1

        instruction format: 00DDD100

        Flags affected: Z, S, P, AC
        """
        tests = [(0x04, Registers.B), (0x0c, Registers.C), (0x14, Registers.D),
                 (0x1C, Registers.E), (0x24, Registers.H), (0x2C, Registers.L), 
                 (0x3c, Registers.A)]
        for op,reg in tests:
            self._clear_flags()
            self.machine._flags[Flags.PARITY] =  1
            self.set_register(reg, 0xaa) # 1010 1010
            self.machine.inr(op)
            self.assertEqual(self.machine._registers[reg], 0xab) # 1010 1011
            self._test_flag(Flags.PARITY, "Parity", 0) 
            self._test_flag(Flags.SIGN, "Sign", 1)
            self._test_flag(Flags.AUX_CARRY, "Aux Carry", 0)
            
        # test "M" register 
        self.machine._flags[Flags.PARITY] =  0
        self.machine.write_memory(0xaaaa, 0xab)  # 1010 1011
        self.set_register(Registers.H, 0xaa)
        self.set_register(Registers.L, 0xaa)
        self.machine.inr(0x34)
        val = self.machine.read_memory(0xaaaa, 1)[0]
        self.assertEqual(val, 0xac)  # 1010 1100
        self._test_flag(Flags.PARITY, "Parity", 1) 

        self.set_register(Registers.B, 0x7f)
        self.machine.inr(0x04)
        self.assertEqual(self.machine._registers[Registers.B], 0x80)
        self._test_flag(Flags.SIGN, "Sign", 1)

        self.set_register(Registers.B, 0xff)
        self.machine.inr(0x04)
        self.assertEqual(self.machine._registers[Registers.B], 0x00)
        self._test_flag(Flags.ZERO, "Zero", 1)

        self.set_register(Registers.B, 0x1f)
        self.machine.inr(0x04)
        self._test_flag(Flags.AUX_CARRY, "Aux Carry", 1)

    def test_dcr(self):
        """
        (R) <- (R) - 1
        instruction format 00DDD101
        Flags: Z, S, P, AC
        """
        tests = [(0x05, Registers.B), (0x0d, Registers.C), (0x15, Registers.D),
                 (0x1D, Registers.E), (0x25, Registers.H), (0x2D, Registers.L), 
                 (0x3D, Registers.A)]
        for op, reg in tests:
            #   Value: 0x3a  0011 1010
            #   DCR:   0x39  0011 1001
            self._set_flags()
            self.machine._flags[Flags.PARITY] = 0
            self.set_register(reg, 0x3a)
            self.machine.dcr(op)
            self.assertEqual(self.machine._registers[reg], 0x39)
            self._test_flag(Flags.ZERO, "Zero", 0) 
            self._test_flag(Flags.SIGN, "Sign", 0) 
            self._test_flag(Flags.PARITY, "Parity", 1) 
            self._test_flag(Flags.AUX_CARRY, "Aux Carry", 0) 
            self._test_flag(Flags.CARRY, "Carry", 1) 
        
        # test DCR M
        self.machine._flags[Flags.PARITY] = 0
        self.machine._flags[Flags.CARRY] = 1  # to make sure it isn't cleared 
        self.machine.write_memory(0xbbbb, 0x3a)
        self.set_register(Registers.H, 0xbb)
        self.set_register(Registers.L, 0xbb)
        self.machine.dcr(0x35)

        val = self.machine.read_memory(0xbbbb, 1)[0]
        self.assertEqual(val, 0x39)
        self._test_flag(Flags.PARITY, "Parity", 1)
        
        # zero flag
        self.set_register(Registers.B, 1)
        self.machine._flags[Flags.ZERO] = 0
        self.machine.dcr(0x05)
        self._test_flag(Flags.ZERO, "Zero", 1)

        # sign flag
        self.machine._flags[Flags.SIGN] = 0
        self.machine.dcr(0x05)
        self.assertEqual(self.machine._registers[Registers.B], 0xff)
        self._test_flag(Flags.SIGN, "Sign", 1)

        # aux carry
        self.machine._flags[Flags.AUX_CARRY] = 0
        self.machine._registers[Registers.B] = 0x40
        self.machine.dcr(0x05)
        self.assertEqual(self.machine._registers[Registers.B], 0x3f)
        self._test_flag(Flags.AUX_CARRY, "Aux Carry", 1)

    def test_dad(self):
        """Add register pair to H and L.

        Carry flag is set.
        """
        # (opcode, RegisterPair encoding)
        tests = [(0x09, 0x00), (0x19, 0x01), (0x29, 0x02)]
        hl = self.machine._registers.get_pairs(0x02) # get HL RegisterPair

        for op, reg in tests:
            pair = self.machine._registers.get_pairs(reg)
            self.machine._flags[Flags.CARRY] = 0x00
            self.machine._registers.set_value_pair(pair, 0xaaaa)
            self.machine._registers.set_value_pair(hl, 0x0001)
            self.machine.dad(op)
            expected = 0xaaab if reg != 0x02 else 0x0002
            self.assertEqual(self.machine._registers.get_value_from_pair(hl), expected)
            self._test_flag(Flags.CARRY, "Carry", 0) 

        self.machine._registers.set_value_pair(hl, 0xffff)
        self.set_register(Registers.B, 0x00)
        self.set_register(Registers.C, 0x01)
        self.machine.dad(0x09)
        self.assertEqual(self.machine._registers.get_value_from_pair(hl), 0x0000)
        self._test_flag(Flags.CARRY, "Carry", 1)

    def test_rst(self):
        """
        (SP)-1 <- (PCH)
        (SP)-2 <- (PCL)
        (SP)   <- (SP)-2
        PC     <- 8 * NNN

        Instruction format:  11NNN111
        """
        opcodes = [0xff, 0xf7, 0xef, 0xe7, 0xdf, 0xd7, 0xcf, 0xc7]
        for op in opcodes:
            nnn = (op >> 3) & 0x7
            self.machine._pc = 0x1234
            self.machine._sp = 0x4321
            self.machine.rst(op)
            self.assertEqual(self.machine._sp, 0x431F)
            lo,hi = self.machine.read_memory(self.machine._sp, 2)
            self.assertEqual(lo, 0x34)
            self.assertEqual(hi, 0x12) 
            self.assertEqual(self.machine._pc, 8*nnn)
    
    def test_adi(self):
        """
        (A) <- (A) + operand
        Flags: Z,S,P,CY,AC
        """
        self.set_register(Registers.A, 0x33)
        self._clear_flags()
        self.machine.adi(0xc6, 0x10)
        self.assertEqual(self.machine._registers[Registers.A], 0x43)
        for f in self.machine._flags:
            self.assertEqual(f, 0)  
        
        # zero, carry, and parity flag
        self.set_register(Registers.A, 0xff)
        self._clear_flags()
        self.machine.adi(0xc6, 0x01)
        self.assertEqual(self.machine._registers[Registers.A], 0x00)
        self._test_flag(Flags.ZERO, "Zero", 1)
        self._test_flag(Flags.PARITY, "Parity", 1)
        self._test_flag(Flags.CARRY, "Carry", 1)
    
        # sign aux. carry flag
        self._clear_flags()
        self.set_register(Registers.A, 0x7f)
        self.machine.adi(0xc6, 0x01)
        self.assertEqual(self.machine._registers[Registers.A], 0x80)
        self._test_flag(Flags.SIGN, "Sign", 1)

        # test that adding zero leaves things unchanged
        self._clear_flags()
        self.set_register(Registers.A, 0x7f)
        self.machine.adi(0xc6, 0x00)
        self._test_flag(Flags.CARRY, "Carry", 0)
        self._test_flag(Flags.AUX_CARRY, "Aux Carry", 0)

    def test_add(self):
        """
        (A) <- (A) + (r)

        Instruction format: 10000SSS
        Flags: Z, S, P, CY, AC
        """
        tests = [(0x80, Registers.B), (0x81, Registers.C), (0x82, Registers.D),
                 (0x83, Registers.E), (0x84, Registers.H), (0x85, Registers.L)]
        for op, reg in tests:
            self._clear_flags()
            self.set_register(reg, 0x23)  # 0010 0011
            self.set_register(Registers.A, 0xa4)  # 1010 0100  (-57) 0xc7
            self.machine.add(op)
            self.assertEqual(self.machine._registers[Registers.A], 0xc7)  # 1100 0111
            self._test_flag(Flags.SIGN, "Sign", 1)
            self._test_flag(Flags.PARITY, "Parity", 0)
            self._test_flag(Flags.CARRY, "Carry", 0)
            self._test_flag(Flags.AUX_CARRY, "Aux Carry", 0)
            self._test_flag(Flags.ZERO, "ZERO", 0)

        self._clear_flags()
        self.set_register(Registers.A, 0xff)
        self.machine.add(0x87)
        self.assertEqual(self.machine._registers[Registers.A], 0xFE) # 1111 1110
        self._test_flag(Flags.SIGN, "Sign", 1)
        self._test_flag(Flags.CARRY, "Carry", 1)
        self._test_flag(Flags.AUX_CARRY, "Aux Carry", 1)

        self._clear_flags()
        self.set_register(Registers.A, 0x3)
        self.machine.add(0x87)
        self.assertEqual(self.machine._registers[Registers.A], 0x6)
        self._test_flag(Flags.PARITY, "Parity", 1)

        self.set_register(Registers.B, 1)
        self.set_register(Registers.A, 0xff)
        self.machine.add(0x80)
        self.assertEqual(self.machine._registers[Registers.A], 0x00)
        self._test_flag(Flags.ZERO, "Zero", 1)

        self.machine.write_memory(0x3434, 0x3)
        self.set_register(Registers.A, 0x1)
        self.set_register(Registers.H, 0x34)
        self.set_register(Registers.L, 0x34)
        self.machine.add(0x86)
        self.assertEqual(self.machine._registers[Registers.A], 0x4)

    def test_adc(self):
        """Add with Carry

        The content of the register (or memory) and the content of the 
        carry bit are added to the accumulator.
        (A) <- (A) + (r) + CY

        instruction format: 10001SSS
        
        Flags: Z, S, P, CY, AC
        """
        tests = [(0x88, Registers.B), (0x89, Registers.C), (0x8a, Registers.D),
                 (0x8b, Registers.E), (0x8b, Registers.H), (0x8c, Registers.L)]

        for op, reg in tests:
            self._clear_flags()
            self.set_register(reg, 0x12)
            self.set_register(Registers.A, 0x12)
            self.machine.adc(op)
            self.assertEqual(self.machine._registers[Registers.A], 0x24)
            self._test_flag(Flags.CARRY, "Carry", 0)
            self._test_flag(Flags.AUX_CARRY, "Aux Carry", 0)
            self._test_flag(Flags.SIGN, "Sign", 0)
            self._test_flag(Flags.ZERO, "ZERO", 0)
            self._test_flag(Flags.PARITY, "Parity", 1)

        # parity
        self._clear_flags()
        self.machine._flags[Flags.PARITY] = 1
        self.machine._flags[Flags.CARRY] = 1
        self.set_register(Registers.B, 0x1)
        self.set_register(Registers.A, 0x0)
        self.machine.adc(0x88)
        self.assertEqual(self.machine._registers[Registers.A], 0x2)
        for f in self.machine._flags:
            self.assertEqual(f, 0)

        self._clear_flags()
        self.set_register(Registers.B, 0xff)
        self.set_register(Registers.A, 0x1)
        self.machine.adc(0x88)
        self.assertEqual(self.machine._registers[Registers.A], 0x00)
        self._test_flag(Flags.CARRY, "Carry", 1)
        self._test_flag(Flags.AUX_CARRY, "Aux Carry", 1)
        self._test_flag(Flags.ZERO, "Zero", 1)

        self._clear_flags()
        self.set_register(Registers.B, 0x7f)
        self.set_register(Registers.A, 0x2)
        self.machine.adc(0x88)
        self._test_flag(Flags.SIGN, "Sign", 1)

    def test_aci(self):
        """Add immediate with carry.
        (A) <- (A) + CY + operands[0]

        Flags: Z, S, P, CY, AC
        """
        self._clear_flags()
        self.set_register(Registers.A, 0x12)
        self.machine.aci(0xce, 0x12)
        self.assertEqual(self.machine._registers[Registers.A], 0x24)
        self._test_flag(Flags.PARITY, "Parity", 1)

        self._clear_flags()
        self.machine._flags[Flags.PARITY] = 1
        self.machine._flags[Flags.CARRY] = 1
        self.set_register(Registers.A, 0x1)
        self.machine.aci(0xce, 0x0)
        self.assertEqual(self.machine._registers[Registers.A], 0x2)
        for f in self.machine._flags:
            self.assertEqual(f, 0)

        self._clear_flags()
        self.set_register(Registers.A, 0x1)
        self.machine.aci(0xce, 0xff)
        self.assertEqual(self.machine._registers[Registers.A], 0x00)
        self._test_flag(Flags.CARRY, "Carry", 1)
        self._test_flag(Flags.AUX_CARRY, "Aux Carry", 1)
        self._test_flag(Flags.ZERO, "Zero", 1)

        self._clear_flags()
        self.set_register(Registers.A, 0x2)
        self.machine.aci(0xce, 0x7f)
        self._test_flag(Flags.SIGN, "Sign", 1)


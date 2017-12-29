import sys
import logging
from collections import namedtuple

from cpu import Flags, Registers, RegisterPair
from utils import byte_to_signed_int, int_to_signed_byte


"""
OpCode object
-- opcode byte
-- length number of bytes in total instruction (opcode and operands)
-- mnemonic string-based instruction
-- optype either "none", "immediate", or "address" to specify if the 
          operands are immediate values or addresses
-- handler function to process the instruction
"""
OpCode = namedtuple('OpCode', ['opcode', "length", "mnemonic", "optype", "handler"])

"""
ConditionalFlag 
-- used to map bit-encoding to the flag and value to trigger a conditional instruction

NZ -- 000  (not zero)
Z  -- 001  (zero)
NC -- 010  (no carry)
C  -- 011  (carry)
PO -- 100  (parity odd)
PE -- 101  (parity even)
P  -- 110  (positive)
M  -- 111  (negative/minus)
"""
ConditionalFlag = namedtuple('ConditionalFlag', ['flag', 'val'])

class RomLoadException(Exception):
    def __init__(self, msg):
        self._msg = msg

    def __str__(self):
        return self._msg


class RomException(Exception):
    def __init__(self, msg):
        self._msg = msg

    def __str__(self):
        return self._msg


class OutOfMemoryException(Exception):
    pass


class EmulatorRuntimeException(Exception):
    def __init__(self, opcode, msg):
        """
        Exception raised when executing the given opcode
        :param opcode: opcode that couldn't be executed
        :param msg: Descriptive message about problem
        """
        self.op = opcode
        self.msg = msg

    def __repr(self):
        return "Error processing instruction {0:02X}: {1}".format(self.op, self.msg)


class HaltException(Exception):
    pass


class Machine8080:
    def __init__(self):
        self._memory = None
        self._pc = 0
        self._flags = Flags()
        self._registers = Registers()
        self._sp = 0
        self._condition_flags = {0: ConditionalFlag(Flags.ZERO, 0),
                                 1: ConditionalFlag(Flags.ZERO, 1),
                                 2: ConditionalFlag(Flags.CARRY, 0),
                                 3: ConditionalFlag(Flags.CARRY, 1),
                                 4: ConditionalFlag(Flags.PARITY, 0),
                                 5: ConditionalFlag(Flags.PARITY, 1),
                                 6: ConditionalFlag(Flags.SIGN, 0),
                                 7: ConditionalFlag(Flags.SIGN, 1)}
        self.opcodes = (
            OpCode(int('00', 16), 1, "NOP", "none", self.nop),
            OpCode(int('01', 16), 3, "LXI B", "immediate", self.lxi),
            OpCode(int('02', 16), 1, "STAX B", "none", self.stax),
            OpCode(int('03', 16), 1, "INX B", "none", self.inx),
            OpCode(int('04', 16), 1, "INR B", "none", self.inr),
            OpCode(int('05', 16), 1, "DCR B", "none", self.dcr),
            OpCode(int('06', 16), 2, "MVI B", "immediate", self.mvi),
            OpCode(int('07', 16), 1, "RLC", "none", self.rlc),
            OpCode(int('08', 16), 1, "UNKNOWN", "none", self.unhandled_instruction),
            OpCode(int('09', 16), 1, "DAD B", "none", self.dad),
            OpCode(int('0a', 16), 1, "LDAX B", "none", self.ldax),
            OpCode(int('0b', 16), 1, "DCX B", "none", self.dcx),
            OpCode(int('0c', 16), 1, "INR C", "none", self.inr),
            OpCode(int('0d', 16), 1, "DCR C", "none", self.dcr),
            OpCode(int('0e', 16), 2, "MVI C", "immediate", self.mvi),
            OpCode(int('0f', 16), 1, "RRC", "none", self.rrc),
            OpCode(int('10', 16), 1, "UNKNOWN", "none", self.unhandled_instruction),
            OpCode(int('11', 16), 3, "LXI D", "immediate", self.lxi),
            OpCode(int('12', 16), 1, "STAX D", "none", self.stax),
            OpCode(int('13', 16), 1, "INX D", "none", self.inx),
            OpCode(int('14', 16), 1, "INR D", "none", self.inr),
            OpCode(int('15', 16), 1, "DCR D", "none", self.dcr),
            OpCode(int('16', 16), 2, "MVI D,", "immediate", self.mvi),
            OpCode(int('17', 16), 1, "RAL", "none", self.ral),
            OpCode(int('18', 16), 1, "UNKNOWN", "none", self.unhandled_instruction),
            OpCode(int('19', 16), 1, "DAD D", "none", self.dad),
            OpCode(int('1a', 16), 1, "LDAX D", "none", self.ldax),
            OpCode(int('1b', 16), 1, "DCX D", "none", self.dcx),
            OpCode(int('1c', 16), 1, "INR E", "none", self.inr),
            OpCode(int('1d', 16), 1, "DCR E", "none", self.dcr),
            OpCode(int('1e', 16), 2, "MVI E,", "immediate", self.mvi),
            OpCode(int('1f', 16), 1, "RAR", "none", self.rar),
            OpCode(int('20', 16), 1, "UNKNOWN", "none", self.unhandled_instruction),
            OpCode(int('21', 16), 3, "LXI H", "immediate", self.lxi),
            OpCode(int('22', 16), 3, "SHLD", "address", self.shld),
            OpCode(int('23', 16), 1, "INX H", "none", self.inx),
            OpCode(int('24', 16), 1, "INR H", "none", self.inr),
            OpCode(int('25', 16), 1, "DCR H", "none", self.dcr),
            OpCode(int('26', 16), 2, "MVI H,", "immediate", self.mvi),
            OpCode(int('27', 16), 1, "DAA", "none", self.unhandled_instruction),
            OpCode(int('28', 16), 1, "UNKNOWN", "none", self.unhandled_instruction),
            OpCode(int('29', 16), 1, "DAD H", "none", self.dad),
            OpCode(int('2a', 16), 3, "LHLD", "address", self.lhld),
            OpCode(int('2b', 16), 1, "DCX H", "none", self.dcx),
            OpCode(int('2c', 16), 1, "UNKNOWN", "none", self.unhandled_instruction),
            OpCode(int('2d', 16), 1, "UNKNOWN", "none", self.unhandled_instruction),
            OpCode(int('2e', 16), 2, "MVI L,", "immediate", self.mvi),
            OpCode(int('2f', 16), 1, "CMA", "none", self.cma),
            OpCode(int('30', 16), 1, "UNKNOWN", "none", self.unhandled_instruction),
            OpCode(int('31', 16), 3, "LXI SP", "immediate", self.lxi),
            OpCode(int('32', 16), 3, "STA", "address", self.sta),
            OpCode(int('33', 16), 1, "INX SP", "none", self.inx),
            OpCode(int('34', 16), 1, "INR M", "none", self.inr),
            OpCode(int('35', 16), 1, "DCR M", "none", self.dcr),
            OpCode(int('36', 16), 2, "MVI M,", "immediate", self.mvi),
            OpCode(int('37', 16), 1, "STC", "none", self.stc),
            OpCode(int('38', 16), 1, "UNKNOWN", "none", self.unhandled_instruction),
            OpCode(int('39', 16), 1, "DAD SP", "none", self.dad),
            OpCode(int('3a', 16), 3, "LDA", "address", self.lda),
            OpCode(int('3b', 16), 1, "DCX SP", "none", self.dcx),
            OpCode(int('3c', 16), 1, "INR A", "none", self.inr),
            OpCode(int('3d', 16), 1, "DCR A", "none", self.dcr),
            OpCode(int('3e', 16), 2, "MVI A,", "immediate", self.mvi),
            OpCode(int('3f', 16), 1, "CMC", "none", self.cmc),
            OpCode(int('40', 16), 1, "MOV B,B", "none", self.mov),
            OpCode(int('41', 16), 1, "MOV B,C", "none", self.mov),
            OpCode(int('42', 16), 1, "MOV B,D", "none", self.mov),
            OpCode(int('43', 16), 1, "MOV B,E", "none", self.mov),
            OpCode(int('44', 16), 1, "MOV B,H", "none", self.mov),
            OpCode(int('45', 16), 1, "MOV B,L", "none", self.mov),
            OpCode(int('46', 16), 1, "MOV B,M", "none", self.mov),
            OpCode(int('47', 16), 1, "MOV B,A", "none", self.mov),
            OpCode(int('48', 16), 1, "MOV C,B", "none", self.mov),
            OpCode(int('49', 16), 1, "MOV C,C", "none", self.mov),
            OpCode(int('4a', 16), 1, "MOV C,D", "none", self.mov),
            OpCode(int('4b', 16), 1, "MOV C,E", "none", self.mov),
            OpCode(int('4c', 16), 1, "MOV C,H", "none", self.mov),
            OpCode(int('4d', 16), 1, "MOV C,L", "none", self.mov),
            OpCode(int('4e', 16), 1, "MOV C,M", "none", self.mov),
            OpCode(int('4f', 16), 1, "MOV C,A", "none", self.mov),
            OpCode(int('50', 16), 1, "MOV D,B", "none", self.mov),
            OpCode(int('51', 16), 1, "MOV D,C", "none", self.mov),
            OpCode(int('52', 16), 1, "MOV D,D", "none", self.mov),
            OpCode(int('53', 16), 1, "MOV D,E", "none", self.mov),
            OpCode(int('54', 16), 1, "MOV D,H", "none", self.mov),
            OpCode(int('55', 16), 1, "MOV D,L", "none", self.mov),
            OpCode(int('56', 16), 1, "MOV D,M", "none", self.mov),
            OpCode(int('57', 16), 1, "MOV D,A", "none", self.mov),
            OpCode(int('58', 16), 1, "MOV E,B", "none", self.mov),
            OpCode(int('59', 16), 1, "MOV E,C", "none", self.mov),
            OpCode(int('5a', 16), 1, "MOV E,D", "none", self.mov),
            OpCode(int('5b', 16), 1, "MOV E,E", "none", self.mov),
            OpCode(int('5c', 16), 1, "MOV E,H", "none", self.mov),
            OpCode(int('5d', 16), 1, "MOV E,L", "none", self.mov),
            OpCode(int('5e', 16), 1, "MOV E,M", "none", self.mov),
            OpCode(int('5f', 16), 1, "MOV E,A", "none", self.mov),
            OpCode(int('60', 16), 1, "MOV H,B", "none", self.mov),
            OpCode(int('61', 16), 1, "MOV H,C", "none", self.mov),
            OpCode(int('62', 16), 1, "MOV H,D", "none", self.mov),
            OpCode(int('63', 16), 1, "MOV H,E", "none", self.mov),
            OpCode(int('64', 16), 1, "MOV H,H", "none", self.mov),
            OpCode(int('65', 16), 1, "MOV H,L", "none", self.mov),
            OpCode(int('66', 16), 1, "MOV H,M", "none", self.mov),
            OpCode(int('67', 16), 1, "MOV H,A", "none", self.mov),
            OpCode(int('68', 16), 1, "MOV L,B", "none", self.mov),
            OpCode(int('69', 16), 1, "MOV L,C", "none", self.mov),
            OpCode(int('6a', 16), 1, "MOV L,D", "none", self.mov),
            OpCode(int('6b', 16), 1, "MOV L,E", "none", self.mov),
            OpCode(int('6c', 16), 1, "MOV L,H", "none", self.mov),
            OpCode(int('6d', 16), 1, "MOV L,L", "none", self.mov),
            OpCode(int('6e', 16), 1, "MOV L,M", "none", self.mov),
            OpCode(int('6f', 16), 1, "MOV L,A", "none", self.mov),
            OpCode(int('70', 16), 1, "MOV M,B", "none", self.mov),
            OpCode(int('71', 16), 1, "MOV M,C", "none", self.mov),
            OpCode(int('72', 16), 1, "MOV M,D", "none", self.mov),
            OpCode(int('73', 16), 1, "MOV M,E", "none", self.mov),
            OpCode(int('74', 16), 1, "MOV M,H", "none", self.mov),
            OpCode(int('75', 16), 1, "MOV M,L", "none", self.mov),
            OpCode(int('76', 16), 1, "HALT", "none", self.halt),
            OpCode(int('77', 16), 1, "MOV M,A", "none", self.mov),
            OpCode(int('78', 16), 1, "MOV A,B", "none", self.mov),
            OpCode(int('79', 16), 1, "MOV A,C", "none", self.mov),
            OpCode(int('7a', 16), 1, "MOV A,D", "none", self.mov),
            OpCode(int('7b', 16), 1, "MOV A,E", "none", self.mov),
            OpCode(int('7c', 16), 1, "MOV A,H", "none", self.mov),
            OpCode(int('7d', 16), 1, "MOV A,L", "none", self.mov),
            OpCode(int('7e', 16), 1, "MOV A,M", "none", self.mov),
            OpCode(int('7f', 16), 1, "MOV A,A", "none", self.mov),
            OpCode(int('80', 16), 1, "ADD B", "none", self.add),
            OpCode(int('81', 16), 1, "ADD C", "none", self.add),
            OpCode(int('82', 16), 1, "ADD D", "none", self.add),
            OpCode(int('83', 16), 1, "ADD E", "none", self.add),
            OpCode(int('84', 16), 1, "ADD H", "none", self.add),
            OpCode(int('85', 16), 1, "ADD L", "none", self.add),
            OpCode(int('86', 16), 1, "ADD M", "none", self.add),
            OpCode(int('87', 16), 1, "ADD A", "none", self.add),
            OpCode(int('88', 16), 1, "ADC B", "none", self.adc),
            OpCode(int('89', 16), 1, "ADC C", "none", self.adc),
            OpCode(int('8a', 16), 1, "ADC D", "none", self.adc),
            OpCode(int('8b', 16), 1, "ADC E", "none", self.adc),
            OpCode(int('8c', 16), 1, "ADC H", "none", self.adc),
            OpCode(int('8d', 16), 1, "ADC L", "none", self.adc),
            OpCode(int('8e', 16), 1, "ADC M", "none", self.adc),
            OpCode(int('8f', 16), 1, "ADC A", "none", self.adc),
            OpCode(int('90', 16), 1, "SUB B", "none", self.sub),
            OpCode(int('91', 16), 1, "SUB C", "none", self.sub),
            OpCode(int('92', 16), 1, "SUB D", "none", self.sub),
            OpCode(int('93', 16), 1, "SUB E", "none", self.sub),
            OpCode(int('94', 16), 1, "SUB H", "none", self.sub),
            OpCode(int('95', 16), 1, "SUB L", "none", self.sub),
            OpCode(int('96', 16), 1, "SUB M", "none", self.sub),
            OpCode(int('97', 16), 1, "SUB A", "none", self.sub),
            OpCode(int('98', 16), 1, "SBB B", "none", self.unhandled_instruction),
            OpCode(int('99', 16), 1, "SBB C", "none", self.unhandled_instruction),
            OpCode(int('9a', 16), 1, "SBB D", "none", self.unhandled_instruction),
            OpCode(int('9b', 16), 1, "SBB E", "none", self.unhandled_instruction),
            OpCode(int('9c', 16), 1, "SBB H", "none", self.unhandled_instruction),
            OpCode(int('9d', 16), 1, "SBB L", "none", self.unhandled_instruction),
            OpCode(int('9e', 16), 1, "SBB M", "none", self.unhandled_instruction),
            OpCode(int('9f', 16), 1, "SBB A", "none", self.unhandled_instruction),
            OpCode(int('a0', 16), 1, "ANA B", "none", self.ana),
            OpCode(int('a1', 16), 1, "ANA C", "none", self.ana),
            OpCode(int('a2', 16), 1, "ANA D", "none", self.ana),
            OpCode(int('a3', 16), 1, "ANA E", "none", self.ana),
            OpCode(int('a4', 16), 1, "ANA H", "none", self.ana),
            OpCode(int('a5', 16), 1, "ANA L", "none", self.ana),
            OpCode(int('a6', 16), 1, "ANA M", "none", self.ana),
            OpCode(int('a7', 16), 1, "ANA A", "none", self.ana),
            OpCode(int('a8', 16), 1, "XRA B", "none", self.xra),
            OpCode(int('a9', 16), 1, "XRA C", "none", self.xra),
            OpCode(int('aa', 16), 1, "XRA D", "none", self.xra),
            OpCode(int('ab', 16), 1, "XRA E", "none", self.xra),
            OpCode(int('ac', 16), 1, "XRA H", "none", self.xra),
            OpCode(int('ad', 16), 1, "XRA L", "none", self.xra),
            OpCode(int('ae', 16), 1, "XRA M", "none", self.xra),
            OpCode(int('af', 16), 1, "XRA A", "none", self.xra),
            OpCode(int('b0', 16), 1, "ORA B", "none", self.ora),
            OpCode(int('b1', 16), 1, "ORA C", "none", self.ora),
            OpCode(int('b2', 16), 1, "ORA D", "none", self.ora),
            OpCode(int('b3', 16), 1, "ORA E", "none", self.ora),
            OpCode(int('b4', 16), 1, "ORA H", "none", self.ora),
            OpCode(int('b5', 16), 1, "ORA L", "none", self.ora),
            OpCode(int('b6', 16), 1, "ORA M", "none", self.ora),
            OpCode(int('b7', 16), 1, "ORA A", "none", self.ora),
            OpCode(int('b8', 16), 1, "CMP B", "none", self.cmp),
            OpCode(int('b9', 16), 1, "CMP C", "none", self.cmp),
            OpCode(int('ba', 16), 1, "CMP D", "none", self.cmp),
            OpCode(int('bb', 16), 1, "CMP E", "none", self.cmp),
            OpCode(int('bc', 16), 1, "CMP H", "none", self.cmp),
            OpCode(int('bd', 16), 1, "CMP L", "none", self.cmp),
            OpCode(int('be', 16), 1, "CMP M", "none", self.cmp),
            OpCode(int('bf', 16), 1, "CMP A", "none", self.cmp),
            OpCode(int('c0', 16), 1, "RNZ", "none", self.conditional_ret),
            OpCode(int('c1', 16), 1, "POP B", "none", self.pop_pair),
            OpCode(int('c2', 16), 3, "JNZ", "address", self.conditional_jmp),
            OpCode(int('c3', 16), 3, "JMP", "address", self.jmp),
            OpCode(int('c4', 16), 3, "CNZ", "address", self.conditional_call),
            OpCode(int('c5', 16), 1, "PUSH B", "none", self.push_pair),
            OpCode(int('c6', 16), 2, "ADI", "immediate", self.adi),
            OpCode(int('c7', 16), 1, "RST", "none", self.rst),
            OpCode(int('c8', 16), 1, "RZ", "none", self.conditional_ret),
            OpCode(int('c9', 16), 1, "RET", "none", self.ret),
            OpCode(int('ca', 16), 3, "JZ", "address", self.conditional_jmp),
            OpCode(int('cb', 16), 1, "UNKNOWN", "none", self.unhandled_instruction),
            OpCode(int('cc', 16), 3, "CZ", "address", self.conditional_call),
            OpCode(int('cd', 16), 3, "CALL", "address", self.call),
            OpCode(int('ce', 16), 2, "ACI", "immediate", self.aci),
            OpCode(int('cf', 16), 1, "RST", "none", self.rst),
            OpCode(int('d0', 16), 1, "RNC", "none", self.conditional_ret),
            OpCode(int('d1', 16), 1, "POP D", "none", self.pop_pair),
            OpCode(int('d2', 16), 3, "JNC", "address", self.conditional_jmp),
            OpCode(int('d3', 16), 2, "OUT", "immediate", self.out),
            OpCode(int('d4', 16), 3, "CNC", "address", self.conditional_call),
            OpCode(int('d5', 16), 1, "PUSH D", "none", self.push_pair),
            OpCode(int('d6', 16), 2, "SUI", "immediate", self.sui),
            OpCode(int('d7', 16), 1, "RST", "none", self.rst),
            OpCode(int('d8', 16), 1, "RC", "none", self.conditional_ret),
            OpCode(int('d9', 16), 1, "UNKNOWN", "none", self.unhandled_instruction),
            OpCode(int('da', 16), 3, "JC", "address", self.conditional_jmp),
            OpCode(int('db', 16), 2, "IN", "immediate", self.input),
            OpCode(int('dc', 16), 3, "CC", "address", self.conditional_call),
            OpCode(int('dd', 16), 1, "UNKNOWN", "none", self.unhandled_instruction),
            OpCode(int('de', 16), 2, "SBI", "immediate", self.unhandled_instruction),
            OpCode(int('df', 16), 1, "RST", "none", self.rst),
            OpCode(int('e0', 16), 1, "RPO", "none", self.conditional_ret),
            OpCode(int('e1', 16), 1, "POP H", "none", self.pop_pair),
            OpCode(int('e2', 16), 3, "JPO", "address", self.conditional_jmp),
            OpCode(int('e3', 16), 1, "XTHL", "none", self.xthl),
            OpCode(int('e4', 16), 3, "CPO", "address", self.conditional_call),
            OpCode(int('e5', 16), 1, "PUSH H", "none", self.push_pair),
            OpCode(int('e6', 16), 2, "ANI", "immediate", self.ani),
            OpCode(int('e7', 16), 1, "RST", "none", self.rst),
            OpCode(int('e8', 16), 1, "RPE", "none", self.conditional_ret),
            OpCode(int('e9', 16), 1, "PCHL", "none", self.pchl),
            OpCode(int('ea', 16), 3, "JPE", "address", self.conditional_jmp),
            OpCode(int('eb', 16), 1, "XCHG", "none", self.xchg),
            OpCode(int('ec', 16), 3, "CPE", "address", self.conditional_call),
            OpCode(int('ed', 16), 1, "UNKNOWN", "none", self.unhandled_instruction),
            OpCode(int('ee', 16), 2, "XRI", "immediate", self.xri),
            OpCode(int('ef', 16), 1, "RST", "none", self.rst),
            OpCode(int('f0', 16), 1, "RP", "none", self.conditional_ret),
            OpCode(int('f1', 16), 1, "POP PSW", "none", self.pop_psw),
            OpCode(int('f2', 16), 3, "JP", "address", self.conditional_jmp),
            OpCode(int('f3', 16), 1, "DI", "none", self.unhandled_instruction),
            OpCode(int('f4', 16), 3, "CP", "address", self.conditional_call),
            OpCode(int('f5', 16), 1, "PUSH PSW", "none", self.push_psw),
            OpCode(int('f6', 16), 2, "ORI", "immediate", self.ori),
            OpCode(int('f7', 16), 1, "RST", "none", self.rst),
            OpCode(int('f8', 16), 1, "RM", "none", self.conditional_ret),
            OpCode(int('f9', 16), 1, "SPHL", "none", self.sphl),
            OpCode(int('fa', 16), 3, "JM", "address", self.conditional_jmp),
            OpCode(int('fb', 16), 1, "EI", "none", self.unhandled_instruction),
            OpCode(int('fc', 16), 3, "CM", "address", self.conditional_call),
            OpCode(int('fd', 16), 1, "UNKNOWN", "none", self.unhandled_instruction),
            OpCode(int('fe', 16), 2, "CPI", "immediate", self.cpi),
            OpCode(int('ff', 16), 1, "RST", "none", self.rst),
        )

    def load(self, romfile):
        """Loads the given ROM file

        :param romfile: full path to the ROM to load

        :raises RomLoadException: if the file cannot be read
        """
        try:
            with open(romfile, "rb") as fp:
                self._memory = bytearray(fp.read())
                self._memory = self._memory + bytearray([0 for x in range(0x10000 - len(self._memory))])
                self._pc = 0
        except Exception as e:
            raise RomLoadException("{0}".format(e))

    def disassemble(self):
        """Disassembles the loaded ROM.

        :raises RomException: if a ROM hasn't been loaded
        """
        if self._memory is None:
            raise RomException("No ROM file loaded.")
        address = 0
        for inst, operands in self.next_instruction():
            print("{0:04X}: {1}  {2} {3}".format(address,
                                                 Machine8080.instruction_bytes(inst, operands),
                                                 inst.mnemonic,
                                                 Machine8080.format_operand(inst, operands)))
            address += inst.length

    def execute(self):
        if self._memory is None:
            raise RomException("No ROM file loaded.")
        for inst, operands in self.next_instruction():
            try:
                inst.handler(inst.opcode, operands)
            except EmulatorRuntimeException as e:
                logging.error("{}".format(e))
            except HaltException:
                break

    @staticmethod
    def format_operand(opcode, ops):
        """
        Return a string representation of the given operands.
        :param opcode:  OpCode tuple for the operands
        :param ops: An iterable thing of operands
        :return: a string
        """
        if len(ops) == 0:
            return ""
        prefix = "#" if opcode.optype == "immediate" else "$"
        tmp = list(ops)
        # 8080 chip is little endian so swap the bytes
        tmp = tmp[::-1]
        return "{0}{1}".format(prefix, "".join(["{:02X}".format(x) for x in tmp]))

    @staticmethod
    def instruction_bytes(opcode, operands):
        """Returns a string of the opcode and operand bytes.
        """
        b = ["{:02X}".format(opcode.opcode)]
        b.extend(["{:02X}".format(o) for o in operands])
        for x in range(3 - len(b)):
            b.append("  ")
        return " ".join(b)

    def next_instruction(self):
        """Parses loaded ROM and returns next instruction.

        The program counter is advanced for every instruction.

        :return tuple:  Returns tuple of OpCode and list of operands (may be empty)
        """
        while self._pc < len(self._memory):
            op = self.opcodes[self._memory[self._pc]]
            operands = [self._memory[self._pc + x] for x in range(1, op.length)]
            self._pc += op.length
            yield (op, operands)

    def read_memory(self, address, size):
        """
        Reads size bytes of memory starting at the given address.
        :param address:
        :param size:
        :return: tuple of memory read or just byte if size == 1
        :raises: OutOfMemory error if the read goes past the end of memory
        """
        if address + size >= len(self._memory):
            raise OutOfMemoryException()
        return [b for b in self._memory[address:address + size]]

    def write_memory(self, address, data):
        """
        Writes the given data one byte to the given address
        :param address:   Memory address
        :param data: Data to write
        :return:
        """
        self._memory[address] = data

    def nop(self, *args):
        logging.info("NOP")

    def mov(self, opcode, *args):
        """
        Move data between registers and memory.

        The bit-encoding for the move instruction is
            0|1|D|S|T|S|R|C

        if the dst or src is Registers.M, then we get an
        address from the H and L registers and do the operation
        between memory.

        *** Note:  You cannot move data from memory to memory.
        This function won't even get called in that case (it's
        HALT instruction)

        :param opcode:
        :param args:  This is ignored; mov is a one byte instruction
        :return:
        """
        logging.info(f'MOV {opcode:02X}')
        dst = Registers.get_register_from_opcode(opcode, 3)
        src = Registers.get_register_from_opcode(opcode, 0)

        if dst != Registers.M and src != Registers.M:
            self._registers[dst] = self._registers[src]
        else:
            addr = self._registers.get_address_from_pair(Registers.H)
            if src == Registers.M:
                self._registers[dst], *_ = self.read_memory(addr, 1)
            else:
                # dst is memory
                self.write_memory(addr, self._registers[src])

    def unhandled_instruction(self, opcode, *args):
        logging.warning(f'Unhandled instruction: {opcode:02X}')

    def stax(self, opcode, *args):
        """
        Contents of accumulator are stored in the address
        stored in pairs B, C (opcode 0x02) or D,E (opcode 0x12)

        :param args:
        :return:
        """
        logging.info(f'STAX {opcode:02X}')
        assert ((opcode == 0x02) or (opcode == 0x12))
        pair = Registers.B if opcode == 0x02 else Registers.D
        address = self._registers.get_address_from_pair(pair)
        self.write_memory(address, self._registers[Registers.A])

    def ldax(self, opcode, *args):
        """
        The contents of the memory location addressed by B,C (opcode 0x0a)
        or D,E (opcode 0x1a) are loaded into the accumulator.
        :param opcode:
        :param args:
        :return:
        """
        logging.info(f'LDAX {opcode:02X}')
        assert (opcode in (0x0a, 0x1a))
        pair = Registers.B if opcode == 0x0a else Registers.D
        address = self._registers.get_address_from_pair(pair)
        self._registers[Registers.A], *_ = self.read_memory(address, 1)

    def pchl(self, *args):
        """
        The contents of the H register replace the most significant 8-bits
        of the program counter and the contents of the L register replace
        the least-significant 8-bits of the program counter.

        In other words, program execution continues at the address stored
        in H and L
        :param args:
        :return:
        """
        logging.info('PCHL')
        self._pc = self._registers.get_address_from_pair(Registers.H)

    def jmp(self, opcode, operands):
        """
        Unconditional jump to address stored in lo and hi
        :param opcode: 0xc3
        :param operands: tuple of lo and hi bytes of address
        :return:
        """
        lo, hi = operands
        logging.info(f'JMP {hi:02X}{lo:02X}')
        self._pc = (hi << 8) | lo

    def conditional_jmp(self, opcode, operands):
        """
        sets the program counter to the address in operands if the condition
        specified by the opcode is true
        :param opcode:
        :param operands:
        :return:
        """
        lo, hi = operands
        logging.info(f'CONDITIONAL JMP {opcode:02X} {hi:02X}{lo:02X}')
        # map opcodes to the flags that dictate them and the expected setting
        jmpbits = {0xda: (Flags.CARRY, 1), 0xd2: (Flags.CARRY, 0), 0xe2: (Flags.PARITY, 0),
                   0xea: (Flags.PARITY, 1), 0xf2: (Flags.SIGN, 0), 0xfa: (Flags.SIGN, 1),
                   0xc2: (Flags.ZERO, 0), 0xca: (Flags.ZERO, 1)}

        flag, res = jmpbits[opcode]
        if self._flags[flag] == res:
            self._pc = (hi << 8) | lo

    def _logical_and_accumulator(self, val):
        """Performs logical AND with val and contents of accumulator.

        sets Zero, Sign, Parity bits appropriately.
        """
        res = val & self._registers[Registers.A]
        self._registers[Registers.A] = res
        self._flags.calculate_parity(res)
        self._flags.set_zero(res)
        self._flags.set_sign(res)
        

    def ana(self, opcode, *args):
        """
        Logical AND the register (or byte at memory) with the accumulator.
        Carry bit is reset to 0

        Condition bits: Carry, zero, sign, parity
        :param opcode:
        :param args:
        :return:
        """
        logging.info(f'ANA {opcode:02X}')
        reg = self._registers.get_register_from_opcode(opcode, 0)
        if reg == Registers.M:
            val, *_ = self.read_memory(self._registers.get_address_from_pair(Registers.H), 1)
        else:
            val = self._registers[reg]

        self._flags.clear(Flags.CARRY)
        self._logical_and_accumulator(val)

    def ani(self, opcode, *operands):
        """Logical AND the immediate byte with the accumulator.

        CY and AC are reset
        """
        logging.info(f'ANI {operands[0]:02X}')
        self._flags.clear(Flags.CARRY)
        self._flags.clear(Flags.AUX_CARRY)
        self._logical_and_accumulator(operands[0])

    def _internal_or(self, val, orfunc):
        """[A] = orfunc([A], val)

        Carry and AUX are reset
        Sign, Zero, Parity are set accordingly
        """
        res = orfunc(val, self._registers[Registers.A])
        logging.debug(f'[_internal_xor] {val:02X} ^ {self._registers[Registers.A]:02X} = {res:02X}')
        self._registers[Registers.A] = res
        self._flags.clear(Flags.CARRY)
        self._flags.clear(Flags.AUX_CARRY)
        self._flags.calculate_parity(res)
        self._flags.set_zero(res)
        self._flags.set_sign(res)

    def xra(self, opcode, *args):
        """
        Exclusive-OR the register (or memory) specified in the opcode

        Carry bit is reset.
        Zero, sign, parity, auxiliary carry?

        The reference manual states that the carry bit is reset but doesn't say
        anything about the aux. carry bit.  The XRI instruction (xor immediate) 
        does NOT affect the aux carry.  So I wonder if it was a mistake by the 
        manual writers to include it here.  I've seen other mistakes in the 
        document.

        (Modern Intel references state that the aux carry is undefined for this 
        instruction)
        :param opcode:
        :param args:
        """
        logging.info(f'XRA {opcode:02X}')
        reg = self._registers.get_register_from_opcode(opcode, 0)
        if reg == Registers.M:
            val, *_ = self.read_memory(self._registers.get_address_from_pair(Registers.H), 1)
        else:
            val = self._registers[reg]
        self._internal_or(val, lambda a,b: a ^ b)

    def xri(self, opcode, operands):
        """
        xor second byte of instruction is xor'd with accumulator

        Carry and AC is cleared
        Zero, Sign, Parity set appropriately

        :param opcode:
        :param operands:
        :return:
        """
        self._internal_or(operands[0], lambda a,b: a ^ b)

    def mvi(self, opcode, operands):
        """
        Move the byte given in operands[0] to the specified register or memory location.

        opcode:
        000rrr110

        :param opcode:
        :param operands:
        :return:
        """
        reg = self._registers.get_register_from_opcode(opcode, 3)
        if reg == Registers.M:
            self.write_memory(self._registers.get_address_from_pair(Registers.H), operands[0])
        else:
            self._registers[reg] = operands[0]

    def lxi(self, opcode, operands):
        """Byte 3 of the instruction is moved into the high-order register of the
        register pair.  Byte 2 is moved into the low-order register of the pair

        Register pairs can be B, D, H, and SP (stack pointer)

        00rp0001
        """
        rp = (opcode >> 4) & 0x3
        logging.debug(f'register pair: {rp:02x}')
        if rp == 0x3: # stack pointer
            self._sp = (operands[1] << 8) | operands[0]
        else:
            pair = self._registers.get_pairs(rp)
            self._registers[pair.lo] = operands[0]
            self._registers[pair.hi] = operands[1]

    def lda(self, opcode, operands):
        """
        Content of the memory address specified in bytes 2 and 3 are moved into accumulator
        :param opcode:
        :param operands:
        :return:
        """
        address = (operands[1] << 8) | operands[0]
        self._registers[Registers.A], *_ = self.read_memory(address, 1)

    def sta(self, opcode, operands):
        """
        The contents of the accumulator are stored in the address (operands[0] = lo) operands.
        :param opcode:
        :param operands:
        :return:
        """
        address = (operands[1] << 8) | operands[0]
        self.write_memory(address, self._registers[Registers.A])

    def lhld(self, opcode, operands):
        """
        The first byte at the address given by the operands is stored in L.  
        The next address is stored in H.

        [L] = (op[1])(op[0])
        [H] = (op[1])(op[0]) + 1
        :param opcode:
        :param operands:
        :return:
        """
        address = (operands[1] << 8) | operands[0]
        self._registers[Registers.L], self._registers[Registers.H] = self.read_memory(address, 2)

    def shld(self, opcodes, operands):
        """
        Content of L is stored in address at operands.
        Content of H is stored in address+1

        :param opcodes:
        :param operands:
        :return:
        """
        address = (operands[1] << 8) | operands[0]
        self.write_memory(address, self._registers[Registers.L])
        self.write_memory(address+1, self._registers[Registers.H])

    def xchg(self, opcode, *args):
        """
        swap H and D registers
        swap L and E registers
        :param opcode:
        :param args:
        :return:
        """
        tmp = self._registers[Registers.H]
        self._registers[Registers.H] = self._registers[Registers.D]
        self._registers[Registers.D] = tmp
        tmp = self._registers[Registers.L]
        self._registers[Registers.L] = self._registers[Registers.E]
        self._registers[Registers.E] = tmp

    def ora(self, opcode, *args):
        """
        Inclusive OR between register encoded in opcode and Accumulator

        Carry and Aux Carry are cleared
        Zero, sign, parity are set appropriately
        :param opcode:
        :param args:
        :return:
        """
        reg = Registers.get_register_from_opcode(opcode, 0)
        if reg == Registers.M:
            address = self._registers.get_address_from_pair(Registers.H)
            val, *_ = self.read_memory(address, 1)
        else:
            val = self._registers[reg]
        self._internal_or(val, lambda a,b: a | b)

    def ori(self, opcode, operands):
        """
        Logical OR with immediate value
        :param opcode:
        :param operands:
        :return:
        """
        self._internal_or(operands[0], lambda  a,b: a | b)

    def call(self, opcode, operands):
        """
        Invoke a function
        ((SP)-1) <- PCH
        ((SP)-2) <- PCL
        (SP) <- (SP)-2
        (PC) <- (operands[1])(operands[0])

        :param opcode:
        :param operands:
        """
        self.write_memory(self._sp-1, (self._pc >> 8) & 0xFF)
        self.write_memory(self._sp-2, self._pc & 0xFF)
        self._sp -= 2
        self._pc = (operands[1] << 8) | operands[0]

    def conditional_call(self, opcode, operands):
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
        bitflag = (opcode >> 3) & 0x07  # mask off 3 bits
        cf = self._condition_flags[bitflag]
        if self._flags[cf.flag] == cf.val:
            self.call(opcode, operands)

    def ret(self, opcode, *args):
        """
        (PCL) <- (SP)
        (PCH) <- (SP)+1
        (SP) <- (SP)+2

        :param opcode:
        :param args:
        """
        lo, hi = self.read_memory(self._sp, 2)
        self._pc = (hi << 8) | lo
        self._sp += 2

    def conditional_ret(self, opcode, *args):
        """
        Instruction format:  11CCC000

        if CCC:
            ret
        :param opcode:
        :param args:
        :return:
        """
        bitflag = (opcode >> 3) & 0x7
        cf = self._condition_flags[bitflag]
        if self._flags[cf.flag] == cf.val:
            self.ret(opcode)

    def cmc(self, *args):
        """
        Complement carry bit
        :return:
        """
        if self._flags[Flags.CARRY] == 1:
            self._flags.clear(Flags.CARRY)
        else:
            self._flags.set(Flags.CARRY)

    def stc(self, *args):
        """
        Set Carry bit to 1
        :param args:
        """
        self._flags.set(Flags.CARRY)

    def cma(self, *args):
        """Complement the contents of the accumulator
        """
        self._registers[Registers.A] ^= 0xff

    def push_pair(self, opcode, *args):
        """
        Instruction: 11RP0101

        ((SP) - 1) <- (rh)
        ((SP)- 2)  <- (rl)
        (SP)       <- (SP) - 2
        :param opcode:
        :param args:
        """
        rh, rl = self._registers.get_pairs((opcode >> 4) & 0x3)
        self.write_memory(self._sp - 1, self._registers[rh])
        self.write_memory(self._sp - 2, self._registers[rl])
        self._sp -= 2

    def push_psw(self, *args):
        """
        ((SP)-1)   <- (A)
        ((SP)-2)
            0  <- CY
            1  <- 1
            2  <- P
            3  <- 0
            4  <- AC
            5  <- 0
            6  <- Z
            7  <- S
        (SP) <- (SP)-2
        :param args:
        """
        self.write_memory(self._sp - 1, self._registers[Registers.A])
        self.write_memory(self._sp - 2, self._flags.flags)
        self._sp -= 2

    def pop_pair(self, opcode, *args):
        """
        Instruction format:  11RP0001

        (rl) <- (SP)
        (rh) <- (sp) +1
        (sp) <- (sp) + 2
        :param opcode:
        :param args:
        """
        hi, lo = self._registers.get_pairs((opcode >> 4) & 0x3)
        self._registers[lo], self._registers[hi] = self.read_memory(self._sp, 2)
        self._sp += 2

    def pop_psw(self, *args):
        """
        flags <- (sp)
        A     <- (sp+1)
        (sp)  <- (sp+2)
        :param args:
        """
        self._flags.flags, self._registers[Registers.A] = self.read_memory(self._sp, 2)
        self._sp += 2

    def xthl(self, *args):
        """"
        (L)  <->  (SP)
        (H)  <->  (SP)+1
        """
        logging.info("XTHL")
        l, h = self.read_memory(self._sp, 2)
        tmp = self._registers[Registers.L]
        self._registers[Registers.L] = l
        self.write_memory(self._sp, tmp)

        tmp = self._registers[Registers.H]
        self._registers[Registers.H] = h
        self.write_memory(self._sp+1, tmp)

    def sphl(self, *args):
        """
        (SP) <- (H)(L)
        :param args:
        """
        logging.info("SPHL")
        self._sp = (self._registers[Registers.H] << 8) | self._registers[Registers.L]

    def halt(self, *args):
        logging.info("HALT")
        raise HaltException()

    def rlc(self, *args):
        """
        (An+1) <- (An); (A0) <- (A7)
        (CY) <- (A7)
        :return:
        """
        logging.info("RLC")
        val = self._registers[Registers.A]
        logging.debug(f'Current value of A: {val:02X}')
        bit = (val >> 7) & 0x1
        logging.debug(f'Current value of bit: {bit:02X}')
        if bit == 0:
            self._flags.clear(Flags.CARRY)
        else:
            self._flags.set(Flags.CARRY)
        val = (val << 1) & 0xff
        val |= bit
        logging.debug(f'New Value of A: {val:02X}')
        self._registers[Registers.A] = val

    def ral(self, *args):
        """
        Rotate left through carry

        Carry bit goes to A0, A7 goes to Carry, everything else shifts left
        :param args:
        """
        logging.info("RAL")
        cy = self._flags[Flags.CARRY]
        A = self._registers[Registers.A]
        self._flags[Flags.CARRY] = (A >> 7)&0x1
        A = (A << 1) & 0xFF
        A |= cy
        self._registers[Registers.A] = A

    def rrc(self, *args):
        """
        Rotate right
        (An-1) <- (An); (A7) <- (A0)
        (CY) <- (A0)
        :param args:
        """
        logging.info("RRC")
        A = self._registers[Registers.A]
        bit = A & 0x01
        A = (A >> 1) & 0xff
        A |= (bit << 7)
        self._flags[Flags.CARRY] = bit
        self._registers[Registers.A] = A

    def rar(self, *args):
        """
        An <- An+1
        CY <- A0
        A7 <- CY
        :param args:
        """
        logging.info(f'RAR')
        cy = self._flags[Flags.CARRY]
        A = self._registers[Registers.A]
        logging.debug("A & 0x01 = {0}".format(A&0x01))
        self._flags[Flags.CARRY] = A & 0x01
        A = ((A >> 1) & 0xff) | (cy << 7)
        self._registers[Registers.A] = A

    def _internal_sub(self, val):
        """Subtract val from A and set flags accordingly.
        :return: A - val
        """
        val = byte_to_signed_int(val)
        A = byte_to_signed_int(self._registers[Registers.A])

        self._flags.clear_all()
        if A < val:
            self._flags.set(Flags.CARRY)
            self._flags.set(Flags.SIGN)
        if (A&0x0f) < (val&0x0f):
            self._flags.set(Flags.AUX_CARRY)
        A -= val
        if A == 0:
            self._flags.set(Flags.ZERO)
        b = int_to_signed_byte(A)
        self._flags.calculate_parity(b)
        return b

    def cmp(self, opcode, *args):
        """
        Instruction format: 10111SSS

        Contents of register (or memory) is subtracted from A.
        Accumulator remains unchanged.  Condition flags are set.

        Z flag is set if (A) == SSS; CY is set if A < SSS
        :param opcode:
        :param args:
        """
        logging.info(f'CMP {opcode:02X}')
        reg = self._registers.get_register_from_opcode(opcode, 0)
        if reg == Registers.M:
            address = self._registers.get_address_from_pair(Registers.H)
            val, *_ = self.read_memory(address, 1)
        else:
            val = self._registers[reg]
        self._internal_sub(val)

    def cpi(self, opcode, operand, *args):
        """The operand is subtracted from the accumulator.  The flags
        are set appropriately.
        """
        logging.info(f'CPI {operand:02X}')
        self._internal_sub(operand)

    def inx(self, opcode, *arg):
        """
        (rh)(rl) <- (rh)(rl) + 1

        instruction: 00RP0011
        """
        logging.info(f'INX {opcode:02X}')
        pair = (opcode >> 4) & 0x3
        if pair == 3:
            self._sp = (self._sp + 1) & 0xffff
        else:
            pair = self._registers.get_pairs(pair)
            val = self._registers.get_value_from_pair(pair)
            val = (val + 1) & 0xffff
            self._registers.set_value_pair(pair, val)

    def dcx(self, opcode, *arg):
        """
        (rh)(rl) <- (rh)(rl)-1
        
        instruction format 00RP1011
        """
        logging.info(f'DCX {opcode:02X}')
        pair = (opcode >> 4) & 0x3
        if pair == 3:
            self._sp = (self._sp - 1) & 0xffff
        else:
            pair = self._registers.get_pairs(pair)
            val = self._registers.get_value_from_pair(pair)
            logging.debug(f'val = {val:04X} val-1 = {(val-1)&0xffff:04X}')
            val = (val - 1) & 0xffff
            self._registers.set_value_pair(pair, val)            

    def _set_register_value(self, reg, val):
        """Saves the given value in the specified register.

        :param reg: One of the defined Registers value, including M.
                    if reg == Registers.M then the value is stored in
                    the address specified by H and L
        :param val: Value to save.
        """
        if reg == Registers.M:
            addr = self._registers.get_address_from_pair(Registers.H)
            self.write_memory(addr, val)
        else:
            self._registers[reg] = val

    def inr(self, opcode, *args):
        """
        (R) <- (R) + 1

        instruction format: 00DDD100

        Flags affected: Z, S, P, AC
        """
        logging.info(f'INR {opcode:02X}')
        reg = Registers.get_register_from_opcode(opcode, 3)
        if reg == Registers.M:
            addr = self._registers.get_address_from_pair(Registers.H)
            val = self.read_memory(addr, 1)[0]
        else:
            val = self._registers[reg]

        if (val & 0x0f) == 0x0f:
            self._flags[Flags.AUX_CARRY] = 1
        else:
            self._flags[Flags.AUX_CARRY] = 0

        val = (val + 1) & 0xff
        self._flags.calculate_parity(val)
        self._flags.set_zero(val)
        self._flags.set_sign(val)

        self._set_register_value(reg, val)

    def dcr(self, opcode, *args):
        """
        (R) <- (R) - 1

        Instruction format: 00DDD101
        Flags: Z, S, P, AC
        """
        logging.info(f'DCR {opcode:02X}')
        reg = Registers.get_register_from_opcode(opcode, 3)
        if reg == Registers.M:
            addr = self._registers.get_address_from_pair(Registers.H)
            val = self.read_memory(addr, 1)[0]
        else:
            val = self._registers[reg]

        self._flags[Flags.AUX_CARRY] = 0
        if val & 0x0f == 0x00:
            self._flags[Flags.AUX_CARRY] = 1

        val = (val - 1) & 0xff
        self._flags.calculate_parity(val)
        self._flags.set_zero(val)
        self._flags.set_sign(val)
        self._set_register_value(reg, val)

    def dad(self, opcode, *args):
        """
        Add register pair to H and L

        (H)(L) <- (H)(L) + (RH)(RL)

        Instruction format 00RP1001
        
        Only Carry bit is set.
        """
        logging.info(f'DAD {opcode:02X}')
        pair = (opcode >> 4) & 0x3
        pair = self._registers.get_pairs(pair) 
        hl = self._registers.get_pairs(0x02)

        hl_val = self._registers.get_value_from_pair(hl)
        val = self._registers.get_value_from_pair(pair)

        logging.debug(f'HL value: {hl_val:04X}  Value {val:04X}')
        hl_val += val
        logging.debug(f'New total: {hl_val:04X}')

        self._flags[Flags.CARRY] = 0
        if hl_val > 0xffff:
            self._flags[Flags.CARRY] = 1
        hl_val = (hl_val & 0xffff)
        self._registers.set_value_pair(hl, hl_val) 

    def rst(self, opcode, *args):
        """
        (SP)-1 <- (PCH)
        (SP)-2 <- (PCL)
        (SP)   <- (SP)-2
        PC     <- 8 * NNN

        Instruction format:  11NNN111
        """
        logging.info(f'RST {opcode:02X}')
        self.write_memory(self._sp - 1, (self._pc  >> 8) & 0xff)
        self.write_memory(self._sp - 2, self._pc & 0xff)
        self._sp -= 2
        self._pc = 8 * ((opcode >> 3)&0x7)

    def adi(self, opcode, *operands):
        """
        (A) <- (A) + operands[0]

        Flags: Z, S, P, CY, AC
        """
        logging.info(f'ADI {operands[0]:02X}')
        self._flags[Flags.CARRY] = 0
        self._flags[Flags.AUX_CARRY] = 0

        A = self._registers[Registers.A]
        if (A & 0xf) + (operands[0]&0xf) > 0xf:
            self._flags[Flags.AUX_CARRY] = 1
        if A + operands[0] > 0xff:
            self._flags[Flags.CARRY] = 1

        A = (A + operands[0]) & 0xff

        self._flags.calculate_parity(A)
        self._flags.set_zero(A)
        self._flags.set_sign(A)
        self._registers[Registers.A] = A

    def add(self, opcode, *args):
        """
        (A) <- (A) + (r)

        Instruction format: 10000SSS
        Flags: Z, S, P, CY, AC
        """
        logging.info(f'ADD {opcode:02X}')
        self._flags[Flags.CARRY] = 0
        self._flags[Flags.AUX_CARRY] = 0

        reg = Registers.get_register_from_opcode(opcode, 0)
        if reg == Registers.M:
            addr = self._registers.get_address_from_pair(Registers.H)
            val = self.read_memory(addr, 1)[0]
        else:
            val = self._registers[reg]

        A = self._registers[Registers.A]
        if (A&0xf) + (val&0xf) > 0xf:
            self._flags[Flags.AUX_CARRY] = 1
        if A + val > 0xff:
            self._flags[Flags.CARRY] = 1

        A = (A + val) & 0xff
        self._flags.set_zero(A)
        self._flags.calculate_parity(A)
        self._flags.set_sign(A)
        self._registers[Registers.A] = A

    def _add_accumulator(self, val):
        """Add accumulator with val.

        Sets Z, S, P, CY, AC as appropriate.
        """
        A = self._registers[Registers.A]
        if (A&0xf) + (val&0xf) > 0xf:
            self._flags[Flags.AUX_CARRY] = 1
        else:
            self._flags[Flags.AUX_CARRY] = 0

        if A + val > 0xff:
            self._flags[Flags.CARRY] = 1
        else:
            self._flags[Flags.CARRY] = 0

        A = (A + val)&0xff
        self._flags.set_zero(A)
        self._flags.calculate_parity(A)
        self._flags.set_sign(A)
        self._registers[Registers.A] = A

    def adc(self, opcode, *args):
        """Add with Carry

        The content of the register (or memory) and the content of the 
        carry bit are added to the accumulator.
        (A) <- (A) + (r) + CY

        instruction format: 10001SSS
        
        Flags: Z, S, P, CY, AC
        """
        logging.info(f'ADC {opcode:02X}')
        CY = self._flags[Flags.CARRY]

        reg = self._registers.get_register_from_opcode(opcode, 0)
        if reg == Registers.M:
            addr = self._registers.get_address_from_pair(Registers.H)
            val = self.read_memory(addr, 1)[0]
        else:
            val = self._registers[reg]
           
        val += CY
        self._add_accumulator(val)

    def aci(self, opcode, *operands):
        """Add immediate with carry.
        (A) <- (A) + CY + operands[0]

        Flags: Z, S, P, CY, AC
        """
        logging.info(f'ACI {operands[0]:02X}')
        val = operands[0] + self._flags[Flags.CARRY]
        self._add_accumulator(val)
    
    def out(self, opcode, port, *args):
        """Puts contents of accumulator onto IO bus at given port.
        """
        logging.info(f'OUT {port:02X}')
        self._io.write(port, self._registers[Registers.A])

    def input(self, opcode, port, *args):
        """Reads a byte from the given port and stores it in the accumulator.

        We can't call this "IN" because that's a keyword.
        """
        logging.info(f'IN {port:02X}')
        self._registers[Registers.A] = self._io.read(port)
    
    def sub(self, opcode, *args):
        """Subtracts contents of register (encoded in opcode) from Accumulator.

        Instruction format:  10010SSS
        Flags: Z, S, P, CY, AC
        """
        logging.info(f'SUB {opcode:02X}')
        reg = Registers.get_register_from_opcode(opcode, 0)
        if reg == Registers.M:
            addr = self._registers.get_address_from_pair(Registers.H)
            val = self.read_memory(addr, 1)[0]
        else:
            val = self._registers[reg]
        self._registers[Registers.A] = self._internal_sub(val)

    def sui(self, opcode, operand, *args):
        """
        """
        logging.info(f'SUI {operand:02X}')
        self._registers[Registers.A] = self._internal_sub(operand)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    machine = Machine8080()
    machine.load(sys.argv[1])
    machine.execute()


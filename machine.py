import sys
import logging
from collections import namedtuple

from cpu import Flags, Registers, RegisterPair

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


class Machine8080:
    def __init__(self):
        self._memory = None
        self._pc = 0
        self._flags = Flags()
        self._registers = Registers()
        self._sp = 0
        self.opcodes = (
            OpCode(int('00', 16), 1, "NOP", "none", self.nop),
            OpCode(int('01', 16), 3, "LXI B", "immediate", self.lxi),
            OpCode(int('02', 16), 1, "STAX B", "none", self.stax),
            OpCode(int('03', 16), 1, "INX B", "none", self.unhandled_instruction),
            OpCode(int('04', 16), 1, "INR B", "none", self.unhandled_instruction),
            OpCode(int('05', 16), 1, "DCR B", "none", self.unhandled_instruction),
            OpCode(int('06', 16), 2, "MVI B", "immediate", self.mvi),
            OpCode(int('07', 16), 1, "RLC", "none", self.unhandled_instruction),
            OpCode(int('08', 16), 1, "UNKNOWN", "none", self.unhandled_instruction),
            OpCode(int('09', 16), 1, "DAD B", "none", self.unhandled_instruction),
            OpCode(int('0a', 16), 1, "LDAX B", "none", self.ldax),
            OpCode(int('0b', 16), 1, "DCX B", "none", self.unhandled_instruction),
            OpCode(int('0c', 16), 1, "INR C", "none", self.unhandled_instruction),
            OpCode(int('0d', 16), 1, "DCR C", "none", self.unhandled_instruction),
            OpCode(int('0e', 16), 2, "MVI C", "immediate", self.mvi),
            OpCode(int('0f', 16), 1, "RRC", "none", self.unhandled_instruction),
            OpCode(int('10', 16), 1, "UNKNOWN", "none", self.unhandled_instruction),
            OpCode(int('11', 16), 3, "LXI D", "immediate", self.lxi),
            OpCode(int('12', 16), 1, "STAX D", "none", self.stax),
            OpCode(int('13', 16), 1, "INX D", "none", self.unhandled_instruction),
            OpCode(int('14', 16), 1, "INR D", "none", self.unhandled_instruction),
            OpCode(int('15', 16), 1, "DCR D", "none", self.unhandled_instruction),
            OpCode(int('16', 16), 2, "MVI D,", "immediate", self.mvi),
            OpCode(int('17', 16), 1, "RAL", "none", self.unhandled_instruction),
            OpCode(int('18', 16), 1, "UNKNOWN", "none", self.unhandled_instruction),
            OpCode(int('19', 16), 1, "DAD D", "none", self.unhandled_instruction),
            OpCode(int('1a', 16), 1, "LDAX D", "none", self.ldax),
            OpCode(int('1b', 16), 1, "DCX D", "none", self.unhandled_instruction),
            OpCode(int('1c', 16), 1, "INR E", "none", self.unhandled_instruction),
            OpCode(int('1d', 16), 1, "DCR E", "none", self.unhandled_instruction),
            OpCode(int('1e', 16), 2, "MVI E,", "immediate", self.mvi),
            OpCode(int('1f', 16), 1, "RAR", "none", self.unhandled_instruction),
            OpCode(int('20', 16), 1, "UNKNOWN", "none", self.unhandled_instruction),
            OpCode(int('21', 16), 3, "LXI H", "immediate", self.lxi),
            OpCode(int('22', 16), 3, "SHLD", "address", self.unhandled_instruction),
            OpCode(int('23', 16), 1, "INX H", "none", self.unhandled_instruction),
            OpCode(int('24', 16), 1, "INR H", "none", self.unhandled_instruction),
            OpCode(int('25', 16), 1, "DCR H", "none", self.unhandled_instruction),
            OpCode(int('26', 16), 2, "MVI H,", "immediate", self.mvi),
            OpCode(int('27', 16), 1, "DAA", "none", self.unhandled_instruction),
            OpCode(int('28', 16), 1, "UNKNOWN", "none", self.unhandled_instruction),
            OpCode(int('29', 16), 1, "DAD H", "none", self.unhandled_instruction),
            OpCode(int('2a', 16), 3, "LHLD", "address", self.lhld),
            OpCode(int('2b', 16), 1, "DCX H", "none", self.unhandled_instruction),
            OpCode(int('2c', 16), 1, "UNKNOWN", "none", self.unhandled_instruction),
            OpCode(int('2d', 16), 1, "UNKNOWN", "none", self.unhandled_instruction),
            OpCode(int('2e', 16), 2, "MVI L,", "immediate", self.mvi),
            OpCode(int('2f', 16), 1, "CMA", "none", self.unhandled_instruction),
            OpCode(int('30', 16), 1, "UNKNOWN", "none", self.unhandled_instruction),
            OpCode(int('31', 16), 3, "LXI SP", "immediate", self.lxi),
            OpCode(int('32', 16), 3, "STA", "address", self.sta),
            OpCode(int('33', 16), 1, "INX SP", "none", self.unhandled_instruction),
            OpCode(int('34', 16), 1, "INR M", "none", self.unhandled_instruction),
            OpCode(int('35', 16), 1, "DCR M", "none", self.unhandled_instruction),
            OpCode(int('36', 16), 2, "MVI M,", "immediate", self.mvi),
            OpCode(int('37', 16), 1, "STC", "none", self.unhandled_instruction),
            OpCode(int('38', 16), 1, "UNKNOWN", "none", self.unhandled_instruction),
            OpCode(int('39', 16), 1, "DAD SP", "none", self.unhandled_instruction),
            OpCode(int('3a', 16), 3, "LDA", "address", self.lda),
            OpCode(int('3b', 16), 1, "DCX SP", "none", self.unhandled_instruction),
            OpCode(int('3c', 16), 1, "INR A", "none", self.unhandled_instruction),
            OpCode(int('3d', 16), 1, "DCR", "none", self.unhandled_instruction),
            OpCode(int('3e', 16), 2, "MVI A,", "immediate", self.mvi),
            OpCode(int('3f', 16), 1, "CMC", "none", self.unhandled_instruction),
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
            OpCode(int('76', 16), 1, "HALT", "none", self.unhandled_instruction),
            OpCode(int('77', 16), 1, "MOV M,A", "none", self.mov),
            OpCode(int('78', 16), 1, "MOV A,B", "none", self.mov),
            OpCode(int('79', 16), 1, "MOV A,C", "none", self.mov),
            OpCode(int('7a', 16), 1, "MOV A,D", "none", self.mov),
            OpCode(int('7b', 16), 1, "MOV A,E", "none", self.mov),
            OpCode(int('7c', 16), 1, "MOV A,H", "none", self.mov),
            OpCode(int('7d', 16), 1, "MOV A,L", "none", self.mov),
            OpCode(int('7e', 16), 1, "MOV A,M", "none", self.mov),
            OpCode(int('7f', 16), 1, "MOV A,A", "none", self.mov),
            OpCode(int('80', 16), 1, "ADD B", "none", self.unhandled_instruction),
            OpCode(int('81', 16), 1, "ADD C", "none", self.unhandled_instruction),
            OpCode(int('82', 16), 1, "ADD D", "none", self.unhandled_instruction),
            OpCode(int('83', 16), 1, "ADD E", "none", self.unhandled_instruction),
            OpCode(int('84', 16), 1, "ADD H", "none", self.unhandled_instruction),
            OpCode(int('85', 16), 1, "ADD L", "none", self.unhandled_instruction),
            OpCode(int('86', 16), 1, "ADD M", "none", self.unhandled_instruction),
            OpCode(int('87', 16), 1, "ADD A", "none", self.unhandled_instruction),
            OpCode(int('88', 16), 1, "ADC B", "none", self.unhandled_instruction),
            OpCode(int('89', 16), 1, "ADC C", "none", self.unhandled_instruction),
            OpCode(int('8a', 16), 1, "ADC D", "none", self.unhandled_instruction),
            OpCode(int('8b', 16), 1, "ADC E", "none", self.unhandled_instruction),
            OpCode(int('8c', 16), 1, "ADC H", "none", self.unhandled_instruction),
            OpCode(int('8d', 16), 1, "ADC L", "none", self.unhandled_instruction),
            OpCode(int('8e', 16), 1, "ADC M", "none", self.unhandled_instruction),
            OpCode(int('8f', 16), 1, "ADC A", "none", self.unhandled_instruction),
            OpCode(int('90', 16), 1, "SUB B", "none", self.unhandled_instruction),
            OpCode(int('91', 16), 1, "SUB C", "none", self.unhandled_instruction),
            OpCode(int('92', 16), 1, "SUB D", "none", self.unhandled_instruction),
            OpCode(int('93', 16), 1, "SUB E", "none", self.unhandled_instruction),
            OpCode(int('94', 16), 1, "SUB H", "none", self.unhandled_instruction),
            OpCode(int('95', 16), 1, "SUB L", "none", self.unhandled_instruction),
            OpCode(int('96', 16), 1, "SUB M", "none", self.unhandled_instruction),
            OpCode(int('97', 16), 1, "SUB A", "none", self.unhandled_instruction),
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
            OpCode(int('b0', 16), 1, "ORA B", "none", self.unhandled_instruction),
            OpCode(int('b1', 16), 1, "ORA C", "none", self.unhandled_instruction),
            OpCode(int('b2', 16), 1, "ORA D", "none", self.unhandled_instruction),
            OpCode(int('b3', 16), 1, "ORA E", "none", self.unhandled_instruction),
            OpCode(int('b4', 16), 1, "ORA H", "none", self.unhandled_instruction),
            OpCode(int('b5', 16), 1, "ORA L", "none", self.unhandled_instruction),
            OpCode(int('b6', 16), 1, "ORA M", "none", self.unhandled_instruction),
            OpCode(int('b7', 16), 1, "ORA A", "none", self.unhandled_instruction),
            OpCode(int('b8', 16), 1, "CMP B", "none", self.unhandled_instruction),
            OpCode(int('b9', 16), 1, "CMP C", "none", self.unhandled_instruction),
            OpCode(int('ba', 16), 1, "CMP D", "none", self.unhandled_instruction),
            OpCode(int('bb', 16), 1, "CMP E", "none", self.unhandled_instruction),
            OpCode(int('bc', 16), 1, "CMP H", "none", self.unhandled_instruction),
            OpCode(int('bd', 16), 1, "CMP L", "none", self.unhandled_instruction),
            OpCode(int('be', 16), 1, "CMP M", "none", self.unhandled_instruction),
            OpCode(int('bf', 16), 1, "CMP A", "none", self.unhandled_instruction),
            OpCode(int('c0', 16), 1, "RNZ", "none", self.unhandled_instruction),
            OpCode(int('c1', 16), 1, "POP B", "none", self.unhandled_instruction),
            OpCode(int('c2', 16), 3, "JNZ", "address", self.conditional_jmp),
            OpCode(int('c3', 16), 3, "JMP", "address", self.jmp),
            OpCode(int('c4', 16), 3, "CNZ", "address", self.unhandled_instruction),
            OpCode(int('c5', 16), 1, "PUSH B", "none", self.unhandled_instruction),
            OpCode(int('c6', 16), 2, "ADI", "immediate", self.unhandled_instruction),
            OpCode(int('c7', 16), 1, "RST", "none", self.unhandled_instruction),
            OpCode(int('c8', 16), 1, "RZ", "none", self.unhandled_instruction),
            OpCode(int('c9', 16), 1, "RET", "none", self.unhandled_instruction),
            OpCode(int('ca', 16), 3, "JZ", "address", self.conditional_jmp),
            OpCode(int('cb', 16), 1, "UNKNOWN", "none", self.unhandled_instruction),
            OpCode(int('cc', 16), 3, "CZ", "address", self.unhandled_instruction),
            OpCode(int('cd', 16), 3, "CALL", "address", self.unhandled_instruction),
            OpCode(int('ce', 16), 2, "ACI", "immediate", self.unhandled_instruction),
            OpCode(int('cf', 16), 1, "RST", "none", self.unhandled_instruction),
            OpCode(int('d0', 16), 1, "RNC", "none", self.unhandled_instruction),
            OpCode(int('d1', 16), 1, "POP D", "none", self.unhandled_instruction),
            OpCode(int('d2', 16), 3, "JNC", "address", self.conditional_jmp),
            OpCode(int('d3', 16), 2, "OUT", "immediate", self.unhandled_instruction),
            OpCode(int('d4', 16), 3, "CNC", "address", self.unhandled_instruction),
            OpCode(int('d5', 16), 1, "PUSH D", "none", self.unhandled_instruction),
            OpCode(int('d6', 16), 2, "SUI", "immediate", self.unhandled_instruction),
            OpCode(int('d7', 16), 1, "RST", "none", self.unhandled_instruction),
            OpCode(int('d8', 16), 1, "RC", "none", self.unhandled_instruction),
            OpCode(int('d9', 16), 1, "UNKONWN", "none", self.unhandled_instruction),
            OpCode(int('da', 16), 3, "JC", "address", self.conditional_jmp),
            OpCode(int('db', 16), 2, "IN", "immediate", self.unhandled_instruction),
            OpCode(int('dc', 16), 3, "CC", "address", self.unhandled_instruction),
            OpCode(int('dd', 16), 1, "UNKNOWN", "none", self.unhandled_instruction),
            OpCode(int('de', 16), 2, "SBI", "immediate", self.unhandled_instruction),
            OpCode(int('df', 16), 1, "RST", "none", self.unhandled_instruction),
            OpCode(int('e0', 16), 1, "RPO", "none", self.unhandled_instruction),
            OpCode(int('e1', 16), 1, "POP H", "none", self.unhandled_instruction),
            OpCode(int('e2', 16), 3, "JPO", "address", self.conditional_jmp),
            OpCode(int('e3', 16), 1, "XTHL", "none", self.unhandled_instruction),
            OpCode(int('e4', 16), 3, "CPO", "address", self.unhandled_instruction),
            OpCode(int('e5', 16), 1, "PUSH H", "none", self.unhandled_instruction),
            OpCode(int('e6', 16), 2, "ANI", "immediate", self.unhandled_instruction),
            OpCode(int('e7', 16), 1, "RST", "none", self.unhandled_instruction),
            OpCode(int('e8', 16), 1, "RPI", "none", self.unhandled_instruction),
            OpCode(int('e9', 16), 1, "PCHL", "none", self.pchl),
            OpCode(int('ea', 16), 3, "JPE", "address", self.conditional_jmp),
            OpCode(int('eb', 16), 1, "XCHG", "none", self.unhandled_instruction),
            OpCode(int('ec', 16), 3, "CPE", "address", self.unhandled_instruction),
            OpCode(int('ed', 16), 1, "UNKNOWN", "none", self.unhandled_instruction),
            OpCode(int('ee', 16), 2, "XRI", "immediate", self.unhandled_instruction),
            OpCode(int('ef', 16), 1, "RST", "none", self.unhandled_instruction),
            OpCode(int('f0', 16), 1, "RP", "none", self.unhandled_instruction),
            OpCode(int('f1', 16), 1, "POP PSW", "none", self.unhandled_instruction),
            OpCode(int('f2', 16), 3, "JP", "address", self.conditional_jmp),
            OpCode(int('f3', 16), 1, "DI", "none", self.unhandled_instruction),
            OpCode(int('f4', 16), 3, "CP", "address", self.unhandled_instruction),
            OpCode(int('f5', 16), 1, "PUSH PSW", "none", self.unhandled_instruction),
            OpCode(int('f6', 16), 2, "ORI", "immediate", self.unhandled_instruction),
            OpCode(int('f7', 16), 1, "RST", "none", self.unhandled_instruction),
            OpCode(int('f8', 16), 1, "RM", "none", self.unhandled_instruction),
            OpCode(int('f9', 16), 1, "SPHL", "none", self.unhandled_instruction),
            OpCode(int('fa', 16), 3, "JM", "address", self.conditional_jmp),
            OpCode(int('fb', 16), 1, "EI", "none", self.unhandled_instruction),
            OpCode(int('fc', 16), 3, "CM", "address", self.unhandled_instruction),
            OpCode(int('fd', 16), 1, "UNKNOWN", "none", self.unhandled_instruction),
            OpCode(int('fe', 16), 2, "CPI", "immediate", self.unhandled_instruction),
            OpCode(int('ff', 16), 1, "RST", "none", self.unhandled_instruction),
        )

    def load(self, romfile):
        """Loads the given ROM file

        :param romfile: full path to the ROM to load

        :raises RomLoadException: if the file cannot be read
        """
        try:
            with open(romfile, "rb") as fp:
                self._memory = bytearray(fp.read())
                self._memory = self._memory \
                               + bytearray([0 for x in range(0x10000 - len(self._memory))])
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
        logging.warning("Unhandled instruction: {0}".format(self.opcodes[opcode]))

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

    def ana(self, opcode, *args):
        """
        Logical AND the register (or byte at memory) with the accumulator.
        Carry bit is reset to 0

        Condition bits: Carry, zero, sign, parity
        :param opcode:
        :param args:
        :return:
        """
        reg = self._registers.get_register_from_opcode(opcode, 0)
        if reg == Registers.M:
            val, *_ = self.read_memory(self._registers.get_address_from_pair(Registers.H), 1)
        else:
            val = self._registers[reg]

        res = val & self._registers[Registers.A]
        self._registers[Registers.A] = res

        self._flags.clear(Flags.CARRY)
        self._flags.calculate_parity(res)
        self._flags.set_zero(res)
        self._flags.set_sign(res)

    def xra(self, opcode, *args):
        """
        Exclusive-OR the register (or memory) specified in the opcode

        Carry bit is reset.
        Zero, sign, parity, auxiliary carry?

        The reference manual states that the carry bit is reset but doesn't say anything
        about the aux. carry bit.  The XRI instruction (xor immediate) does NOT affect
        the aux carry.  So I wonder if it was a mistake by the manual writers to include
        it here.  I've seen other mistakes in the document.

        (Modern Intel references state that the aux carry is undefined for this instruction)
        :param opcode:
        :param args:
        :return:
        """
        reg = self._registers.get_register_from_opcode(opcode, 0)
        if reg == Registers.M:
            val, *_ = self.read_memory(self._registers.get_address_from_pair(Registers.H), 1)
        else:
            val = self._registers[reg]

        res = val ^ self._registers[Registers.A]
        logging.info(f'XRA Register {reg} value {val:02X} result = {res:02X}')
        self._registers[Registers.A] = res
        self._flags.clear(Flags.CARRY)
        self._flags.clear(Flags.AUX_CARRY)
        self._flags.calculate_parity(res)
        self._flags.set_zero(res)
        self._flags.set_sign(res)

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
        logging.info(f'register pair: {rp:02x}')
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
        The first byte at the address given by the operands is stored in L.  The next address
        is stored in H.

        [L] = (op[1])(op[0])
        [H] = (op[1])(op[0]) + 1
        :param opcode:
        :param operands:
        :return:
        """
        address = (operands[1] << 8) | operands[0]
        self._registers[Registers.L], self._registers[Registers.H] = self.read_memory(address, 2)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    machine = Machine8080()
    machine.load(sys.argv[1])
    machine.execute()
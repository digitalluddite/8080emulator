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


class RomException (Exception):
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
        self.opcodes = (
            OpCode(int('00', 16), 1, "NOP", "none", self.nop),
            OpCode(int('01', 16), 3, "LXI B", "immediate", self.unhandled_instruction),
            OpCode(int('02', 16), 1, "STAX B", "none", self.stax),
            OpCode(opcode=int('03', 16), length=1, mnemonic="INX B", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('04', 16), length=1, mnemonic="INR B", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('05', 16), length=1, mnemonic="DCR B", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('06', 16), length=2, mnemonic="MVI B", optype="immediate", handler=self.unhandled_instruction),
            OpCode(opcode=int('07', 16), length=1, mnemonic="RLC", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('08', 16), length=1, mnemonic="UNKNOWN", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('09', 16), length=1, mnemonic="DAD B", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('0a', 16), length=1, mnemonic="LDAX B", optype="none", handler=self.ldax),
            OpCode(opcode=int('0b', 16), length=1, mnemonic="DCX B", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('0c', 16), length=1, mnemonic="INR C", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('0d', 16), length=1, mnemonic="DCR C", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('0e', 16), length=2, mnemonic="MVI C", optype="immediate", handler=self.unhandled_instruction),
            OpCode(opcode=int('0f', 16), length=1, mnemonic="RRC", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('10', 16), length=1, mnemonic="UNKNOWN", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('11', 16), length=3, mnemonic="LXI D", optype="immediate", handler=self.unhandled_instruction),
            OpCode(opcode=int('12', 16), length=1, mnemonic="STAX D", optype="none", handler=self.stax),
            OpCode(opcode=int('13', 16), length=1, mnemonic="INX D", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('14', 16), length=1, mnemonic="INR D", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('15', 16), length=1, mnemonic="DCR D", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('16', 16), length=2, mnemonic="MVI D,", optype="immediate", handler=self.unhandled_instruction),
            OpCode(opcode=int('17', 16), length=1, mnemonic="RAL", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('18', 16), length=1, mnemonic="UNKNOWN", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('19', 16), length=1, mnemonic="DAD D", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('1a', 16), length=1, mnemonic="LDAX D", optype="none", handler=self.ldax),
            OpCode(opcode=int('1b', 16), length=1, mnemonic="DCX D", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('1c', 16), length=1, mnemonic="INR E", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('1d', 16), length=1, mnemonic="DCR E", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('1e', 16), length=2, mnemonic="MVI E,", optype="immediate", handler=self.unhandled_instruction),
            OpCode(opcode=int('1f', 16), length=1, mnemonic="RAR", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('20', 16), length=1, mnemonic="UNKNOWN", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('21', 16), length=3, mnemonic="LXI H", optype="immediate", handler=self.unhandled_instruction),
            OpCode(opcode=int('22', 16), length=3, mnemonic="SHLD", optype="address", handler=self.unhandled_instruction),
            OpCode(opcode=int('23', 16), length=1, mnemonic="INX H", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('24', 16), length=1, mnemonic="INR H", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('25', 16), length=1, mnemonic="DCR H", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('26', 16), length=2, mnemonic="MVI H,", optype="immediate", handler=self.unhandled_instruction),
            OpCode(opcode=int('27', 16), length=1, mnemonic="DAA", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('28', 16), length=1, mnemonic="UNKNOWN", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('29', 16), length=1, mnemonic="DAD H", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('2a', 16), length=3, mnemonic="LHLD", optype="address", handler=self.unhandled_instruction),
            OpCode(opcode=int('2b', 16), length=1, mnemonic="DCX H", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('2c', 16), length=1, mnemonic="UNKNOWN", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('2d', 16), length=1, mnemonic="UNKNOWN", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('2e', 16), length=2, mnemonic="MVI L,", optype="immediate", handler=self.unhandled_instruction),
            OpCode(opcode=int('2f', 16), length=1, mnemonic="CMA", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('30', 16), length=1, mnemonic="UNKNOWN", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('31', 16), length=3, mnemonic="LXI SP", optype="immediate", handler=self.unhandled_instruction),
            OpCode(opcode=int('32', 16), length=3, mnemonic="STA", optype="address", handler=self.unhandled_instruction),
            OpCode(opcode=int('33', 16), length=1, mnemonic="INX SP", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('34', 16), length=1, mnemonic="INR M", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('35', 16), length=1, mnemonic="DCR M", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('36', 16), length=2, mnemonic="MVI M,", optype="immediate", handler=self.unhandled_instruction),
            OpCode(opcode=int('37', 16), length=1, mnemonic="STC", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('38', 16), length=1, mnemonic="UNKNOWN", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('39', 16), length=1, mnemonic="DAD SP", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('3a', 16), length=3, mnemonic="LDA", optype="address", handler=self.unhandled_instruction),
            OpCode(opcode=int('3b', 16), length=1, mnemonic="DCX SP", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('3c', 16), length=1, mnemonic="INR A", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('3d', 16), length=1, mnemonic="DCR", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('3e', 16), length=2, mnemonic="MVI A,", optype="immediate", handler=self.unhandled_instruction),
            OpCode(opcode=int('3f', 16), length=1, mnemonic="CMC", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('40', 16), length=1, mnemonic="MOV B,B", optype="none", handler=self.mov),
            OpCode(opcode=int('41', 16), length=1, mnemonic="MOV B,C", optype="none", handler=self.mov),
            OpCode(opcode=int('42', 16), length=1, mnemonic="MOV B,D", optype="none", handler=self.mov),
            OpCode(opcode=int('43', 16), length=1, mnemonic="MOV B,E", optype="none", handler=self.mov),
            OpCode(opcode=int('44', 16), length=1, mnemonic="MOV B,H", optype="none", handler=self.mov),
            OpCode(opcode=int('45', 16), length=1, mnemonic="MOV B,L", optype="none", handler=self.mov),
            OpCode(opcode=int('46', 16), length=1, mnemonic="MOV B,M", optype="none", handler=self.mov),
            OpCode(opcode=int('47', 16), length=1, mnemonic="MOV B,A", optype="none", handler=self.mov),
            OpCode(opcode=int('48', 16), length=1, mnemonic="MOV C,B", optype="none", handler=self.mov),
            OpCode(opcode=int('49', 16), length=1, mnemonic="MOV C,C", optype="none", handler=self.mov),
            OpCode(opcode=int('4a', 16), length=1, mnemonic="MOV C,D", optype="none", handler=self.mov),
            OpCode(opcode=int('4b', 16), length=1, mnemonic="MOV C,E", optype="none", handler=self.mov),
            OpCode(opcode=int('4c', 16), length=1, mnemonic="MOV C,H", optype="none", handler=self.mov),
            OpCode(opcode=int('4d', 16), length=1, mnemonic="MOV C,L", optype="none", handler=self.mov),
            OpCode(opcode=int('4e', 16), length=1, mnemonic="MOV C,M", optype="none", handler=self.mov),
            OpCode(opcode=int('4f', 16), length=1, mnemonic="MOV C,A", optype="none", handler=self.mov),
            OpCode(opcode=int('50', 16), length=1, mnemonic="MOV D,B", optype="none", handler=self.mov),
            OpCode(opcode=int('51', 16), length=1, mnemonic="MOV D,C", optype="none", handler=self.mov),
            OpCode(opcode=int('52', 16), length=1, mnemonic="MOV D,D", optype="none", handler=self.mov),
            OpCode(opcode=int('53', 16), length=1, mnemonic="MOV D,E", optype="none", handler=self.mov),
            OpCode(opcode=int('54', 16), length=1, mnemonic="MOV D,H", optype="none", handler=self.mov),
            OpCode(opcode=int('55', 16), length=1, mnemonic="MOV D,L", optype="none", handler=self.mov),
            OpCode(opcode=int('56', 16), length=1, mnemonic="MOV D,M", optype="none", handler=self.mov),
            OpCode(opcode=int('57', 16), length=1, mnemonic="MOV D,A", optype="none", handler=self.mov),
            OpCode(opcode=int('58', 16), length=1, mnemonic="MOV E,B", optype="none", handler=self.mov),
            OpCode(opcode=int('59', 16), length=1, mnemonic="MOV E,C", optype="none", handler=self.mov),
            OpCode(opcode=int('5a', 16), length=1, mnemonic="MOV E,D", optype="none", handler=self.mov),
            OpCode(opcode=int('5b', 16), length=1, mnemonic="MOV E,E", optype="none", handler=self.mov),
            OpCode(opcode=int('5c', 16), length=1, mnemonic="MOV E,H", optype="none", handler=self.mov),
            OpCode(opcode=int('5d', 16), length=1, mnemonic="MOV E,L", optype="none", handler=self.mov),
            OpCode(opcode=int('5e', 16), length=1, mnemonic="MOV E,M", optype="none", handler=self.mov),
            OpCode(opcode=int('5f', 16), length=1, mnemonic="MOV E,A", optype="none", handler=self.mov),
            OpCode(opcode=int('60', 16), length=1, mnemonic="MOV H,B", optype="none", handler=self.mov),
            OpCode(opcode=int('61', 16), length=1, mnemonic="MOV H,C", optype="none", handler=self.mov),
            OpCode(opcode=int('62', 16), length=1, mnemonic="MOV H,D", optype="none", handler=self.mov),
            OpCode(opcode=int('63', 16), length=1, mnemonic="MOV H,E", optype="none", handler=self.mov),
            OpCode(opcode=int('64', 16), length=1, mnemonic="MOV H,H", optype="none", handler=self.mov),
            OpCode(opcode=int('65', 16), length=1, mnemonic="MOV H,L", optype="none", handler=self.mov),
            OpCode(opcode=int('66', 16), length=1, mnemonic="MOV H,M", optype="none", handler=self.mov),
            OpCode(opcode=int('67', 16), length=1, mnemonic="MOV H,A", optype="none", handler=self.mov),
            OpCode(opcode=int('68', 16), length=1, mnemonic="MOV L,B", optype="none", handler=self.mov),
            OpCode(opcode=int('69', 16), length=1, mnemonic="MOV L,C", optype="none", handler=self.mov),
            OpCode(opcode=int('6a', 16), length=1, mnemonic="MOV L,D", optype="none", handler=self.mov),
            OpCode(opcode=int('6b', 16), length=1, mnemonic="MOV L,E", optype="none", handler=self.mov),
            OpCode(opcode=int('6c', 16), length=1, mnemonic="MOV L,H", optype="none", handler=self.mov),
            OpCode(opcode=int('6d', 16), length=1, mnemonic="MOV L,L", optype="none", handler=self.mov),
            OpCode(opcode=int('6e', 16), length=1, mnemonic="MOV L,M", optype="none", handler=self.mov),
            OpCode(opcode=int('6f', 16), length=1, mnemonic="MOV L,A", optype="none", handler=self.mov),
            OpCode(opcode=int('70', 16), length=1, mnemonic="MOV M,B", optype="none", handler=self.mov),
            OpCode(opcode=int('71', 16), length=1, mnemonic="MOV M,C", optype="none", handler=self.mov),
            OpCode(opcode=int('72', 16), length=1, mnemonic="MOV M,D", optype="none", handler=self.mov),
            OpCode(opcode=int('73', 16), length=1, mnemonic="MOV M,E", optype="none", handler=self.mov),
            OpCode(opcode=int('74', 16), length=1, mnemonic="MOV M,H", optype="none", handler=self.mov),
            OpCode(opcode=int('75', 16), length=1, mnemonic="MOV M,L", optype="none", handler=self.mov),
            OpCode(opcode=int('76', 16), length=1, mnemonic="HALT", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('77', 16), length=1, mnemonic="MOV M,A", optype="none", handler=self.mov),
            OpCode(opcode=int('78', 16), length=1, mnemonic="MOV A,B", optype="none", handler=self.mov),
            OpCode(opcode=int('79', 16), length=1, mnemonic="MOV A,C", optype="none", handler=self.mov),
            OpCode(opcode=int('7a', 16), length=1, mnemonic="MOV A,D", optype="none", handler=self.mov),
            OpCode(opcode=int('7b', 16), length=1, mnemonic="MOV A,E", optype="none", handler=self.mov),
            OpCode(opcode=int('7c', 16), length=1, mnemonic="MOV A,H", optype="none", handler=self.mov),
            OpCode(opcode=int('7d', 16), length=1, mnemonic="MOV A,L", optype="none", handler=self.mov),
            OpCode(opcode=int('7e', 16), length=1, mnemonic="MOV A,M", optype="none", handler=self.mov),
            OpCode(opcode=int('7f', 16), length=1, mnemonic="MOV A,A", optype="none", handler=self.mov),
            OpCode(opcode=int('80', 16), length=1, mnemonic="ADD B", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('81', 16), length=1, mnemonic="ADD C", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('82', 16), length=1, mnemonic="ADD D", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('83', 16), length=1, mnemonic="ADD E", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('84', 16), length=1, mnemonic="ADD H", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('85', 16), length=1, mnemonic="ADD L", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('86', 16), length=1, mnemonic="ADD M", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('87', 16), length=1, mnemonic="ADD A", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('88', 16), length=1, mnemonic="ADC B", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('89', 16), length=1, mnemonic="ADC C", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('8a', 16), length=1, mnemonic="ADC D", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('8b', 16), length=1, mnemonic="ADC E", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('8c', 16), length=1, mnemonic="ADC H", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('8d', 16), length=1, mnemonic="ADC L", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('8e', 16), length=1, mnemonic="ADC M", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('8f', 16), length=1, mnemonic="ADC A", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('90', 16), length=1, mnemonic="SUB B", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('91', 16), length=1, mnemonic="SUB C", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('92', 16), length=1, mnemonic="SUB D", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('93', 16), length=1, mnemonic="SUB E", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('94', 16), length=1, mnemonic="SUB H", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('95', 16), length=1, mnemonic="SUB L", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('96', 16), length=1, mnemonic="SUB M", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('97', 16), length=1, mnemonic="SUB A", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('98', 16), length=1, mnemonic="SBB B", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('99', 16), length=1, mnemonic="SBB C", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('9a', 16), length=1, mnemonic="SBB D", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('9b', 16), length=1, mnemonic="SBB E", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('9c', 16), length=1, mnemonic="SBB H", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('9d', 16), length=1, mnemonic="SBB L", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('9e', 16), length=1, mnemonic="SBB M", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('9f', 16), length=1, mnemonic="SBB A", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('a0', 16), length=1, mnemonic="ANA B", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('a1', 16), length=1, mnemonic="ANA C", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('a2', 16), length=1, mnemonic="ANA D", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('a3', 16), length=1, mnemonic="ANA E", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('a4', 16), length=1, mnemonic="ANA H", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('a5', 16), length=1, mnemonic="ANA L", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('a6', 16), length=1, mnemonic="ANA M", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('a7', 16), length=1, mnemonic="ANA A", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('a8', 16), length=1, mnemonic="XRA B", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('a9', 16), length=1, mnemonic="XRA C", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('aa', 16), length=1, mnemonic="XRA D", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('ab', 16), length=1, mnemonic="XRA E", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('ac', 16), length=1, mnemonic="XRA H", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('ad', 16), length=1, mnemonic="XRA L", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('ae', 16), length=1, mnemonic="XRA M", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('af', 16), length=1, mnemonic="XRA A", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('b0', 16), length=1, mnemonic="ORA B", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('b1', 16), length=1, mnemonic="ORA C", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('b2', 16), length=1, mnemonic="ORA D", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('b3', 16), length=1, mnemonic="ORA E", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('b4', 16), length=1, mnemonic="ORA H", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('b5', 16), length=1, mnemonic="ORA L", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('b6', 16), length=1, mnemonic="ORA M", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('b7', 16), length=1, mnemonic="ORA A", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('b8', 16), length=1, mnemonic="CMP B", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('b9', 16), length=1, mnemonic="CMP C", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('ba', 16), length=1, mnemonic="CMP D", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('bb', 16), length=1, mnemonic="CMP E", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('bc', 16), length=1, mnemonic="CMP H", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('bd', 16), length=1, mnemonic="CMP L", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('be', 16), length=1, mnemonic="CMP M", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('bf', 16), length=1, mnemonic="CMP A", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('c0', 16), length=1, mnemonic="RNZ", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('c1', 16), length=1, mnemonic="POP B", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('c2', 16), length=3, mnemonic="JNZ", optype="address", handler=self.unhandled_instruction),
            OpCode(opcode=int('c3', 16), length=3, mnemonic="JMP", optype="address", handler=self.unhandled_instruction),
            OpCode(opcode=int('c4', 16), length=3, mnemonic="CNZ", optype="address", handler=self.unhandled_instruction),
            OpCode(opcode=int('c5', 16), length=1, mnemonic="PUSH B", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('c6', 16), length=2, mnemonic="ADI", optype="immediate", handler=self.unhandled_instruction),
            OpCode(opcode=int('c7', 16), length=1, mnemonic="RST", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('c8', 16), length=1, mnemonic="RZ", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('c9', 16), length=1, mnemonic="RET", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('ca', 16), length=3, mnemonic="JZ", optype="address", handler=self.unhandled_instruction),
            OpCode(opcode=int('cb', 16), length=1, mnemonic="UNKNOWN", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('cc', 16), length=3, mnemonic="CZ", optype="address", handler=self.unhandled_instruction),
            OpCode(opcode=int('cd', 16), length=3, mnemonic="CALL", optype="address", handler=self.unhandled_instruction),
            OpCode(opcode=int('ce', 16), length=2, mnemonic="ACI", optype="immediate", handler=self.unhandled_instruction),
            OpCode(opcode=int('cf', 16), length=1, mnemonic="RST", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('d0', 16), length=1, mnemonic="RNC", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('d1', 16), length=1, mnemonic="POP D", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('d2', 16), length=3, mnemonic="JNC", optype="address", handler=self.unhandled_instruction),
            OpCode(opcode=int('d3', 16), length=2, mnemonic="OUT", optype="immediate", handler=self.unhandled_instruction),
            OpCode(opcode=int('d4', 16), length=3, mnemonic="CNC", optype="address", handler=self.unhandled_instruction),
            OpCode(opcode=int('d5', 16), length=1, mnemonic="PUSH D", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('d6', 16), length=2, mnemonic="SUI", optype="immediate", handler=self.unhandled_instruction),
            OpCode(opcode=int('d7', 16), length=1, mnemonic="RST", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('d8', 16), length=1, mnemonic="RC", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('d9', 16), length=1, mnemonic="UNKONWN", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('da', 16), length=3, mnemonic="JC", optype="address", handler=self.unhandled_instruction),
            OpCode(opcode=int('db', 16), length=2, mnemonic="IN", optype="immediate", handler=self.unhandled_instruction),
            OpCode(opcode=int('dc', 16), length=3, mnemonic="CC", optype="address", handler=self.unhandled_instruction),
            OpCode(opcode=int('dd', 16), length=1, mnemonic="UNKNOWN", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('de', 16), length=2, mnemonic="SBI", optype="immediate", handler=self.unhandled_instruction),
            OpCode(opcode=int('df', 16), length=1, mnemonic="RST", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('e0', 16), length=1, mnemonic="RPO", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('e1', 16), length=1, mnemonic="POP H", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('e2', 16), length=3, mnemonic="JPO", optype="address", handler=self.unhandled_instruction),
            OpCode(opcode=int('e3', 16), length=1, mnemonic="XTHL", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('e4', 16), length=3, mnemonic="CPO", optype="address", handler=self.unhandled_instruction),
            OpCode(opcode=int('e5', 16), length=1, mnemonic="PUSH H", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('e6', 16), length=2, mnemonic="ANI", optype="immediate", handler=self.unhandled_instruction),
            OpCode(opcode=int('e7', 16), length=1, mnemonic="RST", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('e8', 16), length=1, mnemonic="RPI", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('e9', 16), length=1, mnemonic="PCHL", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('ea', 16), length=3, mnemonic="JPE", optype="address", handler=self.unhandled_instruction),
            OpCode(opcode=int('eb', 16), length=1, mnemonic="XCHG", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('ec', 16), length=3, mnemonic="CPE", optype="address", handler=self.unhandled_instruction),
            OpCode(opcode=int('ed', 16), length=1, mnemonic="UNKNOWN", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('ee', 16), length=2, mnemonic="XRI", optype="immediate", handler=self.unhandled_instruction),
            OpCode(opcode=int('ef', 16), length=1, mnemonic="RST", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('f0', 16), length=1, mnemonic="RP", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('f1', 16), length=1, mnemonic="POP PSW", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('f2', 16), length=3, mnemonic="JP", optype="address", handler=self.unhandled_instruction),
            OpCode(opcode=int('f3', 16), length=1, mnemonic="DI", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('f4', 16), length=3, mnemonic="CP", optype="address", handler=self.unhandled_instruction),
            OpCode(opcode=int('f5', 16), length=1, mnemonic="PUSH PSW", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('f6', 16), length=2, mnemonic="ORI", optype="immediate", handler=self.unhandled_instruction),
            OpCode(opcode=int('f7', 16), length=1, mnemonic="RST", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('f8', 16), length=1, mnemonic="RM", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('f9', 16), length=1, mnemonic="SPHL", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('fa', 16), length=3, mnemonic="JM", optype="address", handler=self.unhandled_instruction),
            OpCode(opcode=int('fb', 16), length=1, mnemonic="EI", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('fc', 16), length=3, mnemonic="CM", optype="address", handler=self.unhandled_instruction),
            OpCode(opcode=int('fd', 16), length=1, mnemonic="UNKNOWN", optype="none", handler=self.unhandled_instruction),
            OpCode(opcode=int('fe', 16), length=2, mnemonic="CPI", optype="immediate", handler=self.unhandled_instruction),
            OpCode(opcode=int('ff', 16), length=1, mnemonic="RST", optype="none", handler=self.unhandled_instruction),
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
                logging.error("Type of memory: {0}".format(type(self._memory)))
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
        b = [ "{:02X}".format(opcode.opcode) ]
        b.extend( [ "{:02X}".format(o) for o in operands ])
        for x in range(3 - len(b)):
            b.append( "  ")
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
        return [b for b in self._memory[address:address+size]]

    def write_memory(self, address, data):
        """
        Writes the given data one byte to the given address
        :param address:   Memory address
        :param data: Data to write
        :param size:  1 or 2 bytes
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

    def set_carry(self, *args):
        self._flags.set(Flags.CARRY)

    def unhandled_instruction(self, opcode, *args):
        logging.warning("Unhandled instruction: {0}".format(self.opcodes[opcode]))

    def stax(self, opcode, *args):
        """
        Contents of accumulator are stored in the address
        stored in pairs B, C (opcode 0x02) or D,E (opcode 0x12)

        :param args:
        :return:
        """
        assert((opcode == 0x02) or (opcode == 0x12))
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
        assert(opcode in (0x0a, 0x1a))
        pair = Registers.B if opcode == 0x0a else Registers.D
        address = self._registers.get_address_from_pair(pair)
        self._registers[Registers.A], *_ = self.read_memory(address, 1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    machine = Machine8080()
    machine.load(sys.argv[1])
    machine.execute()

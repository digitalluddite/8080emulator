
from collections import namedtuple

OpCode = namedtuple('OpCode', ['opcode', "length", "mnemonic", "optype"])


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


class Machine8080:
    def __init__(self):
        self.opcodes = (
            OpCode(opcode=int('00', 16), length=1, mnemonic="NOP", optype="none"),
            OpCode(opcode=int('01', 16), length=3, mnemonic="LXI B", optype="immediate"),
            OpCode(opcode=int('02', 16), length=1, mnemonic="NOP", optype="none"),
            OpCode(opcode=int('03', 16), length=1, mnemonic="INX B", optype="none"),
            OpCode(opcode=int('04', 16), length=1, mnemonic="INR B", optype="none"),
            OpCode(opcode=int('05', 16), length=1, mnemonic="DCR B", optype="none"),
            OpCode(opcode=int('06', 16), length=2, mnemonic="MVI B", optype="immediate"),
            OpCode(opcode=int('07', 16), length=1, mnemonic="RLC", optype="none"),
            OpCode(opcode=int('08', 16), length=1, mnemonic="UNKNOWN", optype="none"),
            OpCode(opcode=int('09', 16), length=1, mnemonic="DAD B", optype="none"),
            OpCode(opcode=int('0a', 16), length=1, mnemonic="LDAX B", optype="none"),
            OpCode(opcode=int('0b', 16), length=1, mnemonic="DCX B", optype="none"),
            OpCode(opcode=int('0c', 16), length=1, mnemonic="INR C", optype="none"),
            OpCode(opcode=int('0d', 16), length=1, mnemonic="DCR C", optype="none"),
            OpCode(opcode=int('0e', 16), length=2, mnemonic="MVI C", optype="immediate"),
            OpCode(opcode=int('0f', 16), length=1, mnemonic="RRC", optype="none"),
            OpCode(opcode=int('10', 16), length=1, mnemonic="UNKNOWN", optype="none"),
            OpCode(opcode=int('11', 16), length=3, mnemonic="LXI D", optype="immediate"),
            OpCode(opcode=int('12', 16), length=1, mnemonic="STAX D", optype="none"),
            OpCode(opcode=int('13', 16), length=1, mnemonic="INX D", optype="none"),
            OpCode(opcode=int('14', 16), length=1, mnemonic="INR D", optype="none"),
            OpCode(opcode=int('15', 16), length=1, mnemonic="DCR D", optype="none"),
            OpCode(opcode=int('16', 16), length=2, mnemonic="MVI D,", optype="immediate"),
            OpCode(opcode=int('17', 16), length=1, mnemonic="RAL", optype="none"),
            OpCode(opcode=int('18', 16), length=1, mnemonic="UNKNOWN", optype="none"),
            OpCode(opcode=int('19', 16), length=1, mnemonic="DAD D", optype="none"),
            OpCode(opcode=int('1a', 16), length=1, mnemonic="LDAX D", optype="none"),
            OpCode(opcode=int('1b', 16), length=1, mnemonic="DCX D", optype="none"),
            OpCode(opcode=int('1c', 16), length=1, mnemonic="INR E", optype="none"),
            OpCode(opcode=int('1d', 16), length=1, mnemonic="DCR E", optype="none"),
            OpCode(opcode=int('1e', 16), length=2, mnemonic="MVI E,", optype="immediate"),
            OpCode(opcode=int('1f', 16), length=1, mnemonic="RAR", optype="none"),
            OpCode(opcode=int('20', 16), length=1, mnemonic="UNKNOWN", optype="none"),
            OpCode(opcode=int('21', 16), length=3, mnemonic="LXI H", optype="immediate"),
            OpCode(opcode=int('22', 16), length=3, mnemonic="SHLD", optype="address"),
            OpCode(opcode=int('23', 16), length=1, mnemonic="INX H", optype="none"),
            OpCode(opcode=int('24', 16), length=1, mnemonic="INR H", optype="none"),
            OpCode(opcode=int('25', 16), length=1, mnemonic="DCR H", optype="none"),
            OpCode(opcode=int('26', 16), length=2, mnemonic="MVI H,", optype="immediate"),
            OpCode(opcode=int('27', 16), length=1, mnemonic="DAA", optype="none"),
            OpCode(opcode=int('28', 16), length=1, mnemonic="UNKNOWN", optype="none"),
            OpCode(opcode=int('29', 16), length=1, mnemonic="DAD H", optype="none"),
            OpCode(opcode=int('2a', 16), length=3, mnemonic="LHLD", optype="address"),
            OpCode(opcode=int('2b', 16), length=1, mnemonic="DCX H", optype="none"),
            OpCode(opcode=int('2c', 16), length=1, mnemonic="UNKNOWN", optype="none"),
            OpCode(opcode=int('2d', 16), length=1, mnemonic="UNKNOWN", optype="none"),
            OpCode(opcode=int('2e', 16), length=2, mnemonic="MVI L,", optype="immediate"),
            OpCode(opcode=int('2f', 16), length=1, mnemonic="CMA", optype="none"),
            OpCode(opcode=int('30', 16), length=1, mnemonic="UNKNOWN", optype="none"),
            OpCode(opcode=int('31', 16), length=3, mnemonic="LXI SP", optype="immediate"),
            OpCode(opcode=int('32', 16), length=3, mnemonic="STA", optype="address"),
            OpCode(opcode=int('33', 16), length=1, mnemonic="INX SP", optype="none"),
            OpCode(opcode=int('34', 16), length=1, mnemonic="INR M", optype="none"),
            OpCode(opcode=int('35', 16), length=1, mnemonic="DCR M", optype="none"),
            OpCode(opcode=int('36', 16), length=2, mnemonic="MVI M,", optype="immediate"),
            OpCode(opcode=int('37', 16), length=1, mnemonic="STC", optype="none"),
            OpCode(opcode=int('38', 16), length=1, mnemonic="UNKNOWN", optype="none"),
            OpCode(opcode=int('39', 16), length=1, mnemonic="DAD SP", optype="none"),
            OpCode(opcode=int('3a', 16), length=3, mnemonic="LDA", optype="address"),
            OpCode(opcode=int('3b', 16), length=1, mnemonic="DCX SP", optype="none"),
            OpCode(opcode=int('3c', 16), length=1, mnemonic="INR A", optype="none"),
            OpCode(opcode=int('3d', 16), length=1, mnemonic="DCR", optype="none"),
            OpCode(opcode=int('3e', 16), length=2, mnemonic="MVI A,", optype="immediate"),
            OpCode(opcode=int('3f', 16), length=1, mnemonic="CMC", optype="none"),
            OpCode(opcode=int('40', 16), length=1, mnemonic="MOV B,B", optype="none"),
            OpCode(opcode=int('41', 16), length=1, mnemonic="MOV B,C", optype="none"),
            OpCode(opcode=int('42', 16), length=1, mnemonic="MOV B,D", optype="none"),
            OpCode(opcode=int('43', 16), length=1, mnemonic="MOV B,E", optype="none"),
            OpCode(opcode=int('44', 16), length=1, mnemonic="MOV B,H", optype="none"),
            OpCode(opcode=int('45', 16), length=1, mnemonic="MOV B,L", optype="none"),
            OpCode(opcode=int('46', 16), length=1, mnemonic="MOV B,M", optype="none"),
            OpCode(opcode=int('47', 16), length=1, mnemonic="MOV B,A", optype="none"),
            OpCode(opcode=int('48', 16), length=1, mnemonic="MOV C,B", optype="none"),
            OpCode(opcode=int('49', 16), length=1, mnemonic="MOV C,C", optype="none"),
            OpCode(opcode=int('4a', 16), length=1, mnemonic="MOV C,D", optype="none"),
            OpCode(opcode=int('4b', 16), length=1, mnemonic="MOV C,E", optype="none"),
            OpCode(opcode=int('4c', 16), length=1, mnemonic="MOV C,H", optype="none"),
            OpCode(opcode=int('4d', 16), length=1, mnemonic="MOV C,L", optype="none"),
            OpCode(opcode=int('4e', 16), length=1, mnemonic="MOV C,M", optype="none"),
            OpCode(opcode=int('4f', 16), length=1, mnemonic="MOV C,A", optype="none"),
            OpCode(opcode=int('50', 16), length=1, mnemonic="MOV D,B", optype="none"),
            OpCode(opcode=int('51', 16), length=1, mnemonic="MOV D,C", optype="none"),
            OpCode(opcode=int('52', 16), length=1, mnemonic="MOV D,D", optype="none"),
            OpCode(opcode=int('53', 16), length=1, mnemonic="MOV D,E", optype="none"),
            OpCode(opcode=int('54', 16), length=1, mnemonic="MOV D,H", optype="none"),
            OpCode(opcode=int('55', 16), length=1, mnemonic="MOV D,L", optype="none"),
            OpCode(opcode=int('56', 16), length=1, mnemonic="MOV D,M", optype="none"),
            OpCode(opcode=int('57', 16), length=1, mnemonic="MOV D,A", optype="none"),
            OpCode(opcode=int('58', 16), length=1, mnemonic="MOV E,B", optype="none"),
            OpCode(opcode=int('59', 16), length=1, mnemonic="MOV E,C", optype="none"),
            OpCode(opcode=int('5a', 16), length=1, mnemonic="MOV E,D", optype="none"),
            OpCode(opcode=int('5b', 16), length=1, mnemonic="MOV E,E", optype="none"),
            OpCode(opcode=int('5c', 16), length=1, mnemonic="MOV E,H", optype="none"),
            OpCode(opcode=int('5d', 16), length=1, mnemonic="MOV E,L", optype="none"),
            OpCode(opcode=int('5e', 16), length=1, mnemonic="MOV E,M", optype="none"),
            OpCode(opcode=int('5f', 16), length=1, mnemonic="MOV E,A", optype="none"),
            OpCode(opcode=int('60', 16), length=1, mnemonic="MOV H,B", optype="none"),
            OpCode(opcode=int('61', 16), length=1, mnemonic="MOV H,C", optype="none"),
            OpCode(opcode=int('62', 16), length=1, mnemonic="MOV H,D", optype="none"),
            OpCode(opcode=int('63', 16), length=1, mnemonic="MOV H,E", optype="none"),
            OpCode(opcode=int('64', 16), length=1, mnemonic="MOV H,H", optype="none"),
            OpCode(opcode=int('65', 16), length=1, mnemonic="MOV H,L", optype="none"),
            OpCode(opcode=int('66', 16), length=1, mnemonic="MOV H,M", optype="none"),
            OpCode(opcode=int('67', 16), length=1, mnemonic="MOV H,A", optype="none"),
            OpCode(opcode=int('68', 16), length=1, mnemonic="MOV L,B", optype="none"),
            OpCode(opcode=int('69', 16), length=1, mnemonic="MOV L,C", optype="none"),
            OpCode(opcode=int('6a', 16), length=1, mnemonic="MOV L,D", optype="none"),
            OpCode(opcode=int('6b', 16), length=1, mnemonic="MOV L,E", optype="none"),
            OpCode(opcode=int('6c', 16), length=1, mnemonic="MOV L,H", optype="none"),
            OpCode(opcode=int('6d', 16), length=1, mnemonic="MOV L,L", optype="none"),
            OpCode(opcode=int('6e', 16), length=1, mnemonic="MOV L,M", optype="none"),
            OpCode(opcode=int('6f', 16), length=1, mnemonic="MOV L,A", optype="none"),
            OpCode(opcode=int('70', 16), length=1, mnemonic="MOV M,B", optype="none"),
            OpCode(opcode=int('71', 16), length=1, mnemonic="MOV M,C", optype="none"),
            OpCode(opcode=int('72', 16), length=1, mnemonic="MOV M,D", optype="none"),
            OpCode(opcode=int('73', 16), length=1, mnemonic="MOV M,E", optype="none"),
            OpCode(opcode=int('74', 16), length=1, mnemonic="MOV M,H", optype="none"),
            OpCode(opcode=int('75', 16), length=1, mnemonic="MOV M,L", optype="none"),
            OpCode(opcode=int('76', 16), length=1, mnemonic="HALT", optype="none"),
            OpCode(opcode=int('77', 16), length=1, mnemonic="MOV M,A", optype="none"),
            OpCode(opcode=int('78', 16), length=1, mnemonic="MOV A,B", optype="none"),
            OpCode(opcode=int('79', 16), length=1, mnemonic="MOV A,C", optype="none"),
            OpCode(opcode=int('7a', 16), length=1, mnemonic="MOV A,D", optype="none"),
            OpCode(opcode=int('7b', 16), length=1, mnemonic="MOV A,E", optype="none"),
            OpCode(opcode=int('7c', 16), length=1, mnemonic="MOV A,H", optype="none"),
            OpCode(opcode=int('7d', 16), length=1, mnemonic="MOV A,L", optype="none"),
            OpCode(opcode=int('7e', 16), length=1, mnemonic="MOV A,M", optype="none"),
            OpCode(opcode=int('7f', 16), length=1, mnemonic="MOV A,A", optype="none"),
            OpCode(opcode=int('80', 16), length=1, mnemonic="ADD B", optype="none"),
            OpCode(opcode=int('81', 16), length=1, mnemonic="ADD C", optype="none"),
            OpCode(opcode=int('82', 16), length=1, mnemonic="ADD D", optype="none"),
            OpCode(opcode=int('83', 16), length=1, mnemonic="ADD E", optype="none"),
            OpCode(opcode=int('84', 16), length=1, mnemonic="ADD H", optype="none"),
            OpCode(opcode=int('85', 16), length=1, mnemonic="ADD L", optype="none"),
            OpCode(opcode=int('86', 16), length=1, mnemonic="ADD M", optype="none"),
            OpCode(opcode=int('87', 16), length=1, mnemonic="ADD A", optype="none"),
            OpCode(opcode=int('88', 16), length=1, mnemonic="ADC B", optype="none"),
            OpCode(opcode=int('89', 16), length=1, mnemonic="ADC C", optype="none"),
            OpCode(opcode=int('8a', 16), length=1, mnemonic="ADC D", optype="none"),
            OpCode(opcode=int('8b', 16), length=1, mnemonic="ADC E", optype="none"),
            OpCode(opcode=int('8c', 16), length=1, mnemonic="ADC H", optype="none"),
            OpCode(opcode=int('8d', 16), length=1, mnemonic="ADC L", optype="none"),
            OpCode(opcode=int('8e', 16), length=1, mnemonic="ADC M", optype="none"),
            OpCode(opcode=int('8f', 16), length=1, mnemonic="ADC A", optype="none"),
            OpCode(opcode=int('90', 16), length=1, mnemonic="SUB B", optype="none"),
            OpCode(opcode=int('91', 16), length=1, mnemonic="SUB C", optype="none"),
            OpCode(opcode=int('92', 16), length=1, mnemonic="SUB D", optype="none"),
            OpCode(opcode=int('93', 16), length=1, mnemonic="SUB E", optype="none"),
            OpCode(opcode=int('94', 16), length=1, mnemonic="SUB H", optype="none"),
            OpCode(opcode=int('95', 16), length=1, mnemonic="SUB L", optype="none"),
            OpCode(opcode=int('96', 16), length=1, mnemonic="SUB M", optype="none"),
            OpCode(opcode=int('97', 16), length=1, mnemonic="SUB A", optype="none"),
            OpCode(opcode=int('98', 16), length=1, mnemonic="SBB B", optype="none"),
            OpCode(opcode=int('99', 16), length=1, mnemonic="SBB C", optype="none"),
            OpCode(opcode=int('9a', 16), length=1, mnemonic="SBB D", optype="none"),
            OpCode(opcode=int('9b', 16), length=1, mnemonic="SBB E", optype="none"),
            OpCode(opcode=int('9c', 16), length=1, mnemonic="SBB H", optype="none"),
            OpCode(opcode=int('9d', 16), length=1, mnemonic="SBB L", optype="none"),
            OpCode(opcode=int('9e', 16), length=1, mnemonic="SBB M", optype="none"),
            OpCode(opcode=int('9f', 16), length=1, mnemonic="SBB A", optype="none"),
            OpCode(opcode=int('a0', 16), length=1, mnemonic="ANA B", optype="none"),
            OpCode(opcode=int('a1', 16), length=1, mnemonic="ANA C", optype="none"),
            OpCode(opcode=int('a2', 16), length=1, mnemonic="ANA D", optype="none"),
            OpCode(opcode=int('a3', 16), length=1, mnemonic="ANA E", optype="none"),
            OpCode(opcode=int('a4', 16), length=1, mnemonic="ANA H", optype="none"),
            OpCode(opcode=int('a5', 16), length=1, mnemonic="ANA L", optype="none"),
            OpCode(opcode=int('a6', 16), length=1, mnemonic="ANA M", optype="none"),
            OpCode(opcode=int('a7', 16), length=1, mnemonic="ANA A", optype="none"),
            OpCode(opcode=int('a8', 16), length=1, mnemonic="XRA B", optype="none"),
            OpCode(opcode=int('a9', 16), length=1, mnemonic="XRA C", optype="none"),
            OpCode(opcode=int('aa', 16), length=1, mnemonic="XRA D", optype="none"),
            OpCode(opcode=int('ab', 16), length=1, mnemonic="XRA E", optype="none"),
            OpCode(opcode=int('ac', 16), length=1, mnemonic="XRA H", optype="none"),
            OpCode(opcode=int('ad', 16), length=1, mnemonic="XRA L", optype="none"),
            OpCode(opcode=int('ae', 16), length=1, mnemonic="XRA M", optype="none"),
            OpCode(opcode=int('af', 16), length=1, mnemonic="XRA A", optype="none"),
            OpCode(opcode=int('b0', 16), length=1, mnemonic="ORA B", optype="none"),
            OpCode(opcode=int('b1', 16), length=1, mnemonic="ORA C", optype="none"),
            OpCode(opcode=int('b2', 16), length=1, mnemonic="ORA D", optype="none"),
            OpCode(opcode=int('b3', 16), length=1, mnemonic="ORA E", optype="none"),
            OpCode(opcode=int('b4', 16), length=1, mnemonic="ORA H", optype="none"),
            OpCode(opcode=int('b5', 16), length=1, mnemonic="ORA L", optype="none"),
            OpCode(opcode=int('b6', 16), length=1, mnemonic="ORA M", optype="none"),
            OpCode(opcode=int('b7', 16), length=1, mnemonic="ORA A", optype="none"),
            OpCode(opcode=int('b8', 16), length=1, mnemonic="CMP B", optype="none"),
            OpCode(opcode=int('b9', 16), length=1, mnemonic="CMP C", optype="none"),
            OpCode(opcode=int('ba', 16), length=1, mnemonic="CMP D", optype="none"),
            OpCode(opcode=int('bb', 16), length=1, mnemonic="CMP E", optype="none"),
            OpCode(opcode=int('bc', 16), length=1, mnemonic="CMP H", optype="none"),
            OpCode(opcode=int('bd', 16), length=1, mnemonic="CMP L", optype="none"),
            OpCode(opcode=int('be', 16), length=1, mnemonic="CMP M", optype="none"),
            OpCode(opcode=int('bf', 16), length=1, mnemonic="CMP A", optype="none"),
            OpCode(opcode=int('c0', 16), length=1, mnemonic="RNZ", optype="none"),
            OpCode(opcode=int('c1', 16), length=1, mnemonic="POP B", optype="none"),
            OpCode(opcode=int('c2', 16), length=3, mnemonic="JNZ", optype="address"),
            OpCode(opcode=int('c3', 16), length=3, mnemonic="JMP", optype="address"),
            OpCode(opcode=int('c4', 16), length=3, mnemonic="CNZ", optype="address"),
            OpCode(opcode=int('c5', 16), length=1, mnemonic="PUSH B", optype="none"),
            OpCode(opcode=int('c6', 16), length=2, mnemonic="ADI", optype="immediate"),
            OpCode(opcode=int('c7', 16), length=1, mnemonic="RST", optype="none"),
            OpCode(opcode=int('c8', 16), length=1, mnemonic="RZ", optype="none"),
            OpCode(opcode=int('c9', 16), length=1, mnemonic="RET", optype="none"),
            OpCode(opcode=int('ca', 16), length=3, mnemonic="JZ", optype="address"),
            OpCode(opcode=int('cb', 16), length=1, mnemonic="UNKNOWN", optype="none"),
            OpCode(opcode=int('cc', 16), length=3, mnemonic="CZ", optype="address"),
            OpCode(opcode=int('cd', 16), length=3, mnemonic="CALL", optype="address"),
            OpCode(opcode=int('ce', 16), length=2, mnemonic="ACI", optype="immediate"),
            OpCode(opcode=int('cf', 16), length=1, mnemonic="RST", optype="none"),
            OpCode(opcode=int('d0', 16), length=1, mnemonic="RNC", optype="none"),
            OpCode(opcode=int('d1', 16), length=1, mnemonic="POP D", optype="none"),
            OpCode(opcode=int('d2', 16), length=3, mnemonic="JNC", optype="address"),
            OpCode(opcode=int('d3', 16), length=2, mnemonic="OUT", optype="immediate"),
            OpCode(opcode=int('d4', 16), length=3, mnemonic="CNC", optype="address"),
            OpCode(opcode=int('d5', 16), length=1, mnemonic="PUSH D", optype="none"),
            OpCode(opcode=int('d6', 16), length=2, mnemonic="SUI", optype="immediate"),
            OpCode(opcode=int('d7', 16), length=1, mnemonic="RST", optype="none"),
            OpCode(opcode=int('d8', 16), length=1, mnemonic="RC", optype="none"),
            OpCode(opcode=int('d9', 16), length=1, mnemonic="UNKONWN", optype="none"),
            OpCode(opcode=int('da', 16), length=3, mnemonic="JC", optype="address"),
            OpCode(opcode=int('db', 16), length=2, mnemonic="IN", optype="immediate"),
            OpCode(opcode=int('dc', 16), length=3, mnemonic="CC", optype="address"),
            OpCode(opcode=int('dd', 16), length=1, mnemonic="UNKNOWN", optype="none"),
            OpCode(opcode=int('de', 16), length=2, mnemonic="SBI", optype="immediate"),
            OpCode(opcode=int('df', 16), length=1, mnemonic="RST", optype="none"),
            OpCode(opcode=int('e0', 16), length=1, mnemonic="RPO", optype="none"),
            OpCode(opcode=int('e1', 16), length=1, mnemonic="POP H", optype="none"),
            OpCode(opcode=int('e2', 16), length=3, mnemonic="JPO", optype="address"),
            OpCode(opcode=int('e3', 16), length=1, mnemonic="XTHL", optype="none"),
            OpCode(opcode=int('e4', 16), length=3, mnemonic="CPO", optype="address"),
            OpCode(opcode=int('e5', 16), length=1, mnemonic="PUSH H", optype="none"),
            OpCode(opcode=int('e6', 16), length=2, mnemonic="ANI", optype="immediate"),
            OpCode(opcode=int('e7', 16), length=1, mnemonic="RST", optype="none"),
            OpCode(opcode=int('e8', 16), length=1, mnemonic="RPI", optype="none"),
            OpCode(opcode=int('e9', 16), length=1, mnemonic="PCHL", optype="none"),
            OpCode(opcode=int('ea', 16), length=3, mnemonic="JPE", optype="address"),
            OpCode(opcode=int('eb', 16), length=1, mnemonic="XCHG", optype="none"),
            OpCode(opcode=int('ec', 16), length=3, mnemonic="CPE", optype="address"),
            OpCode(opcode=int('ed', 16), length=1, mnemonic="UNKNOWN", optype="none"),
            OpCode(opcode=int('ee', 16), length=2, mnemonic="XRI", optype="immediate"),
            OpCode(opcode=int('ef', 16), length=1, mnemonic="RST", optype="none"),
            OpCode(opcode=int('f0', 16), length=1, mnemonic="RP", optype="none"),
            OpCode(opcode=int('f1', 16), length=1, mnemonic="POP PSW", optype="none"),
            OpCode(opcode=int('f2', 16), length=3, mnemonic="JP", optype="address"),
            OpCode(opcode=int('f3', 16), length=1, mnemonic="DI", optype="none"),
            OpCode(opcode=int('f4', 16), length=3, mnemonic="CP", optype="address"),
            OpCode(opcode=int('f5', 16), length=1, mnemonic="PUSH PSW", optype="none"),
            OpCode(opcode=int('f6', 16), length=2, mnemonic="ORI", optype="immediate"),
            OpCode(opcode=int('f7', 16), length=1, mnemonic="RST", optype="none"),
            OpCode(opcode=int('f8', 16), length=1, mnemonic="RM", optype="none"),
            OpCode(opcode=int('f9', 16), length=1, mnemonic="SPHL", optype="none"),
            OpCode(opcode=int('fa', 16), length=3, mnemonic="JM", optype="address"),
            OpCode(opcode=int('fb', 16), length=1, mnemonic="EI", optype="none"),
            OpCode(opcode=int('fc', 16), length=3, mnemonic="CM", optype="address"),
            OpCode(opcode=int('fd', 16), length=1, mnemonic="UNKNOWN", optype="none"),
            OpCode(opcode=int('fe', 16), length=2, mnemonic="CPI", optype="immediate"),
            OpCode(opcode=int('ff', 16), length=1, mnemonic="RST", optype="none"),
        )
        self._memory = None

    def load(self, romfile):
        """Loads the given ROM file

        :param romfile: full path to the ROM to load

        :raises RomLoadException: if the file cannot be read
        """
        try:
            with open(romfile, "rb") as fp:
                self._memory = fp.read()
                self._memory = self._memory \
                               + bytearray([0 for x in range(0x10000 - len(self._memory))])
                self._pc = 0
        except Exception as e:
            raise RomLoadException("{0}".format(e))

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
        b = [ "{:02X}".format(opcode.opcode) ]
        b.extend( [ "{:02X}".format(o) for o in operands ])
        for x in range(3 - len(b)):
            b.append( "  ")
        return " ".join(b)

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

    def next_instruction(self):
        """Parses loaded ROM and returns next instruction.

        The program counter is advanced for every instruction.

        :return tuple:  Returns tuple of OpCode and list of operands (may be empty)
        """
        while self._pc < len(self._memory):
            op = self.opcodes[self._memory[self._pc]]
            operands = [self._memory[self._pc + x] for x in range(1, op.length) ]
            self._pc += op.length
            yield (op, operands)



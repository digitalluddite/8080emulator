from unittest import TestCase

from machine import Machine8080
from machine import OutOfMemoryException
from cpu import Registers

ROM_PATH = "/home/mdonovan/emulator/invaders/invaders"


class TestMachine8080(TestCase):
    def setUp(self):
        self.machine = Machine8080()
        self.machine.load(ROM_PATH)

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



from unittest import TestCase
import logging

from machine import Machine8080
from machine import OutOfMemoryException
from cpu import Registers


ROM_PATH = "/Users/mdonovan/Projects/emulator/invaders/rom"


class TestMachine8080(TestCase):
    def setUp(self):
        self.machine = Machine8080()
        self.machine.load(ROM_PATH)
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

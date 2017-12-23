from unittest import TestCase

from utils import byte_to_signed_int, int_to_signed_byte


class TestTo_signed_binary(TestCase):
    def test_to_signed_binary(self):
        """
        Takes a signed integer and returns the appropriate byte
        :return:
        """
        v = 0x80
        for x in range(-128, 1):
            y = int_to_signed_byte(x)
            print(f'Comparing (x={x}) {v} to {y}')
            self.assertEqual(v, y)
            v = (v+1) % 256 
        v = 1
        for x in range(1, 128):
            y = int_to_signed_byte(x)
            print(f'Comparing (x={x}) {v} to {y}')
            self.assertEqual(v, y)
            v += 1

    def test_get_signed_int(self):
        """
        get_signed_int() takes a byte that represents a signed byte
        and converts it appropriate:  0x80 = -128
        :return:
        """
        v = -128
        for x in range(0x80, 0x100): 
            self.assertEqual(byte_to_signed_int(x), v)
            v += 1
        for x in range(0, 0x7f):
            self.assertEqual(byte_to_signed_int(x), v)
            v += 1        


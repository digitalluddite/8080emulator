
import argparse
from machine import Machine8080, RomLoadException, RomException

if __name__ == "__main__":
    parser = argparse.ArgumentParser(usage="./disassemble.py ROM")
    parser.add_argument("rom", metavar="ROM", nargs=1, help="The file to be disassembled")

    args = parser.parse_args()
    machine = Machine8080()
    try:
        machine.load(args.rom[0])
        machine.disassemble()
    except RomLoadException as e:
        print("Error reading ROM: {0}".format(e))
    except RomException as e:
        print("Error parsing ROM: {0}".format(e))

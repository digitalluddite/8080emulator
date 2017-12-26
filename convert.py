
import re


if __name__ == "__main__":
    pattern = re.compile(r'^\s+{\s*{0x([0-9a-f]+), (\d), "([^"]+)", (none|immediate|address)\},.*$')
    outfp = open('machine.py', 'a')
    with open("machine.c", "r") as fp:
        for l in fp.readlines():
            match = pattern.match(l)
            if match is not None:
                print("OpCode(opcode=int('{0}', 16), length={1}, mnemonic=\"{2}\", optype=\"{3}\"),"
                      .format(match.group(1), match.group(2), match.group(3), match.group(4)), file=outfp)


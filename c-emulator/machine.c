
#include "machine.h"
#include "stdio.h"

typedef struct {
	OPCODE_INFO inst;
	cpufunc impl; // function that implements the OPCODE
} MACHINE;



int nop(CPU* cpu, const INSTRUCTION *inst) {
	return 0;
}

int unimplemented_instruction(CPU* cpu, const INSTRUCTION *inst)
{ 
	fprintf(stderr, "Unimplemented opcode: 0x%02X\n", inst->opcode);
}

MACHINE inst_set[] = {
	{ {0x00, 1, "NOP", none}, nop},
	/*
		LXI B Low high
		the third byte of the instruction (the most significant 8 bits of the 
		16-bit immediate data) is loaded into the first register of the 
		specified pair, while the second byte of the instruction (least 
		significant byte is loaded into second register of the pair.  
	*/
	{ {0x01, 3, "LXI B", immediate}, unimplemented_instruction }, // LXI B,C
	/*
		store accumulator at memory B,C (e.g., B=3f, C=16, STAX B stores 
		accumulator at 3F16H)
	*/
	{ {0x02, 1, "STAX B", none} , unimplemented_instruction }, 
	{ {0x03, 1, "INX B", none}, unimplemented_instruction }, // increment B,C
	{ {0x04, 1, "INR B", none}, inr},
	{ {0x05, 1, "DCR B", none}, dcr},
	{ {0x06, 2, "MVI B", immediate}, unimplemented_instruction },// move into B
	/*
		RLC  The carry bit is set equal to the high order bit of the accumulator
		the contents of the accumulator are rotated one bit position to the left
		with the high order bit being transfer to the low-order bit position.
	*/
	{ {0x07, 1, "RLC", none}, unimplemented_instruction }, 
	{ {0x08, 1, "UNKNOWN", none}, unimplemented_instruction },
	/*
		DAD -- double add
		the 16-bit number in the specified register pair is added ot the 16-bit 
		number held in the H,L register using 2's complement arithmetic.  The 
		result replaces the contents of the H,L registers.

		carry bit
	*/	
	{{0x09, 1, "DAD B", none}, unimplemented_instruction }, // double add B,C 
	{{0x0a, 1, "LDAX B", none}, unimplemented_instruction }, // load accumulator from B,C
	{{0x0b, 1, "DCX B", none}, unimplemented_instruction }, // decrement B,C
	{{0x0c, 1, "INR C", none}, inr},
	{{0x0d, 1, "DCR C", none}, dcr},
	{{0x0e, 2, "MVI C", immediate}, unimplemented_instruction }, 
	/*
		RRC Rotate accumulator right
		The carry bit is set equal to the low-order bit of the accumuluator.  The contents
		of the accumulator are rotated one bit position to the right with the low-order bit
		being transferred to the high-order bit position
	*/
	{{0x0f, 1, "RRC", none}, unimplemented_instruction },
	{{0x10, 1, "UNKNOWN", none}, unimplemented_instruction },
	{{0x11, 3, "LXI D", immediate}, unimplemented_instruction }, // see 0x01 instruction
	{{0x12, 1, "STAX D", none}, unimplemented_instruction }, // store accumulator at memory D,E
	{{0x13, 1, "INX D", none}, unimplemented_instruction }, // increment D,E
	{{0x14, 1, "INR D", none}, inr},
	{{0x15, 1, "DCR D", none}, dcr},
	{{0x16, 2, "MVI D,", immediate}, unimplemented_instruction },
	/*
		Rotate accumulator left through carry

		the contents of the accumulator are rotated one bit position to he left.  the 
		high-order bit of the accumulator replaces the carry bit whilt the carry bit 
		replaces the high order bit of the accumulator.
	*/
	{{0x17, 1, "RAL", none}, unimplemented_instruction },
	{{0x18, 1, "UNKNOWN", none}, unimplemented_instruction },
	{{0x19, 1, "DAD D", none}, unimplemented_instruction }, // doubl-add D,E
	{{0x1a, 1, "LDAX D", none}, unimplemented_instruction }, // load accumulator from D,E
	{{0x1b, 1, "DCX D", none}, unimplemented_instruction }, // decrement D,E
	{{0x1c, 1, "INR E", none}, inr},
	{{0x1d, 1, "DCR E", none}, dcr},
	{{0x1e, 2, "MVI E,", immediate}, unimplemented_instruction },
	/*
		rotate accumulator right through carry.  The contents of the accumulator are rotated
		one bite position to the riht.  The low-order bit of the accumulator replaces the carry
		bit, while the carry bit replaces the high-order bit of the accumulator
	*/
	{{0x1f, 1, "RAR", none}, unimplemented_instruction },
	{{0x20, 1, "UNKNOWN", none}, unimplemented_instruction },
	{{0x21, 3, "LXI H", immediate}, unimplemented_instruction },
	/*
		the contents of the L register are stored at memory address formed
		by catting HI ADD with LOW Add.  the contents of H are stored at the 
		next higer memory address
	*/
	{{0x22, 3, "SHLD", address}, unimplemented_instruction },
	{{0x23, 1, "INX H", none}, unimplemented_instruction }, // increment pair H,L
	{{0x24, 1, "INR H", none}, inr},
	{{0x25, 1, "DCR H", none}, dcr},
	{{0x26, 2, "MVI H,", immediate}, unimplemented_instruction },
/*
	DAA Decimal Adjust Accumulator

	The 8-bit hex number in the accuulator is adjusted to 
	form two fout-bit binary-coded decimal digits by the following
	1.  If the least sig. four bits is greater than 9 or if the aux
		carry bit is 1, the accumulator is incremented by 6
	2.  If the most sign fou bits of the accumulator _now_ represent a 
		number greater than 9 or if normal carry is 1, most sig. bits
		are incremented by 6

	if carry out of least sig 4 bits occurs during step 1, aux carry is set
	otherwise it is reset.  If the carry out of most sig. four bits occurs
	during step 2, then carry is set, otherwise, it's unaffected
*/
	{{0x27, 1, "DAA", none}, unimplemented_instruction }, 	
	{{0x28, 1, "UNKNOWN", none}, unimplemented_instruction },
	{{0x29, 1, "DAD H", none}, unimplemented_instruction }, // double-add H,L
	/*
		the byte at memory address formed by catting HI with LOW replaces
		the contents of L, the byte at the next higher memory address replaces
		H
	*/
	{{0x2a, 3, "LHLD", address}, unimplemented_instruction },
	{{0x2b, 1, "DCX H", none}, unimplemented_instruction }, // decrememt H,L
	{{0x2c, 1, "UNKNOWN", none}, unimplemented_instruction },
	{{0x2d, 1, "UNKNOWN", none}, unimplemented_instruction },
	{{0x2e, 2, "MVI L,", immediate}, unimplemented_instruction },
	{{0x2f, 1, "CMA", none}, cma},	// each bit of accumulator is complemented
	{{0x30, 1, "UNKNOWN", none}, unimplemented_instruction },
	/*
		the second byte of the instruction replaces the least significant
		byte of the stack pointer, while the third byte replaces the most
		significant byte of the stack pointer
	*/
	{{0x31, 3, "LXI SP", immediate}, unimplemented_instruction },
	/*
		contents of the accumulator replace the byte at teh memory address 
		formed by concatenating HI ADD with LOW ADD
	*/
	{{0x32, 3, "STA", address}, unimplemented_instruction },
	{{0x33, 1, "INX SP", none}, unimplemented_instruction }, // increment SP
	{{0x34, 1, "INR M", none}, inr},
	{{0x35, 1, "DCR M", none}, dcr},
	{{0x36, 2, "MVI M,", immediate}, unimplemented_instruction },
	{{0x37, 1, "STC", none}, stc},
	{{0x38, 1, "UNKNOWN", none}, unimplemented_instruction },
	{{0x39, 1, "DAD SP", none}, unimplemented_instruction }, // double-add SP
	/*
		the byte at the memory address formed by concat'ing HI ADD with LOW ADD
		replaces the contents of the accumulator
	*/
	{{0x3a, 3, "LDA", address}, unimplemented_instruction },
	{{0x3b, 1, "DCX SP", none}, unimplemented_instruction }, // decrememt SP
	{{0x3c, 1, "INR A", none}, inr},
	{{0x3d, 1, "DCR", none}, dcr},
	{{0x3e, 2, "MVI A,", immediate}, unimplemented_instruction },
	{{0x3f, 1, "CMC", none}, cmc},
	{{0x40, 1, "MOV B,B", none}, unimplemented_instruction }, // mov dst,src
	{{0x41, 1, "MOV B,C", none}, unimplemented_instruction },
	{{0x42, 1, "MOV B,D", none}, unimplemented_instruction },
	{{0x43, 1, "MOV B,E", none}, unimplemented_instruction },
	{{0x44, 1, "MOV B,H", none}, unimplemented_instruction },
	{{0x45, 1, "MOV B,L", none}, unimplemented_instruction },
	{{0x46, 1, "MOV B,M", none}, unimplemented_instruction },
	{{0x47, 1, "MOV B,A", none}, unimplemented_instruction },
	{{0x48, 1, "MOV C,B", none}, unimplemented_instruction },
	{{0x49, 1, "MOV C,C", none}, unimplemented_instruction },
	{{0x4a, 1, "MOV C,D", none}, unimplemented_instruction },
	{{0x4b, 1, "MOV C,E", none}, unimplemented_instruction },
	{{0x4c, 1, "MOV C,H", none}, unimplemented_instruction },
	{{0x4d, 1, "MOV C,L", none}, unimplemented_instruction },
	{{0x4e, 1, "MOV C,M", none}, unimplemented_instruction },
	{{0x4f, 1, "MOV C,A", none}, unimplemented_instruction },
	{{0x50, 1, "MOV D,B", none}, unimplemented_instruction },
	{{0x51, 1, "MOV D,C", none}, unimplemented_instruction },
	{{0x52, 1, "MOV D,D", none}, unimplemented_instruction },
	{{0x53, 1, "MOV D,E", none}, unimplemented_instruction },
	{{0x54, 1, "MOV D,H", none}, unimplemented_instruction },
	{{0x55, 1, "MOV D,L", none}, unimplemented_instruction },
	{{0x56, 1, "MOV D,M", none}, unimplemented_instruction },
	{{0x57, 1, "MOV D,A", none}, unimplemented_instruction },
	{{0x58, 1, "MOV E,B", none}, unimplemented_instruction },
	{{0x59, 1, "MOV E,C", none}, unimplemented_instruction },
	{{0x5a, 1, "MOV E,D", none}, unimplemented_instruction },
	{{0x5b, 1, "MOV E,E", none}, unimplemented_instruction },
	{{0x5c, 1, "MOV E,H", none}, unimplemented_instruction },
	{{0x5d, 1, "MOV E,L", none}, unimplemented_instruction },
	{{0x5e, 1, "MOV E,M", none}, unimplemented_instruction },
	{{0x5f, 1, "MOV E,A", none}, unimplemented_instruction },
	{{0x60, 1, "MOV H,B", none}, unimplemented_instruction },
	{{0x61, 1, "MOV H,C", none}, unimplemented_instruction },
	{{0x62, 1, "MOV H,D", none}, unimplemented_instruction },
	{{0x63, 1, "MOV H,E", none}, unimplemented_instruction },
	{{0x64, 1, "MOV H,H", none}, unimplemented_instruction },
	{{0x65, 1, "MOV H,L", none}, unimplemented_instruction },
	{{0x66, 1, "MOV H,M", none}, unimplemented_instruction },
	{{0x67, 1, "MOV H,A", none}, unimplemented_instruction },
	{{0x68, 1, "MOV L,B", none}, unimplemented_instruction },
	{{0x69, 1, "MOV L,C", none}, unimplemented_instruction },
	{{0x6a, 1, "MOV L,D", none}, unimplemented_instruction },
	{{0x6b, 1, "MOV L,E", none}, unimplemented_instruction },
	{{0x6c, 1, "MOV L,H", none}, unimplemented_instruction },
	{{0x6d, 1, "MOV L,L", none}, unimplemented_instruction },
	{{0x6e, 1, "MOV L,M", none}, unimplemented_instruction },
	{{0x6f, 1, "MOV L,A", none}, unimplemented_instruction },
	{{0x70, 1, "MOV M,B", none}, unimplemented_instruction },
	{{0x71, 1, "MOV M,C", none}, unimplemented_instruction },
	{{0x72, 1, "MOV M,D", none}, unimplemented_instruction },
	{{0x73, 1, "MOV M,E", none}, unimplemented_instruction },
	{{0x74, 1, "MOV M,H", none}, unimplemented_instruction },
	{{0x75, 1, "MOV M,L", none}, unimplemented_instruction },
	/*
		the program counter is increment to the address of the
		next sedquential instruction.  CPU then enters STOPPED state
		and no further activity takes place until an interrupt occurs
	*/
	{{0x76, 1, "HALT", none}, unimplemented_instruction },
	{{0x77, 1, "MOV M,A", none}, unimplemented_instruction },
	{{0x78, 1, "MOV A,B", none}, unimplemented_instruction },
	{{0x79, 1, "MOV A,C", none}, unimplemented_instruction },
	{{0x7a, 1, "MOV A,D", none}, unimplemented_instruction },
	{{0x7b, 1, "MOV A,E", none}, unimplemented_instruction },
	{{0x7c, 1, "MOV A,H", none}, unimplemented_instruction },
	{{0x7d, 1, "MOV A,L", none}, unimplemented_instruction },
	{{0x7e, 1, "MOV A,M", none}, unimplemented_instruction },
	{{0x7f, 1, "MOV A,A", none}, unimplemented_instruction },
	/*
	 add value at B to A, carry, sign, zero, parity, aux carry
	*/
	{{0x80, 1, "ADD B", none}, unimplemented_instruction },		
	{{0x81, 1, "ADD C", none}, unimplemented_instruction },
	{{0x82, 1, "ADD D", none}, unimplemented_instruction },
	{{0x83, 1, "ADD E", none}, unimplemented_instruction },
	{{0x84, 1, "ADD H", none}, unimplemented_instruction },
	{{0x85, 1, "ADD L", none}, unimplemented_instruction },
	{{0x86, 1, "ADD M", none}, unimplemented_instruction },
	{{0x87, 1, "ADD A", none}, unimplemented_instruction },
	/*
		ADC -- add register or memory to accumulator with carry	
		The specified byte plus the content of the carry bit is added 
		to the contents of the accumulator

		carry, sign, zero, parity, aux carry
	*/
	{{0x88, 1, "ADC B", none}, unimplemented_instruction },
	{{0x89, 1, "ADC C", none}, unimplemented_instruction },
	{{0x8a, 1, "ADC D", none}, unimplemented_instruction },
	{{0x8b, 1, "ADC E", none}, unimplemented_instruction },
	{{0x8c, 1, "ADC H", none}, unimplemented_instruction },
	{{0x8d, 1, "ADC L", none}, unimplemented_instruction },
	{{0x8e, 1, "ADC M", none}, unimplemented_instruction },
	{{0x8f, 1, "ADC A", none}, unimplemented_instruction },
	/*
		SUB - specified byte  is subtraceted from the accumulator using two's complement

		if there is no carry out of the hig-order bit, indicating that a borrow occurred,
		the carry bit is set; otherwise it is reset.

		carry, sign, zero, parity, aux carry
	*/
	{{0x90, 1, "SUB B", none}, unimplemented_instruction },
	{{0x91, 1, "SUB C", none}, unimplemented_instruction }, 
	{{0x92, 1, "SUB D", none}, unimplemented_instruction },
	{{0x93, 1, "SUB E", none}, unimplemented_instruction },
	{{0x94, 1, "SUB H", none}, unimplemented_instruction },
	{{0x95, 1, "SUB L", none}, unimplemented_instruction },
	{{0x96, 1, "SUB M", none}, unimplemented_instruction },
	{{0x97, 1, "SUB A", none}, unimplemented_instruction },
	/*
		SBB -- subtract register or memory from accumulator with borrow

		The carry bit is internally added to the contents of the specified
		byte.  This ivalue is then subtracted from the accumulator using two's
		complement arithmetic.

		carry, sign, zero, parity, aux carry
	*/	
	{{0x98, 1, "SBB B", none}, unimplemented_instruction },
	{{0x99, 1, "SBB C", none}, unimplemented_instruction },
	{{0x9a, 1, "SBB D", none}, unimplemented_instruction },
	{{0x9b, 1, "SBB E", none}, unimplemented_instruction },
	{{0x9c, 1, "SBB H", none}, unimplemented_instruction },
	{{0x9d, 1, "SBB L", none}, unimplemented_instruction },
	{{0x9e, 1, "SBB M", none}, unimplemented_instruction },
	{{0x9f, 1, "SBB A", none}, unimplemented_instruction },
	/*
		ANA logical AND register or memory with accumulator

		carry bit is reset
	*/
	{{0xa0, 1, "ANA B", none}, unimplemented_instruction },
	{{0xa1, 1, "ANA C", none}, unimplemented_instruction },
	{{0xa2, 1, "ANA D", none}, unimplemented_instruction },
	{{0xa3, 1, "ANA E", none}, unimplemented_instruction },
	{{0xa4, 1, "ANA H", none}, unimplemented_instruction },
	{{0xa5, 1, "ANA L", none}, unimplemented_instruction },
	{{0xa6, 1, "ANA M", none}, unimplemented_instruction },
	{{0xa7, 1, "ANA A", none}, unimplemented_instruction },
	/*
		XRA logical exclusive-or register or memory with accumulator
		carry bit is reset.

		affect carry, zero, sig, parity, aux carry
	*/
	{{0xa8, 1, "XRA B", none}, unimplemented_instruction },
	{{0xa9, 1, "XRA C", none}, unimplemented_instruction },
	{{0xaa, 1, "XRA D", none}, unimplemented_instruction },
	{{0xab, 1, "XRA E", none}, unimplemented_instruction },
	{{0xac, 1, "XRA H", none}, unimplemented_instruction },
	{{0xad, 1, "XRA L", none}, unimplemented_instruction },
	{{0xae, 1, "XRA M", none}, unimplemented_instruction },
	{{0xaf, 1, "XRA A", none}, unimplemented_instruction },
	/*
		ORA Logical OR register or memory
	
		carry bit is reset
		zero, sign, parity
	*/
	{{0xb0, 1, "ORA B", none}, unimplemented_instruction },
	{{0xb1, 1, "ORA C", none}, unimplemented_instruction },
	{{0xb2, 1, "ORA D", none}, unimplemented_instruction },
	{{0xb3, 1, "ORA E", none}, unimplemented_instruction },
	{{0xb4, 1, "ORA H", none}, unimplemented_instruction },
	{{0xb5, 1, "ORA L", none}, unimplemented_instruction },
	{{0xb6, 1, "ORA M", none}, unimplemented_instruction },
	{{0xb7, 1, "ORA A", none}, unimplemented_instruction },
	/*
		CMP Compare register or memory with accumulator

		comparison is perofmred by internally subtracting the contents
		of REG from the accumulator (leaving both unchanged) and setting
		the condition bits according to the result.

		carry, zero, sign, parity, aux carry
	*/
	{{0xb8, 1, "CMP B", none}, unimplemented_instruction },
	{{0xb9, 1, "CMP C", none}, unimplemented_instruction },
	{{0xba, 1, "CMP D", none}, unimplemented_instruction },
	{{0xbb, 1, "CMP E", none}, unimplemented_instruction },
	{{0xbc, 1, "CMP H", none}, unimplemented_instruction },
	{{0xbd, 1, "CMP L", none}, unimplemented_instruction },
	{{0xbe, 1, "CMP M", none}, unimplemented_instruction },
	{{0xbf, 1, "CMP A", none}, unimplemented_instruction },

	{{0xc0, 1, "RNZ", none}, unimplemented_instruction }, // return if zero bit is 0
	{{0xc1, 1, "POP B", none}, unimplemented_instruction },  // pop b,c
	/*
		if zero bit is zero, program execution jumps
	*/
	{{0xc2, 3, "JNZ", address}, unimplemented_instruction },
	/*
		program execution continues unconditionally at memory address
	*/
	{{0xc3, 3, "JMP", address}, unimplemented_instruction },
	{{0xc4, 3, "CNZ", address}, unimplemented_instruction }, // call if zero bit is zero
	{{0xc5, 1, "PUSH B", none}, unimplemented_instruction }, // push b,c pair
	/*
		add byte to accumulator
		carry, sign, zero, parity, aux carry
	*/
	{{0xc6, 2, "ADI", immediate}, unimplemented_instruction }, 
	/*
		format of RST instruction: 11EXP111

		The program counter is pushed onto the stack.  Program
		execution continues at memory address:
		0000000000EXP000B

	*/
	{{0xc7, 1, "RST", none}, unimplemented_instruction }, 
	{{0xc8, 1, "RZ", none}, unimplemented_instruction }, // return if zero bit is 1
	{{0xc9, 1, "RET", none}, unimplemented_instruction }, // pop address off stack, set to PC
	/*
		if zero bit is one, program execution continues at address
	*/
	{{0xca, 3, "JZ", address}, unimplemented_instruction },
	{{0xcb, 1, "UNKNOWN", none}, unimplemented_instruction },
	{{0xcc, 3, "CZ", address}, unimplemented_instruction }, // call if zero bit is  one
	{{0xcd, 3, "CALL", address}, unimplemented_instruction },
	/*
		the byte of data is added to the accumulator plus the contents of the carry bit.
		carry, sign, zero, parity, aux carry
	*/
	{{0xce, 2, "ACI", immediate}, unimplemented_instruction },
	{{0xcf, 1, "RST", none}, unimplemented_instruction },
	{{0xd0, 1, "RNC", none}, unimplemented_instruction }, // return if caryy bit is 0
	{{0xd1, 1, "POP D", none}, unimplemented_instruction }, // pop d,e
	/*
		if the carry bit is zero, continues at address	
	*/
	{{0xd2, 3, "JNC", address}, unimplemented_instruction },
	{{0xd3, 2, "OUT", immediate}, unimplemented_instruction }, // contents of accumulator are sent to output device
	{{0xd4, 3, "CNC", address}, unimplemented_instruction }, // call if carry is zero
	{{0xd5, 1, "PUSH D", none}, unimplemented_instruction }, // push d,e pair
	/*
		byte of immediate data is subtracted from accumulator using
		two's complement airthmetic.

		since this is a subtraction, the carry bit is set (indicating a borrow)
		if there is no carry out of the high-order position, and reset if there
		is a carry out
		carry sign, zero, parity, aux. carry
	*/
	{{0xd6, 2, "SUI", immediate}, unimplemented_instruction },
	{{0xd7, 1, "RST", none}, unimplemented_instruction },
	{{0xd8, 1, "RC", none}, unimplemented_instruction }, // return if carry is 1
	{{0xd9, 1, "UNKONWN", none}, unimplemented_instruction },
	/*
		if the carry bit is one, program execution continues at address 
	*/
	{{0xda, 3, "JC", address}, unimplemented_instruction },
	/*
		1 byte is read from input device number EXP (operand) into the accumulator
	*/
	{{0xdb, 2, "IN", immediate}, unimplemented_instruction },
	{{0xdc, 3, "CC", address}, unimplemented_instruction }, // call if carry bit is one
	{{0xdd, 1, "UNKNOWN", none}, unimplemented_instruction },
	/*
		subtract immediate from accumulator with borrow
		the carry bit is internally added to the byte of 
		immediate data.  This value is then subtracted from
		the accumulator using two's complement arithmetic.

		the carry bit is set if there's no carry out of the high order
		position, and reset if there is a carry out
		carry, sign, zero, parity, aux. carry
	*/
	{{0xde, 2, "SBI", immediate}, unimplemented_instruction },
	{{0xdf, 1, "RST", none}, unimplemented_instruction },
	{{0xe0, 1, "RPO", none}, unimplemented_instruction }, // return if parity is 0
	{{0xe1, 1, "POP H", none}, unimplemented_instruction }, // pop h,l
	/*
		if parity is 0 (odd parity) jump
	*/
	{{0xe2, 3, "JPO", address}, unimplemented_instruction },
	/*
		the contents of the L register are exhcnaged with the contents of the 
		memory byte who address i shelop in the stack pointer.  The contents of 
		the H register are exchanged with the contents of the memory byte whose
		address is one greater than that held in the stack pointer
	*/
	{{0xe3, 1, "XTHL", none}, unimplemented_instruction }, // exchange stack 
	{{0xe4, 3, "CPO", address}, unimplemented_instruction }, // call if parity odd
	{{0xe5, 1, "PUSH H", none}, unimplemented_instruction }, // push h,l pair 
	/*
		And immediate with acucmulator

		byte of immediate data is logicalled ANDed with accumulator
		carry bit is reset to zero
		carry, zero, sign, parity
	*/
	{{0xe6, 2, "ANI", immediate}, unimplemented_instruction },
	{{0xe7, 1, "RST", none}, unimplemented_instruction },
	{{0xe8, 1, "RPI", none}, unimplemented_instruction }, // return if parity is 1
	/*
		the contents of the H register replace the most significant byte of the 
		program counter; the contents of L replace the least significant

		program execution continues at the address contained in H,L registers
	*/
	{{0xe9, 1, "PCHL", none}, unimplemented_instruction }, // load program counter
	/*
		if parity bit is 1 (even parity) jump
	*/
	{{0xea, 3, "JPE", address}, unimplemented_instruction },
	{{0xeb, 1, "XCHG", none}, unimplemented_instruction }, // 16 bites in H,L are exchanged with D,E
	{{0xec, 3, "CPE", address}, unimplemented_instruction }, // call if parity is 1
	{{0xed, 1, "UNKNOWN", none}, unimplemented_instruction },
	/*
		exclusive or immediate with accumulator

		carry bit is set to zero
		carry, zero, sign, parity
	*/
	{{0xee, 2, "XRI", immediate}, unimplemented_instruction },
	{{0xef, 1, "RST", none}, unimplemented_instruction },
	{{0xf0, 1, "RP", none}, unimplemented_instruction }, // return if sign bit is 0
	{{0xf1, 1, "POP PSW", none}, unimplemented_instruction }, // pop PSW (flags and register)
	/*
		if sign bit is zero (postive result) jump
	*/
	{{0xf2, 3, "JP", address}, unimplemented_instruction },
	{{0xf3, 1, "DI", none}, unimplemented_instruction }, // disable interrupts (resets INTE flip-flop)
	{{0xf4, 3, "CP", address}, unimplemented_instruction }, // call if sign bit is o
	{{0xf5, 1, "PUSH PSW", none}, unimplemented_instruction }, // push PSW (flags and register A)
	/*
		byte of immediate data is logically OR'd with contents of the accumulator
		carry bit is reset; zero, sign, parity are set accordingly
	*/
	{{0xf6, 2, "ORI", immediate}, unimplemented_instruction },
	{{0xf7, 1, "RST", none}, unimplemented_instruction },
	{{0xf8, 1, "RM", none}, unimplemented_instruction }, // return if sign bit is 1
	/*
		the 16 bits of data held in the H,L registers replaces the contents
		of the stack pointer.  The contents of H,L are unchanged
	*/
	{{0xf9, 1, "SPHL", none}, unimplemented_instruction },
	/*
		if sign bit is one, jump
	*/
	{{0xfa, 3, "JM", address}, unimplemented_instruction },
	{{0xfb, 1, "EI", none}, unimplemented_instruction },  // enable interupts (sets INTE flip-flop
	{{0xfc, 3, "CM", address}, unimplemented_instruction }, // call if minus (sign bit is 1)
	{{0xfd, 1, "UNKNOWN", none}, unimplemented_instruction },
	/*
		byte compared with accumulator
		performed by internally subtracting data from accumulator
		using two's complement arithmetic, leaving accumulator unchanged.
		zero bit is set if qualtities are equal, reset if unequal

		since a subtract operation is performed, the carry bit will be set
		if there is no carry out of bit 7 indicating the immediate data is
		greater than the contents of the accumulator), and reset otherwise
	*/
	{{0xfe, 2, "CPI", immediate}, unimplemented_instruction },
	{{0xff, 1, "RST", none}, unimplemented_instruction }
};

cpufunc get_cpu_function(CPU *cpu) {
	MACHINE* m = inst_set+cpu->memory[cpu->pc];
	return m->impl;
}

/*
	returns the length of the next instruction (where pc is pointing to)
*/
int get_instruction_length(CPU *cpu) {
	return inst_set[cpu->memory[cpu->pc]].inst.length;
}

OPCODE_INFO get_opcode_info(uint8_t opcode) {
	return inst_set[opcode].inst;
}




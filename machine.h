
#ifndef _MACHINE_H_
#define _MACHINE_H_

#include "cpu.h"


typedef enum {
	none,
	address,
	immediate
} inst_op_type;

typedef struct opcode {
	unsigned char opcode;
	int length;
	const char* mnemonic;
	inst_op_type op_type;
} OPCODE_INFO;

typedef int (*cpufunc)(CPU*, const INSTRUCTION *);

/*
	returns the function that implements the next 
	instruction (pointed to by cpu->pc).  

	This function does NOT advance the PC.
*/
cpufunc get_cpu_function(CPU *cpu);

/*
	returns the length of the next instruction (where pc is pointing to)
*/
int get_instruction_length(CPU *cpu);

OPCODE_INFO get_opcode_info(uint8_t opcode);

#endif

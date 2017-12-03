

#ifndef _CPU_H_
#define _CPU_H_

#include <stdint.h>

typedef struct _cond_bits {
	char carry:1;
	char one:1;			// always 1
	char parity:1;
	char alwayszero:1;  	// always 0
	char aux_carry:1;
	char alwayszero2:1;	// always 0
	char zero:1;
	char sign:1;
} CONDITION_FLAGS;



#define REG_B 0
#define REG_C 1
#define REG_D 2
#define REG_E 3
#define REG_H 4
#define REG_L 5
#define OP_M 6 // not really a register but tells us to use HL to access memory
#define REG_A 7

typedef enum {
	PAIR_B,
	PAIR_D,
	PAIR_H
} REGISTER_PAIR;



typedef struct {
	CONDITION_FLAGS flags;
	uint16_t pc; // program counter
	uint16_t sp; // stack pointer
	int8_t registers[8];

	uint8_t* stack;
	uint8_t* memory;	
} CPU;

#define ADDRESS_FROM_REGISTER(l,h) \
	

typedef enum {
	none,
	address,
	immediate
} inst_op_type;

typedef struct instruction {
	unsigned char opcode;
	int length;
	const char* mnemonic;
	inst_op_type op_type;
} INSTRUCTION;


#define EMFUNC(_name) int _name(CPU *cpu, const INSTRUCTION *inst)

/*
	create and initialize a CPU struct
*/
CPU* initialize_cpu();

EMFUNC(mov);
EMFUNC(inr);
EMFUNC(cmc);
EMFUNC(stc);
EMFUNC(dcr); // TODO: not sure how to calculate aux carry
EMFUNC(cma);



#endif


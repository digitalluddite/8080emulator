

#ifndef _CPU_H_
#define _CPU_H_

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

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


typedef struct instruction {
	uint8_t opcode;
	uint8_t operand1;
	uint8_t operand2;
} INSTRUCTION;


#define EMFUNC(_name) int _name(CPU *cpu, const INSTRUCTION *inst)

/*
	create and initialize a CPU struct
*/
CPU* initialize_cpu();
void free_cpu(CPU *cpu);

EMFUNC(cmc);
EMFUNC(stc);
EMFUNC(dcr); // TODO: not sure how to calculate aux carry
EMFUNC(inr);
EMFUNC(cma);

EMFUNC(mov);

#ifdef __cplusplus
}
#endif

#endif


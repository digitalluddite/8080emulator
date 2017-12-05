
#include <stdlib.h>
#include <strings.h>
#include "cpu.h"


CPU *initialize_cpu () {
	CPU *cpu = (CPU*)malloc(sizeof(CPU));
	bzero(cpu, sizeof(CPU));
	cpu->flags.one = 1;
	cpu->pc = 0;
	cpu->sp = 0;
	cpu->memory = (uint8_t*)malloc(0x10000);
	return cpu;
}

void free_cpu(CPU *cpu) {
	free(cpu->memory);
	free(cpu);	
}


static int calc_parity_bit(uint8_t byte) {
	int i = 0; 
	int counter = 0; 
	for (i = 0 ; i < 8 ; ++i) {
		counter += (byte >> i) & 1;
	}
	return (counter%2 == 0);
}


static int8_t get_address_from_pair(CPU *cpu, REGISTER_PAIR pair) {
	uint16_t addr = 0x0000;
	uint8_t lo, hi;

	switch (pair) {
		case PAIR_B:
			lo = REG_C;
			hi = REG_B;
			break;
		case PAIR_D:
			lo = REG_E;
			hi = REG_D;
			break;
		case PAIR_H:
			lo = REG_L;
			hi = REG_H;
			break;
	}
	addr |= cpu->registers[lo];
	return addr |= (cpu->registers[hi] << 8);	
}


static int8_t get_memory(CPU* cpu, uint16_t address) {
	return (int8_t)cpu->memory[address];
}

static void set_memory(CPU* cpu, uint16_t address, uint8_t val) {
	cpu->memory[address] = val;
}



int mov (CPU *cpu, const INSTRUCTION *inst)
{
	return 0;
}


int inr (CPU *cpu, const INSTRUCTION *inst)
{
	uint8_t mask = 0x38; // 00111000B which gets us our registers
	int reg = (inst->opcode & mask) >> 3;
	// doesn't affect carry			
	int8_t val;
	if (reg == OP_M) {
		val = get_memory(cpu, get_address_from_pair(cpu, PAIR_H));
	} else 
		val = cpu->registers[reg];

	cpu->flags.aux_carry = ((val & 0xf) + 1 > 0xf);
	val += 1;
	cpu->flags.parity = calc_parity_bit(val);	
	cpu->flags.zero = (val == 0);
	cpu->flags.sign = (val < 0);

	if (reg == OP_M)
		set_memory(cpu, get_address_from_pair(cpu, PAIR_H), val);
	else
		cpu->registers[reg] = val;

	return 0;
}


int dcr (CPU *cpu, const INSTRUCTION *inst) {
	uint8_t mask = 0x38; // 00111000B which gets us our registers
	int reg = (inst->opcode & mask) >> 3;
	// doesn't affect carry			
	int8_t val;
	if (reg == OP_M) {
		val = get_memory(cpu, get_address_from_pair(cpu, PAIR_H));
	} else 
		val = cpu->registers[reg];

	// TODO:  I'm not sure how to set this
	cpu->flags.aux_carry = ((val & 0xf) + 1 > 0xf);
	val += 1;
	cpu->flags.parity = calc_parity_bit(val);	
	cpu->flags.zero = (val == 0);
	cpu->flags.sign = (val < 0);

	if (reg == OP_M)
		set_memory(cpu, get_address_from_pair(cpu, PAIR_H), val);
	else
		cpu->registers[reg] = val;

	return 0;
}


//  Complement carry - toggle carry bit
int cmc(CPU *cpu, const INSTRUCTION *inst)
{
	cpu->flags.carry = ~cpu->flags.carry;
	return 0;
}

// set carry -- set carry bit to one
int stc(CPU* cpu, const INSTRUCTION *inst)
{
	cpu->flags.carry = 1;
	return 0;
}

int cma(CPU* cpu, const INSTRUCTION *inst)
{
	cpu->registers[REG_A] = ~cpu->registers[REG_A];
	return 0;
}




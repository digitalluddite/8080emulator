
#include <stdio.h>

void print_bits(uint8_t b) {
	printf("%d%d%d%d %d%d%d%d",
			(b & (1 << 7)) >> 7,
			(b & (1 << 6)) >> 6,
			(b & (1 << 5)) >> 5,
			(b & (1 << 4)) >> 4,
			(b & (1 << 3)) >> 3,
			(b & (1 << 2)) >> 2,
			(b & (1 << 1)) >> 1,
			(b & (1)));
}

void dump_cpu_state(const CPU *cpu)
{
	printf("PC 0x%04X\n", cpu->pc);
	printf("SP 0x%04X\n", cpu->sp);
	printf("FLAGS\n");
	printf("\tCarry       %d\n", cpu->flags.carry);
	printf("\tParity      %d\n", cpu->flags.parity);
	printf("\tAux Carry   %d\n", cpu->flags.aux_carry);
	printf("\tZero        %d\n", cpu->flags.zero);
	printf("\tSign        %d\n", cpu->flags.sign);

	printf("\nRegisters\n");
	printf("\tB   %02X\n", cpu->registers[REG_B]);
	printf("\tC   %02X\n", cpu->registers[REG_C]);
	printf("\tD   %02X\n", cpu->registers[REG_D]);
	printf("\tE   %02X\n", cpu->registers[REG_E]);
	printf("\tH   %02X\n", cpu->registers[REG_H]);
	printf("\tL   %02X\n", cpu->registers[REG_L]);
	printf("\tA   %02X\n", cpu->registers[REG_A]);
}



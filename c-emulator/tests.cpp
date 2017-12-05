
#define CATCH_CONFIG_MAIN
#include "catch.hpp"

#include "cpu.h"
#include "machine.h"


#define INIT_INSTRUCTION(inst, op, op1, op2) \
INSTRUCTION inst = { op, op1, op2 }



TEST_CASE("Simple test to see what happens", "[foo]") {
	CPU *cpu = initialize_cpu();
	INIT_INSTRUCTION(inst, 0x3f, 0, 0);

	SECTION("Simple test") {
		cmc(cpu, &inst);
		printf("carry = %02x\n", cpu->flags);
		REQUIRE(cpu->flags.carry == 1);
	}
	SECTION("Simple test") {
		cpu->flags.carry = 0;
		cmc(cpu, &inst);
		REQUIRE(cpu->flags.carry == 0);
	}

	free_cpu(cpu);
}









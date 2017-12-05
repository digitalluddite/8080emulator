

#include <stdio.h>
#include <stdint.h>




#ifdef _TEST_
int main () {
	uint8_t i;
	for (i = 0 ; i <= 0xff ; ++i) {
		printf("%02X\t", i); print_bits(i); printf("\n");
		if (i == 0xff) break;
	}
}
#endif



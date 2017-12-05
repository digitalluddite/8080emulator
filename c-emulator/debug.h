#ifndef _DEBUG_H_
#define _DEBUG_H_

#ifdef __cplusplus
extern "C" {
#endif

#include "cpu.h"
#include "machine.h"

void debug_console(const CPU *cpu);

#ifdef __cplusplus
}
#endif

#endif



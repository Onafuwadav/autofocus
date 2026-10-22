// Hardware settings. Every value here is a placeholder for the rebuilt
// firmware: check each one against the actual build before powering anything.
#pragma once

// Stepper driver (STEP/DIR/EN interface, e.g. A4988, DRV8825 or TMC2209).
#define PIN_STEP 3
#define PIN_DIR  4
#define PIN_EN   5      // active low

// Step pulse spacing (microseconds) at full speed and at the start/end of a move.
#define STEP_US_FAST 400
#define STEP_US_SLOW 2000
#define RAMP_STEPS   50

// Refuse single moves larger than this (microsteps) as a safety limit.
#define MAX_STEPS_PER_MOVE 20000L

// Piezo: 12-bit MCP4725 DAC on I2C feeding the analogue input of the piezo
// amplifier. 0..4095 maps linearly onto 0..PIEZO_RANGE_NM of travel; any
// gain needed to reach the amplifier's input range is done in hardware.
#define DAC_I2C_ADDR   0x60
#define PIEZO_RANGE_NM 100000L   // 100 um travel

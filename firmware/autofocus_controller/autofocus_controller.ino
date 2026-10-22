// Autofocus axis controller: stepper (coarse) + piezo via DAC (fine).
//
// RECONSTRUCTION. The original firmware was lost. This sketch rebuilds the
// control scheme described in the dissertation (Chapter 6): a host PC scores
// camera frames, and a microcontroller drives a stepper/lead screw for coarse
// focus and a piezo objective positioner for fine focus, using a hill climb.
// Pin numbers, the DAC, travel and step sizes are placeholders: set them in
// config.h to match the hardware before use.
//
// Serial protocol (115200 baud, one command per line, one reply per command):
//   ?              -> POS <stepper_steps> <piezo_nm>
//   C <steps>      -> OK C <stepper_steps>      relative stepper move (microsteps)
//   F <nm>         -> OK F <piezo_nm>           absolute piezo position
//   A <step> <min> -> OK A                      start an on-board fine hill climb
//                                               (piezo step and stop step, nm)
//   S <score>      -> STEP F <nm> | DONE F <nm> feed the score of the latest frame
//                                               to the hill climb
//   X              -> OK X                      abort hill climb, hold position
//   E <0|1>        -> OK E <0|1>                stepper driver enable
// Errors reply "ERR <reason>".

#include <Wire.h>
#include "config.h"

// ---------------------------------------------------------------- piezo DAC

static long piezoNm = PIEZO_RANGE_NM / 2;

static void dacWrite(uint16_t code) {
  // MCP4725 "fast write": two bytes, 12-bit value.
  Wire.beginTransmission(DAC_I2C_ADDR);
  Wire.write((code >> 8) & 0x0F);
  Wire.write(code & 0xFF);
  Wire.endTransmission();
}

static void setPiezo(long nm) {
  if (nm < 0) nm = 0;
  if (nm > PIEZO_RANGE_NM) nm = PIEZO_RANGE_NM;
  piezoNm = nm;
  dacWrite((uint16_t)((nm * 4095L) / PIEZO_RANGE_NM));
}

// ------------------------------------------------------------------ stepper

static long stepperPos = 0;

static void stepperMove(long steps) {
  digitalWrite(PIN_DIR, steps >= 0 ? HIGH : LOW);
  long n = steps >= 0 ? steps : -steps;
  // Trapezoidal-ish ramp: start slow, speed up, slow down for the last steps.
  for (long i = 0; i < n; i++) {
    long fromEdge = min(i, n - 1 - i);
    unsigned int us = STEP_US_FAST;
    if (fromEdge < RAMP_STEPS)
      us = STEP_US_SLOW - (unsigned int)((long)(STEP_US_SLOW - STEP_US_FAST) * fromEdge / RAMP_STEPS);
    digitalWrite(PIN_STEP, HIGH);
    delayMicroseconds(4);
    digitalWrite(PIN_STEP, LOW);
    delayMicroseconds(us);
  }
  stepperPos += steps;
}

// --------------------------------------------------- on-board hill climb
//
// The host sends the score of each frame. The MCU keeps the best position so
// far and steps the piezo. A worse score reverses direction and halves the
// step. The climb finishes when the step drops below the minimum, and the
// piezo returns to the best position.

static bool climbing = false;
static bool haveBest = false;
static long bestNm, stepNm, minStepNm;
static int direction;
static float bestScore;

static void climbStart(long step, long minStep) {
  climbing = true;
  haveBest = false;
  stepNm = step;
  minStepNm = minStep;
  direction = 1;
}

// Returns true when the climb has finished.
static bool climbFeed(float score) {
  if (!haveBest) {  // first score belongs to the starting position
    haveBest = true;
    bestNm = piezoNm;
    bestScore = score;
  } else if (score > bestScore) {
    bestNm = piezoNm;
    bestScore = score;
  } else {
    direction = -direction;
    stepNm /= 2;
  }
  while (stepNm >= minStepNm) {
    long next = bestNm + direction * stepNm;
    if (next >= 0 && next <= PIEZO_RANGE_NM) {
      setPiezo(next);
      return false;
    }
    direction = -direction;  // hit the end of travel
    stepNm /= 2;
  }
  setPiezo(bestNm);
  climbing = false;
  return true;
}

// ------------------------------------------------------------ serial parser

static char line[48];
static uint8_t len = 0;

static void handle(char *cmd) {
  char op = cmd[0];
  char *arg = cmd + 1;
  switch (op) {
    case '?':
      Serial.print(F("POS ")); Serial.print(stepperPos);
      Serial.print(' '); Serial.println(piezoNm);
      break;
    case 'C': {
      long steps = atol(arg);
      if (labs(steps) > MAX_STEPS_PER_MOVE) { Serial.println(F("ERR too far")); break; }
      stepperMove(steps);
      Serial.print(F("OK C ")); Serial.println(stepperPos);
      break;
    }
    case 'F':
      setPiezo(atol(arg));
      Serial.print(F("OK F ")); Serial.println(piezoNm);
      break;
    case 'A': {
      char *end;
      long step = strtol(arg, &end, 10);
      long minStep = strtol(end, NULL, 10);
      if (step <= 0 || minStep <= 0) { Serial.println(F("ERR args")); break; }
      climbStart(step, minStep);
      Serial.println(F("OK A"));
      break;
    }
    case 'S':
      if (!climbing) { Serial.println(F("ERR not climbing")); break; }
      Serial.print(climbFeed(atof(arg)) ? F("DONE F ") : F("STEP F "));
      Serial.println(piezoNm);
      break;
    case 'X':
      climbing = false;
      Serial.println(F("OK X"));
      break;
    case 'E': {
      int on = atoi(arg);
      digitalWrite(PIN_EN, on ? LOW : HIGH);  // driver enable is active low
      Serial.print(F("OK E ")); Serial.println(on ? 1 : 0);
      break;
    }
    default:
      Serial.println(F("ERR unknown"));
  }
}

void setup() {
  pinMode(PIN_STEP, OUTPUT);
  pinMode(PIN_DIR, OUTPUT);
  pinMode(PIN_EN, OUTPUT);
  digitalWrite(PIN_EN, LOW);
  Wire.begin();
  setPiezo(PIEZO_RANGE_NM / 2);
  Serial.begin(115200);
  Serial.println(F("READY autofocus_controller"));
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\r') continue;
    if (c == '\n') {
      line[len] = '\0';
      if (len) handle(line);
      len = 0;
    } else if (len < sizeof(line) - 1) {
      line[len++] = c;
    }
  }
}

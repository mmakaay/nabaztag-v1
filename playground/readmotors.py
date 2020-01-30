#!/usr/bin/env python3

# Motor 0 = left ear 
# Motor 1 = right ear
# Motorvalue
#   0 = off
#   1 = forward (in sequence pointing top, forward, down and backward)
#   2 = backward (in sequence pointing top, back, down and forward)

# Registers
R_MOTOR = 0x0a
R_MOTION = 0x0b
R_VAL_CURRENT = 0x0c
R_VAL_NEW = 0x03
R_COUNTER = 0x04
R_COLOR = 0x05
R_EORVAL = 0x06
R_BRIGHTNESS = 0x07
R_LED_ID = 0x08
R_TRANSITION = 0x09

# Operations
NOP = 0x70
MOTOR = 0xae
MOTOR_ARGS = 0xab
MOTORGET = 0xc0
WAIT = 0x7e
JUMP = 0x9c
CMP = 0x92
BNE = 0x9e
INC = 0x81
EOR = 0x8c
PALETTE = 0xa8
SET_LED = 0xa7
COPY_REGISTER = 0x86
SEND = 0xc4

app = [
    NOP,
    R_MOTOR, 0, R_MOTION, 0, MOTOR, MOTOR_ARGS, # @ 0x0012 turn motor 0 off
    R_MOTOR, 1, R_MOTION, 0, MOTOR, MOTOR_ARGS, # @ 0x0018 turn motor 1 off
    R_MOTOR, 0, R_MOTION, 0, MOTOR, MOTOR_ARGS, # @ 0x001e turn motor 0 on, forward
    MOTORGET, 0xca,                               # @ 0x0024
    R_COUNTER, 0,                                 # @ 0x0026
    R_COLOR, 1,                                   # @ 0x0028

    WAIT, 1,                       # @ 0x002a
    MOTORGET, 0x3a,                # @ 0x002c
    SEND, 0xc3,                    # @ 0x002e
    #CMP, 0xc3,                     # @ 0x0030
    #BNE, 0x00, 0x3a,               # @ 0x0032 jump on new value for motor
    #INC, R_COUNTER,                # @ 0x0035
    JUMP, 0x00, 0x2a,              # @ 0x0037

    R_EORVAL, 2,                   # @ 0x003a
    EOR, 0x56,                     # @ 0x003c alternates between color 1 and 3
    R_COUNTER, 0,                  # @ 0x003e reset counter
    COPY_REGISTER, 0xc3, 
    R_BRIGHTNESS, 255,
    PALETTE, R_COLOR, R_BRIGHTNESS,
    R_LED_ID, 4,
    R_TRANSITION, 0,
    SET_LED, R_LED_ID, R_TRANSITION,
    JUMP, 0x00, 0x2a           # loop
]

# ----------------------------------------------------------------------

from nabaztag.bytecode import Response, BytecodeFrame

bytecode = BytecodeFrame(program_code=app)
response = Response().add(bytecode)
message = response.build()

with open("readmotors.bin", "wb") as f:
    f.write(bytes(message))

#!/usr/bin/env python3

app = [
    # 0x0011
    0x70,
    0x09, 0x01,         # R9 = 1 (motor state)
    0x05, 0x00,         # R5 = 0 (motor id)
    0xae, 0x59,         # set_motor(R5, R9), start motor
    0xc0, 0x65,         # R6 = get_motor(R5), init current value

    # 0x001a
    0x86, 0x76,         # R7 = R6
    0x08, 0x00,         # R8 = 0 (counter)

    # 0x001e
    0xc0, 0x65,         # R6 = get_motor(R5)
    0x92, 0x76,         # Compare R6 (new) to R7 (current)
    0x9e, 0x00, 0x2c,   # R6 != R7? Jump!
    0x81, 0x08,         # R8++
    0x7e, 0x01,         # WAIT
    0x9c, 0x00, 0x1e,   # loop

    # 0x002c
    # The counter is about 6 per tick on the encoder in this code.
    # Based on some experimentation, I get the following detection values:
    # - threshold 0 - 6 : consistent ticks
    # - threshold 7 - 7 : bad gap detection (occasional false positive)
    # - threshold 8 - 26 : consistent gap detection
    # - threshold 27 - *  : no gap detection 
    # Based on these outcomes, I went for a threshold of 16, which so far
    # has proven to work very well.
    0x09, 0x10,         # R9 = 10 (decoder threshold for hole detection)
    0x92, 0x89,         # Compare R8 (counter) to R9 (threshold)
    0xa1, 0x00, 0x1a,   # R8 (counter) < R9 (threshold)? Return, do next!

    0x81, 0x0a,         # RA = RA + 1 (color)
    0x0b, 0xff,         # RB = 255 (brightness)      
    0x0c, 0x04,         # RC = 4 (LED id)
    0x0d, 0x00,         # RD = 0 (duration)
    0xa8, 0xab,         # initialize color
    0xa7, 0xcd,         # set LED to color

    # Stop motor
    0x09, 0x00,         # R9 = 0 (motor state)
    0x05, 0x00,         # R5 = 0 (motor id)
    0xae, 0x59,         # set_motor(R5, R9), stop motor

    0x9c, 0x00, 0x1a    # Return, do next!
]

# ----------------------------------------------------------------------

from nabaztag.response import Response, BytecodeFrame

bytecode = BytecodeFrame(program_code=app)
response = Response().add(bytecode)
message = response.build()

with open("readmotors2.bin", "wb") as f:
    f.write(bytes(message))

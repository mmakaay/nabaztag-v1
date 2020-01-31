#!/usr/bin/env python3

app = [
    0x00, 0x00,
    0x01, 0x01, 
    0x02, 0x00,         # R2 = 0
    0xc0, 0x02,         # R0 = set to motor value, R2 = motor ID 0
    0x02, 0x01,         # R2 = 1
    0xc0, 0x12,         # R1 = set to motor value, R2 = motor ID 1
    0xc4, 0x01,         # Send R0 + R1 to server
    0x7e, 0x01,         # WAIT
    0x9c, 0x00, 0x11    # loop
]

# ----------------------------------------------------------------------

from nabaztag.bytecode import Response, BytecodeFrame

bytecode = BytecodeFrame(program_code=app)
response = Response().add(bytecode)
message = response.build()

with open("syncmotors.bin", "wb") as f:
    f.write(bytes(message))

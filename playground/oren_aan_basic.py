#!/usr/bin/env python3

loop = [
    0x7f, 0x00,         # R0 = random byte
    0x7f, 0x01,         # R1 = random byte
    0x7f, 0x02,         # R2 = random byte
    0x04, 0x00,
    0x05, 0x05,
    0xa7, 0x45,
    0x04, 0x02,
    0xa7, 0x45,

    # 0x021
    0x00, 0x00,         # R0 = 0
    0x01, 0x01,         # R1 = 1
    0xae, 0x01,         # MOTOR R0 (0) to R1 (1) -> ear 1 direction 1
    0x00, 0x01,         # R0 = 1
    0x01, 0x02,         # R1 = 2
    0xae, 0x01,         # MOTOR R0 (1) to R1 (1) -> ear 2 direction 2
    0x7f, 0x03,         # R3 = random byte
    0x33, 0x1f,         # R3 = R3 & 31 (limits random range 0 - 31)
    0x7d, 0x03,         # wait random steps 
    0x00, 0x00,         # R0 = 0
    0x01, 0x02,         # R1 = 2
    0xae, 0x01,         # MOTOR R0 (0) to R1 (0) -> ear 1 direction 2
    0x00, 0x01,         # R0 = 1
    0x01, 0x01,         # R1 = 1
    0xae, 0x01,         # MOTOR R0 (1) to R1 (0) -> ear 2 direction 1
    0x7f, 0x03,         # R3 = random byte
    0x33, 0x1f,         # R3 = R3 & 31 (limits random range 0 - 31)
    0x7d, 0x03,         # wait random steps 
    0x9c, 0x00, 0x21    # jump to start of loop
]

app = [
    *loop,
]

# ----------------------------------------------------------------------

from nabaztag.bytecode import Response, BytecodeFrame

bytecode = BytecodeFrame(program_code=app)
response = Response().add(bytecode)
message = response.build()

with open("oren_aan_basic.bin", "wb") as f:
    f.write(bytes(message))

#!/usr/bin/env python3

from nabaztag.bytecode import Response, BytecodeFrame

message = Response().build()

with open("really_nop.bin", "wb") as f:
    f.write(bytes(message))

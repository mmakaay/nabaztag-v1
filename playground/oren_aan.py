#!/usr/bin/env python3

from nabaztag.bytecode import Response, BytecodeFrame

start = 0x11

on_button_down = [
    0x00, 0x06,         # R0 = 1 (color)
    0x01, 0x40,         # R1 = 64 (brightness)
    0xa8, 0x01,         # init color
    0x04, 0x01,         # R4 = 1 (LED id)
    0x05, 0x02,         # R5 = 0 (transition time)
    0xa7, 0x45,         # turn LED on
    0x72                # RTI
]

on_button_up = [
    0x00, 0x00,         # R0 = 0
    0x01, 0x00,         # R1 = 0
    0x02, 0x00,         # R2 = 0
    0x04, 0x01,         # R4 = 1 (LED id)
    0x05, 0x02,         # R5 = 0 (transition time)
    0xa7, 0x45,         # turn LED off
    0x72                # RTI
]

loop = [
    0x00, 0x00,         # R0 = 0
    0x01, 0x02,         # R1 = 2
    0xae, 0x01,         # MOTOR R0 (0) to R1 (1) -> ear 1 direction 1
    0x00, 0x01,         # R0 = 1
    0x01, 0x02,         # R1 = 2
    0xae, 0x01,         # MOTOR R0 (1) to R1 (1) -> ear 2 direction 2
    0x7f, 0x03,         # R3 = random byte
    0x33, 0x1f,         # R3 = R3 & 31 (limits random range 0 - 31)
    0x7d, 0x03,         # wait random steps 
    0x00, 0x00,         # R0 = 0
    0x01, 0x01,         # R1 = 1
    0xae, 0x01,         # MOTOR R0 (0) to R1 (0) -> ear 1 direction 2
    0x00, 0x01,         # R0 = 1
    0x01, 0x01,         # R1 = 1
    0xae, 0x01,         # MOTOR R0 (1) to R1 (0) -> ear 2 direction 1
    0x7f, 0x03,         # R3 = random byte
    0x33, 0x1f,         # R3 = R3 & 31 (limits random range 0 - 31)
    0x7d, 0x03,         # wait random steps 
    0x9c, 0x00, 0x00    # jump to start of loop
]

setup = [
    # Install interrupt handlers
    0x00, 0x00,         # R0 = 0 (press push button interrupt)
    0x9a, 0x00, 0x00, 0x00,
    0x00, 0x01,         # R0 = 1 (release push button interrupt)
    0x9a, 0x00, 0x00, 0x00,

    # Set bottom LED to random color.
    0x7f, 0x00,         # R0 = random byte
    0x7f, 0x01,         # R1 = random byte
    0x7f, 0x02,         # R2 = random byte
    0x05, 0x00,         # R5 = 0 (transition time)
    0x04, 0x00,         # R4 = 0 (LED id)
    0xa7, 0x45,         # turn LED on

    # Turn other LEDs off.
    0x00, 0x00,         # R0 = 0 (black, off)
    0x01, 0x00,         # R1 = 0 (brightness)
    0xa8, 0x01,         # init color
    0x04, 0x01,         # R4 = 1 (LED id)
    0xa7, 0x45,         # turn LED off
    0x04, 0x02,         # R4 = 2 (LED id)
    0xa7, 0x45,         # turn LED off
    0x04, 0x03,         # R4 = 3 (LED id)
    0xa7, 0x45,         # turn LED off
    0x04, 0x04,         # R4 = 4 (LED id)
    0xa7, 0x45,         # turn LED off
]

setup_addr = start
loop_addr = setup_addr + len(setup)
on_button_down_addr = loop_addr + len(loop)
on_button_up_addr = on_button_down_addr + len(on_button_down)

# Update jump addresses.
loop[-2] = loop_addr & 0xff00
loop[-1] = loop_addr & 0x00ff
setup[4] = on_button_down_addr & 0xff00
setup[5] = on_button_down_addr & 0x00ff
setup[10] = on_button_up_addr & 0xff00
setup[11] = on_button_up_addr & 0x00ff

app = [
    *setup,
    *loop,
    *on_button_down,
    *on_button_up
]

# ----------------------------------------------------------------------

bytecode = BytecodeFrame(program_code=app)
response = Response().add(bytecode)
message = response.build()

with open("oren_aan.bin", "wb") as f:
    f.write(bytes(message))

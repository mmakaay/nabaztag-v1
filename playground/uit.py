#!/usr/bin/env python3

code = [
    0x70,
    0x00, 0x00,
    0x01, 0x00,
    0x02, 0x00,
    0x05, 0x00,         # R5 = 0 (transition time)
    0x04, 0x00,         # R4 = 0 (LED id)
    0xa7, 0x45,         # turn LED off
    0x04, 0x01,         # R4 = 1 (LED id)
    0xa7, 0x45,         # turn LED off
    0x04, 0x02,         # R4 = 2 (LED id)
    0xa7, 0x45,         # turn LED off
    0x04, 0x03,         # R4 = 3 (LED id)
    0xa7, 0x45,         # turn LED off
    0x04, 0x04,         # R4 = 4 (LED id)
    0xa7, 0x45,         # turn LED off

    0x00, 0x00,         # R0 = 0
    0x01, 0x00,         # R1 = 0
    0xae, 0x01,         # MOTOR 
    0x00, 0x01,         # R0 = 1
    0x01, 0x00,         # R1 = 0
    0xae, 0x01,         # MOTOR

    0x7e, 0x40,         # WAIT 64
    0x9c, 0x00, 0x11    # loop
]

def itobin3(i):
    return [i & 0xff0000, i & 0x00ff00, i & 0x0000ff]

def itobin4(i):
    return [i & 0xff000000, i & 0x00ff0000, i & 0x0000ff00, i & 0x000000ff]

def assemble(app, id=1, priority=1):

    frame = [
        0x05,
        *itobin3(len(app) + 4 + 8 + 15), # 4 size, 8 music, 15 overhead
        *map(ord, "amber"),
        *itobin4(id),
        priority,
        *itobin4(len(app)),
        *app,

        # No music
        0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 
        0,
        *map(ord, "mind")
    ]

    checksum = compute_checksum(frame)
    frame[-5] = checksum

    result = [0x7f, *frame, 0xff]
    print(repr(result))

    with open("uit.bin", "wb") as f:
        f.write(bytes(result))


def compute_checksum(bytecode):
    byte_total = 0
    for b in bytecode:
        byte_total += b
        if byte_total > 256:
            byte_total -= 256 
    checksum = 255 - byte_total
    if checksum < 0:
        checksum = 256 + checksum
    return checksum

assemble(code)

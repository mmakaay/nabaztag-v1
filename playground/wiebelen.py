#!/usr/bin/env python3

code = [
    # 0x0011
    0xb2,               # stop midi
    0xb0,               # stop audio
    0x00, 0x40,         # R0 = 64
    0xb7, 0x00,         # set master volume to R0
    0xb6, 0x00,         # set app volume to R0
    0x00, 0x00,         # R0 = 0
    0xaf, 0x00,         # start audio file R0
    # 0x001d
    0x7e, 0x01,         # wait 1
    0xc1, 0x00,         # R0 = music status
    0x85, 0x00,         # test R0
    0x9e, 0x00, 0x1d,   # if R0 != 0, then jump back

    0x00, 0x01,         # R0 = 1
    0x01, 0x40,         # R1 = 64
    0xa8, 0x01,         # init color
    0x05, 0x20,         # R5 = 32
    0x04, 0x04,         # R4 = 4
    0xa7, 0x45,         # turn LED 4 on

    # 0x0032
    0x7e, 0x05,         # WAIT
    0x9c, 0x00, 0x32    # loop back
]

def itobin3(i):
    return [i >> 16 & 0xff, i >> 8 & 0xff, i & 0xff]

def itobin4(i):
    return [i >> 24 & 0xff, i >> 16 & 0xff, i >> 8 & 0xff, i & 0xff]

def assemble(app, audio, id=1, priority=1):

    frame = [
        0x05,
        *itobin3(len(app) + 4 + 12 + len(audio) + 15), # 4 size, 8 music, 15 overhead
        *map(ord, "amber"),
        *itobin4(id),
        priority,
        *itobin4(len(app)),
        *app,

        # Audio
        0x00, 0x00, 0x00, 0x01, 
        *itobin4(len(audio)),
        *audio, 
        0x00, 0x00, 0x00, 0x00,

        0,
        *map(ord, "mind")
    ]

    checksum = compute_checksum(frame)
    frame[-5] = checksum

    result = [0x7f, *frame, 0xff]

    with open("wiebelen.bin", "wb") as f:
        f.write(bytes(result))


def compute_checksum(bytecode):
    byte_total = sum(bytecode) % 256
    checksum = (255 - byte_total)%256
    return checksum

f = open("ping.vox", "rb")
vox = f.read()
f.close()

assemble(code, vox)

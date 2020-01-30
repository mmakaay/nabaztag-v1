import re
from nabaztag.exceptions import UnknownOpcodeError, InvalidOperandsError


# In the opcoe definitions below, the supported opcodes are described.
#
# The main level is a dictionary, in which the keys are the opcode
# mnemonics and the values are lists that describe the possible forms
# in which the opcode can be used.
#
# Multiple forms are allowed, to make it possible to use the same opcode
# in multiple ways. This allows for example the use of the "LD" opcode
# for both "LD_ri" and "LD_rr" from the original specification.
#
# Each operand form is described using a tuple, with the follow fields:
#
#   1. operand typing
#   2. bytecode for the operation
#   3. description
#   4. description of 1st operand (optional)
#   5. description of 2nd operand (optional)
#   r. description of 3rd operand (optional)
#
# For field 1 (operand typing), the following types are recognized:
#
#   o  No operands
#   r  Register: R0 .. R15 (Note: R15 is used as the stack pointer)
#   i  8-bit integer: 0 - 255 / 0x0 - 0xff / 0b0 - 0b11111111
#   w  16-bit address: a @symbolic_pointer, 0-65535, 0x0-0xffff
#
# Various combinations of these types are possible (limited by the
# specification). Combinations are expressed by concatenating multiple
# types, e.g. a combination of a register and an integer operand is
# represented by "ri".

OPCODES = {
    'LD': [
        ('ri', 0x00, 'Load a register with the value of byte integer',
            'Register to load the value into',
            'Integer byte value to load'),
        ('rr', 0x86, 'Load a register with the value of anothe register',
            'Register to copy the value to',
            'Register to copy the value from')],
    'ADD': [
        ('ri', 0x10, 'Add the value of an integer to a register',
            'Register to add the integer to',
            'Integer byte value to add to the register'),
        ('rr', 0x87, 'Add the value of a register to a register',
            'Register to add the register to',
            'Register to add to the first register')],
    'SUB': [
        ('ri', 0x20, 'Subtract the value of the integer from the register',
            'Register to subtract the integer from',
            'Integer byte value to subtract from the register'),
        ('rr', 0x88, 'Subtract the value of a register from a register',
            'Register to subtract the register from',
            'Register to subtract from the first register')],
    'AND': [
        ('ri', 0x30, 'Set register to the logical AND of register and integer',
            'Register to perform the AND on',
            'Integer byte value to apply'),
        ('rr', 0x8a, 'Set register to the logical AND of two registers',
            'Register to perform the AND on',
            'Register to apply')],
    'OR': [
        ('ri', 0x40, 'Set register to the logical OR of register and integer',
            'Register to perform the OR on',
            'Integer byte value to apply'),
        ('rr', 0x8b, 'Set register to the logical OR of two registers',
            'Register to perform the OR on',
            'Register to apply')],
    'LDR': [
        ('ri', 0x50, 'Load a register with a byte from the RAM',
            'Register to load the value into',
            'Integer byte indicating the RAM address to load'),
        ('rr', 0x94, 'Load a register with a byte from the RAM',
            'Register to load the value into',
            'Register that indicates the RAM address to load'),
        ('rir', 0x95, 'Load a register with a byte from the RAM',
            'Register to load the value into',
            'Integer defining a base offset in the RAM',
            'Register defining an additional offset from the base offset')],
    'STR': [
        ('ri', 0x60, 'Store a register in the RAM',
            'Register to store in the RAM',
            'Integer byte indicating the RAM address to use for storage'),
        ('rr', 0x96, 'Store a register in the RAM',
            'Register to store in the RAM',
            'Register that indicates the RAM address to use for storage'),
        ('rir', 0x97, 'Store a register in the RAM',
            'Register to store in the RAM',
            'Integer defining a base offset in the RAM for storage',
            'Register defining an additional offset from the base offset')],
    'NOP': [
        ('o', 0x70, 'No operation')],
    'RTI': [
        ('o', 0x72, 'Return from interrupt, pops PC, CC, CMP1, CMP2 from stack')],
    'CLRCC': [
        ('o', 0x73, 'Clear CC (carry bit)')],
    'SETCC': [
        ('o', 0x74, 'Set CC (carry bit)')],
    'ADDCC': [
        ('rr', 0x75, 'Add the value of two registers and carry to CC',
            'Register to add the second register to',
            'Register to add to the first register')],
    'SUBCC': [
        ('rr', 0x76, 'Subtract the value of two registers and carry to CC',
            'Register to subtract the second register from',
            'Register to subtract from the first register')],
    'INCW': [
        ('rr', 0x77, 'Increment 16-bit counter, consisting of the two registers',
            'Register that forms the most significant byte of the counter',
            'Register that forms the least significant byte of the counter')],
    'DECW': [
        ('rr', 0x78, 'Decrement 16-bit counter, consisting of the two registers',
            'Register that forms the most significant byte of the counter',
            'Register that forms the least significant byte of the counter')],
    'MULW': [
        ('rr', 0x79, 'Multiply two registers and store results in them',
            'Register that forms the most significant byte of the result',
            'Register that forms the least significant byte of the result')],
    'INPUTRST': [
        ('r', 0x7a, 'Resets an interrupt handler',
            'Register that holds the number of the interrupt to reset')],
    'INT': [
        ('r', 0x7b, 'Cause a software interrupt',
            'Register that holds the number of the interrupt to trigger')],
    'WAIT': [
        ('r', 0x7d, 'Wait a number of steps before continuing',
            'Wait value register (number of steps to wait)'),
        ('i', 0x7e, 'Wait a number of steps before continuing',
            'Wait value integer (number of steps to wait)')],
    'RND': [
        ('r', 0x7f, 'Set a register to an 8-bit random value',
            'The register to set')],
    'DEC': [
        ('r', 0x80, 'Decrement a register with a value of 1',
            'Register to decrement')],
    'INC': [
        ('r', 0x81, 'Increment a register with a value of 1',
            'Register to increment')],
    'CLR': [
        ('r', 0x82, 'Clear a register value by setting it to 0',
            'The register to clear')],
    'NEG': [
        ('r', 0x83, 'Reverse the sign of a register',
            'The register for which to switch the sign')],
    'NOT': [
        ('r', 0x84, 'Perform a logical NOT on a register (bits 0->1 and 1->0)',
            'The register to modify')],
    'TST': [
        ('r', 0x85, 'Test register (Cmp1 becomes register value, Cmp2 becomes 0)',
            'The register to test')],
    'MUL': [
        ('rr', 0x89, 'Multiply two registers',
            'Register to store the result to',
            'Register to multiply the first register by')],
    'EOR': [
        ('rr', 0x8c, 'Set register to the logical EXCLUSIVE OR of two registers',
            'Register to perform the EXLUSIVE OR on',
            'Register to apply')],
    'LSL': [
        ('rr', 0x8d, 'Perform a logical shift left on a register',
            'Register to logical shift to the left',
            'Register defining the number of bits to shift')],
    'LSR': [
        ('rr', 0x8e, 'Perform a logical shift right on a register',
            'Register to logical shift to the right',
            'Register defining the number of bits to shift')],
    'ASR': [
        ('rr', 0x8f, 'Perform an arithmatic shift right on a register',
            'Register to arithmatic shift to the right',
            'Register defining the number of bits to shift')],
    'ROL': [
        ('rr', 0x8d, 'Perform a left rotate on a register',
            'Register to rotate to the left',
            'Register defining the number of bits to rotate')],
    'ROR': [
        ('rr', 0x8e, 'Perform a right rotate on a register',
            'Register to rotate to the right',
            'Register defining the number of bits to rotate')],
    'CMP': [
        ('rr', 0x92, 'Compare two registers (combine with BNE, BGT, etc.)',
            'The register to compare (stored in Cmp1)',
            'The register to compare to (stored in Cmp2)')],
    'BIT': [
        ('rr', 0x93, 'Perform a logical AND between two registers, without update',
            'The first register for the bit test',
            'The second register for the bit teset')],
    'LDT': [
        ('rrw', 0x98, 'Load a register with the i-th value of a table',
            'Register to load the value into',
            'Register that defines the offset in the table',
            'Address that points at the table')],
    'LDTW': [
        ('rw', 0x99, 'Load a register with the i-th value of a table, i = R3+R4',
            'Register to load the value into',
            'Address that points at the table')],
    'INPUT': [
        ('rw', 0x9a, 'Set the address of an interrupt handler',
            'Register that indicates the interrupt number',
            'Address that points at the interrupt handler code')],
    'RTIJ': [
        ('w', 0x9b, 'Return from interrupt, with a jump',
            'Address to jump to')],
    'BRA': [
        ('w', 0x9c, 'Branch always: unconditional jump to address',
            'The address to jump to')],
    'BEQ': [
        ('w', 0x9d, 'Branch if equal, jump if Cmp1 = Cmp2',
            'The address to jump to')],
    'BNE': [
        ('w', 0x9e, 'Branch if not equal, jump if Cmp1 <> Cmp2',
            'The address to jump to')],
    'BGT': [
        ('w', 0x9f, 'Branch if greater than, jump if Cmp1 > Cmp2 (signed)',
            'The address to jump to')],
    'BGE': [
        ('w', 0xa0, 'Branch if greater of equal, jump if Cmp1 >= Cmp2 (signed)',
            'The address to jump to')],
    'BLT': [
        ('w', 0xa1, 'Branch if less than, Jump if Cmp1 < Cmp2 (signed)',
            'The address to jump to')],
    'BLE': [
        ('w', 0xa2, 'Branch if less than or equal, jump if Cmp1 <= Cmp2 (signed)',
            'The address to jump to')],
    'BHI': [
        ('w', 0xa3, 'Branch on higher than, jump if Cmp1 > Cmp2 (unsigned)',
            'The address to jump to')],
    'BHS': [
        ('w', 0xa4, 'Branch on higher than or same, jump when Cmp1 >= Cmp2 (unsigned)',
            'The address to jump to')],
    'BLO': [
        ('w', 0xa5, 'Branch on lower, jump if Cmp1 < Cmp2 (unsigned)',
            'The address to jump to')],
    'BLS': [
        ('w', 0xa6, 'Branch on lower or same, jump if Cmp1 <= Cmp2 (unsigned)',
            'The address to jump to')],
    'LED': [
        ('rr', 0xa7, 'Modifies the state of a LED',
            'LED number register (0: bottom, 1:left, 2:mid, 3:right, 4:nose',
            'Transition register, defining the transition time in steps')],
    'PALETTE': [
        ('rr', 0xa8, 'Fills R0, R1, R2 with a color.',
            'Color register (e.g. 0:off, 1:green, 2:yellow, ...)',
            'Intensity register (0:off .. 255:very clear)')],
    'PUSH': [
        ('ii', 0xaa, 'Push registers onto stack',
            'Byte, representing CC, R14, .. R8 (bitwise, bit on: do push)',
            'Byte, representing C7 .. R0 (bitwise, bit on: do push)')],
    'PULL': [
        ('ii', 0xab, 'Pull registers from stack',
            'Byte, representing CC, R14, .. R8 (bitwise, bit on: do pull)',
            'Byte, representing C7 .. R0 (bitwise, bit on: do pull)')],
    'BSR': [
        ('w', 0xac, 'Branch to subroutine, push PC onto stack and jump to address',
            'The address to jump to')],
    'RTS': [
        ('o', 0xad, 'Return from subroutine, pops PC from stack')],
    'MOTOR': [
        ('rr', 0xae, 'Motor control',
            'Motor number register (0: left, 1: right)',
            'Direction register (0: stop, 1: forward, 2: reverse)')],
    'MIDIPLAY': [
        ('r', 0xaf, 'Start the MIDI player on an audio file',
            'Register indicating the audio file number to play')],
    'MIDISTOP': [
        ('o', 0xb0, 'Stop the MIDI player')],
    'WAVPLAY': [
        ('r', 0xb1, 'Start the ADPCM player on an audio file',
            'Register indicating the audio file number to play')],
    'WAVSTOP': [
        ('o', 0xb2, 'Stop the ADPCM player')],
    'MSEC': [
        ('rr', 0xb3, 'Returns a 16-bit time value in milliseconds',
            'Register to hold the most significant byte',
            'Register to hold the least significant byte')],
    'SEC': [
        ('rr', 0xb4, 'Returns a 16-bit time value in seconds',
            'Register to hold the most significant byte',
            'Register to hold the least significant byte)')],
    'BUT3': [
        ('r', 0xb5, 'Load a register with the 3-state button state (0, 1, 2)',
            'Register to load the state into')],
    'VOL': [
        ('r', 0xb6, 'Adjust the application volume',
            'Register holding the application volume to apply')],
    'MVOL': [
        ('r', 0xb7, 'Adjst the master volume',
            'Register holding the master volume to apply')],
    'PUSHBUTTON': [
        ('r', 0xb8, 'Load a register with the pushbutton state (0, 1)',
            'Register to load the state into')],
    'SRC': [
        ('rr', 0xb9, 'Load a register with the i-th source RAM value',
            'Register to load the source RAM value into',
            'Register holding the source RAM address to load')],
    'BRAT': [
        ('rw', 0xba, 'Branch always to an address from a table',
            'Register holding the offset to use for the table',
            'Address holding the address of the table')],
    'BSRT': [
        ('rw', 0xbb, 'Branch to a subroutine at an address from a table',
            'Register holding the offset to use for the table',
            'Address holding the address of the table')],
    'OSC': [
        ('rr', 0xbc, 'Load a register with 128 * (1 - cos(r2) * pi / 128)',
            'Register to load the result into',
            'Register that holds the value of r2 in this computation')],
    'INV': [
        ('rr', 0xbd, 'Load two registers with the result of 65536 / r2',
            'Register to hold the most significant result byte',
            'Register that provides r1, and holds the least significant result byte')],
    'DIV': [
        ('rr', 0xbe, 'Load two registers with the result of 256 * r1/r2',
            'Register that provides r1 and holds the most significant result byte',
            'Register that provides r2 and holds the least significant result byte')],
    'HSV': [
        ('o', 0xbf, 'HSV -> RGB conversion on R0, R1, R2')],
    'MOTORGET': [
        ('rr', 0xc0, 'Set register to the motor encoder value',
            'Register to load the value in',
            'Motor number register (0: left, 1: right)')],
    'MUSIC': [
        ('r', 0xc1, 'Get music player status (0: off, 1: playing, 2:loading)',
            'Register to load the player status into')],
    'DOWNLOAD': [
        ('r', 0xc2, 'Get network status (bit 1: downloading, bit 2: requesting)',
            'Register to load the network status into')],
    'SEND': [
        ('rr', 0xc4 , 'Send 16-bit value to server, also triggers a download',
            'Register that holds the most significant byte',
            'Register that holds the least significant byte')],
    'SENDREADY': [
        ('r', 0xc5, 'Load sending machine status (1: ready to send)',
            'Register to load the sending machine status into')],
    'LASTPING': [
        ('rr', 0xc6, 'Get 16-bit time in seconds since last server contact',
            'Register to hold the most significant result byte',
            'Register to hold the least significant result byte')]
}


def parse_instruction(opcode, operands):
    opcode, specs = _get_opcode_specs(opcode)
    spec, parsed_operands = _parse_operands(specs, opcode, operands)

    return opcode, spec[1], spec[0], parsed_operands


def _get_opcode_specs(opcode):
    """Retrieve the opcode specifications that match the provided opcode.
       This returns a list of options, because some opcodes can take
       multiple forms of input. E.g. LD, which can be used to load an integer
       value into a register (LD R5, 10) or a register into another register
       (LD R6, R5).
       When the opcode is unknown, an UnknownOpcodeError is raised."""
    try:
        opcode = opcode.upper()
        specs = OPCODES[opcode]
        return opcode, specs
    except KeyError:
        raise UnknownOpcodeError(opcode)


def _parse_operands(specs, opcode, operands):
    """Go over all available specs. The first one for which the provided
       operands match the operand types from the spec is returned.
       When none of the specs match the operands, an exception is raised."""
    for spec in specs:
        # Check for no operands.
        if spec[0] == 'o':
            if operands:
                continue
            return spec, []

        # Check for mismatch in number of operands.
        if len(spec[0]) != len(operands):
            continue

        # Check if the type definition(s) matches the operand(s).
        parsed_operands = []
        operands_match = True
        for i, expected_type in enumerate(spec[0]):
            o = operands[i]
            parsed_operand = _try_parse_operand(expected_type, o)
            if parsed_operand is None:
                operands_match = False
                break
            parsed_operands.append(parsed_operand)
        if operands_match:
            return spec, parsed_operands

    raise InvalidOperandsError(opcode, operands)


SYMBOLIC_ADDRESS = re.compile('^@(__local\d|[a-zA-Z])\S*$')
REGISTER = re.compile('^R(?:[0-9]|1[0-5])$')

def _try_parse_operand(expected_type, operand):
    try:
        if expected_type == 'i':
            value = int(operand, 0)
            if value >= 0x00 and value <= 0xff:
                return ('integer', value)
        elif expected_type == 'w':
            if SYMBOLIC_ADDRESS.match(operand):
                return ('symbol', operand)
            value = int(operand, 0)
            if value >= 0x0000 and value <= 0xffff:
                return ('address', value)
        elif expected_type == 'r':
            if REGISTER.match(operand):
                value = int(operand[1:], 0)
                return ('register', value)
    except ValueError:
        pass
    return None


def get_instruction_size(instruction):
    opcode_type = instruction[2]
    if opcode_type == 'o':
        return 1
    elif opcode_type in ['i', 'r', 'ri', 'rr']:
        return 2
    elif opcode_type in ['ii', 'rir', 'w']:
        return 3
    elif opcode_type in ['rw', 'rrw']:
        return 4
    else:
        raise NotImplementedError("opcode type '%s'" % opcode_type)


def instruction_to_bytecode(instruction):
    _, opcode, opcode_type, operands = instruction
    if opcode_type == 'o':
        # Not operands, just an opcode.
        yield opcode
    elif opcode_type == 'i':
        # An 8-bit integer. The operand byte stores the integer value.
        yield opcode
        yield operands[0][1]
    elif opcode_type == 'r':
        # A register. The 4 least significant bytes of the operand byte
        # store the register.
        yield opcode
        yield operands[0][1]
    elif opcode_type == 'ri':
        # The opcode uses the 4 most significant bits. The 4 least
        # significant bits store the register. The integer value is
        # added as the second byte.
        yield opcode + operands[0][1]
        yield operands[1][1]
    elif opcode_type == 'rr':
        # Two registers. The first uses the 4 most significant bits of
        # the operand, the second uses the 4 least significant bits.
        yield opcode
        yield (operands[0][1] << 4) + (operands[1][1] & 0x0f)
    elif opcode_type == 'ii':
        # Two integers. The first uses the first and the second uses the
        # second operand byte.
        yield opcode
        yield operands[0][1]
        yield operands[1][1]
    elif opcode_type == 'rir':
        # Two registers and an integer. The first byte of the operand
        # combines the two register (just like with 'rr'), the second
        # operand byte holds the integer value.
        yield opcode
        yield (operands[0][1] << 4) + operands[2][1]
        yield operands[1][1]
    elif opcode_type == 'w':
        # A 16-byte address, stored in two bytes, BigEndian order.
        yield opcode
        yield operands[0][1] >> 8 & 0xff
        yield operands[0][1] >> 0 & 0xff
    elif opcode_type == 'rw':
        # A register and a 16-byte address. The register is stored in the
        # 4 least significant bits of the first operand byte. The address
        # is stored in the following two operand bytes (just like with 'w').
        yield opcode
        yield operands[0][1]
        yield operands[1][1] >> 8 & 0xff
        yield operands[1][1] >> 0 & 0xff
    elif opcode_type == 'rrw':
        # Two registers and a 16-byte address. The first operand byte
        # combines the two registers (just like with 'rr'). The address
        # is stored in the following two operand bytes (just like with 'w').
        yield opcode
        yield (operands[0][1] << 4) + operands[1][1]
        yield operands[2][1] >> 8 & 0xff
        yield operands[2][1] >> 0 & 0xff
    else:
        raise NotImplementedError("opcode type '%s'" % opcode_type)

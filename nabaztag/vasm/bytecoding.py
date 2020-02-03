from nabaztag.exceptions import UnresolvedSymbolError, AsmEmptyError
from nabaztag.vasm.opcodes import \
        parse_instruction, get_instruction_size, instruction_to_bytecode


# The entrypoint for bytecode that is run on the Nabaztag.
ENTRYPOINT = 0x0011


def ast_to_bytecode(preprocessed, ast):
    program_code = _create_program_code(ast)
    music_data = _create_music_data(preprocessed)
    return program_code + music_data

def _create_program_code(ast):
    if not ast:
        raise AsmEmptyError()
    _create_entrypoint(ast)
    symbol_table = _make_symbol_table(ast)
    _resolve_symbols(ast, symbol_table)
    bytecode = _turn_instructions_into_bytecode(ast)
    return _as_4_bytes(len(bytecode)) + bytecode

def _create_entrypoint(ast):
    """Inject a fragment of code at the very start of the code tree,
       which handles jumping to the @main symbol.
       Also adds a NOP to the start of the code, since that is done
       by all 3rd party byte code that I found."""
    entrypoint = []
    first_symbol = list(ast.keys())[1]
    if ast[first_symbol][0][0] != 'NOP':
        entrypoint.append(parse_instruction('NOP', []))
    if list(ast.keys())[1] != '@Main':
        entrypoint.append(parse_instruction('BRA', ['@Main']))
    ast["entrypoint"] = entrypoint

def _make_symbol_table(ast):
    """Create a symbol table that map symbols to their respective addresses."""
    pointer = ENTRYPOINT
    symbol_table = dict()
    for _, (symbol, block) in enumerate(ast.items()):
        symbol_table[symbol] = pointer
        pointer += _get_block_size(block)
    return symbol_table

def _get_block_size(block):
    """Compute the byte size of a code block."""
    return sum((get_instruction_size(i[1], i[2]) for i in block))

def _resolve_symbols(ast, symbol_table):
    """Go over the syntax tree, and try to resolve all values of
       type 'symbol' into actual addresses."""
    for _, (symbol, block) in enumerate(ast.items()):
        for instruction in block:
            for i, (t, symbol) in enumerate(instruction[3]):
                if t == 'symbol':
                    if symbol not in symbol_table:
                        raise UnresolvedSymbolError(symbol)
                    instruction[3][i] = ('address', symbol_table[symbol])

def _turn_instructions_into_bytecode(ast):
    bytecode = []
    for block in ast.values():
        for instruction in block:
            bytecode.extend(instruction_to_bytecode(instruction))
    return bytecode

def _create_music_data(preprocessed):
    count = 0
    data = []
    offsets = []
    for _, _, music_file in preprocessed.music_files.values():
        count += 1
        data.extend(music_file)
        offsets.extend(_as_4_bytes(len(data)))
    return _as_4_bytes(count) + offsets + data

def _as_4_bytes(i):
    """Return the value of the provided integer as an array of 4 bytes."""
    return [
        i >> 0x18 & 0xff,
        i >> 0x10 & 0xff,
        i >> 0x08 & 0xff,
        i >> 0x00 & 0xff
    ]

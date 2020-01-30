from nabaztag.exceptions import UnresolvedSymbolError, AsmEmptyError
from nabaztag.asm.opcodes import \
        parse_instruction, get_instruction_size, instruction_to_bytecode


# The entrypoint for bytecode that is run on the Nabaztag.
ENTRYPOINT = 0x0011


def ast_to_bytecode(ast):
    if not ast:
        raise AsmEmptyError()
    _create_entrypoint(ast)
    table = _make_symbol_table(ast)
    _resolve_symbols(ast, table)
    bytecode = _make_bytecode(ast)
    return bytecode

def _create_entrypoint(ast):
    """Inject a fragment of code at the very start of the code tree,
       which handles jumping to the @main symbol.
       Also adds a NOP to the start of the code, since that is done
       by all 3rd party byte code that I found."""
    entrypoint = [parse_instruction('NOP', [])]
    if list(ast.keys())[1] != '@main':
        entrypoint.append(parse_instruction('BRA', ['@main']))
    ast["entrypoint"] = entrypoint

def _make_symbol_table(ast):
    """Create a table that map symbols to their respective addresses."""
    pointer = ENTRYPOINT
    table = dict()
    for _, (symbol, block) in enumerate(ast.items()):
        table[symbol] = pointer
        pointer += _get_block_size(block)
    return table

def _get_block_size(block):
    """Compute the byte size of a code block."""
    return sum((get_instruction_size(i) for i in block))

def _resolve_symbols(ast, table):
    """Go over the syntax tree, and try to resolve all values of
       type 'symbol' into actual addresses."""
    for _, (symbol, block) in enumerate(ast.items()):
        for instruction in block:
            for i, (t, symbol) in enumerate(instruction[3]):
                if t == 'symbol':
                    if symbol not in table:
                        raise UnresolvedSymbolError(symbol)
                    instruction[3][i] = ('address', table[symbol])

def _make_bytecode(ast):
    bytecode = []
    for _, (_, block) in enumerate(ast.items()):
        for instruction in block:
            bytecode.extend(instruction_to_bytecode(instruction))
    return bytecode
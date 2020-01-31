import re
from collections import OrderedDict
from nabaztag.exceptions import NabaztagException, AsmSyntaxError
from nabaztag.asm.opcodes import parse_instruction


SYMBOL = re.compile('^(@\S*)\s*$')
SPLITTER = re.compile('(?:\s*,\s*|\s+)')


def parse(preprocessed):
    """Take lines of instructions and code sources as provided by the
       preprocessor and parse their contents into an abstract syntax tree."""
    ast = OrderedDict()
    ast["entrypoint"] = []
    instructions = None

    for line, src_nr, line_nr in preprocessed.lines:
        def syntax_error(msg):
            location = "%s:%d" % (preprocessed.sources[src_nr], line_nr)
            raise AsmSyntaxError(msg, location)

        # Handle the start of a new symbol.
        if SYMBOL.match(line):
            symbol = SYMBOL.search(line)[1]
            if symbol == '@':
                syntax_error("empty @symbol name")
            if symbol in ast:
                syntax_error("duplicate use of @symbol: %s" % symbol)
            instructions = []
            ast[symbol] = instructions
            continue

        if instructions is None:
            syntax_error("no @symbol defined before instruction")

        # Handle line of opcode.
        opcode, *operands = SPLITTER.split(line)
        try:
            instruction = parse_instruction(opcode, operands)
            instructions.append(instruction)
        except NabaztagException as e:
            syntax_error(str(e))

    return ast

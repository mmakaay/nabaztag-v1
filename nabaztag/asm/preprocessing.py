import re
import os.path
from collections import OrderedDict
from nabaztag.exceptions import AsmIncludeNotFound

PATH = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'includes')
]

def add_include_path(path):
    path = os.path.abspath(path)
    PATH = [path, *PATH]

def preprocess(path):
    lines, sources, _ = _load(path)
    return lines, sources

DEFINE = re.compile('^define (\S+) (.+)$')
GLOBAL_MACRO = re.compile('^[^a-zA-Z]*[A-Z]')
IMPORT = re.compile('^include (\S+)$')

def _load(path, sources=[], macros=OrderedDict()):
    local_macros = OrderedDict()
    line_nr = 0
    lines = []

    # Check if the source file was already included.
    if path in sources:
        return lines, sources, macros
    source_nr = len(sources)
    sources.append(path)

    src = open(path)
    new_macros = False
    new_local_macros = False
    for line in src:
        line_nr += 1
        line = _normalize_input(line)

        # Skip empty lines.
        if line == "":
            continue

        # Handle include.
        if IMPORT.match(line):
            matches = IMPORT.search(line)
            name = matches[1]
            include_path = _find_import_file(name)
            if include_path is None:
                raise AsmIncludeNotFound(name, path, line_nr)
            include_lines, sources, macros = _load(include_path, sources, macros)
            lines.extend(include_lines)
            continue

        # Handle macro definition.
        # Two kinds of macros are supported: global and local.
        # Global macros are identified by the fact that the first letter
        # in the macro is upper case (e.g. "Lalala", "%MY_CONSTANT", "123OK").
        # All other macros are local and will only be applied within the
        # context of the source file that is currently being processed.
        if DEFINE.match(line):
            matches = DEFINE.search(line)
            find = matches[1]
            replace = matches[2]
            if GLOBAL_MACRO.match(find):
                macros[find] = replace
                new_macros = True
            else:
                local_macros[find] = replace
                new_local_macros = True
            continue

        # When new macros have been defined, sort the macros
        # by length of the macro name, so longest matches will
        # be applied first.
        if new_macros:
            by_len = sorted(macros.items(), key=lambda x: -len(x[0]))
            macros = OrderedDict(by_len)
            new_macros = False
        if new_local_macros:
            by_len = sorted(local_macros.items(), key=lambda x: -len(x[0]))
            local_macros = OrderedDict(by_len)
            new_local_macros = False

        line = _apply_macros(line, local_macros, macros)
        lines.append((line, source_nr, line_nr))

    src.close()
    lines = _mangle_local_symbols(lines)
    return lines, sources, macros

COMMENTS = re.compile('\s*#.*$')
TRIMMABLE_WHITESPACE = re.compile('(^\s+|\s+$)')
WHITESPACE = re.compile('\s+')

def _normalize_input(line):
    line = COMMENTS.sub('', line)
    line = TRIMMABLE_WHITESPACE.sub('', line)
    line = WHITESPACE.sub(' ', line)
    return line

def _find_import_file(name):
    for path in PATH:
        path = os.path.join(path, name + ".basm")
        if os.path.exists(path):
            return path
    return None

def _apply_macros(line, local_macros, macros):
    orig_line = ""
    while orig_line != line:
        orig_line = line
        for find, replace in local_macros.items():
            line = line.replace(find, replace)
        for find, replace in macros.items():
            line = line.replace(find, replace)
    return line

LOCAL_SYMBOL = re.compile('^@[a-z]\S*$')
SPLITTER = re.compile('(?:\s*,\s*|\s+)')
MANGLE_ID = 0

def _mangle_local_symbols(lines):
    global MANGLE_ID
    MANGLE_ID+=1

    # Pass 1: mangle all local symbols that are defined.
    # These are the ones that appear on a line by their own.
    local_symbols = dict()
    for i, (line, path, line_nr) in enumerate(lines):
        if LOCAL_SYMBOL.match(line):
            rewrite = '@__local%d_%s' % (MANGLE_ID, line[1:])
            local_symbols[line] = rewrite
            lines[i] = (rewrite, path, line_nr)

    # Pass 2: mangle all local symbols that are used as operand
    # in an opcode and rewrite these, when we've seen a definition
    # for them in pass 1.
    for i, (line, path, line_nr) in enumerate(lines):
        if '@' not in line or LOCAL_SYMBOL.match(line):
            continue
        opcode, *operands = SPLITTER.split(line)
        for j, operand in enumerate(operands):
            mangled = False
            if operand in local_symbols:
                operands[j] = local_symbols[operand]
                mangled = True
            if mangled:
                rewrite = '%s %s' % (opcode, ', '.join(operands))
                lines[i] = (rewrite, path, line_nr)

    return lines
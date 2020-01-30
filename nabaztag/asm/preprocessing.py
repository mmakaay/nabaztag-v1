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

COMMENTS = re.compile('\s*#.*$')
TRIMMABLE_WHITESPACE = re.compile('(^\s+|\s+$)')
WHITESPACE = re.compile('\s+')
DEFINE = re.compile('^define (\S+) (.+)$')
IMPORT = re.compile('^include (\S+)$')

def _load(path, sources=[], macros=OrderedDict()):
    private_macros = OrderedDict()
    line_nr = 0
    lines = []

    # Check if the source file was already included.
    if path in sources:
        return lines, sources, macros
    source_nr = len(sources)
    sources.append(path)

    src = open(path)
    new_macros = False
    new_private_macros = False
    for line in src:
        line_nr += 1

        # Cleanup and normalize the line of input.
        line = COMMENTS.sub('', line)
        line = TRIMMABLE_WHITESPACE.sub('', line)
        line = WHITESPACE.sub(' ', line)

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
            i_lines, sources, macros = _load(include_path, sources, macros)
            lines.extend(i_lines)
            continue

        # Handle macro definition.
        if DEFINE.match(line):
            matches = DEFINE.search(line)
            macros[matches[1]] = matches[2]
            new_macros = True
            continue

        # WHen new macros have been defined, soft the macros
        # by length of the macro name, so longest matches will
        # be applied first.
        if new_macros:
            by_len = sorted(macros.items(), key=lambda x: -len(x[0]))
            macros = OrderedDict(by_len)
            new_macros = False

        line = _apply_macros(line, macros)
        lines.append((line, source_nr, line_nr))

    src.close()
    return lines, sources, macros

def _find_import_file(name):
    for path in PATH:
        path = os.path.join(path, name + ".basm")
        if os.path.exists(path):
            return path
    return None

def _apply_macros(line, macros):
    orig_line = ""
    while orig_line != line:
        orig_line = line
        for find, replace in macros.items():
            line = line.replace(find, replace)
    return line

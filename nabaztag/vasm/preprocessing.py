import re
from os.path import abspath, dirname, join as pathjoin, exists as pathexists
from random import randint
from collections import OrderedDict
from nabaztag.exceptions import \
    AsmFileNotFound, AsmMusicFileNotFound, AsmMusicFileConflict


COMMENTS = re.compile('\s*#.*$')
TRIMMABLE_WHITESPACE = re.compile('(^\s+|\s+$)')
WHITESPACE = re.compile('\s+')
MACRO = re.compile('^(\S+) EQU (.+)$', flags=re.IGNORECASE)
GLOBAL_MACRO = re.compile('^[^a-z0-9A-Z]*[A-Z]')
IMPORT = re.compile('^IMPORT (\S+)$', flags=re.IGNORECASE)
PUSHPULL = re.compile('^(PUSH|PULL) (.+)$', flags=re.IGNORECASE)
RAM_RESERVATION = re.compile('^(\S+) RMB (.+)$', flags=re.IGNORECASE)
MUSICFILE = re.compile('^music_file (\S+) (.+)$')
LOCAL_SYMBOL = re.compile('^@(?!__local_)[^a-z0-9A-Z]*[a-z0-9]\S*$')
SPLITTER = re.compile('\s+')
MUSIC_FILE_REF = re.compile('^music_file:(\S+)$')
EXTENSION = ".vasm"

# Bitcodes for the use of registers with the PUSH and PULL opcodes.
PUSHPULL_REGS = {
    'CC' : 0b1000000000000000, 'R14': 0b0100000000000000,
    'R13': 0b0010000000000000, 'R12': 0b0001000000000000,
    'R11': 0b0000100000000000, 'R10': 0b0000010000000000,
    'R9' : 0b0000001000000000, 'R8' : 0b0000000100000000,
    'R7' : 0b0000000010000000, 'R6' : 0b0000000001000000,
    'R5' : 0b0000000000100000, 'R4' : 0b0000000000010000,
    'R3' : 0b0000000000001000, 'R2' : 0b0000000000000100,
    'R1' : 0b0000000000000010, 'R0' : 0b0000000000000001
}

class Preprocessor():
    def __init__(self, src_path):
        """Instantiate a preprocessor for the provided source file."""
        self.src_path = src_path
        self._init_search_path()

    def _init_search_path(self):
        """Setup the default search path: source file path +
           the path to the package-provided source files."""
        get_dir = lambda p: dirname(abspath(p))
        self.path = [
            get_dir(self.src_path),
            abspath(pathjoin(get_dir(__file__), '../src'))
        ]

    def with_path(self, path):
        """Add an extra path to the preprocessor's paths, used for finding
           files that are imported from the source code (e.g. other source
           files or audio files).
           When adding a path, this one is added at the start of the
           already established path. Therefore files that can be
           found in this path will take precedence."""
        self.path.insert(0, path)
        return self

    def execute(self):
        """Run the preprocessor on the provided source file."""
        self._init_working_data()
        self._load(self.src_path)
        return self

    def _init_working_data(self):
        self.lines = []
        self.sources = []
        self.ram_pointer = 0
        self.macros = Macros()
        self.music_files = dict()
        self.mangle_rand = "%04x" % randint(0x1000, 0xffff)
        self.mangle_id = 0

    def _load(self, path, from_frame=None):
        full_path = self._find_file_in_path(path)
        if full_path is None:
            location = "preprocessor" if not from_frame else from_frame.location
            raise AsmFileNotFound(self.src_path, location)
        if self._already_loaded(full_path):
            return
        frame = StackFrame(path, len(self.sources))
        self.sources.append(path)

        with open(full_path) as src:
            for line in src:
                frame.line_nr += 1
                line = self._normalize_input(line)
                self._handle_empty_line(frame, line) or \
                self._handle_import(frame, line) or \
                self._handle_music_file(frame, line) or \
                self._handle_ram_reservation(frame, line) or \
                self._handle_define_macro(frame, line) or \
                self._handle_push_or_pull_line(frame, line) or \
                self._handle_other_line(frame, line)
        self._mangle_local_symbols()
        self._rewrite_music_file_labels()

    def _find_file_in_path(self, name):
        for path in self.path:
            path = pathjoin(path, name)
            if pathexists(path):
                return path
        return None

    def _already_loaded(self, path):
        return path in self.sources

    def _normalize_input(self, line):
        line = COMMENTS.sub('', line)
        line = TRIMMABLE_WHITESPACE.sub('', line)
        line = WHITESPACE.sub(' ', line)
        return line

    def _handle_empty_line(self, frame, line):
        return line == ""

    def _handle_import(self, frame, line):
        if not IMPORT.match(line):
            return False
        matches = IMPORT.search(line)
        name = matches[1] + EXTENSION
        full_path = self._find_file_in_path(name)
        if full_path is None:
            raise AsmFileNotFound(name, frame.location)
        self._load(full_path, frame)
        return True

    def _handle_music_file(self, frame, line):
        """Handle importing a music file into the code, referenced by
           a label, e.g. "music_file BOOP audio/boop.mid". The label is
           used to fill the operand register for the WAVPLAY and MIDIPLAY
           opcodes by referencing "music_file:<label>",
           e.g. "LD R0 music_file:BOOP"."""
        if not MUSICFILE.match(line):
            return False
        matches = MUSICFILE.search(line)
        label = matches[1]
        name = matches[2]
        full_path = self._find_file_in_path(name)
        if full_path is None:
            raise AsmMusicFileNotFound(label, name, frame.location)
        if label in self.music_files:
            if self.music_files[label][1] != full_path:
                raise AsmMusicFileConflict(label, frame.location)
            return True
        with open(full_path, "rb") as f:
            music_data = bytes(f.read())
        self.music_files[label] = (len(self.music_files), full_path, music_data)
        return True

    def _handle_ram_reservation(self, frame, line):
        """The pseudo-opcode "<label> RMB <bytelen>" (reserve memory block)
           can be used to reserve the requested number bytes in the RAM,
           and to make the <label> point to the position of that reserved
           space (0 - 255). The <label> can then be used with the STR and
           LDR opcodes as the RAM offset value."""
        match = RAM_RESERVATION.match(line)
        if not match:
            return False

        find = match[1]
        replace = str(self.ram_pointer)

        bytelen = int(match[2], 0)
        self.ram_pointer += bytelen

        macro_set = self.macros if GLOBAL_MACRO.match(find) else frame.macros
        macro_set.add(find, replace)
        return True

    def _handle_define_macro(self, frame, line):
        """The pseudo-opcode "<find> EQU <replace> (equate) can be used to
           define a simple macro. Two kinds of macros are supported: global
           and local. Global macros are identified by the fact that the first
           letter in the macro is upper case (e.g. "Lalala", "%MY_CONSTANT",
           "123OK"). All other macros are local and will only be applied
           within the context of the source file that is currently being
           processed."""
        if not MACRO.match(line):
            return False
        matches = MACRO.search(line)
        find = matches[1]
        replace = matches[2]
        macro_set = self.macros if GLOBAL_MACRO.match(find) else frame.macros
        macro_set.add(find, replace)
        return True

    def _handle_push_or_pull_line(self, frame, line):
        """The PUSH and PULL opcodes can be a bit tricky, since these
           require a two byte input, based on a bitwise pattern that describes
           the registers to push onto or pull from the stack. Here, additional
           syntax is implemented to allow for the following forms:
           PUSH/PULL ALL (equivalent to PUSH/PULL 255, 255),
           PUSH/PULL <Reg1>, <Reg2>, .., <RegN> (regs being: CC, R0 .. R14),
           PULL LAST (pulls the registers from the related PUSH)"""
        if not PUSHPULL.match(line):
            return False
        opcode, *operands = SPLITTER.split(line.upper())

        hi,lo = 0, 0
        if len(operands) == 1 and operands[0] == 'LAST' and frame.pushes:
            hi, lo = frame.pushes[-1]
        elif len(operands) == 1 and operands[0] == 'ALL':
            hi = 255
            lo = 255
        elif operands and all((o in PUSHPULL_REGS for o in operands)):
            regs = 0
            for o in operands:
                regs = regs | PUSHPULL_REGS[o]
            hi = regs >> 8
            lo = regs & 255
        else:
            return False
            
        if opcode == 'PUSH':
            frame.pushes.append((hi, lo))
        elif frame.pushes:
            frame.pushes.pop()

        line = "%s %d %d" % (opcode, hi, lo)
        self.lines.append((line, frame.source_nr, frame.line_nr))
        return True

    def _handle_other_line(self, frame, line):
        line = frame.macros.apply(line)
        line = self.macros.apply(line)
        self.lines.append((line, frame.source_nr, frame.line_nr))

    def _mangle_local_symbols(self):
        self.mangle_id += 1

        # Pass 1: mangle all local symbols that are defined.
        # These are the ones that appear on a line by their own.
        local_symbols = dict()
        for i, (line, path, line_nr) in enumerate(self.lines):
            if LOCAL_SYMBOL.match(line):
                rewrite = '@__local_%s_%d_%s' % (self.mangle_rand, self.mangle_id, line[1:])
                local_symbols[line] = rewrite
                self.lines[i] = (rewrite, path, line_nr)

        # Pass 2: mangle all local symbols that are used as operand
        # in an opcode and rewrite these, when we've seen a definition
        # for them in pass 1.
        for i, (line, path, line_nr) in enumerate(self.lines):
            if '@' not in line or LOCAL_SYMBOL.match(line):
                continue
            opcode, *operands = SPLITTER.split(line)
            for j, operand in enumerate(operands):
                mangled = False
                if operand in local_symbols:
                    operands[j] = local_symbols[operand]
                    mangled = True
                if mangled:
                    rewrite = '%s %s' % (opcode, ' '.join(operands))
                    self.lines[i] = (rewrite, path, line_nr)

    def _rewrite_music_file_labels(self):
        """Find all operands that look like a music_file:<label> reference,
           and replace them with the music file id for that <label>.
           The files that can be referenced must be registered in the
           source code using the "music_file <label> <path> directive."""
        for i, (line, path, line_nr) in enumerate(self.lines):
            if 'music_file:' not in line:
                continue
            opcode, *operands = SPLITTER.split(line)
            rewritten = False
            for j, operand in enumerate(operands):
                if MUSIC_FILE_REF.match(operand):
                    matches = MUSIC_FILE_REF.search(operand)
                    label = matches[1]
                    if label not in self.music_files:
                        location = "%s:%d" % (path, line_nr)
                        raise AsmMusicFileLabelUnknown(label, location)
                    operands[j] = str(self.music_files[label][0])
                    rewritten = True
                if rewritten:
                    rewrite = '%s %s' % (opcode, ' '.join(operands))
                    self.lines[i] = (rewrite, path, line_nr)


class Macros():
    """A container that holds a list of simple find/replace macros."""
    def __init__(self):
        self._macros = OrderedDict()
        self._modified = False

    def add(self, find, replace):
        """Add a new find/replace macro."""
        self._macros[find] = replace
        self._modified = True

    def apply(self, data):
        """Apply the find/replace macros to the provided input.
           Longer macros are applied before shorter macros."""
        if self._modified:
            by_len = lambda x: -len(x[0])
            self._macros = OrderedDict(sorted(self._macros.items(), key=by_len))
        for find, replace in self._macros.items():
            data = data.replace(find, replace)
        return data


class StackFrame():
    """A stack frame, used to remember data that is bound
       to a single source file. This is used to keep global data
       and local data separated on recursive source inclusions."""
    def __init__(self, path, source_nr):
        self.path = path
        self.source_nr = source_nr
        self.line_nr = 0
        self.macros = Macros()
        self.pushes = []

    @property
    def location(self):
        """A string, describing the current file position
          (<path>:<line number>)."""
        return "%s:%d" % (self.path, self.line_nr)

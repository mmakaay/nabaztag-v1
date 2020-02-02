class NabaztagException(Exception):
   pass

class AsmSyntaxError(NabaztagException):
    def __init__(self, msg, location):
        super().__init__("%s: %s" % (location, msg))

class AsmFileNotFound(NabaztagException):
    def __init__(self, name, location):
        super().__init__(
                "%s: File '%s' not found in search path" %
                (location, name))

class AsmMusicFileNotFound(NabaztagException):
    def __init__(self, label, name, location):
        super().__init__(
                "%s: Music file '%s' (label '%s') not found in search path" %
                (location, name, label))

class AsmMusicFileConflict(NabaztagException):
    def __init__(self, label, location):
        super().__init__(
            "%s: Duplicate use of music file label '%s'" %
            (location, label))

class AsmMusicFileLabelUnknown(NabaztagException):
    def __init__(self, label, location):
        super().__init__(
            "%s: unknown music file label '%s'" %
            (location, label))

class UnknownOpcodeError(NabaztagException):
    def __init__(self, opcode):
        super().__init__("Unknown opcode: %s" % opcode)

class UnknownBytecodeError(NabaztagException):
    def __init__(self, bytecode):
        super().__init__("Unknown bytecode: 0x%02x" % bytecode)

class InvalidOperandsError(NabaztagException):
    def __init__(self, opcode, operands):
        super().__init__(
                "Invalid operands for opcode %s: %s" %
                (opcode, ", ".join(operands)))

class UnresolvedSymbolError(NabaztagException):
    def __init__(self, symbol):
        super().__init__(
                "Cannot resolve symbol: %s" % symbol)

class AsmEmptyError(NabaztagException):
    def __init__(self):
        super().__init__("The assembly code is empty")

class ProgramEmptyError(NabaztagException):
    def __init__(self):
        super().__init__("The program code must not be empty")

class ProgramTooLargeError(NabaztagException):
    def __init__(self, size, max_size):
        super().__init__(
            "Program bytecode too large (%dB exceeds max size of %dB)" %
            (size, max_size))

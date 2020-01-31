class NabaztagException(Exception):
   pass

class AsmSyntaxError(NabaztagException):
    def __init__(self, msg, src, line_nr):
        super().__init__(
            "%s:%d: %s" %
            (src, line_nr, msg))

class AsmFileNotFound(NabaztagException):
    def __init__(self, name, frame):
        location = frame.location if frame else ""
        super().__init__(
                "%sFile '%s' not found in search path" % (location, name))

class AsmMusicFileNotFound(NabaztagException):
    def __init__(self, label, name, frame):
        location = frame.location if frame else ""
        super().__init__(
                "%sMusic file '%s' (label '%s') not found in search path" %
                (location, name, label))

class UnknownOpcodeError(NabaztagException):
    def __init__(self, opcode):
        super().__init__("Unknown opcode: %s" % opcode)


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
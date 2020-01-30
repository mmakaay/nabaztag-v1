class NabaztagException(Exception):
   pass

class AsmSyntaxError(NabaztagException):
    def __init__(self, msg, src, line_nr):
        super().__init__(
            "%s:%d: %s" %
            (src, line_nr, msg))

class AsmIncludeNotFound(NabaztagException):
    def __init__(self, name, src, line_nr):
        super().__init__(
                "%s:%d: Include '%s' not found in search path" %
                (src, line_nr, name))

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

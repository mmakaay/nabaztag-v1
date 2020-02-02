from nabaztag.exceptions import ProgramEmptyError, ProgramTooLargeError


AMBER = list(map(ord, "amber"))
MIND = list(map(ord, "mind"))
CHECKSUM_PLACEHOLDER = [0x00]
OPERATION_START = [0x7f]
OPERATION_SRCMOD = [0x04]
OPERATION_BYTECODE_FRAME = [0x05]
OPERATION_END = [0xff]
MAX_RESPONSE_SIZE = 0xffff


class Response():
    def __init__(self, operations=[]):
        self.operations = operations

    def add(self, operation):
        self.operations.append(operation)
        return self

    def build(self):
        response = OPERATION_START
        for o in self.operations:
            response += o.build()
        response += OPERATION_END

        # Temp disabled, I need to find out if this is related to the music
        # files as well, or only the program bytecode (I suspect the latter).
        #if len(response) > MAX_RESPONSE_SIZE:
        #    raise ProgramTooLargeError(len(response), MAX_RESPONSE_SIZE)

        return response

class SourcesModification():
    def __init__(self):
        raise NotImplementedError("Sources modification")


class BytecodeFrame():
    """This class implements a bytecode frame operation for the Nabaztag
       virtual machine. Such operation contains program code and optionally
       audio files (MIDI or ADPCM2)."""
    def __init__(self, bytecode=[], frame_id=1, priority=1):
        self.frame_id = frame_id
        self.priority = priority
        self.bytecode = bytecode

    def build(self):
        """Build the bytecode frame for the Nabaztag virtual machine."""
        payload = (
            AMBER +
            self._get_id_bytes() +
            self._get_priority_bytes() +
            self.bytecode +
            CHECKSUM_PLACEHOLDER +
            MIND
        )
        frame = (
            OPERATION_BYTECODE_FRAME +
            _as_3_bytes(len(payload)) +
            payload
        )
        self._add_checksum(frame)
        return frame

    def _get_id_bytes(self):
        frame_id = 1 if not self.frame_id else self.frame_id
        return _as_4_bytes(self.frame_id)

    def _get_priority_bytes(self):
        priority = 1 if not self.priority else self.priority
        return [priority]

    def _add_checksum(self, frame):
        """Add the checksum to the provided frame. The checksum is caculated
           so that the (byte)sum of all the bytes in the frame makes 255."""
        byte_sum = 0
        for b in frame:
            byte_sum = (byte_sum + b) & 0xff
        checksum = (255 - byte_sum) & 0xff
        frame[-5] = checksum


def _as_3_bytes(i):
    """Return the value of the provided integer as an array of 3 bytes."""
    return [
        i >> 0x10 & 0xff,
        i >> 0x08 & 0xff,
        i >> 0x00 & 0xff
    ]

def _as_4_bytes(i):
    """Return the value of the provided integer as an array of 4 bytes."""
    return [
        i >> 0x18 & 0xff,
        i >> 0x10 & 0xff,
        i >> 0x08 & 0xff,
        i >> 0x00 & 0xff
    ]


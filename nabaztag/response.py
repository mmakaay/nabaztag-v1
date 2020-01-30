class NabaztagException(Exception):
    pass


def as_3_bytes(i):
    """Return the value of the provided integer as an array of 3 bytes."""
    return [
        i >> 0x10 & 0xff,
        i >> 0x08 & 0xff,
        i >> 0x00 & 0xff
    ]


def as_4_bytes(i):
    """Return the value of the provided integer as an array of 4 bytes."""
    return [
        i >> 0x18 & 0xff,
        i >> 0x10 & 0xff,
        i >> 0x08 & 0xff,
        i >> 0x00 & 0xff
    ]


AMBER = list(map(ord, "amber"))
MIND = list(map(ord, "mind"))
ZERO_AS_4BYTES = as_4_bytes(0)
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

        if len(response) > MAX_RESPONSE_SIZE:
            raise NabaztagException(
                "Reponse message too large (%dB exceeds max size of %dB)" %
                (len(response) , MAX_RESPONSE_SIZE))

        return response

class SourcesModification():
    def __init__(self):
        raise NabaztagException("Not yet implemented")


class BytecodeFrame():
    """This class implements a bytecode frame operation for the Nabaztag
       virtual machine. Such operation contains program code and optionally
       audio files (midi or ADPCM2)."""
    def __init__(self, id=1, priority=1, program_code=[], audio_files=[]):
        self.id = id
        self.priority = priority
        self.program_code = program_code
        self.audio_files = audio_files 

    def build(self):
        """Build the bytecode frame for the Nabaztag virtual machine."""
        payload = (
            AMBER +
            self._get_id_bytes() +
            self._get_priority_bytes() +
            self._get_program_bytes() +
            self._get_audio_bytes() +
            CHECKSUM_PLACEHOLDER +
            MIND
        )
        frame = (
            OPERATION_BYTECODE_FRAME +
            as_3_bytes(len(payload)) +
            payload
        )
        self._add_checksum(frame)
        return frame

    def _get_id_bytes(self):
        id = 1 if not self.id else self.id
        return as_4_bytes(self.id)

    def _get_priority_bytes(self):
        priority = 1 if not self.priority else self.priority
        return [priority]

    def _get_program_bytes(self):
        if not self.program_code:
            raise NabaztagException("The program code must not be empty")
        return as_4_bytes(len(self.program_code)) + self.program_code

    def _get_audio_bytes(self):
        if not self.audio_files:
            self.audio_files = []
        bytes = as_4_bytes(len(self.audio_files))
        for audio_file in self.audio_files:
            bytes += as_3_bytes(len(audio_file)) + audio_file
        bytes += ZERO_AS_4BYTES
        return bytes

    def _add_checksum(self, frame):
        """Add the checksum to the provided frame. The checksum is caculated
           so that the (byte)sum of all the bytes in the frame makes 255."""
        byte_sum = 0
        for b in frame:
            byte_sum = (byte_sum + b) & 0xff
        checksum = (255 - byte_sum) & 0xff
        frame[-5] = checksum

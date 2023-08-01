# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

import kaitaistruct
from kaitaistruct import ReadWriteKaitaiStruct, KaitaiStream, BytesIO
from enum import Enum


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 9):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class EmliteData(ReadWriteKaitaiStruct):
    """EMOP data field is embedded in each EMOP frame (see emlite_frame.ksy).
    It contains a 3 byte object id (Obi) and a payload. The Obi identifies what
    the data in the payload relates to. A number of Obis and corresponding data
    are defined in the document "Meter and Smart Module Obis Commands iss1.5.pdf".
    """

    class ReadWriteFlags(Enum):
        read = 0
        write = 1
    def __init__(self, len_data, _io=None, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self.len_data = len_data

    def _read(self):
        self.format = self._io.read_bytes(1)
        if not (self.format == b"\x01"):
            raise kaitaistruct.ValidationNotEqualError(b"\x01", self.format, self._io, u"/seq/0")
        self.object_id = self._io.read_bytes(3)
        self.read_write = KaitaiStream.resolve_enum(EmliteData.ReadWriteFlags, self._io.read_u1())
        self.payload = self._io.read_bytes((self.len_data - 5))


    def _fetch_instances(self):
        pass


    def _write__seq(self, io=None):
        super(EmliteData, self)._write__seq(io)
        self._io.write_bytes(self.format)
        self._io.write_bytes(self.object_id)
        self._io.write_u1(self.read_write.value)
        self._io.write_bytes(self.payload)


    def _check(self):
        pass
        if (len(self.format) != 1):
            raise kaitaistruct.ConsistencyError(u"format", len(self.format), 1)
        if not (self.format == b"\x01"):
            raise kaitaistruct.ValidationNotEqualError(b"\x01", self.format, self._io, u"/seq/0")
        if (len(self.object_id) != 3):
            raise kaitaistruct.ConsistencyError(u"object_id", len(self.object_id), 3)
        if (len(self.payload) != (self.len_data - 5)):
            raise kaitaistruct.ConsistencyError(u"payload", len(self.payload), (self.len_data - 5))

    # NOTE: Following, not generated, manually added, TODO: replace with a subclass or wrapper that ads this
    def __str__(self):
        return (
            f"EmliteData(object_id={self.object_id.hex()},rw={self.read_write.value},"
            f"payload=[{self.payload.hex()}])"
        )
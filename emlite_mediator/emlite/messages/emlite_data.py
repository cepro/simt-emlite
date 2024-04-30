# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

import kaitaistruct
from kaitaistruct import ReadWriteKaitaiStruct, KaitaiStream
from enum import Enum


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 9):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class EmliteData(ReadWriteKaitaiStruct):
    """EMOP data field is embedded in each EMOP frame (see emlite_frame.ksy).
    Most (see default_rec) contain a 3 byte object id (Obi) and a payload.
    The Obi identifies what the data in the payload relates to. A number of
    Obis and corresponding payloads are defined in the document "Meter and 
    Smart Module Obis Commands iss1.5.pdf".
    """

    class ReadWriteFlags(Enum):
        read = 0
        write = 1

    class RecordFormat(Enum):
        default = 1
        profile_log_1 = 3
        profile_log_2 = 4
    def __init__(self, len_data, _io=None, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self.len_data = len_data

    def _read(self):
        self.format = KaitaiStream.resolve_enum(EmliteData.RecordFormat, self._io.read_u1())
        _on = self.format
        if _on == EmliteData.RecordFormat.default:
            pass
            self.message = EmliteData.DefaultRec(self.len_data, self._io, self, self._root)
            self.message._read()
        elif _on == EmliteData.RecordFormat.profile_log_1:
            pass
            self.message = EmliteData.ProfileLogRec(self.len_data, self._io, self, self._root)
            self.message._read()
        elif _on == EmliteData.RecordFormat.profile_log_2:
            pass
            self.message = EmliteData.ProfileLogRec(self.len_data, self._io, self, self._root)
            self.message._read()


    def _fetch_instances(self):
        pass
        _on = self.format
        if _on == EmliteData.RecordFormat.default:
            pass
            self.message._fetch_instances()
        elif _on == EmliteData.RecordFormat.profile_log_1:
            pass
            self.message._fetch_instances()
        elif _on == EmliteData.RecordFormat.profile_log_2:
            pass
            self.message._fetch_instances()


    def _write__seq(self, io=None):
        super(EmliteData, self)._write__seq(io)
        self._io.write_u1(self.format.value)
        _on = self.format
        if _on == EmliteData.RecordFormat.default:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteData.RecordFormat.profile_log_1:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteData.RecordFormat.profile_log_2:
            pass
            self.message._write__seq(self._io)


    def _check(self):
        pass
        _on = self.format
        if _on == EmliteData.RecordFormat.default:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(u"message", self.message._root, self._root)
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(u"message", self.message._parent, self)
            if (self.message.len_data != self.len_data):
                raise kaitaistruct.ConsistencyError(u"message", self.message.len_data, self.len_data)
        elif _on == EmliteData.RecordFormat.profile_log_1:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(u"message", self.message._root, self._root)
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(u"message", self.message._parent, self)
            if (self.message.len_data != self.len_data):
                raise kaitaistruct.ConsistencyError(u"message", self.message.len_data, self.len_data)
        elif _on == EmliteData.RecordFormat.profile_log_2:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(u"message", self.message._root, self._root)
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(u"message", self.message._parent, self)
            if (self.message.len_data != self.len_data):
                raise kaitaistruct.ConsistencyError(u"message", self.message.len_data, self.len_data)

    class DefaultRec(ReadWriteKaitaiStruct):
        """Default emlite data format (format 0x01) - most messages use this format."""
        def __init__(self, len_data, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root
            self.len_data = len_data

        def _read(self):
            self.object_id = self._io.read_bytes(3)
            self.read_write = KaitaiStream.resolve_enum(EmliteData.ReadWriteFlags, self._io.read_u1())
            self.payload = self._io.read_bytes((self.len_data - 5))


        def _fetch_instances(self):
            pass


        def _write__seq(self, io=None):
            super(EmliteData.DefaultRec, self)._write__seq(io)
            self._io.write_bytes(self.object_id)
            self._io.write_u1(self.read_write.value)
            self._io.write_bytes(self.payload)


        def _check(self):
            pass
            if (len(self.object_id) != 3):
                raise kaitaistruct.ConsistencyError(u"object_id", len(self.object_id), 3)
            if (len(self.payload) != (self.len_data - 5)):
                raise kaitaistruct.ConsistencyError(u"payload", len(self.payload), (self.len_data - 5))


    class ProfileLogRec(ReadWriteKaitaiStruct):
        """Profile log messages use this format (formats 0x03 and 0x04)."""
        def __init__(self, len_data, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root
            self.len_data = len_data

        def _read(self):
            self.timestamp = self._io.read_u4le()
            if (self.len_data > 5):
                pass
                self.response_payload = self._io.read_bytes(80)



        def _fetch_instances(self):
            pass
            if (self.len_data > 5):
                pass



        def _write__seq(self, io=None):
            super(EmliteData.ProfileLogRec, self)._write__seq(io)
            self._io.write_u4le(self.timestamp)
            if (self.len_data > 5):
                pass
                self._io.write_bytes(self.response_payload)



        def _check(self):
            pass
            if (self.len_data > 5):
                pass
                if (len(self.response_payload) != 80):
                    raise kaitaistruct.ConsistencyError(u"response_payload", len(self.response_payload), 80)





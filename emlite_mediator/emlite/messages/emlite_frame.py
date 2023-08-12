# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

import kaitaistruct
from kaitaistruct import ReadWriteKaitaiStruct, KaitaiStream, BytesIO
from enum import Enum


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 9):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

from .emlite_data import EmliteData

class EmliteFrame(ReadWriteKaitaiStruct):
    """The EMOP protocol exists to enable communication with Emlite (em-lite.co.uk) smart meters.
    In EMOP "all information is exchanged via a fixed format frame".
    That frame format is specified here with reference to the "SS0001 BM Interface Specification".
    """

    class AckNakCodes(Enum):
        ok = 0
        fcs_error = 1
        format_error = 2
        frame_len_incorrect = 3
        max_data_payload_exceeded = 4
        uknown_object_id = 5
        security_not_granted = 6
        frame_addr_incorrect = 7
    def __init__(self, _io=None, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self

    def _read(self):
        self.frame_delimeter = self._io.read_bytes(1)
        if not (self.frame_delimeter == b"\x7E"):
            raise kaitaistruct.ValidationNotEqualError(b"\x7E", self.frame_delimeter, self._io, u"/seq/0")
        self.frame_length = self._io.read_u1()
        self.destination_device_type = self._io.read_bytes(1)
        self.destination_address = self._io.read_bytes(3)
        self.source_device_type = self._io.read_bytes(1)
        self.source_address = self._io.read_bytes(3)
        self.control = self._io.read_u1()
        self._raw_data = self._io.read_bytes(self.len_data)
        _io__raw_data = KaitaiStream(BytesIO(self._raw_data))
        self.data = EmliteData(self.len_data, _io__raw_data)
        self.data._read()
        self.crc16 = self._io.read_bytes(2)


    def _fetch_instances(self):
        pass
        self.data._fetch_instances()


    def _write__seq(self, io=None):
        super(EmliteFrame, self)._write__seq(io)
        self._io.write_bytes(self.frame_delimeter)
        self._io.write_u1(self.frame_length)
        self._io.write_bytes(self.destination_device_type)
        self._io.write_bytes(self.destination_address)
        self._io.write_bytes(self.source_device_type)
        self._io.write_bytes(self.source_address)
        self._io.write_u1(self.control)
        _io__raw_data = KaitaiStream(BytesIO(bytearray(self.len_data)))
        self._io.add_child_stream(_io__raw_data)
        _pos2 = self._io.pos()
        self._io.seek(self._io.pos() + (self.len_data))
        def handler(parent, _io__raw_data=_io__raw_data):
            self._raw_data = _io__raw_data.to_byte_array()
            if (len(self._raw_data) != self.len_data):
                raise kaitaistruct.ConsistencyError(u"raw(data)", len(self._raw_data), self.len_data)
            parent.write_bytes(self._raw_data)
        _io__raw_data.write_back_handler = KaitaiStream.WriteBackHandler(_pos2, handler)
        self.data._write__seq(_io__raw_data)
        self._io.write_bytes(self.crc16)


    def _check(self):
        pass
        if (len(self.frame_delimeter) != 1):
            raise kaitaistruct.ConsistencyError(u"frame_delimeter", len(self.frame_delimeter), 1)
        if not (self.frame_delimeter == b"\x7E"):
            raise kaitaistruct.ValidationNotEqualError(b"\x7E", self.frame_delimeter, self._io, u"/seq/0")
        if (len(self.destination_device_type) != 1):
            raise kaitaistruct.ConsistencyError(u"destination_device_type", len(self.destination_device_type), 1)
        if (len(self.destination_address) != 3):
            raise kaitaistruct.ConsistencyError(u"destination_address", len(self.destination_address), 3)
        if (len(self.source_device_type) != 1):
            raise kaitaistruct.ConsistencyError(u"source_device_type", len(self.source_device_type), 1)
        if (len(self.source_address) != 3):
            raise kaitaistruct.ConsistencyError(u"source_address", len(self.source_address), 3)
        if (self.data.len_data != self.len_data):
            raise kaitaistruct.ConsistencyError(u"data", self.data.len_data, self.len_data)
        if (len(self.crc16) != 2):
            raise kaitaistruct.ConsistencyError(u"crc16", len(self.crc16), 2)

    @property
    def len_data(self):
        if hasattr(self, '_m_len_data'):
            return self._m_len_data

        self._m_len_data = (self.frame_length - 12)
        return getattr(self, '_m_len_data', None)

    def _invalidate_len_data(self):
        del self._m_len_data
    @property
    def seq_num(self):
        if hasattr(self, '_m_seq_num'):
            return self._m_seq_num

        self._m_seq_num = (self.control & 1)
        return getattr(self, '_m_seq_num', None)

    def _invalidate_seq_num(self):
        del self._m_seq_num
    @property
    def ack_nak_code(self):
        if hasattr(self, '_m_ack_nak_code'):
            return self._m_ack_nak_code

        self._m_ack_nak_code = KaitaiStream.resolve_enum(EmliteFrame.AckNakCodes, (self.control & 128))
        return getattr(self, '_m_ack_nak_code', None)

    def _invalidate_ack_nak_code(self):
        del self._m_ack_nak_code

    # NOTE: Following, not generated, manually added, TODO: replace with a subclass or wrapper that ads this
    def __str__(self):
        return (
            f"EmliteFrame(seq={self.seq_num},ack_nak_code={self.ack_nak_code.name},len={self.frame_length},"
            f"src={self.source_device_type.hex()}:{self.source_address.hex()},"
            f"dst={self.destination_device_type.hex()}:{self.destination_address.hex()},"
            f"data=[{self.data}],crc={self.crc16.hex()})"
        )
    
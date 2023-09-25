# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

import kaitaistruct
from kaitaistruct import ReadWriteKaitaiStruct, KaitaiStream, BytesIO
from enum import Enum


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 9):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class EmliteResponse(ReadWriteKaitaiStruct):
    """EMOP response data depends on the object being read. 
    This spec defines a number of known response types.
    Some are defined in the document "Meter and Smart Module
    Obis Commands iss1.5.pdf". Some were obtained by reverse
    engineering the protocol.
    """

    class DayOfWeekType(Enum):
        monday = 0
        tuesday = 1
        wednesday = 2
        thursday = 3
        friday = 4
        saturday = 5
        sunday = 6

    class ObjectIdType(Enum):
        firmware_version = 513
        instantaneous_active_power = 67328
        total_active_import_energy = 67584
        total_active_export_energy = 133120
        instantaneous_reactive_power = 198400
        instantaneous_current = 722688
        average_current = 727040
        instantaneous_voltage = 788224
        average_voltage = 792576
        instantaneous_power_factor = 853760
        instantaneous_frequency = 919296
        average_frequency = 923648
        element_a_instantaneous_active_power_import = 1378048
        three_phase_instantaneous_voltage_l1 = 2098944
        element_b_instantaneous_active_power_import = 2688768
        three_phase_instantaneous_voltage_l2 = 3409664
        three_phase_instantaneous_voltage_l3 = 4720384
        serial = 6291712
        hardware_version = 6324224
        time = 8390656
        three_phase_read = 14091786
        three_phase_initiate_read = 14092812
        three_phase_serial = 14155536
        prepay_balance = 16762882
        csq_net_op = 16776477
        prepay_enabled_flag = 16776973
        element_b = 16777208
        element_a = 16777212
    def __init__(self, len_response, object_id, _io=None, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self.len_response = len_response
        self.object_id = object_id

    def _read(self):
        _on = self.object_id
        if _on == EmliteResponse.ObjectIdType.three_phase_instantaneous_voltage_l3:
            pass
            self.response = EmliteResponse.ThreePhaseInstantaneousVoltageL3Rec(self._io, self, self._root)
            self.response._read()
        elif _on == EmliteResponse.ObjectIdType.csq_net_op:
            pass
            self.response = EmliteResponse.CsqNetOpRec(self._io, self, self._root)
            self.response._read()
        elif _on == EmliteResponse.ObjectIdType.hardware_version:
            pass
            self.response = EmliteResponse.HardwareRec(self._io, self, self._root)
            self.response._read()
        elif _on == EmliteResponse.ObjectIdType.time:
            pass
            self.response = EmliteResponse.TimeRec(self._io, self, self._root)
            self.response._read()
        elif _on == EmliteResponse.ObjectIdType.three_phase_instantaneous_voltage_l1:
            pass
            self.response = EmliteResponse.ThreePhaseInstantaneousVoltageL1Rec(self._io, self, self._root)
            self.response._read()
        elif _on == EmliteResponse.ObjectIdType.serial:
            pass
            self.response = EmliteResponse.SerialRec(self._io, self, self._root)
            self.response._read()
        elif _on == EmliteResponse.ObjectIdType.instantaneous_voltage:
            pass
            self.response = EmliteResponse.InstantaneousVoltageRec(self._io, self, self._root)
            self.response._read()
        elif _on == EmliteResponse.ObjectIdType.prepay_balance:
            pass
            self.response = EmliteResponse.PrepayBalanceRec(self._io, self, self._root)
            self.response._read()
        elif _on == EmliteResponse.ObjectIdType.three_phase_instantaneous_voltage_l2:
            pass
            self.response = EmliteResponse.ThreePhaseInstantaneousVoltageL2Rec(self._io, self, self._root)
            self.response._read()
        elif _on == EmliteResponse.ObjectIdType.prepay_enabled_flag:
            pass
            self.response = EmliteResponse.PrepayEnabledRec(self._io, self, self._root)
            self.response._read()
        else:
            pass
            self.response = EmliteResponse.DefaultRec(self._io, self, self._root)
            self.response._read()


    def _fetch_instances(self):
        pass
        _on = self.object_id
        if _on == EmliteResponse.ObjectIdType.three_phase_instantaneous_voltage_l3:
            pass
            self.response._fetch_instances()
        elif _on == EmliteResponse.ObjectIdType.csq_net_op:
            pass
            self.response._fetch_instances()
        elif _on == EmliteResponse.ObjectIdType.hardware_version:
            pass
            self.response._fetch_instances()
        elif _on == EmliteResponse.ObjectIdType.time:
            pass
            self.response._fetch_instances()
        elif _on == EmliteResponse.ObjectIdType.three_phase_instantaneous_voltage_l1:
            pass
            self.response._fetch_instances()
        elif _on == EmliteResponse.ObjectIdType.serial:
            pass
            self.response._fetch_instances()
        elif _on == EmliteResponse.ObjectIdType.instantaneous_voltage:
            pass
            self.response._fetch_instances()
        elif _on == EmliteResponse.ObjectIdType.prepay_balance:
            pass
            self.response._fetch_instances()
        elif _on == EmliteResponse.ObjectIdType.three_phase_instantaneous_voltage_l2:
            pass
            self.response._fetch_instances()
        elif _on == EmliteResponse.ObjectIdType.prepay_enabled_flag:
            pass
            self.response._fetch_instances()
        else:
            pass
            self.response._fetch_instances()


    def _write__seq(self, io=None):
        super(EmliteResponse, self)._write__seq(io)
        _on = self.object_id
        if _on == EmliteResponse.ObjectIdType.three_phase_instantaneous_voltage_l3:
            pass
            self.response._write__seq(self._io)
        elif _on == EmliteResponse.ObjectIdType.csq_net_op:
            pass
            self.response._write__seq(self._io)
        elif _on == EmliteResponse.ObjectIdType.hardware_version:
            pass
            self.response._write__seq(self._io)
        elif _on == EmliteResponse.ObjectIdType.time:
            pass
            self.response._write__seq(self._io)
        elif _on == EmliteResponse.ObjectIdType.three_phase_instantaneous_voltage_l1:
            pass
            self.response._write__seq(self._io)
        elif _on == EmliteResponse.ObjectIdType.serial:
            pass
            self.response._write__seq(self._io)
        elif _on == EmliteResponse.ObjectIdType.instantaneous_voltage:
            pass
            self.response._write__seq(self._io)
        elif _on == EmliteResponse.ObjectIdType.prepay_balance:
            pass
            self.response._write__seq(self._io)
        elif _on == EmliteResponse.ObjectIdType.three_phase_instantaneous_voltage_l2:
            pass
            self.response._write__seq(self._io)
        elif _on == EmliteResponse.ObjectIdType.prepay_enabled_flag:
            pass
            self.response._write__seq(self._io)
        else:
            pass
            self.response._write__seq(self._io)


    def _check(self):
        pass
        _on = self.object_id
        if _on == EmliteResponse.ObjectIdType.three_phase_instantaneous_voltage_l3:
            pass
            if self.response._root != self._root:
                raise kaitaistruct.ConsistencyError(u"response", self.response._root, self._root)
            if self.response._parent != self:
                raise kaitaistruct.ConsistencyError(u"response", self.response._parent, self)
        elif _on == EmliteResponse.ObjectIdType.csq_net_op:
            pass
            if self.response._root != self._root:
                raise kaitaistruct.ConsistencyError(u"response", self.response._root, self._root)
            if self.response._parent != self:
                raise kaitaistruct.ConsistencyError(u"response", self.response._parent, self)
        elif _on == EmliteResponse.ObjectIdType.hardware_version:
            pass
            if self.response._root != self._root:
                raise kaitaistruct.ConsistencyError(u"response", self.response._root, self._root)
            if self.response._parent != self:
                raise kaitaistruct.ConsistencyError(u"response", self.response._parent, self)
        elif _on == EmliteResponse.ObjectIdType.time:
            pass
            if self.response._root != self._root:
                raise kaitaistruct.ConsistencyError(u"response", self.response._root, self._root)
            if self.response._parent != self:
                raise kaitaistruct.ConsistencyError(u"response", self.response._parent, self)
        elif _on == EmliteResponse.ObjectIdType.three_phase_instantaneous_voltage_l1:
            pass
            if self.response._root != self._root:
                raise kaitaistruct.ConsistencyError(u"response", self.response._root, self._root)
            if self.response._parent != self:
                raise kaitaistruct.ConsistencyError(u"response", self.response._parent, self)
        elif _on == EmliteResponse.ObjectIdType.serial:
            pass
            if self.response._root != self._root:
                raise kaitaistruct.ConsistencyError(u"response", self.response._root, self._root)
            if self.response._parent != self:
                raise kaitaistruct.ConsistencyError(u"response", self.response._parent, self)
        elif _on == EmliteResponse.ObjectIdType.instantaneous_voltage:
            pass
            if self.response._root != self._root:
                raise kaitaistruct.ConsistencyError(u"response", self.response._root, self._root)
            if self.response._parent != self:
                raise kaitaistruct.ConsistencyError(u"response", self.response._parent, self)
        elif _on == EmliteResponse.ObjectIdType.prepay_balance:
            pass
            if self.response._root != self._root:
                raise kaitaistruct.ConsistencyError(u"response", self.response._root, self._root)
            if self.response._parent != self:
                raise kaitaistruct.ConsistencyError(u"response", self.response._parent, self)
        elif _on == EmliteResponse.ObjectIdType.three_phase_instantaneous_voltage_l2:
            pass
            if self.response._root != self._root:
                raise kaitaistruct.ConsistencyError(u"response", self.response._root, self._root)
            if self.response._parent != self:
                raise kaitaistruct.ConsistencyError(u"response", self.response._parent, self)
        elif _on == EmliteResponse.ObjectIdType.prepay_enabled_flag:
            pass
            if self.response._root != self._root:
                raise kaitaistruct.ConsistencyError(u"response", self.response._root, self._root)
            if self.response._parent != self:
                raise kaitaistruct.ConsistencyError(u"response", self.response._parent, self)
        else:
            pass
            if self.response._root != self._root:
                raise kaitaistruct.ConsistencyError(u"response", self.response._root, self._root)
            if self.response._parent != self:
                raise kaitaistruct.ConsistencyError(u"response", self.response._parent, self)

    class ThreePhaseInstantaneousVoltageL1Rec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.voltage = self._io.read_u2le()


        def _fetch_instances(self):
            pass


        def _write__seq(self, io=None):
            super(EmliteResponse.ThreePhaseInstantaneousVoltageL1Rec, self)._write__seq(io)
            self._io.write_u2le(self.voltage)


        def _check(self):
            pass


    class SerialRec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.serial = (self._io.read_bytes_full()).decode(u"ASCII")


        def _fetch_instances(self):
            pass


        def _write__seq(self, io=None):
            super(EmliteResponse.SerialRec, self)._write__seq(io)
            self._io.write_bytes((self.serial).encode(u"ASCII"))
            if not self._io.is_eof():
                raise kaitaistruct.ConsistencyError(u"serial", self._io.size() - self._io.pos(), 0)


        def _check(self):
            pass


    class PrepayBalanceRec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.balance = self._io.read_s4le()


        def _fetch_instances(self):
            pass


        def _write__seq(self, io=None):
            super(EmliteResponse.PrepayBalanceRec, self)._write__seq(io)
            self._io.write_s4le(self.balance)


        def _check(self):
            pass


    class CsqNetOpRec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.network_operator = self._io.read_bits_int_be(3)
            self.csq = self._io.read_bits_int_be(5)


        def _fetch_instances(self):
            pass


        def _write__seq(self, io=None):
            super(EmliteResponse.CsqNetOpRec, self)._write__seq(io)
            self._io.write_bits_int_be(3, self.network_operator)
            self._io.write_bits_int_be(5, self.csq)


        def _check(self):
            pass


    class ThreePhaseInstantaneousVoltageL3Rec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.voltage = self._io.read_u2le()


        def _fetch_instances(self):
            pass


        def _write__seq(self, io=None):
            super(EmliteResponse.ThreePhaseInstantaneousVoltageL3Rec, self)._write__seq(io)
            self._io.write_u2le(self.voltage)


        def _check(self):
            pass


    class InstantaneousVoltageRec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.voltage = self._io.read_u2le()


        def _fetch_instances(self):
            pass


        def _write__seq(self, io=None):
            super(EmliteResponse.InstantaneousVoltageRec, self)._write__seq(io)
            self._io.write_u2le(self.voltage)


        def _check(self):
            pass


    class ThreePhaseInstantaneousVoltageL2Rec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.voltage = self._io.read_u2le()


        def _fetch_instances(self):
            pass


        def _write__seq(self, io=None):
            super(EmliteResponse.ThreePhaseInstantaneousVoltageL2Rec, self)._write__seq(io)
            self._io.write_u2le(self.voltage)


        def _check(self):
            pass


    class PrepayEnabledRec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.enabled_flag = self._io.read_u1()


        def _fetch_instances(self):
            pass


        def _write__seq(self, io=None):
            super(EmliteResponse.PrepayEnabledRec, self)._write__seq(io)
            self._io.write_u1(self.enabled_flag)


        def _check(self):
            pass


    class HardwareRec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.hardware = (self._io.read_bytes_full()).decode(u"ASCII")


        def _fetch_instances(self):
            pass


        def _write__seq(self, io=None):
            super(EmliteResponse.HardwareRec, self)._write__seq(io)
            self._io.write_bytes((self.hardware).encode(u"ASCII"))
            if not self._io.is_eof():
                raise kaitaistruct.ConsistencyError(u"hardware", self._io.size() - self._io.pos(), 0)


        def _check(self):
            pass


    class TimeRec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.year = self._io.read_u1()
            self.month = self._io.read_u1()
            self.date = self._io.read_u1()
            self.hour = self._io.read_u1()
            self.minute = self._io.read_u1()
            self.second = self._io.read_u1()
            self.day_of_week = KaitaiStream.resolve_enum(EmliteResponse.DayOfWeekType, self._io.read_u1())


        def _fetch_instances(self):
            pass


        def _write__seq(self, io=None):
            super(EmliteResponse.TimeRec, self)._write__seq(io)
            self._io.write_u1(self.year)
            self._io.write_u1(self.month)
            self._io.write_u1(self.date)
            self._io.write_u1(self.hour)
            self._io.write_u1(self.minute)
            self._io.write_u1(self.second)
            self._io.write_u1(self.day_of_week.value)


        def _check(self):
            pass


    class DefaultRec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.payload = self._io.read_bytes_full()


        def _fetch_instances(self):
            pass


        def _write__seq(self, io=None):
            super(EmliteResponse.DefaultRec, self)._write__seq(io)
            self._io.write_bytes(self.payload)
            if not self._io.is_eof():
                raise kaitaistruct.ConsistencyError(u"payload", self._io.size() - self._io.pos(), 0)


        def _check(self):
            pass




from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ObjectId(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    DEFAULT: _ClassVar[ObjectId]
    FIRMWARE_VERSION: _ClassVar[ObjectId]
    INSTANTANEOUS_ACTIVE_POWER: _ClassVar[ObjectId]
    TOTAL_ACTIVE_IMPORT_ENERGY: _ClassVar[ObjectId]
    TOTAL_ACTIVE_EXPORT_ENERGY: _ClassVar[ObjectId]
    INSTANTANEOUS_REACTIVE_POWER: _ClassVar[ObjectId]
    INSTANTANEOUS_CURRENT: _ClassVar[ObjectId]
    AVERAGE_CURRENT: _ClassVar[ObjectId]
    INSTANTANEOUS_VOLTAGE: _ClassVar[ObjectId]
    AVERAGE_VOLTAGE: _ClassVar[ObjectId]
    INSTANTANEOUS_POWER_FACTOR: _ClassVar[ObjectId]
    INSTANTANEOUS_FREQUENCY: _ClassVar[ObjectId]
    AVERAGE_FREQUENCY: _ClassVar[ObjectId]
    ELEMENT_A_INSTANTANEOUS_ACTIVE_POWER_IMPORT: _ClassVar[ObjectId]
    ELEMENT_B_INSTANTANEOUS_ACTIVE_POWER_IMPORT: _ClassVar[ObjectId]
    SERIAL: _ClassVar[ObjectId]
    HARDWARE_VERSION: _ClassVar[ObjectId]
    TIME: _ClassVar[ObjectId]
    THREE_PHASE_READ: _ClassVar[ObjectId]
    THREE_PHASE_INITIATE_READ: _ClassVar[ObjectId]
    THREE_PHASE_SERIAL: _ClassVar[ObjectId]
    PREPAY_BALANCE: _ClassVar[ObjectId]
    PREPAY_ENABLED_FLAG: _ClassVar[ObjectId]
    ELEMENT_B: _ClassVar[ObjectId]
    ELEMENT_A: _ClassVar[ObjectId]
DEFAULT: ObjectId
FIRMWARE_VERSION: ObjectId
INSTANTANEOUS_ACTIVE_POWER: ObjectId
TOTAL_ACTIVE_IMPORT_ENERGY: ObjectId
TOTAL_ACTIVE_EXPORT_ENERGY: ObjectId
INSTANTANEOUS_REACTIVE_POWER: ObjectId
INSTANTANEOUS_CURRENT: ObjectId
AVERAGE_CURRENT: ObjectId
INSTANTANEOUS_VOLTAGE: ObjectId
AVERAGE_VOLTAGE: ObjectId
INSTANTANEOUS_POWER_FACTOR: ObjectId
INSTANTANEOUS_FREQUENCY: ObjectId
AVERAGE_FREQUENCY: ObjectId
ELEMENT_A_INSTANTANEOUS_ACTIVE_POWER_IMPORT: ObjectId
ELEMENT_B_INSTANTANEOUS_ACTIVE_POWER_IMPORT: ObjectId
SERIAL: ObjectId
HARDWARE_VERSION: ObjectId
TIME: ObjectId
THREE_PHASE_READ: ObjectId
THREE_PHASE_INITIATE_READ: ObjectId
THREE_PHASE_SERIAL: ObjectId
PREPAY_BALANCE: ObjectId
PREPAY_ENABLED_FLAG: ObjectId
ELEMENT_B: ObjectId
ELEMENT_A: ObjectId

class SendRawMessageRequest(_message.Message):
    __slots__ = ["dataField"]
    DATAFIELD_FIELD_NUMBER: _ClassVar[int]
    dataField: bytes
    def __init__(self, dataField: _Optional[bytes] = ...) -> None: ...

class SendRawMessageReply(_message.Message):
    __slots__ = ["response"]
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    response: bytes
    def __init__(self, response: _Optional[bytes] = ...) -> None: ...

class ReadElementRequest(_message.Message):
    __slots__ = ["objectId"]
    OBJECTID_FIELD_NUMBER: _ClassVar[int]
    objectId: ObjectId
    def __init__(self, objectId: _Optional[_Union[ObjectId, str]] = ...) -> None: ...

class ReadElementReply(_message.Message):
    __slots__ = ["response"]
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    response: bytes
    def __init__(self, response: _Optional[bytes] = ...) -> None: ...

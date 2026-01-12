from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class SendRawMessageRequest(_message.Message):
    __slots__ = ("serial", "dataField")
    SERIAL_FIELD_NUMBER: _ClassVar[int]
    DATAFIELD_FIELD_NUMBER: _ClassVar[int]
    serial: str
    dataField: bytes
    def __init__(self, serial: _Optional[str] = ..., dataField: _Optional[bytes] = ...) -> None: ...

class SendRawMessageReply(_message.Message):
    __slots__ = ("response",)
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    response: bytes
    def __init__(self, response: _Optional[bytes] = ...) -> None: ...

class ReadElementRequest(_message.Message):
    __slots__ = ("serial", "objectId")
    SERIAL_FIELD_NUMBER: _ClassVar[int]
    OBJECTID_FIELD_NUMBER: _ClassVar[int]
    serial: str
    objectId: int
    def __init__(self, serial: _Optional[str] = ..., objectId: _Optional[int] = ...) -> None: ...

class ReadElementReply(_message.Message):
    __slots__ = ("response",)
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    response: bytes
    def __init__(self, response: _Optional[bytes] = ...) -> None: ...

class WriteElementRequest(_message.Message):
    __slots__ = ("serial", "objectId", "payload")
    SERIAL_FIELD_NUMBER: _ClassVar[int]
    OBJECTID_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    serial: str
    objectId: int
    payload: bytes
    def __init__(self, serial: _Optional[str] = ..., objectId: _Optional[int] = ..., payload: _Optional[bytes] = ...) -> None: ...

class WriteElementReply(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetInfoRequest(_message.Message):
    __slots__ = ("serial",)
    SERIAL_FIELD_NUMBER: _ClassVar[int]
    serial: str
    def __init__(self, serial: _Optional[str] = ...) -> None: ...

class GetInfoReply(_message.Message):
    __slots__ = ("json_data",)
    JSON_DATA_FIELD_NUMBER: _ClassVar[int]
    json_data: str
    def __init__(self, json_data: _Optional[str] = ...) -> None: ...

class GetMetersRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetMetersReply(_message.Message):
    __slots__ = ("json_meters",)
    JSON_METERS_FIELD_NUMBER: _ClassVar[int]
    json_meters: str
    def __init__(self, json_meters: _Optional[str] = ...) -> None: ...

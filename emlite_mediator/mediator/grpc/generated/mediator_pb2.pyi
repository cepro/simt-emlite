from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

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
    objectId: int
    def __init__(self, objectId: _Optional[int] = ...) -> None: ...

class ReadElementReply(_message.Message):
    __slots__ = ["response"]
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    response: bytes
    def __init__(self, response: _Optional[bytes] = ...) -> None: ...

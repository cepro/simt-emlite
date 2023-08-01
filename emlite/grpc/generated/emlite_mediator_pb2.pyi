from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class SendMessageRequest(_message.Message):
    __slots__ = ["dataFrame"]
    DATAFRAME_FIELD_NUMBER: _ClassVar[int]
    dataFrame: bytes
    def __init__(self, dataFrame: _Optional[bytes] = ...) -> None: ...

class SendMessageReply(_message.Message):
    __slots__ = ["response"]
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    response: bytes
    def __init__(self, response: _Optional[bytes] = ...) -> None: ...

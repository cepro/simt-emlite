import sys

from kaitaistruct import KaitaiStream, BytesIO

from emlite_mediator.emlite.messages.emlite_frame import EmliteFrame
from emlite_mediator.emlite.messages.emlite_data import EmliteData


if __name__ == '__main__':
    # frame_hex = "7E1201FFFFFFC01234560501FFFF0B010169C6"
    frame_hex = sys.argv[1]
    # => EmliteFrame(seq=1,ack_nak_code=ok,len=18,src=c0:123456,dst=01:ffffff,data=[EmliteData(object_id=ffff0b,rw=1,payload=[01])],crc=69c6)
    frame_bytes = bytearray.fromhex(frame_hex)

    frame = EmliteFrame(KaitaiStream(BytesIO(frame_bytes)))
    frame._read()
    print(frame)

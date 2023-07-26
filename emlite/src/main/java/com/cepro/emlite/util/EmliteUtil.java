package com.cepro.emlite.util;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;

import com.blinkhub.lib.util.NumberUtils;
import com.cepro.emlite.model.EmlitePacket;

public class EmliteUtil {

    public static EmlitePacket decodeStreamPacket(ByteBuffer buf) {
        buf.flip();
        int remaining = EmlitePacket.checkPacket(buf);
        while (remaining < 0) {
            if (remaining == EmlitePacket.BAD_DELIM || remaining == EmlitePacket.BAD_LENGTH
                    || remaining == EmlitePacket.BAD_CRC) {
                buf.get();
            }
            if (buf.remaining() == 0) {
                buf.clear();
            } else {
                remaining = EmlitePacket.checkPacket(buf);
            }
        }
        if (remaining == 0) {
            EmlitePacket packet = EmlitePacket.decode(buf);
            buf.compact();
            return packet;
        } else if (remaining > 0) {
            buf.compact();
        }
        return null;
    }

    public static Integer getInt16(byte[] val) {
        if (val == null) {
            return null;
        }
        return NumberUtils.unsign(NumberUtils.decodeShortLE(val));
    }

    public static Integer getInt32(byte[] val, int offset) {
        return (int) NumberUtils.unsign(NumberUtils.decodeInteger(ByteOrder.LITTLE_ENDIAN, val, offset, 4));
    }

    public static Integer getInt32(byte[] val) {
        return getInt32(val, 0);
    }

    public static Double getFixed16(byte[] val, double multiplier) {
        Integer i = getInt16(val);
        if (i == null) {
            return null;
        }
        return i * multiplier;
    }

    public static Double getFixed32(byte[] val, int offset, double multiplier) {
        Integer i = getInt32(val, offset);
        if (i == null) {
            return null;
        }
        return i * multiplier;
    }

    public static Double getFixed32(byte[] val, double multiplier) {
        return getFixed32(val, 0, multiplier);
    }

}

package com.cepro.emlite.util;

import java.nio.ByteOrder;

import com.blinkhub.lib.util.Format;

/**
 * x^16 + x^12 + x^5 + 1 = (1) 0001 0000 0010 0001 = 0x1021
 * x^16 + x^15 + x^2 + 1 = (1) 1000 0000 0000 0101 = 0x8005
 * 
 * @author robbie
 *
 */
public class CRC16 {

    /**
     * x^16+x^12+x^5+1 = (1) 0001 0000 0010 0001 = 0x1021 (big Endian)
     */
    public static final short CCITT_BE = 0x1021;

    /**
     * x^16 + x^15 + x^2 + 1 = (1) 1000 0000 0000 0101 = 0x8005 (big Endian)
     */
    public static final short ANSI_BE = (short) 0x8005;

    public final short polynomial;
    public final ByteOrder endian;
    public final short preset;
    public final short postInvert;
    public final short valid;

    public class Stream {
        private short crc = preset;

        public Stream next(byte b) {
            if (endian == ByteOrder.LITTLE_ENDIAN) {
                crc ^= b & 0xFF;
                for (int j = 0; j < 8; j++) {
                    if ((crc & 0x0001) != 0) {
                        crc = (short) (((crc >> 1) & 0x7fff) ^ polynomial);
                    } else {
                        crc = (short) ((crc >> 1) & 0x7fff);
                    }
                }
            } else {
                crc ^= b << 8;
                for (int j = 0; j < 8; j++) {
                    if ((crc & 0x8000) != 0) {
                        crc = (short) ((crc << 1) ^ polynomial);
                    } else {
                        crc <<= 1;
                    }
                }
            }
            return this;
        }

        public Stream next(byte[] data) {
            return next(data, 0, data.length);
        }

        public Stream next(byte[] data, int offset, int size) {
            for (int i = offset; i < offset + size; ++i) {
                next(data[i]);
            }
            return this;
        }

        public short crc() {
            return (short) (crc ^ postInvert);
        }
    }

    public CRC16(short polynomial, ByteOrder endian, short preset, short postInvert) {
        this.polynomial = polynomial;
        this.endian = endian;
        this.preset = preset;
        this.postInvert = postInvert;
        if (postInvert == 0) {
            valid = 0;
        } else {
            byte lsb = (byte) ((postInvert ^ preset) & 0xFF);
            byte msb = (byte) ((postInvert ^ preset) >> 8);
            if (endian == ByteOrder.LITTLE_ENDIAN) {
                valid = calculate(new byte[] { lsb, msb });
            } else {
                valid = calculate(new byte[] { msb, lsb });
            }
        }
    }

    public CRC16(short polynomial, ByteOrder endian, boolean invertStart, boolean invertEnd) {
        this(polynomial, endian, invertStart ? (short) 0xFFFF : (short) 0x0000,
                invertEnd ? (short) 0xFFFF : (short) 0x0000);
    }

    public CRC16(short polynomial, ByteOrder endian) {
        this(polynomial, endian, (short) 0x0000, (short) 0x0000);
    }

    public Stream start() {
        return new Stream();
    }

    public short calculate(byte[] data, int offset, int size) {
        return start().next(data, offset, size).crc();
    }

    public short calculate(byte[] data) {
        return calculate(data, 0, data.length);
    }

    public short insert(byte[] data, int offset, int size) {
        short crc = calculate(data, offset, size - 2);
        byte lsb = (byte) (crc & 0xFF);
        byte msb = (byte) (crc >> 8);
        data[offset + size - 2] = (endian == ByteOrder.LITTLE_ENDIAN) ? lsb : msb;
        data[offset + size - 1] = (endian == ByteOrder.LITTLE_ENDIAN) ? msb : lsb;
        return crc;
    }

    public short insert(byte[] data) {
        return insert(data, 0, data.length);
    }

    public boolean validate(byte[] data, int offset, int size) {
        short crc = calculate(data, offset, size);
        return crc == valid;
    }

    public boolean validate(byte[] data) {
        return validate(data, 0, data.length);
    }

    @Override
    public String toString() {
        return "CRC16 ["
                + "polynomial=0x" + Format.toHex(polynomial)
                + ", preset=0x" + Format.toHex(preset)
                + ", postInvert=0x" + Format.toHex(postInvert)
                + ", valid=0x" + Format.toHex(valid)
                + "]";
    }

}

package com.cepro.emlite.util;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.ByteOrder;
import java.util.Random;

import org.junit.jupiter.api.Test;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@SuppressWarnings("unused")
public class CRC16Test {

    private static final Logger log = LoggerFactory.getLogger(CRC16Test.class);

    @Test
    public void testEmlite() {
        CRC16 emliteCRC = new CRC16(CRC16.CCITT_BE, ByteOrder.BIG_ENDIAN, true, false);
        for (byte[][] pp : SampleEmliteSession.SESSION) {
            for (byte[] p : pp) {
                assert (emliteCRC.validate(p, 1, p.length - 1));
                // short expected = NumberUtils.decodeShort(p, p.length-2, 2);
                // short crc = CRC16.calculateCCITT(p, 1, p.length-3);
                // assertEquals(expected, crc);
                // if (expected == crc) {
                // log.trace("CRC16 CCITT: {} == {}", Format.toHex(expected),
                // Format.toHex(crc));
                // } else {
                // log.error("CRC16 CCITT: {} != {}", Format.toHex(expected),
                // Format.toHex(crc));
                // }
            }
        }
    }

    public static final byte[][] ANSI_PACKETS = new byte[][] {
    };

    public static final short[] ANSI_CRCs = new short[] {
    };

    @Test
    public void testANSI() {
        assertEquals(ANSI_PACKETS.length, ANSI_CRCs.length);
        CRC16 crc16ansi = new CRC16(CRC16.ANSI_BE, ByteOrder.BIG_ENDIAN);
        for (int i = 0; i != ANSI_PACKETS.length; ++i) {
            byte[] packet = ANSI_PACKETS[i];
            short expected = ANSI_CRCs[i];
            short crc = crc16ansi.calculate(packet);
            assertEquals(expected, crc);
            // if (expected == crc) {
            // log.trace("CRC16 IBM/ANSI: {} == {}", Format.toHex(expected),
            // Format.toHex(crc));
            // } else {
            // log.error("CRC16 IBM/ANSI: {} != {}", Format.toHex(expected),
            // Format.toHex(crc));
            // }
        }
    }

    @Test
    public void testRandom() {
        Random random = new Random(0);
        for (int i = 0; i != 100; ++i) {
            short poly = (short) random.nextInt();
            ByteOrder endian = random.nextBoolean() ? ByteOrder.BIG_ENDIAN : ByteOrder.LITTLE_ENDIAN;
            short preset = (short) random.nextInt();
            short postInvert = (short) random.nextInt();
            CRC16 rndCRC = new CRC16(poly, endian, preset, postInvert);
            // log.trace(rndCRC.toString());
            byte[] bytes = new byte[random.nextInt(256) + 3];
            random.nextBytes(bytes);
            short crc = rndCRC.insert(bytes);
            short valid = rndCRC.calculate(bytes);
            // log.trace(Format.packHex(bytes));
            // if (valid == rndCRC.valid) {
            // log.trace("RND CRC: {} / {}", Format.toHex(crc), Format.toHex(valid));
            // } else {
            // log.error("RND CRC: {} / {} != {}", Format.toHex(crc), Format.toHex(valid),
            // Format.toHex(rndCRC.valid));
            // }
            assertTrue(rndCRC.validate(bytes));
        }
    }

}

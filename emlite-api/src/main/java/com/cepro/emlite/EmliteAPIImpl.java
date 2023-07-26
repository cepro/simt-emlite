package com.cepro.emlite;

import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.util.Calendar;
import java.util.TimeZone;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.blinkhub.lib.util.Format;
import com.blinkhub.lib.util.NumberUtils;
import com.cepro.emlite.model.EmlitePacket;
import com.cepro.emlite.model.Obis;
import com.cepro.emlite.model.ObisId;
import com.cepro.emlite.util.EmliteUtil;

public class EmliteAPIImpl implements EmliteAPI {

    private static final Logger log = LoggerFactory.getLogger(EmliteAPIImpl.class);
    private static final Charset US_ASCII = StandardCharsets.US_ASCII;
    private static final TimeZone GMT = TimeZone.getTimeZone("GMT");

    /*
     * How long to wait for response (millisesonds); default = 10seconds
     */
    public static final long TIMEOUT_MILLIS = 10 * 1000L;

    private final EmliteChannel channel;
    public final int srcId;
    private int dstId = 0;
    private final EmlitePacketConstructor epc;

    public EmliteAPIImpl(EmliteChannel channel) {
        this(channel, EmlitePacketConstructor.makeSource());
    }

    public EmliteAPIImpl(EmliteChannel channel, int srcId) {
        this.channel = channel;
        this.srcId = srcId;
        this.epc = new EmlitePacketConstructor(srcId);
    }

    private void checkDst(int dst) {
        if (dst != 0 && dstId != dst) {
            if (dstId != 0) {
                log.warn("Destination ID has changed from {} to {}", Format.toHex(dstId), Format.toHex(dst));
            }
            dstId = dst;
            epc.dst = dst;
        }
    }

    @Override
    public synchronized byte[] getRegister(ObisId id) throws IOException {
        return getRegister(id, null, epc, null);
    }

    @Override
    public synchronized byte[] getRegister(Integer readTime, EmlitePacketConstructor packetConstructor)
            throws IOException {
        return getRegister(null, readTime, packetConstructor, null);
    }

    @Override
    public synchronized byte[] getRegister(ObisId id, EmlitePacketConstructor packetConstructor, byte[] writePayload)
            throws IOException {
        return getRegister(id, null, packetConstructor, writePayload);
    }

    private synchronized byte[] getRegister(
            ObisId id,
            Integer readTime,
            EmlitePacketConstructor packetConstructor,
            byte[] writePayload) throws IOException {
        long to = System.currentTimeMillis() + TIMEOUT_MILLIS;
        boolean byObisId = id != null;
        EmlitePacket req;
        if (byObisId) {
            if (writePayload == null || writePayload.length == 0) {
                req = packetConstructor.read(id);
            } else {
                req = packetConstructor.write(id, writePayload);
            }
        } else {
            req = packetConstructor.read(readTime);
        }
        channel.write(req);
        EmlitePacket rsp = null;
        do {
            if (rsp != null) {
                channel.write(req);
            }
            rsp = channel.read();
            checkDst(rsp.src);
            if (rsp.getSequence() == req.getSequence() && rsp.dst == srcId) {
                if (rsp.getAckNak() == 0) {
                    return rsp.value;
                } else if (rsp.getAckNak() == 5) {
                    log.info("Register not recognised {} ({})", Obis.lookup(id), id);
                    return null;
                } else {
                    log.warn("Received AckNck code {}, in {}", rsp.getAckNak(), rsp);
                }
            } else {
                log.warn("Unexpected packet received. Sent {}, Received {}", req, rsp);
            }
        } while (System.currentTimeMillis() < to);
        log.warn(
                "Timeout requesting {} ({})",
                byObisId ? Obis.lookup(id) : "Profile Log",
                byObisId ? id : readTime);
        return null;
    }

    @Override
    public Integer getId() {
        return dstId == 0 ? null : dstId;
    }

    @Override
    public double[] getElementATotals() throws IOException {
        byte[] val = getRegister(Obis.ElementA.id);
        return new double[] {
                EmliteUtil.getFixed32(val, 0, 0.001f),
                EmliteUtil.getFixed32(val, 4, 0.001f),
                EmliteUtil.getFixed32(val, 8, 0.001f),
                EmliteUtil.getFixed32(val, 12, 0.001f)
        };
    }

    public double[] getElementBTotals() throws IOException {
        byte[] val = getRegister(Obis.ElementB.id);
        return new double[] {
                EmliteUtil.getFixed32(val, 0, 0.001f),
                EmliteUtil.getFixed32(val, 4, 0.001f),
                EmliteUtil.getFixed32(val, 8, 0.001f),
                EmliteUtil.getFixed32(val, 12, 0.001f)
        };
    }

    @Override
    public Integer getInstantaneousVoltage() throws IOException {
        byte[] val = getRegister(Obis.InstantaneousVoltage.id);
        return EmliteUtil.getInt16(val);
    }

    @Override
    public Double getInstantaneousCurrent() throws IOException {
        byte[] val = getRegister(Obis.InstantaneousCurrent.id);
        return EmliteUtil.getFixed16(val, 0.1);
    }

    @Override
    public Integer getInstantaneousActivePower() throws IOException {
        byte[] val = getRegister(Obis.InstantaneousActivePower.id);
        return EmliteUtil.getInt16(val);
    }

    @Override
    public Integer getInstantaneousReactivePower() throws IOException {
        byte[] val = getRegister(Obis.InstantaneousReactivePower.id);
        return EmliteUtil.getInt16(val);
    }

    @Override
    public Double getInstantaneousPowerFactor() throws IOException {
        byte[] val = getRegister(Obis.InstantaneousPowerFactor.id);
        return EmliteUtil.getFixed16(val, 0.01);
    }

    @Override
    public Double getInstantaneousFrequency() throws IOException {
        byte[] val = getRegister(Obis.InstantaneousFrequency.id);
        return EmliteUtil.getFixed16(val, 0.1);
    }

    @Override
    public Integer getAverageVoltage() throws IOException {
        byte[] val = getRegister(Obis.AverageVoltage.id);
        return EmliteUtil.getInt16(val);
    }

    @Override
    public Double getAverageCurrent() throws IOException {
        byte[] val = getRegister(Obis.AverageCurrent.id);
        return EmliteUtil.getFixed16(val, 0.1);
    }

    @Override
    public Double getAverageFrequency() throws IOException {
        byte[] val = getRegister(Obis.AverageFrequency.id);
        return EmliteUtil.getFixed16(val, 0.1);
    }

    @Override
    public Double getTotalActiveImportEnergy() throws IOException {
        byte[] val = getRegister(Obis.TotalActiveImportEnergy.id);
        return EmliteUtil.getFixed32(val, 0.001);
    }

    @Override
    public Double getTotalActiveExportEnergy() throws IOException {
        byte[] val = getRegister(Obis.TotalActiveExportEnergy.id);
        return EmliteUtil.getFixed32(val, 0.001);
    }

    @Override
    public Calendar getTime() throws IOException {
        byte[] val = getRegister(Obis.Time.id);
        Calendar time = Calendar.getInstance(GMT);
        time.set(2000 + val[0], val[1] - 1, val[2], val[3], val[4], val[5]);
        if (time.get(Calendar.DAY_OF_WEEK) != val[6] + 1) {
            log.warn("Day of week does not match: Calendar: {}; emlite: {}", time.get(Calendar.DAY_OF_WEEK),
                    val[6] + 1);
        }
        return time;
    }

    @Override
    public String getSerial() throws IOException {
        byte[] val = getRegister(Obis.Serial.id);
        if (val == null) {
            return null;
        }
        return new String(val, US_ASCII).trim();
    }

    @Override
    public String getHardwareVersion() throws IOException {
        byte[] val = getRegister(Obis.HardwareVersion.id);
        if (val == null) {
            return null;
        }
        return new String(val, US_ASCII).trim();
    }

    @Override
    public String getFirmwareVersion() throws IOException {
        byte[] val = getRegister(Obis.FirmwareVersion.id);
        if (val == null) {
            return null;
        }
        return new String(val, US_ASCII).trim();
    }

    /**
     * Reads 8 and 1/2 hours of 1/2 hourly interval data.
     * 
     * @param readTime Seconds since 1/1/2000 00:00:00 to start read from
     * @throws IOException
     */
    @Override
    public byte[] getProfileLog1(int readTime) throws IOException {
        return getRegister(
                readTime,
                new EmlitePacketConstructor(srcId, (byte) 3));
    }

    @Override
    public byte[] getProfileLog2(int readTime) throws IOException {
        return getRegister(
                readTime,
                new EmlitePacketConstructor(srcId, (byte) 4));
    }

    @Override
    public String getThreePhaseSerial() throws IOException {
        byte[] val = getRegister(Obis.ThreePhaseSerial.id);
        if (val == null) {
            return null;
        }
        return new String(val, US_ASCII).trim();
    }

    @Override
    public void initiateThreePhaseRead() throws IOException {
        byte[] val = getRegister(
                Obis.ThreePhaseInitiateRead.id);
        log.info("initiateThreePhaseRead response: {}", Format.toHex(val));
    }

    @Override
    public byte[] getThreePhaseLogs(byte[] writePayload) throws IOException {
        if (writePayload == null || writePayload.length == 0) {
            return getRegister(Obis.ThreePhaseRead.id);
        }
        return getRegister(
                Obis.ThreePhaseRead.id,
                new EmlitePacketConstructor(srcId),
                writePayload);
    }

    @Override
    public Double getPrepayBalance() throws IOException {
        byte[] val = getRegister(Obis.PrepayBalance.id);
        return ((double) NumberUtils.decodeIntegerLE(val)) / 100000;
    }

    @Override
    public Boolean getPrepayEnabledFlag() throws IOException {
        byte[] val = getRegister(Obis.PrepayEnabledFlag.id);
        return val[0] == 1;
    }

}

package com.cepro.emlite.model;

import java.io.Serializable;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.blinkhub.lib.codec.AbstractEncodableCodec;
import com.blinkhub.lib.codec.Codec;
import com.blinkhub.lib.codec.Encodable;
import com.blinkhub.lib.util.Format;
import com.blinkhub.lib.util.NumberUtils;
import com.cepro.util.CRC16;

public class EmlitePacket implements Serializable, Encodable {

	private static final long serialVersionUID = 4185953658703889556L;

	private static final Logger log = LoggerFactory.getLogger(EmlitePacket.class);

	public static final int BUFFER_EMPTY = -1;
	public static final int BAD_DELIM = -2;
	public static final int BAD_LENGTH = -3;
	public static final int BAD_CRC = -4;

	public static final byte DELIM = 0x7E;

	public static final CRC16 EMLITE_CRC = new CRC16(CRC16.CCITT_BE, ByteOrder.BIG_ENDIAN, true, false);

	public final int dst;
	public final int src;
	public final byte control;
	public final byte format;
	public final ObisId id;
	public final byte read;
	public final byte[] value;
	public final Integer profileReadTime; // For Profile Log 1 and 2 only

	public EmlitePacket(int dst, int src, byte control, byte format, ObisId id, byte read, byte[] value) {
		this(dst, src, control, format, id, null, read, value);
	}

	public EmlitePacket(int dst, int src, byte control, byte format, int profileReadTime, byte read, byte[] value) {
		this(dst, src, control, format, null, profileReadTime, read, value);
	}

	private EmlitePacket(int dst, int src, byte control, byte format, ObisId id, Integer profileReadTime, byte read, byte[] value) {
		this.dst = dst;
		this.src = src;
		this.control = control;
		this.format = format;
		this.id = id;
		this.profileReadTime = profileReadTime;
		this.read = read;
		this.value = value;
	}

	public int getLength() {
		return (value == null) ? 18 : (18 + value.length);
	}

	public byte getSequence() {
		return (byte)(control & 7);
	}

	public byte getAckNak() {
		return (byte)((control >> 3) & 0x1F);
	}

	@Override
	public void encode(ByteBuffer buf) {
		System.out.println(this.toString());

  	boolean isObisIdPacket = id != null;

		buf.put(DELIM);

		// TODO: was 17 before for Obids based packet but i count only 16 bytes ...
		//       test this still works with length 16
		//       17 is correct for the Profile Log based packets
		byte length = (byte)17; // (isObisIdPacket ? 16 : 17);
		if (value != null) {
			length += value.length;
		}

		byte[] bytes = new byte[length];
		ByteBuffer temp = ByteBuffer.wrap(bytes);
		
		temp.put(length);
		temp.putInt(dst);
		temp.putInt(src);
		temp.put(control);
		temp.put(format);

		if (isObisIdPacket) {
			temp.put(id.a);
			temp.put(id.b);
			temp.put(id.c);
		} else if (profileReadTime != null && profileReadTime > 0) { // Profile Log reads
			temp.putInt(profileReadTime);
		}

		temp.put(read);

		if (value != null) {
			temp.put(value);
		}

		EMLITE_CRC.insert(bytes);
		buf.put(bytes);
	}

	public static int checkPacket(ByteBuffer buf) {
		if (buf.remaining() == 0) {
			log.error("Empty Buffer");
			return BUFFER_EMPTY;
		}
		buf = buf.duplicate();
		byte bb = buf.get();
		if (bb != DELIM) {
			log.error("Packet must start with 0x7E; instead 0x{}", Format.toHex(bb));
			return BAD_DELIM;
		}
		if (buf.remaining() < 1) {
			log.warn("Not enough of packet received yet; only delim");
			return 1;
		}
		short length = NumberUtils.unsign(buf.get());
		if (buf.remaining() < length-1) {
			log.warn("Not enough of packet received yet; have {} need {}", buf.remaining()+1, length);
			return length - 1 - buf.remaining();
		}
		if (length < 17) {
			byte[] bytes = new byte[length];
			buf.get(bytes);
			log.error("Packet too short for protocol: length = {} [{}]", length, Format.toHex(bytes));
			return BAD_LENGTH;
		}
		byte[] bytes = new byte[length];
		bytes[0] = (byte)length;
		buf.get(bytes, 1, length-1);
		if (!EMLITE_CRC.validate(bytes)) {
			short expectedCRC = NumberUtils.decodeShort(bytes, length-2, 2);
			short calcCRC = EMLITE_CRC.calculate(bytes, 0, length-2);
			log.error("CRC-16-CCITT does not match; received {}, calculated {}", Format.toHex(expectedCRC), Format.toHex(calcCRC));
			return BAD_CRC;
		}
		return 0;
	}

	public static EmlitePacket decode(ByteBuffer buf) {
		if (buf.remaining() == 0) {
			log.error("Empty Buffer");
			return null;
		}
		byte bb = buf.get();
		if (bb != DELIM) {
			log.error("Packet must start with 0x7E; instead 0x{}", Format.toHex(bb));
			return null;
		}
		if (buf.remaining() < 3) {
			log.warn("Not enough of packet received yet; less than 3 bytes");
			return null;
		}
		short length = NumberUtils.unsign(buf.get());
		if (buf.remaining() < length-1) {
			log.warn("Not enough of packet received yet; have {}, expect {}", buf.remaining()+1, length);
			return null;
		}
		if (length < 17) {
			log.error("Packet too short for protocol: length = {}", length);
			return null;
		}

		byte[] bytes = new byte[length];
		bytes[0] = (byte)length;
		buf.get(bytes, 1, length-1);

		if (!EMLITE_CRC.validate(bytes)) {
			short expectedCRC = NumberUtils.decodeShort(bytes, length-3, 2);
			short calcCRC = EMLITE_CRC.calculate(bytes);
			log.error("CRC-16-CCITT does not match; received {}, calculated {}", Format.toHex(expectedCRC), Format.toHex(calcCRC));
			return null;
		}

		buf = ByteBuffer.wrap(bytes, 1, length-3);
		int dst = buf.getInt();
		int src = buf.getInt();
		byte control = buf.get();
		byte format = buf.get();
		byte a = buf.get();
		byte b = buf.get();
		byte c = buf.get();
		ObisId id = new ObisId(a, b, c);
		byte read = buf.get();
		byte[] value = null;
		if (length > 17) {
			value = new byte[length-17];
			buf.get(value);
		}

		return new EmlitePacket(dst, src, control, format, id, read, value);
	}

	public static Codec<EmlitePacket> getCodec() {
		return new AbstractEncodableCodec<EmlitePacket>(EmlitePacket.class) {
			@Override
			public EmlitePacket decode(ByteBuffer buf) {
				return EmlitePacket.decode(buf);
			}
		};
	}

	@Override
	public String toString() {
		return "EmlitePacket ["
				+ "dst=" + Format.toHex(dst)
				+ ", src=" + Format.toHex(src)
				+ ", control=" + control
				+ ", format=" + format
				+ ", id=" + id
				+ ", profileReadTime=" + profileReadTime
				+ ", read=" + read
				+ (value == null ? "" : (", value=" + Format.packHex(value)))
				+ "]";
	}
}


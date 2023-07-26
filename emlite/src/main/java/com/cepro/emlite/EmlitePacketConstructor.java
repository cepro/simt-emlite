package com.cepro.emlite;

import com.cepro.emlite.model.EmlitePacket;
import com.cepro.emlite.model.ObisId;

public class EmlitePacketConstructor {

	public static final byte FORMAT = 1;
	public static final byte READ = 0;
	public static final byte WRITE = 1;

	public final int src;
	public int dst = 0;

	public byte format = FORMAT;

	private byte seq = -1;

	public EmlitePacketConstructor() {
		this(makeSource());
	}

	public EmlitePacketConstructor(int src) {
		this.src = src;
	}

	public EmlitePacketConstructor(int src, int dst) {
		this.src = src;
		this.dst = dst;
	}

	public EmlitePacketConstructor(int src, byte format) {
		this.src = src;
		this.format = format;
	}

	public static int makeSource() {
		double rnd = Math.floor(Math.random() * 0x1000000L);
		return (int)(0x80000000L + (long)rnd);
	}

	public EmlitePacket read(ObisId id) {
		byte control = (byte)(++seq & 0x07);
		return new EmlitePacket(dst, src, control, format, id, READ, null);
	}

	public EmlitePacket read(int readTime) {
		byte control = (byte)(++seq & 0x07);
		return new EmlitePacket(dst, src, control, format, readTime, READ, null);
	}

	public EmlitePacket write(ObisId id, byte[] value) {
		byte control = (byte)(++seq & 0x07);
		return new EmlitePacket(dst, src, control, format, id, WRITE, value);
	}

}


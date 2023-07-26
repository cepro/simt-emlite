package com.cepro.emlite.model;

import java.io.Serializable;
import java.util.regex.Pattern;

import com.blinkhub.lib.util.Format;
import com.blinkhub.lib.util.NumberUtils;

public class ObisId implements Serializable, Comparable<ObisId> {

	private static final long serialVersionUID = -3876650519363080758L;

	public final byte a;
	public final byte b;
	public final byte c;

	public ObisId(byte a, byte b, byte c) {
		this.a = a;
		this.b = b;
		this.c = c;
	}

	public ObisId(byte[] bytes) {
		this(bytes, 0);
	}

	public ObisId(byte[] bytes, int offset) {
		this(bytes[offset++], bytes[offset++], bytes[offset++]);
	}

	public ObisId(int value) {
		a = (byte)((value >> 16) & 0xFF);
		b = (byte)((value >> 8) & 0xFF);
		c = (byte)(value & 0xFF);
	}

	public int intValue() {
		return (NumberUtils.unsign(a) << 16) | (NumberUtils.unsign(b) << 8) | NumberUtils.unsign(c);
	}

	public static ObisId parse(String id) throws NumberFormatException {
		String[] digits = id.split("[.]");
		Pattern p = Pattern.compile("\\p{XDigit}{2}"); 
		if (digits.length != 3) {
			throw new NumberFormatException("Expected ID in format XX.XX.XX");
		}
		if (p.matcher(digits[0]).matches() && p.matcher(digits[1]).matches() && p.matcher(digits[2]).matches()) {
			byte a = Format.parseByte(digits[0], false);
			byte b = Format.parseByte(digits[1], false);
			byte c = Format.parseByte(digits[2], false);
			return new ObisId(a,b,c);
		} else {
			throw new NumberFormatException("Expected ID to contain hex digits XX.XX.XX");
		}
	}

	@Override
	public int hashCode() {
		final int prime = 31;
		int result = 1;
		result = prime * result + a;
		result = prime * result + b;
		result = prime * result + c;
		return result;
	}

	@Override
	public boolean equals(Object obj) {
		if (this == obj)
			return true;
		if (obj == null)
			return false;
		if (getClass() != obj.getClass())
			return false;
		ObisId other = (ObisId) obj;
		if (a != other.a)
			return false;
		if (b != other.b)
			return false;
		if (c != other.c)
			return false;
		return true;
	}

	@Override
	public String toString() {
		return Format.toHex(a) + "." + Format.toHex(b) + "." + Format.toHex(c);
	}

	@Override
	public int compareTo(ObisId o) {
		return (int)Math.signum(intValue() - o.intValue());
	}

}


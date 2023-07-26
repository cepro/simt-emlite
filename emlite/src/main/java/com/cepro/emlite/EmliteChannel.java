package com.cepro.emlite;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.ReadableByteChannel;
import java.nio.channels.WritableByteChannel;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.blinkhub.lib.util.Format;
import com.cepro.emlite.model.EmlitePacket;

public class EmliteChannel {

	private static final Logger log = LoggerFactory.getLogger(EmliteChannel.class);

	private final ReadableByteChannel in;
	private final WritableByteChannel out;
	private final ByteBuffer buffer = ByteBuffer.wrap(new byte[257]);
	private final ByteBuffer bufin = ByteBuffer.allocate(128);

	public EmliteChannel(ReadableByteChannel in, WritableByteChannel out) {
		this.in = in;
		this.out = out;
	}

	public boolean isOpen() {
		return in.isOpen() && out.isOpen();
	}

	public void close() throws IOException {
		try {
			in.close();
		} finally {
			out.close();
		}
	}

	public void write(EmlitePacket packet) throws IOException {
		byte[] bytes = new byte[packet.getLength()];
		ByteBuffer buf = ByteBuffer.wrap(bytes);
		log.trace("Encoding Emlite packet: {}", packet);
		packet.encode(buf);
		log.debug("Sending: {}", Format.toHex(bytes));
		buf.flip();
		while (buf.remaining() > 0) {
			out.write(buf);
		}
	}

	public EmlitePacket read() throws IOException {
		long last = 0;
		while (in.read(bufin) > 0) {
			long curr = System.currentTimeMillis();
			if (curr - last > 5*1000l) {
				buffer.clear();
			}
			last = curr;
			bufin.flip();
			buffer.put(bufin);
			bufin.compact();
			buffer.flip();
			int remaining = EmlitePacket.checkPacket(buffer);
			while (remaining < 0) {
				if (remaining == EmlitePacket.BAD_DELIM || remaining == EmlitePacket.BAD_LENGTH || remaining == EmlitePacket.BAD_CRC) {
					buffer.get();
				}
				if (buffer.remaining() == 0) {
					buffer.clear();
					return null;
				} else {
					remaining = EmlitePacket.checkPacket(buffer);
				}
			}
			if (remaining == 0) {
				EmlitePacket packet = EmlitePacket.decode(buffer);
				log.trace("Decoded Emlite packet: {}", packet);
				buffer.compact();
				return packet;
			} else if (remaining > 0) {
				buffer.compact();
			}
		}
		return null;
	}

}


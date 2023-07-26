package com.cepro.emlite;

import java.net.Socket;
import java.nio.channels.Channels;
import java.nio.channels.ReadableByteChannel;
import java.nio.channels.WritableByteChannel;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class EmliteConnect {

    private static final Logger log = LoggerFactory.getLogger(EmliteConnect.class);

    public static void main(String[] args) throws Exception {
        final String host = "100.79.244.27";
        final int port = 8080;

        EmliteAPI emlite;
        try (Socket socket = new Socket(host, port);
                ReadableByteChannel inputChannel = Channels.newChannel(socket.getInputStream());
                WritableByteChannel outputChannel = Channels.newChannel(socket.getOutputStream())) {
            EmliteChannel ec = new EmliteChannel(
                    inputChannel,
                    outputChannel);
            emlite = new EmliteAPIImpl(ec);
        } catch (Exception e) {
            log.error("Failed to open connection to meter {}", e.toString());
            return;
        }

        String serial = emlite.getSerial().trim();
        log.info("got serial {}", serial);
    }
}

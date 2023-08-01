package com.cepro.emlite.mediator.grpc;

import java.util.concurrent.TimeUnit;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.cepro.mediator.emlite.grpc.EmliteMediatorServiceGrpc;
import com.cepro.mediator.emlite.grpc.GetFirmwareVersionReply;
import com.cepro.mediator.emlite.grpc.GetFirmwareVersionRequest;
import com.cepro.mediator.emlite.grpc.GetHardwareVersionReply;
import com.cepro.mediator.emlite.grpc.GetHardwareVersionRequest;
import com.cepro.mediator.emlite.grpc.GetSerialReply;
import com.cepro.mediator.emlite.grpc.GetSerialRequest;
import com.cepro.mediator.emlite.grpc.SendMessageReply;
import com.cepro.mediator.emlite.grpc.SendMessageRequest;
import com.google.protobuf.ByteString;

import io.grpc.Channel;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import io.grpc.StatusRuntimeException;

public class EmliteMediatorClient {
    private static final Logger log = LoggerFactory.getLogger(EmliteMediatorClient.class);

    private final EmliteMediatorServiceGrpc.EmliteMediatorServiceBlockingStub blockingStub;

    /**
     * Construct client for accessing RouteGuide server using the existing channel.
     */
    public EmliteMediatorClient(Channel channel) {
        blockingStub = EmliteMediatorServiceGrpc.newBlockingStub(channel);
    }

    public void getSerial() {
        log.info("Will try to get serial");
        GetSerialRequest request = GetSerialRequest.newBuilder().build();
        GetSerialReply response;
        try {
            response = blockingStub.getSerial(request);
        } catch (StatusRuntimeException e) {
            log.warn("RPC failed: " + e.getStatus());
            log.warn(e.toString());
            return;
        }
        log.info("Serial: " + response.getSerial());
    }

    public void getHardwareVersion() {
        log.info("Will try to get hardware version");
        GetHardwareVersionRequest request = GetHardwareVersionRequest.newBuilder().build();
        GetHardwareVersionReply response;
        try {
            response = blockingStub.getHardwareVersion(request);
        } catch (StatusRuntimeException e) {
            log.warn("RPC failed: " + e.getStatus());
            log.warn(e.toString());
            return;
        }
        log.info("Hardware Version: " + response.getVersion());
    }

    public void getFirmwareVersion() {
        log.info("Will try to get firmware version");
        GetFirmwareVersionRequest request = GetFirmwareVersionRequest.newBuilder().build();
        GetFirmwareVersionReply response;
        try {
            response = blockingStub.getFirmwareVersion(request);
        } catch (StatusRuntimeException e) {
            log.warn("RPC failed: " + e.getStatus());
            log.warn(e.toString());
            return;
        }
        log.info("Firmware Version: " + response.getVersion());
    }

    public void sendMessage() {
        log.info("Will try to send message ");

        byte[] stubDataFrameBytes = new byte[] { 0x09, 0x08, 0x07 };
        ByteString stubDataFrame = ByteString.copyFrom(stubDataFrameBytes);

        SendMessageRequest request = SendMessageRequest.newBuilder().setDataFrame(stubDataFrame).build();
        SendMessageReply response;
        try {
            response = blockingStub.sendMessage(request);
        } catch (StatusRuntimeException e) {
            log.warn("RPC failed: " + e.getStatus());
            log.warn(e.toString());
            return;
        }
        log.info("response bytes : " + response.getResponse());
    }

    public static void main(String[] args) throws Exception {
        String targetServer = "localhost:50051";
        // them until the application shuts down.
        ManagedChannel channel = ManagedChannelBuilder.forTarget(targetServer)
                // Channels are secure by default (via SSL/TLS). For the example we disable TLS
                // to avoid
                // needing certificates.
                .usePlaintext()
                .build();
        try {
            EmliteMediatorClient client = new EmliteMediatorClient(channel);

            client.getSerial();
            client.getHardwareVersion();
            client.getFirmwareVersion();
            // client.sendMessage();

        } finally {
            // ManagedChannels use resources like threads and TCP connections. To prevent
            // leaking these
            // resources the channel should be shut down when it will no longer be used. If
            // it may be used
            // again leave it running.
            channel.shutdownNow().awaitTermination(5, TimeUnit.SECONDS);
        }
    }
}

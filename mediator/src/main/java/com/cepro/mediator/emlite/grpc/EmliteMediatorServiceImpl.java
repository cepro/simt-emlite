package com.cepro.mediator.emlite.grpc;

import java.io.IOException;
import java.net.Socket;
import java.nio.channels.Channels;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.cepro.emlite.EmliteAPI;
import com.cepro.emlite.EmliteAPIImpl;
import com.cepro.emlite.EmliteChannel;
import com.google.protobuf.ByteString;

import io.grpc.Status;
import io.grpc.stub.StreamObserver;

class EmliteMediatorServiceImpl extends EmliteMediatorServiceGrpc.EmliteMediatorServiceImplBase {
    private static final Logger log = LoggerFactory.getLogger(EmliteMediatorServiceImpl.class);

    private final EmliteAPI emlite;

    public EmliteMediatorServiceImpl() throws IOException {
        final String hostStr = System.getenv("EMLITE_HOST");
        final String portStr = System.getenv("EMLITE_PORT");
        if (hostStr == null || portStr == null) {
            throw new IllegalStateException("EMLITE_HOST and EMLITE_PORT not set");
        }

        final int port;
        try {
            port = Integer.valueOf(portStr);
        } catch (NumberFormatException nfe) {
            throw new IllegalStateException("EMLITE_PORT is not a valid port number");
        }

        final Socket socket = new Socket(hostStr, port);
        final EmliteChannel ec = new EmliteChannel(
                Channels.newChannel(socket.getInputStream()),
                Channels.newChannel(socket.getOutputStream()));
        emlite = new EmliteAPIImpl(ec);
    }

    @Override
    public void getSerial(
            GetSerialRequest req,
            StreamObserver<GetSerialReply> responseObserver) {
        final String serial;
        try {
            serial = emlite.getSerial();
        } catch (IOException ioe) {
            log.error("emlite.getSerial failed: " + ioe.toString());
            responseObserver.onError(
                    Status.INTERNAL.withDescription("emlite IO error").asException());
            return;
        }

        GetSerialReply reply = GetSerialReply
                .newBuilder()
                .setSerial(serial)
                .build();
        responseObserver.onNext(reply);
        responseObserver.onCompleted();
    }

    @Override
    public void getHardwareVersion(
            GetHardwareVersionRequest req,
            StreamObserver<GetHardwareVersionReply> responseObserver) {
        final String version;
        try {
            version = emlite.getHardwareVersion();
        } catch (IOException ioe) {
            log.error("emlite.getHardwareVersion failed: " + ioe.toString());
            responseObserver.onError(
                    Status.INTERNAL.withDescription("emlite IO error").asException());
            return;
        }

        GetHardwareVersionReply reply = GetHardwareVersionReply
                .newBuilder()
                .setVersion(version)
                .build();
        responseObserver.onNext(reply);
        responseObserver.onCompleted();
    }

    @Override
    public void getFirmwareVersion(
            GetFirmwareVersionRequest req,
            StreamObserver<GetFirmwareVersionReply> responseObserver) {
        final String version;
        try {
            version = emlite.getFirmwareVersion();
        } catch (IOException ioe) {
            log.error("emlite.getFirmwareVersion failed: " + ioe.toString());
            responseObserver.onError(
                    Status.INTERNAL.withDescription("emlite IO error").asException());
            return;
        }

        GetFirmwareVersionReply reply = GetFirmwareVersionReply
                .newBuilder()
                .setVersion(version)
                .build();
        responseObserver.onNext(reply);
        responseObserver.onCompleted();
    }

    @Override
    public void sendMessage(
            SendMessageRequest req,
            StreamObserver<SendMessageReply> responseObserver) {
        log.info("received dataFrame: " + req.getDataFrame());

        byte[] stubRspBytes = new byte[] { 0x00, 0x01, 0x02 };
        ByteString stubRsp = ByteString.copyFrom(stubRspBytes);

        SendMessageReply reply = SendMessageReply
                .newBuilder()
                .setResponse(stubRsp)
                .build();
        responseObserver.onNext(reply);
        responseObserver.onCompleted();
    }

}

package com.cepro.emlite;

import java.io.IOException;
import java.util.Calendar;

import com.cepro.emlite.model.ObisId;

public interface EmliteAPI {

	public byte[] getRegister(ObisId id) throws IOException;
	public byte[] getRegister(Integer readTime, EmlitePacketConstructor packetConstructor) throws IOException;
	public byte[] getRegister(ObisId id, EmlitePacketConstructor packetConstructor, byte[] writePayload) throws IOException;

	public Integer getId();

	/**
	 * 
	 * @return {total active import, total active export, total reactive import, total reactive export}
	 * @throws IOException
	 */
	public double[] getElementATotals() throws IOException;
	public double[] getElementBTotals() throws IOException;

	public Integer getInstantaneousVoltage() throws IOException;
	public Double getInstantaneousCurrent() throws IOException;
	public Integer getInstantaneousActivePower() throws IOException;
	public Integer getInstantaneousReactivePower() throws IOException;
	public Double getInstantaneousPowerFactor() throws IOException;
	public Double getInstantaneousFrequency() throws IOException;

	public Integer getAverageVoltage() throws IOException;
	public Double getAverageCurrent() throws IOException;
	public Double getAverageFrequency() throws IOException;

	public Double getTotalActiveImportEnergy() throws IOException;
	public Double getTotalActiveExportEnergy() throws IOException;

	public Calendar getTime() throws IOException;

	public String getSerial() throws IOException;
	public String getHardwareVersion() throws IOException;
	public String getFirmwareVersion() throws IOException;

	public byte[] getProfileLog1(int readTime) throws IOException;
	public byte[] getProfileLog2(int readTime) throws IOException;

	public String getThreePhaseSerial() throws IOException;
	public void initiateThreePhaseRead() throws IOException;
	public byte[] getThreePhaseLogs(byte[] writePayload) throws IOException;

	public Double getPrepayBalance() throws IOException;
	public Boolean getPrepayEnabledFlag() throws IOException;
}


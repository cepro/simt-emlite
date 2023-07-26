package com.cepro.emlite.model;

/**
 * Patterns in Object IDs:
 * <ul>
 * <li>01.xx.xx: Active Import Power</li>
 * <li>02.xx.xx: Active Export Power</li>
 * <li>03.xx.xx: Reactive Power (Import?)</li>
 * <li>0B.xx.xx: Current</li>
 * <li>0C.xx.xx: Voltage</li>
 * <li>0D.xx.xx: Power factor</li>
 * <li>0E.xx.xx: Frequency</li>
 * <li>0x.07.00: Instantaneous Reading</li>
 * <li>0x.18.00: Average Value</li>
 * <li>0x.18.00: Average Value</li>
 * <li>0x.08.00: Total</li>
 * <li>0x.08.01: Channel (1?)</li>
 * </ul>
 * 
 * @author robbie
 *
 */
public enum Obis {
    ElementA(new ObisId((byte) 0xFF, (byte) 0xFF, (byte) 0xFC)),
    ElementB(new ObisId((byte) 0xFF, (byte) 0xFF, (byte) 0xF8)),
    InstantaneousVoltage(new ObisId((byte) 0x0C, (byte) 0x07, (byte) 0x00)),
    InstantaneousCurrent(new ObisId((byte) 0x0B, (byte) 0x07, (byte) 0x00)),
    InstantaneousActivePower(new ObisId((byte) 0x01, (byte) 0x07, (byte) 0x00)),
    InstantaneousReactivePower(new ObisId((byte) 0x03, (byte) 0x07, (byte) 0x00)),
    InstantaneousPowerFactor(new ObisId((byte) 0x0D, (byte) 0x07, (byte) 0x00)),
    InstantaneousFrequency(new ObisId((byte) 0x0E, (byte) 0x07, (byte) 0x00)),
    AverageVoltage(new ObisId((byte) 0x0C, (byte) 0x18, (byte) 0x00)),
    AverageCurrent(new ObisId((byte) 0x0B, (byte) 0x18, (byte) 0x00)),
    AverageFrequency(new ObisId((byte) 0x0E, (byte) 0x18, (byte) 0x00)),
    TotalActiveImportEnergy(new ObisId((byte) 0x01, (byte) 0x08, (byte) 0x00)),
    // ?
    TotalActiveExportEnergy(new ObisId((byte) 0x02, (byte) 0x08, (byte) 0x00)),
    ElementAInstantaneousActivePowerImport(new ObisId((byte) 0x15, (byte) 0x07, (byte) 0x00)),
    ElementBInstantaneousActivePowerImport(new ObisId((byte) 0x29, (byte) 0x07, (byte) 0x00)),
    Time(new ObisId((byte) 0x80, (byte) 0x08, (byte) 0x00)),
    Serial(new ObisId((byte) 0x60, (byte) 0x01, (byte) 0x00)),
    HardwareVersion(new ObisId((byte) 0x60, (byte) 0x80, (byte) 0x00)),
    FirmwareVersion(new ObisId((byte) 0x00, (byte) 0x02, (byte) 0x01)),
    // see #390 - no docs on the following but have reverse engineered these from
    // the data:
    ThreePhaseSerial(new ObisId((byte) 0xD7, (byte) 0xFF, (byte) 0x10)),
    ThreePhaseInitiateRead(new ObisId((byte) 0xD7, (byte) 0x0A, (byte) 0x0C)),
    ThreePhaseRead(new ObisId((byte) 0xD7, (byte) 0x06, (byte) 0x0A)),

    // Prepay Balance ("Credit Level" under SMC Connect > MonetaryInfo)
    PrepayBalance(new ObisId((byte) 0xFF, (byte) 0xC8, (byte) 0x02)),
    PrepayEnabledFlag(new ObisId((byte) 0xFF, (byte) 0xFF, (byte) 0x0D));

    public final ObisId id;

    private Obis(ObisId id) {
        this.id = id;
    }

    public static Obis lookup(ObisId id) {
        for (Obis register : values()) {
            if (register.id.equals(id)) {
                return register;
            }
        }
        return null;
    }

}

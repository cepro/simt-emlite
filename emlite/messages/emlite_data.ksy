meta:
  id: emlite_data
  title: Emlite object protocol (EMOP) data field
  ks-version: 0.10

doc: |
  EMOP data field is embedded in each EMOP frame (see emlite_frame.ksy).
  It contains a 3 byte object id (Obi) and a payload. The Obi identifies what
  the data in the payload relates to. A number of Obis and corresponding data
  are defined in the document "Meter and Smart Module Obis Commands iss1.5.pdf".

params:
  - id: len_data
    type: u1
    doc: Length of the payload field.

seq:
  - id: format
    contents: [0x01]
  - id: object_id
    size: 3
    # want to use an enum like the following commented out line.
    # but there is no u3 so how to make it work with u4?
    # enum: object_id_type
  - id: read_write
    type: u1
    enum: read_write_flags
  - id: payload
    size: len_data - 5

enums:
  read_write_flags:
    0x00: read
    0x01: write

  # See section 1.2.6.2 of the "EMOP EM-Lite Object Protocol" version 1.7.
  # See "Meter and Smart Module Obis Commands"
  # These are actually unused (see comment on object_id above) but are left
  # in for reference.
  # See also enum defined in the grpc interface.
  object_id_type:
    0x800800: time
    0x600100: serial
    0x608000: hardware_version
    0x000201: firmware_version
    0xffc802: prepay_balance
    0xffff0d: prepay_enabled_flag
    0xfffffc: element_a
    0xfffff8: element_b
    0x0c0700: instantaneous_voltage
    0x0b0700: instantaneous_current
    0x010700: instantaneous_active_power
    0x030700: instantaneous_reactive_power
    0x0d0700: instantaneous_power_factor
    0x0e0700: instantaneous_frequency
    0x0c1800: average_voltage
    0x0b1800: average_current
    0x0e1800: average_frequency
    0x010800: total_active_import_energy
    0x020800: total_active_export_energy
    0x150700: element_a_instantaneous_active_power_import
    0x290700: element_b_instantaneous_active_power_import
    0xd7ff10: three_phase_serial
    0xd70a0c: three_phase_initiate_read
    0xd7060a: three_phase_read

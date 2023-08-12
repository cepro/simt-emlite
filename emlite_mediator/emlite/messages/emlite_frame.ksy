meta:
  id: emlite_frame
  title: Emlite object protocol (EMOP) frame
  ks-version: 0.10
  imports:
    - emlite_data

doc: |
  The EMOP protocol exists to enable communication with Emlite (em-lite.co.uk) smart meters.
  In EMOP "all information is exchanged via a fixed format frame".
  That frame format is specified here with reference to the "SS0001 BM Interface Specification".

seq:
  - id: frame_delimeter
    contents: [0x7e]
    doc: Fixed byte marks start of frame
  - id: frame_length
    type: u1
    doc: Total length of the frame in bytes excluding the frame_delimiter
  - id: destination_device_type
    size: 1
  - id: destination_address
    size: 3
  - id: source_device_type
    size: 1
  - id: source_address
    size: 3
  - id: control
    type: u1
  - id: data
    size: len_data
    type: emlite_data(len_data)
  - id: crc16
    size: 2
    doc: |
      The frame check sequence is a 16bit CRC computed over entire length of
      the frame excluding the opening FD and the FSC itself.

instances:
  len_data:
    value: frame_length - 12
  seq_num:
    value: control & 0x01
  ack_nak_code:
    enum: ack_nak_codes
    value: control & 0x80

enums:
  # see section 1.2.5.1 of the SS0001 BM Interface Specification
  ack_nak_codes:
    # Frame FCS error.
    0: ok
    # Frame formatting error.
    1: fcs_error
    # Frame address incorrect.
    2: format_error
    # Frame length incorrect ( or data object length incorrect ).
    3: frame_len_incorrect
    # Maximum requested data payload exceeded.
    4: max_data_payload_exceeded
    # Data object not recognised.
    5: uknown_object_id
    # Security level not granted, attempted write of a read only object or internal storage condition.
    6: security_not_granted
    # Frame address incorrect.
    7: frame_addr_incorrect

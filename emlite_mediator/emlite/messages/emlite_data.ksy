meta:
  id: emlite_data
  title: Emlite object protocol (EMOP) data field
  ks-version: 0.10

doc: |
  EMOP data field is embedded in each EMOP frame (see emlite_frame.ksy).
  Most (see default_rec) contain a 3 byte object id (Obi) and a payload.
  The Obi identifies what the data in the payload relates to. A number of
  Obis and corresponding payloads are defined in the document "Meter and 
  Smart Module Obis Commands iss1.5.pdf".

params:
  - id: len_data
    type: u1
    doc: Length of the data field.

seq:
  - id: format
    type: u1
    enum: record_format
  - id: message
    type:
      switch-on: format
      cases:
        "record_format::default": default_rec(len_data)
        "record_format::profile_log_1": profile_log_rec(len_data)
        "record_format::profile_log_2": profile_log_rec(len_data)

types:
  default_rec:
    doc: Default emlite data format (format 0x01) - most messages use this format
    params:
      - id: len_data
        type: u1
        doc: Length of the data field.
    seq:
      - id: object_id
        size: 3
        doc: |
          ideally would use enum from `emlite_message.object_id_type` here
          but there is no u3 so how to make it work with u4?
          enum: object_id_type
      - id: read_write
        type: u1
        enum: read_write_flags
      - id: payload
        size: len_data - 5

  profile_log_rec:
    doc: Profile log messages use this format (formats 0x03 and 0x04)
    params:
      - id: len_data
        type: u1
        doc: Length of the payload bytes.
    seq:
      - id: timestamp
        type: u4le
        doc: Timestamp to read the profile log from
      - id: response_payload
        size: 80
        if: len_data > 5
        doc: |
          Response only data - when the data field is > 5 bytes of data which
          is the size of the request. The size should then be 80 bytes.

enums:
  read_write_flags:
    0x00: read
    0x01: write
  record_format:
    1: default
    3: profile_log_1
    4: profile_log_2

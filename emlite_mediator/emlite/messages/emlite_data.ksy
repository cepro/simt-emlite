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
    # ideally would use enum from `emlite_response.object_id_type` here
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

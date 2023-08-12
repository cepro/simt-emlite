meta:
  id: emlite_response
  title: Emlite object protocol (EMOP) response data
  ks-version: 0.10

doc: |
  EMOP response data depends on the object being read. 
  This spec defines a number of known response types.
  Some are defined in the document "Meter and Smart Module
  Obis Commands iss1.5.pdf". Some were obtained by reverse
  engineering the protocol.

params:
  - id: len_response
    type: u1
    doc: Length of the response bytes.
  - id: object_id
    type: u4
    enum: object_id_type
    doc: Object id of request that obtained the response bytes.

seq:
  - id: response
    type:
      switch-on: object_id
      cases:
        "object_id_type::time": time_rec
        "object_id_type::serial": serial_rec
        "object_id_type::csq_net_op": csq_net_op_rec
        _: default_rec

types:
  serial_rec:
    seq:
      - id: serial
        type: str
        size-eos: true
        encoding: ASCII
  time_rec:
    seq:
      - id: year
        type: u1
      - id: month
        type: u1
      - id: date
        type: u1
      - id: hour
        type: u1
      - id: minute
        type: u1
      - id: second
        type: u1
      - id: day_of_week
        type: u1
        enum: day_of_week_type
  csq_net_op_rec:
    seq:
      - id: network_operator
        type: b3
      - id: csq
        type: b5
  default_rec:
    seq:
      - id: payload
        size-eos: true

enums:
  day_of_week_type:
    0: monday
    1: tuesday
    2: wednesday
    3: thursday
    4: friday
    5: saturday
    6: sunday

  # See section 1.2.6.2 of the "EMOP EM-Lite Object Protocol" version 1.7.
  # See "Meter and Smart Module Obis Commands"
  #
  # NOTE: this enum would make more sense in a separate ksy file as it's
  #   associated more with requests than responses. however i was unable
  #   to do that and import it in here. so it remains here for now.
  object_id_type:
    8390656: time # 0x800800
    6291712: serial # 0x600100
    6324224: hardware_version # 0x608000
    513: firmware_version # 0x000201
    16762882: prepay_balance # 0xffc802
    16776973: prepay_enabled_flag # 0xffff0d
    16777212: element_a # 0xfffffc
    16777208: element_b # 0xfffff8
    16776477: csq_net_op # 0xfffd1d
    788224: instantaneous_voltage # 0x0c0700
    722688: instantaneous_current # 0x0b0700
    67328: instantaneous_active_power # 0x010700
    198400: instantaneous_reactive_power # 0x030700
    853760: instantaneous_power_factor # 0x0d0700
    919296: instantaneous_frequency # 0x0e0700
    792576: average_voltage # 0x0c1800
    727040: average_current # 0x0b1800
    923648: average_frequency # 0x0e1800
    67584: total_active_import_energy # 0x010800
    133120: total_active_export_energy # 0x020800
    1378048: element_a_instantaneous_active_power_import # 0x150700
    2688768: element_b_instantaneous_active_power_import # 0x290700
    14155536: three_phase_serial # 0xd7ff10
    14092812: three_phase_initiate_read # 0xd70a0c
    14091786: three_phase_read # 0xd7060a

meta:
  id: emlite_message
  title: Emlite object protocol (EMOP) message structure
  ks-version: 0.10

doc: |
  EMOP message data structure depends on the object being read. 
  This spec defines the structure for a number of known EMOP messages.
  Some are defined in the document "Meter and Smart Module Obis Commands
  iss1.5.pdf". Most were obtained by reverse engineering the protocol.

params:
  - id: len_message
    type: u1
    doc: Length of the message bytes.
  - id: object_id
    type: u4
    enum: object_id_type
    doc: Object id of message.

seq:
  - id: message
    type:
      switch-on: object_id
      cases:
        "object_id_type::time": time_rec
        "object_id_type::serial": serial_rec
        "object_id_type::hardware_version": hardware_rec
        "object_id_type::firmware_version": firmware_rec
        "object_id_type::csq_net_op": csq_net_op_rec
        "object_id_type::instantaneous_voltage": instantaneous_voltage_rec
        "object_id_type::prepay_enabled_flag": prepay_enabled_rec
        "object_id_type::prepay_balance": prepay_balance_rec
        "object_id_type::prepay_token_send": prepay_token_send_rec
        "object_id_type::three_phase_instantaneous_voltage_l1": three_phase_instantaneous_voltage_l1_rec
        "object_id_type::three_phase_instantaneous_voltage_l2": three_phase_instantaneous_voltage_l2_rec
        "object_id_type::three_phase_instantaneous_voltage_l3": three_phase_instantaneous_voltage_l3_rec
        "object_id_type::monetary_info_transaction_count": monetary_info_transaction_count_rec
        "object_id_type::monetary_info_transaction_details": monetary_info_transaction_details_rec
        "object_id_type::tariff_time_switch_element_a_or_single": tariff_time_switch_settings_rec
        "object_id_type::tariff_time_switch_element_b": tariff_time_switch_settings_rec
        "object_id_type::tariff_active_standing_charge": u4le_value_rec
        "object_id_type::tariff_active_threshold_mask": tariff_threshold_mask_rec
        "object_id_type::tariff_active_threshold_values": tariff_threshold_values_rec
        "object_id_type::tariff_active_gas": u4le_value_rec
        "object_id_type::tariff_active_tou_rate_current": u1_value_rec
        "object_id_type::tariff_active_block_rate_current": u1_value_rec
        "object_id_type::tariff_active_price_index_current": u1_value_rec
        "object_id_type::tariff_active_price": u4le_value_rec
        "object_id_type::tariff_active_prepayment_emergency_credit": u4le_value_rec
        "object_id_type::tariff_active_prepayment_ecredit_availability": u4le_value_rec
        "object_id_type::tariff_active_prepayment_debt_recovery_rate": u4le_value_rec
        "object_id_type::tariff_active_element_b_tou_rate_current": u1_value_rec
        "object_id_type::tariff_active_element_b_price_index_current": u1_value_rec
        "object_id_type::tariff_active_element_b_price": u4le_value_rec
        "object_id_type::tariff_active_element_b_tou_rate_1": u4le_value_rec
        "object_id_type::tariff_active_element_b_tou_rate_2": u4le_value_rec
        "object_id_type::tariff_active_element_b_tou_rate_3": u4le_value_rec
        "object_id_type::tariff_active_element_b_tou_rate_4": u4le_value_rec
        "object_id_type::tariff_active_block_1_rate_1": u4le_value_rec
        "object_id_type::tariff_active_block_1_rate_2": u4le_value_rec
        "object_id_type::tariff_active_block_1_rate_3": u4le_value_rec
        "object_id_type::tariff_active_block_1_rate_4": u4le_value_rec
        "object_id_type::tariff_active_block_1_rate_5": u4le_value_rec
        "object_id_type::tariff_active_block_1_rate_6": u4le_value_rec
        "object_id_type::tariff_active_block_1_rate_7": u4le_value_rec
        "object_id_type::tariff_active_block_1_rate_8": u4le_value_rec
        # "object_id_type::tariff_active_block_2_rate_1": u4le_value_rec
        # "object_id_type::tariff_active_block_2_rate_2": u4le_value_rec
        # "object_id_type::tariff_active_block_2_rate_3": u4le_value_rec
        # "object_id_type::tariff_active_block_2_rate_4": u4le_value_rec
        # "object_id_type::tariff_active_block_2_rate_5": u4le_value_rec
        # "object_id_type::tariff_active_block_2_rate_6": u4le_value_rec
        # "object_id_type::tariff_active_block_2_rate_7": u4le_value_rec
        # "object_id_type::tariff_active_block_2_rate_8": u4le_value_rec
        # "object_id_type::tariff_active_block_3_rate_1": u4le_value_rec
        # "object_id_type::tariff_active_block_3_rate_2": u4le_value_rec
        # "object_id_type::tariff_active_block_3_rate_3": u4le_value_rec
        # "object_id_type::tariff_active_block_3_rate_4": u4le_value_rec
        # "object_id_type::tariff_active_block_3_rate_5": u4le_value_rec
        # "object_id_type::tariff_active_block_3_rate_6": u4le_value_rec
        # "object_id_type::tariff_active_block_3_rate_7": u4le_value_rec
        # "object_id_type::tariff_active_block_3_rate_8": u4le_value_rec
        # "object_id_type::tariff_active_block_4_rate_1": u4le_value_rec
        # "object_id_type::tariff_active_block_4_rate_2": u4le_value_rec
        # "object_id_type::tariff_active_block_4_rate_3": u4le_value_rec
        # "object_id_type::tariff_active_block_4_rate_4": u4le_value_rec
        # "object_id_type::tariff_active_block_4_rate_5": u4le_value_rec
        # "object_id_type::tariff_active_block_4_rate_6": u4le_value_rec
        # "object_id_type::tariff_active_block_4_rate_7": u4le_value_rec
        # "object_id_type::tariff_active_block_4_rate_8": u4le_value_rec
        # "object_id_type::tariff_active_block_5_rate_1": u4le_value_rec
        # "object_id_type::tariff_active_block_5_rate_2": u4le_value_rec
        # "object_id_type::tariff_active_block_5_rate_3": u4le_value_rec
        # "object_id_type::tariff_active_block_5_rate_4": u4le_value_rec
        # "object_id_type::tariff_active_block_5_rate_5": u4le_value_rec
        # "object_id_type::tariff_active_block_5_rate_6": u4le_value_rec
        # "object_id_type::tariff_active_block_5_rate_7": u4le_value_rec
        # "object_id_type::tariff_active_block_5_rate_8": u4le_value_rec
        # "object_id_type::tariff_active_block_6_rate_1": u4le_value_rec
        # "object_id_type::tariff_active_block_6_rate_2": u4le_value_rec
        # "object_id_type::tariff_active_block_6_rate_3": u4le_value_rec
        # "object_id_type::tariff_active_block_6_rate_4": u4le_value_rec
        # "object_id_type::tariff_active_block_6_rate_5": u4le_value_rec
        # "object_id_type::tariff_active_block_6_rate_6": u4le_value_rec
        # "object_id_type::tariff_active_block_6_rate_7": u4le_value_rec
        # "object_id_type::tariff_active_block_6_rate_8": u4le_value_rec
        # "object_id_type::tariff_active_block_7_rate_1": u4le_value_rec
        # "object_id_type::tariff_active_block_7_rate_2": u4le_value_rec
        # "object_id_type::tariff_active_block_7_rate_3": u4le_value_rec
        # "object_id_type::tariff_active_block_7_rate_4": u4le_value_rec
        # "object_id_type::tariff_active_block_7_rate_5": u4le_value_rec
        # "object_id_type::tariff_active_block_7_rate_6": u4le_value_rec
        # "object_id_type::tariff_active_block_7_rate_7": u4le_value_rec
        # "object_id_type::tariff_active_block_7_rate_8": u4le_value_rec
        # "object_id_type::tariff_active_block_8_rate_1": u4le_value_rec
        # "object_id_type::tariff_active_block_8_rate_2": u4le_value_rec
        # "object_id_type::tariff_active_block_8_rate_3": u4le_value_rec
        # "object_id_type::tariff_active_block_8_rate_4": u4le_value_rec
        # "object_id_type::tariff_active_block_8_rate_5": u4le_value_rec
        # "object_id_type::tariff_active_block_8_rate_6": u4le_value_rec
        # "object_id_type::tariff_active_block_8_rate_7": u4le_value_rec
        # "object_id_type::tariff_active_block_8_rate_8": u4le_value_rec
        "object_id_type::tariff_future_tou_flag": u1_value_rec
        "object_id_type::tariff_future_standing_charge": u4le_value_rec
        "object_id_type::tariff_future_threshold_mask": tariff_threshold_mask_rec
        "object_id_type::tariff_future_threshold_values": tariff_threshold_values_rec
        "object_id_type::tariff_future_activation_datetime": u4le_value_rec
        "object_id_type::tariff_future_gas": u4le_value_rec
        "object_id_type::tariff_future_prepayment_emergency_credit": u4le_value_rec
        "object_id_type::tariff_future_prepayment_ecredit_availability": u4le_value_rec
        "object_id_type::tariff_future_prepayment_debt_recovery_rate": u4le_value_rec
        "object_id_type::tariff_future_element_b_tou_rate_1": u4le_value_rec
        "object_id_type::tariff_future_element_b_tou_rate_2": u4le_value_rec
        "object_id_type::tariff_future_element_b_tou_rate_3": u4le_value_rec
        "object_id_type::tariff_future_element_b_tou_rate_4": u4le_value_rec
        "object_id_type::tariff_future_block_1_rate_1": u4le_value_rec
        "object_id_type::tariff_future_block_1_rate_2": u4le_value_rec
        "object_id_type::tariff_future_block_1_rate_3": u4le_value_rec
        "object_id_type::tariff_future_block_1_rate_4": u4le_value_rec
        "object_id_type::tariff_future_block_1_rate_5": u4le_value_rec
        "object_id_type::tariff_future_block_1_rate_6": u4le_value_rec
        "object_id_type::tariff_future_block_1_rate_7": u4le_value_rec
        "object_id_type::tariff_future_block_1_rate_8": u4le_value_rec
        # "object_id_type::tariff_future_block_2_rate_1": u4le_value_rec
        # "object_id_type::tariff_future_block_2_rate_2": u4le_value_rec
        # "object_id_type::tariff_future_block_2_rate_3": u4le_value_rec
        # "object_id_type::tariff_future_block_2_rate_4": u4le_value_rec
        # "object_id_type::tariff_future_block_2_rate_5": u4le_value_rec
        # "object_id_type::tariff_future_block_2_rate_6": u4le_value_rec
        # "object_id_type::tariff_future_block_2_rate_7": u4le_value_rec
        # "object_id_type::tariff_future_block_2_rate_8": u4le_value_rec
        # "object_id_type::tariff_future_block_3_rate_1": u4le_value_rec
        # "object_id_type::tariff_future_block_3_rate_2": u4le_value_rec
        # "object_id_type::tariff_future_block_3_rate_3": u4le_value_rec
        # "object_id_type::tariff_future_block_3_rate_4": u4le_value_rec
        # "object_id_type::tariff_future_block_3_rate_5": u4le_value_rec
        # "object_id_type::tariff_future_block_3_rate_6": u4le_value_rec
        # "object_id_type::tariff_future_block_3_rate_7": u4le_value_rec
        # "object_id_type::tariff_future_block_3_rate_8": u4le_value_rec
        # "object_id_type::tariff_future_block_4_rate_1": u4le_value_rec
        # "object_id_type::tariff_future_block_4_rate_2": u4le_value_rec
        # "object_id_type::tariff_future_block_4_rate_3": u4le_value_rec
        # "object_id_type::tariff_future_block_4_rate_4": u4le_value_rec
        # "object_id_type::tariff_future_block_4_rate_5": u4le_value_rec
        # "object_id_type::tariff_future_block_4_rate_6": u4le_value_rec
        # "object_id_type::tariff_future_block_4_rate_7": u4le_value_rec
        # "object_id_type::tariff_future_block_4_rate_8": u4le_value_rec
        # "object_id_type::tariff_future_block_5_rate_1": u4le_value_rec
        # "object_id_type::tariff_future_block_5_rate_2": u4le_value_rec
        # "object_id_type::tariff_future_block_5_rate_3": u4le_value_rec
        # "object_id_type::tariff_future_block_5_rate_4": u4le_value_rec
        # "object_id_type::tariff_future_block_5_rate_5": u4le_value_rec
        # "object_id_type::tariff_future_block_5_rate_6": u4le_value_rec
        # "object_id_type::tariff_future_block_5_rate_7": u4le_value_rec
        # "object_id_type::tariff_future_block_5_rate_8": u4le_value_rec
        # "object_id_type::tariff_future_block_6_rate_1": u4le_value_rec
        # "object_id_type::tariff_future_block_6_rate_2": u4le_value_rec
        # "object_id_type::tariff_future_block_6_rate_3": u4le_value_rec
        # "object_id_type::tariff_future_block_6_rate_4": u4le_value_rec
        # "object_id_type::tariff_future_block_6_rate_5": u4le_value_rec
        # "object_id_type::tariff_future_block_6_rate_6": u4le_value_rec
        # "object_id_type::tariff_future_block_6_rate_7": u4le_value_rec
        # "object_id_type::tariff_future_block_6_rate_8": u4le_value_rec
        # "object_id_type::tariff_future_block_7_rate_1": u4le_value_rec
        # "object_id_type::tariff_future_block_7_rate_2": u4le_value_rec
        # "object_id_type::tariff_future_block_7_rate_3": u4le_value_rec
        # "object_id_type::tariff_future_block_7_rate_4": u4le_value_rec
        # "object_id_type::tariff_future_block_7_rate_5": u4le_value_rec
        # "object_id_type::tariff_future_block_7_rate_6": u4le_value_rec
        # "object_id_type::tariff_future_block_7_rate_7": u4le_value_rec
        # "object_id_type::tariff_future_block_7_rate_8": u4le_value_rec
        # "object_id_type::tariff_future_block_8_rate_1": u4le_value_rec
        # "object_id_type::tariff_future_block_8_rate_2": u4le_value_rec
        # "object_id_type::tariff_future_block_8_rate_3": u4le_value_rec
        # "object_id_type::tariff_future_block_8_rate_4": u4le_value_rec
        # "object_id_type::tariff_future_block_8_rate_5": u4le_value_rec
        # "object_id_type::tariff_future_block_8_rate_6": u4le_value_rec
        # "object_id_type::tariff_future_block_8_rate_7": u4le_value_rec
        # "object_id_type::tariff_future_block_8_rate_8": u4le_value_rec

        _: default_rec

types:
  default_rec:
    seq:
      - id: payload
        size-eos: true
  serial_rec:
    seq:
      - id: serial
        type: str
        size-eos: true
        encoding: ASCII
  hardware_rec:
    seq:
      - id: hardware
        type: str
        size-eos: true
        encoding: ASCII
  firmware_rec:
    seq:
      # single phase meters: return 4 bytes ascii string
      # three phase meters: return 2 bytes with meaning not yet known
      # therefore we just get variable length bytes here and let the client
      # try decode it based on length
      - id: version_bytes
        type: u1
        repeat: eos
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
  instantaneous_voltage_rec:
    seq:
      - id: voltage
        type: u2le
  prepay_enabled_rec:
    seq:
      - id: enabled_flag
        type: u1
  prepay_balance_rec:
    seq:
      - id: balance
        type: s4le
  prepay_token_send_rec:
    seq:
      - id: token
        type: str
        size: 20
        encoding: ASCII
  three_phase_instantaneous_voltage_l1_rec:
    seq:
      - id: voltage
        type: u2le
  three_phase_instantaneous_voltage_l2_rec:
    seq:
      - id: voltage
        type: u2le
  three_phase_instantaneous_voltage_l3_rec:
    seq:
      - id: voltage
        type: u2le
  monetary_info_transaction_count_rec:
    seq:
      - id: count
        type: u2le
  monetary_info_transaction_details_rec:
    seq:
      - id: undecoded_bytes
        size: 8
        doc: |
          As yet undecoded - looks like various properties under
          'transaction details' in the emlite software.
      - id: payment_time
        type: u4le
      - id: payment_value
        type: s4le
  tariff_threshold_mask_rec:
    seq:
      - id: rate1
        type: b1
      - id: rate2
        type: b1
      - id: rate3
        type: b1
      - id: rate4
        type: b1
      - id: rate5
        type: b1
      - id: rate6
        type: b1
      - id: rate7
        type: b1
      - id: rate8
        type: b1
  tariff_threshold_values_rec:
    seq:
      - id: th1
        type: u2le
      - id: th2
        type: u2le
      - id: th3
        type: u2le
      - id: th4
        type: u2le
      - id: th5
        type: u2le
      - id: th6
        type: u2le
      - id: th7
        type: u2le
  tariff_time_switch_settings_rec:
    seq:
      - id: switch_settings
        size: 80
        doc: |
          Bytes containing all the various switch settings. We treat it as one
          large block for now as we only want the whole thing zero'd out.
          If in future we need time switches we could define the internals of
          these bytes here.
  u4le_value_rec:
    seq:
      - id: value
        type: u4le
  u1_value_rec:
    seq:
      - id: value
        type: u1

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
    8390656: time # 800800
    6291712: serial # 600100
    6324224: hardware_version # 608000
    513: firmware_version # 000201
    16762882: prepay_balance # ffc802
    16776973: prepay_enabled_flag # ffff0d
    16777212: element_a # fffffc
    16777208: element_b # fffff8
    16776477: csq_net_op # fffd1d
    16762883: prepay_token_send # ffc803
    788224: instantaneous_voltage # 0c0700
    722688: instantaneous_current # 0b0700
    67328: instantaneous_active_power # 010700
    198400: instantaneous_reactive_power # 030700
    853760: instantaneous_power_factor # 0d0700
    919296: instantaneous_frequency # 0e0700
    792576: average_voltage # 0c1800
    727040: average_current # 0b1800
    923648: average_frequency # 0e1800
    67584: total_active_import_energy # 010800
    133120: total_active_export_energy # 020800
    1378048: element_a_instantaneous_active_power_import # 150700
    2688768: element_b_instantaneous_active_power_import # 290700
    14155536: three_phase_serial # d7ff10
    14092812: three_phase_initiate_read # d70a0c
    14091786: three_phase_read # d7060a
    2098944: three_phase_instantaneous_voltage_l1 # 200700
    3409664: three_phase_instantaneous_voltage_l2 # 340700
    4720384: three_phase_instantaneous_voltage_l3 # 480700
    16762942: monetary_info_transaction_count # ffc83e
    16762944: monetary_info_transaction_details # ffc840
    851968: tariff_time_switch_element_a_or_single # 0d0000
    852223: tariff_time_switch_element_b # 0d00ff
    16777038: tariff_active_tou_flag # ffff4e
    16776994: tariff_active_standing_charge # ffff22
    16776992: tariff_active_threshold_mask # ffff20
    16776990: tariff_active_threshold_values # ffff1e
    16763236: tariff_active_gas # ffc964
    16777003: tariff_active_tou_rate_current # ffff2b
    16777004: tariff_active_block_rate_current # ffff2c
    16777005: tariff_active_price_index_current # ffff2d
    16777006: tariff_active_price # ffff2e
    16762885: tariff_active_prepayment_emergency_credit # ffc805
    16762886: tariff_active_prepayment_ecredit_availability # ffc806
    16762887: tariff_active_prepayment_debt_recovery_rate # ffc807
    16777035: tariff_active_element_b_tou_rate_current # ffff4b
    16777036: tariff_active_element_b_price_index_current # ffff4c
    16777037: tariff_active_element_b_price # ffff4d
    16774913: tariff_active_element_b_tou_rate_1 # fff701
    16774914: tariff_active_element_b_tou_rate_2 # fff702
    16774915: tariff_active_element_b_tou_rate_3 # fff703
    16774916: tariff_active_element_b_tou_rate_4 # fff704
    16775425: tariff_active_block_1_rate_1 # fff901
    16775426: tariff_active_block_1_rate_2 # fff902
    16775427: tariff_active_block_1_rate_3 # fff903
    16775428: tariff_active_block_1_rate_4 # fff904
    16775429: tariff_active_block_1_rate_5 # fff905
    16775430: tariff_active_block_1_rate_6 # fff906
    16775431: tariff_active_block_1_rate_7 # fff907
    16775432: tariff_active_block_1_rate_8 # fff908
    # 16775433: tariff_active_block_2_rate_1 # fff909
    # 16775434: tariff_active_block_2_rate_2 # fff90a
    # 16775435: tariff_active_block_2_rate_3 # fff90b
    # 16775436: tariff_active_block_2_rate_4 # fff90c
    # 16775437: tariff_active_block_2_rate_5 # fff90d
    # 16775438: tariff_active_block_2_rate_6 # fff90e
    # 16775439: tariff_active_block_2_rate_7 # fff90f
    # 16775440: tariff_active_block_2_rate_8 # fff910
    # 16775441: tariff_active_block_3_rate_1 # fff911
    # 16775442: tariff_active_block_3_rate_2 # fff912
    # 16775443: tariff_active_block_3_rate_3 # fff913
    # 16775444: tariff_active_block_3_rate_4 # fff914
    # 16775445: tariff_active_block_3_rate_5 # fff915
    # 16775446: tariff_active_block_3_rate_6 # fff916
    # 16775447: tariff_active_block_3_rate_7 # fff917
    # 16775448: tariff_active_block_3_rate_8 # fff918
    # 16775449: tariff_active_block_4_rate_1 # fff919
    # 16775450: tariff_active_block_4_rate_2 # fff91a
    # 16775451: tariff_active_block_4_rate_3 # fff91b
    # 16775452: tariff_active_block_4_rate_4 # fff91c
    # 16775453: tariff_active_block_4_rate_5 # fff91d
    # 16775454: tariff_active_block_4_rate_6 # fff91e
    # 16775455: tariff_active_block_4_rate_7 # fff91f
    # 16775456: tariff_active_block_4_rate_8 # fff920
    # 16775457: tariff_active_block_5_rate_1 # fff921
    # 16775458: tariff_active_block_5_rate_2 # fff922
    # 16775459: tariff_active_block_5_rate_3 # fff923
    # 16775460: tariff_active_block_5_rate_4 # fff924
    # 16775461: tariff_active_block_5_rate_5 # fff925
    # 16775462: tariff_active_block_5_rate_6 # fff926
    # 16775463: tariff_active_block_5_rate_7 # fff927
    # 16775464: tariff_active_block_5_rate_8 # fff928
    # 16775465: tariff_active_block_6_rate_1 # fff929
    # 16775466: tariff_active_block_6_rate_2 # fff92a
    # 16775467: tariff_active_block_6_rate_3 # fff92b
    # 16775468: tariff_active_block_6_rate_4 # fff92c
    # 16775469: tariff_active_block_6_rate_5 # fff92d
    # 16775470: tariff_active_block_6_rate_6 # fff92e
    # 16775471: tariff_active_block_6_rate_7 # fff92f
    # 16775472: tariff_active_block_6_rate_8 # fff930
    # 16775473: tariff_active_block_7_rate_1 # fff931
    # 16775474: tariff_active_block_7_rate_2 # fff932
    # 16775475: tariff_active_block_7_rate_3 # fff933
    # 16775476: tariff_active_block_7_rate_4 # fff934
    # 16775477: tariff_active_block_7_rate_5 # fff935
    # 16775478: tariff_active_block_7_rate_6 # fff936
    # 16775479: tariff_active_block_7_rate_7 # fff937
    # 16775480: tariff_active_block_7_rate_8 # fff938
    # 16775481: tariff_active_block_8_rate_1 # fff939
    # 16775482: tariff_active_block_8_rate_2 # fff93a
    # 16775483: tariff_active_block_8_rate_3 # fff93b
    # 16775484: tariff_active_block_8_rate_4 # fff93c
    # 16775485: tariff_active_block_8_rate_5 # fff93d
    # 16775486: tariff_active_block_8_rate_6 # fff93e
    # 16775487: tariff_active_block_8_rate_7 # fff93f
    # 16775488: tariff_active_block_8_rate_8 # fff940
    16777039: tariff_future_tou_flag # ffff4f
    16776995: tariff_future_standing_charge # ffff23
    16776993: tariff_future_threshold_mask # ffff21
    16776991: tariff_future_threshold_values # ffff1f
    16776996: tariff_future_activation_datetime # ffff24
    16763237: tariff_future_gas # ffc965
    16762888: tariff_future_prepayment_emergency_credit # ffc808
    16762889: tariff_future_prepayment_ecredit_availability # ffc809
    16762890: tariff_future_prepayment_debt_recovery_rate # ffc80a
    16774657: tariff_future_element_b_tou_rate_1 # fff601
    16774658: tariff_future_element_b_tou_rate_2 # fff602
    16774659: tariff_future_element_b_tou_rate_3 # fff603
    16774660: tariff_future_element_b_tou_rate_4 # fff604
    16775169: tariff_future_block_1_rate_1 # fff801
    16775170: tariff_future_block_1_rate_2 # fff802
    16775171: tariff_future_block_1_rate_3 # fff803
    16775172: tariff_future_block_1_rate_4 # fff804
    16775173: tariff_future_block_1_rate_5 # fff805
    16775174: tariff_future_block_1_rate_6 # fff806
    16775175: tariff_future_block_1_rate_7 # fff807
    16775176: tariff_future_block_1_rate_8 # fff808
    # 16775177: tariff_future_block_2_rate_1 # fff809
    # 16775178: tariff_future_block_2_rate_2 # fff80a
    # 16775179: tariff_future_block_2_rate_3 # fff80b
    # 16775180: tariff_future_block_2_rate_4 # fff80c
    # 16775181: tariff_future_block_2_rate_5 # fff80d
    # 16775182: tariff_future_block_2_rate_6 # fff80e
    # 16775183: tariff_future_block_2_rate_7 # fff80f
    # 16775184: tariff_future_block_2_rate_8 # fff810
    # 16775185: tariff_future_block_3_rate_1 # fff811
    # 16775186: tariff_future_block_3_rate_2 # fff812
    # 16775187: tariff_future_block_3_rate_3 # fff813
    # 16775188: tariff_future_block_3_rate_4 # fff814
    # 16775189: tariff_future_block_3_rate_5 # fff815
    # 16775190: tariff_future_block_3_rate_6 # fff816
    # 16775191: tariff_future_block_3_rate_7 # fff817
    # 16775192: tariff_future_block_3_rate_8 # fff818
    # 16775193: tariff_future_block_4_rate_1 # fff819
    # 16775194: tariff_future_block_4_rate_2 # fff81a
    # 16775195: tariff_future_block_4_rate_3 # fff81b
    # 16775196: tariff_future_block_4_rate_4 # fff81c
    # 16775197: tariff_future_block_4_rate_5 # fff81d
    # 16775198: tariff_future_block_4_rate_6 # fff81e
    # 16775199: tariff_future_block_4_rate_7 # fff81f
    # 16775200: tariff_future_block_4_rate_8 # fff820
    # 16775201: tariff_future_block_5_rate_1 # fff821
    # 16775202: tariff_future_block_5_rate_2 # fff822
    # 16775203: tariff_future_block_5_rate_3 # fff823
    # 16775204: tariff_future_block_5_rate_4 # fff824
    # 16775205: tariff_future_block_5_rate_5 # fff825
    # 16775206: tariff_future_block_5_rate_6 # fff826
    # 16775207: tariff_future_block_5_rate_7 # fff827
    # 16775208: tariff_future_block_5_rate_8 # fff828
    # 16775209: tariff_future_block_6_rate_1 # fff829
    # 16775210: tariff_future_block_6_rate_2 # fff82a
    # 16775211: tariff_future_block_6_rate_3 # fff82b
    # 16775212: tariff_future_block_6_rate_4 # fff82c
    # 16775213: tariff_future_block_6_rate_5 # fff82d
    # 16775214: tariff_future_block_6_rate_6 # fff82e
    # 16775215: tariff_future_block_6_rate_7 # fff82f
    # 16775216: tariff_future_block_6_rate_8 # fff830
    # 16775217: tariff_future_block_7_rate_1 # fff831
    # 16775218: tariff_future_block_7_rate_2 # fff832
    # 16775219: tariff_future_block_7_rate_3 # fff833
    # 16775220: tariff_future_block_7_rate_4 # fff834
    # 16775221: tariff_future_block_7_rate_5 # fff835
    # 16775222: tariff_future_block_7_rate_6 # fff836
    # 16775223: tariff_future_block_7_rate_7 # fff837
    # 16775224: tariff_future_block_7_rate_8 # fff838
    # 16775225: tariff_future_block_8_rate_1 # fff839
    # 16775226: tariff_future_block_8_rate_2 # fff83a
    # 16775227: tariff_future_block_8_rate_3 # fff83b
    # 16775228: tariff_future_block_8_rate_4 # fff83c
    # 16775229: tariff_future_block_8_rate_5 # fff83d
    # 16775230: tariff_future_block_8_rate_6 # fff83e
    # 16775231: tariff_future_block_8_rate_7 # fff83f
    # 16775232: tariff_future_block_8_rate_8 # fff840

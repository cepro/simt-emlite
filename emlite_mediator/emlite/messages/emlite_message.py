# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

from enum import Enum

import kaitaistruct
from kaitaistruct import KaitaiStream, ReadWriteKaitaiStruct

if getattr(kaitaistruct, "API_VERSION", (0, 9)) < (0, 9):
    raise Exception(
        "Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s"
        % (kaitaistruct.__version__)
    )


class EmliteMessage(ReadWriteKaitaiStruct):
    """EMOP message data structure depends on the object being read.
    This spec defines the structure for a number of known EMOP messages.
    Some are defined in the document "Meter and Smart Module Obis Commands
    iss1.5.pdf". Most were obtained by reverse engineering the protocol.
    """

    class DayOfWeekType(Enum):
        monday = 0
        tuesday = 1
        wednesday = 2
        thursday = 3
        friday = 4
        saturday = 5
        sunday = 6

    class ObjectIdType(Enum):
        firmware_version = 513
        instantaneous_active_power = 67328
        total_active_import_energy = 67584
        total_active_export_energy = 133120
        instantaneous_reactive_power = 198400
        instantaneous_current = 722688
        average_current = 727040
        instantaneous_voltage = 788224
        average_voltage = 792576
        tariff_time_switch_element_a_or_single = 851968
        tariff_time_switch_element_b = 852223
        instantaneous_power_factor = 853760
        instantaneous_frequency = 919296
        average_frequency = 923648
        element_a_instantaneous_active_power_import = 1378048
        three_phase_instantaneous_voltage_l1 = 2098944
        element_b_instantaneous_active_power_import = 2688768
        three_phase_instantaneous_voltage_l2 = 3409664
        three_phase_instantaneous_voltage_l3 = 4720384
        serial = 6291712
        hardware_version = 6324224
        time = 8390656
        three_phase_read = 14091786
        three_phase_initiate_read = 14092812
        three_phase_serial = 14155536
        prepay_balance = 16762882
        prepay_token_send = 16762883
        tariff_active_prepayment_emergency_credit = 16762885
        tariff_active_prepayment_ecredit_availability = 16762886
        tariff_active_prepayment_debt_recovery_rate = 16762887
        tariff_future_prepayment_emergency_credit = 16762888
        tariff_future_prepayment_ecredit_availability = 16762889
        tariff_future_prepayment_debt_recovery_rate = 16762890
        monetary_info_transaction_count = 16762942
        monetary_info_transaction_details = 16762944
        tariff_active_gas = 16763236
        tariff_future_gas = 16763237
        tariff_future_element_b_tou_rate_1 = 16774657
        tariff_future_element_b_tou_rate_2 = 16774658
        tariff_future_element_b_tou_rate_3 = 16774659
        tariff_future_element_b_tou_rate_4 = 16774660
        tariff_active_element_b_tou_rate_1 = 16774913
        tariff_active_element_b_tou_rate_2 = 16774914
        tariff_active_element_b_tou_rate_3 = 16774915
        tariff_active_element_b_tou_rate_4 = 16774916
        tariff_future_block_1_rate_1 = 16775169
        tariff_future_block_1_rate_2 = 16775170
        tariff_future_block_1_rate_3 = 16775171
        tariff_future_block_1_rate_4 = 16775172
        tariff_future_block_1_rate_5 = 16775173
        tariff_future_block_1_rate_6 = 16775174
        tariff_future_block_1_rate_7 = 16775175
        tariff_future_block_1_rate_8 = 16775176
        tariff_active_block_1_rate_1 = 16775425
        tariff_active_block_1_rate_2 = 16775426
        tariff_active_block_1_rate_3 = 16775427
        tariff_active_block_1_rate_4 = 16775428
        tariff_active_block_1_rate_5 = 16775429
        tariff_active_block_1_rate_6 = 16775430
        tariff_active_block_1_rate_7 = 16775431
        tariff_active_block_1_rate_8 = 16775432
        csq_net_op = 16776477
        prepay_enabled_flag = 16776973
        tariff_active_threshold_values = 16776990
        tariff_future_threshold_values = 16776991
        tariff_active_threshold_mask = 16776992
        tariff_future_threshold_mask = 16776993
        tariff_active_standing_charge = 16776994
        tariff_future_standing_charge = 16776995
        tariff_future_activation_datetime = 16776996
        tariff_active_tou_rate_current = 16777003
        tariff_active_block_rate_current = 16777004
        tariff_active_price_index_current = 16777005
        tariff_active_price = 16777006
        tariff_active_element_b_tou_rate_current = 16777035
        tariff_active_element_b_price_index_current = 16777036
        tariff_active_element_b_price = 16777037
        tariff_active_tou_flag = 16777038
        tariff_future_tou_flag = 16777039
        element_b = 16777208
        element_a = 16777212

    def __init__(self, len_message, object_id, _io=None, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self.len_message = len_message
        self.object_id = object_id

    def _read(self):
        _on = self.object_id
        if _on == EmliteMessage.ObjectIdType.tariff_active_element_b_tou_rate_3:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_threshold_values:
            pass
            self.message = EmliteMessage.TariffThresholdValuesRec(
                self._io, self, self._root
            )
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_4:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif (
            _on
            == EmliteMessage.ObjectIdType.tariff_active_prepayment_ecredit_availability
        ):
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_4:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_8:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_2:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_element_b_tou_rate_1:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.three_phase_instantaneous_voltage_l3:
            pass
            self.message = EmliteMessage.ThreePhaseInstantaneousVoltageL3Rec(
                self._io, self, self._root
            )
            self.message._read()
        elif (
            _on
            == EmliteMessage.ObjectIdType.tariff_active_element_b_price_index_current
        ):
            pass
            self.message = EmliteMessage.U1ValueRec(self._io, self, self._root)
            self.message._read()
        elif (
            _on == EmliteMessage.ObjectIdType.tariff_active_prepayment_emergency_credit
        ):
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_activation_datetime:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_element_b_tou_rate_4:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_time_switch_element_a_or_single:
            pass
            self.message = EmliteMessage.TariffTimeSwitchSettingsRec(
                self._io, self, self._root
            )
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.prepay_token_send:
            pass
            self.message = EmliteMessage.PrepayTokenSendRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.csq_net_op:
            pass
            self.message = EmliteMessage.CsqNetOpRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_8:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_element_b_tou_rate_2:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_7:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.hardware_version:
            pass
            self.message = EmliteMessage.HardwareRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_standing_charge:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_element_b_tou_rate_1:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif (
            _on
            == EmliteMessage.ObjectIdType.tariff_future_prepayment_debt_recovery_rate
        ):
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.time:
            pass
            self.message = EmliteMessage.TimeRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_1:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif (
            _on == EmliteMessage.ObjectIdType.tariff_future_prepayment_emergency_credit
        ):
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_3:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_5:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.monetary_info_transaction_details:
            pass
            self.message = EmliteMessage.MonetaryInfoTransactionDetailsRec(
                self._io, self, self._root
            )
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_time_switch_element_b:
            pass
            self.message = EmliteMessage.TariffTimeSwitchSettingsRec(
                self._io, self, self._root
            )
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.three_phase_instantaneous_voltage_l1:
            pass
            self.message = EmliteMessage.ThreePhaseInstantaneousVoltageL1Rec(
                self._io, self, self._root
            )
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_standing_charge:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.serial:
            pass
            self.message = EmliteMessage.SerialRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_1:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.instantaneous_voltage:
            pass
            self.message = EmliteMessage.InstantaneousVoltageRec(
                self._io, self, self._root
            )
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_gas:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_6:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_element_b_tou_rate_2:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_6:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_gas:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.prepay_balance:
            pass
            self.message = EmliteMessage.PrepayBalanceRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_price_index_current:
            pass
            self.message = EmliteMessage.U1ValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_2:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_3:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_tou_rate_current:
            pass
            self.message = EmliteMessage.U1ValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_threshold_values:
            pass
            self.message = EmliteMessage.TariffThresholdValuesRec(
                self._io, self, self._root
            )
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_element_b_tou_rate_3:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.three_phase_instantaneous_voltage_l2:
            pass
            self.message = EmliteMessage.ThreePhaseInstantaneousVoltageL2Rec(
                self._io, self, self._root
            )
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_element_b_tou_rate_current:
            pass
            self.message = EmliteMessage.U1ValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_tou_flag:
            pass
            self.message = EmliteMessage.U1ValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_7:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_rate_current:
            pass
            self.message = EmliteMessage.U1ValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_5:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_threshold_mask:
            pass
            self.message = EmliteMessage.TariffThresholdMaskRec(
                self._io, self, self._root
            )
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_element_b_tou_rate_4:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.prepay_enabled_flag:
            pass
            self.message = EmliteMessage.PrepayEnabledRec(self._io, self, self._root)
            self.message._read()
        elif (
            _on
            == EmliteMessage.ObjectIdType.tariff_active_prepayment_debt_recovery_rate
        ):
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_element_b_price:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_price:
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.firmware_version:
            pass
            self.message = EmliteMessage.FirmwareRec(self._io, self, self._root)
            self.message._read()
        elif (
            _on
            == EmliteMessage.ObjectIdType.tariff_future_prepayment_ecredit_availability
        ):
            pass
            self.message = EmliteMessage.U4leValueRec(self._io, self, self._root)
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_threshold_mask:
            pass
            self.message = EmliteMessage.TariffThresholdMaskRec(
                self._io, self, self._root
            )
            self.message._read()
        elif _on == EmliteMessage.ObjectIdType.monetary_info_transaction_count:
            pass
            self.message = EmliteMessage.MonetaryInfoTransactionCountRec(
                self._io, self, self._root
            )
            self.message._read()
        else:
            pass
            self.message = EmliteMessage.DefaultRec(self._io, self, self._root)
            self.message._read()

    def _fetch_instances(self):
        pass
        _on = self.object_id
        if _on == EmliteMessage.ObjectIdType.tariff_active_element_b_tou_rate_3:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_threshold_values:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_4:
            pass
            self.message._fetch_instances()
        elif (
            _on
            == EmliteMessage.ObjectIdType.tariff_active_prepayment_ecredit_availability
        ):
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_4:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_8:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_2:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_element_b_tou_rate_1:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.three_phase_instantaneous_voltage_l3:
            pass
            self.message._fetch_instances()
        elif (
            _on
            == EmliteMessage.ObjectIdType.tariff_active_element_b_price_index_current
        ):
            pass
            self.message._fetch_instances()
        elif (
            _on == EmliteMessage.ObjectIdType.tariff_active_prepayment_emergency_credit
        ):
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_activation_datetime:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_element_b_tou_rate_4:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_time_switch_element_a_or_single:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.prepay_token_send:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.csq_net_op:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_8:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_element_b_tou_rate_2:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_7:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.hardware_version:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_standing_charge:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_element_b_tou_rate_1:
            pass
            self.message._fetch_instances()
        elif (
            _on
            == EmliteMessage.ObjectIdType.tariff_future_prepayment_debt_recovery_rate
        ):
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.time:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_1:
            pass
            self.message._fetch_instances()
        elif (
            _on == EmliteMessage.ObjectIdType.tariff_future_prepayment_emergency_credit
        ):
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_3:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_5:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.monetary_info_transaction_details:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_time_switch_element_b:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.three_phase_instantaneous_voltage_l1:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_standing_charge:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.serial:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_1:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.instantaneous_voltage:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_gas:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_6:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_element_b_tou_rate_2:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_6:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_gas:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.prepay_balance:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_price_index_current:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_2:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_3:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_tou_rate_current:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_threshold_values:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_element_b_tou_rate_3:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.three_phase_instantaneous_voltage_l2:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_element_b_tou_rate_current:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_tou_flag:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_7:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_rate_current:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_5:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_threshold_mask:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_future_element_b_tou_rate_4:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.prepay_enabled_flag:
            pass
            self.message._fetch_instances()
        elif (
            _on
            == EmliteMessage.ObjectIdType.tariff_active_prepayment_debt_recovery_rate
        ):
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_element_b_price:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_price:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.firmware_version:
            pass
            self.message._fetch_instances()
        elif (
            _on
            == EmliteMessage.ObjectIdType.tariff_future_prepayment_ecredit_availability
        ):
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.tariff_active_threshold_mask:
            pass
            self.message._fetch_instances()
        elif _on == EmliteMessage.ObjectIdType.monetary_info_transaction_count:
            pass
            self.message._fetch_instances()
        else:
            pass
            self.message._fetch_instances()

    def _write__seq(self, io=None):
        super(EmliteMessage, self)._write__seq(io)
        _on = self.object_id
        if _on == EmliteMessage.ObjectIdType.tariff_active_element_b_tou_rate_3:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_active_threshold_values:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_4:
            pass
            self.message._write__seq(self._io)
        elif (
            _on
            == EmliteMessage.ObjectIdType.tariff_active_prepayment_ecredit_availability
        ):
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_4:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_8:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_2:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_future_element_b_tou_rate_1:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.three_phase_instantaneous_voltage_l3:
            pass
            self.message._write__seq(self._io)
        elif (
            _on
            == EmliteMessage.ObjectIdType.tariff_active_element_b_price_index_current
        ):
            pass
            self.message._write__seq(self._io)
        elif (
            _on == EmliteMessage.ObjectIdType.tariff_active_prepayment_emergency_credit
        ):
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_future_activation_datetime:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_active_element_b_tou_rate_4:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_time_switch_element_a_or_single:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.prepay_token_send:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.csq_net_op:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_8:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_future_element_b_tou_rate_2:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_7:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.hardware_version:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_future_standing_charge:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_active_element_b_tou_rate_1:
            pass
            self.message._write__seq(self._io)
        elif (
            _on
            == EmliteMessage.ObjectIdType.tariff_future_prepayment_debt_recovery_rate
        ):
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.time:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_1:
            pass
            self.message._write__seq(self._io)
        elif (
            _on == EmliteMessage.ObjectIdType.tariff_future_prepayment_emergency_credit
        ):
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_3:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_5:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.monetary_info_transaction_details:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_time_switch_element_b:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.three_phase_instantaneous_voltage_l1:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_active_standing_charge:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.serial:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_1:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.instantaneous_voltage:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_active_gas:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_6:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_active_element_b_tou_rate_2:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_6:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_future_gas:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.prepay_balance:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_active_price_index_current:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_2:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_3:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_active_tou_rate_current:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_future_threshold_values:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_future_element_b_tou_rate_3:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.three_phase_instantaneous_voltage_l2:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_active_element_b_tou_rate_current:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_future_tou_flag:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_7:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_rate_current:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_5:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_future_threshold_mask:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_future_element_b_tou_rate_4:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.prepay_enabled_flag:
            pass
            self.message._write__seq(self._io)
        elif (
            _on
            == EmliteMessage.ObjectIdType.tariff_active_prepayment_debt_recovery_rate
        ):
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_active_element_b_price:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_active_price:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.firmware_version:
            pass
            self.message._write__seq(self._io)
        elif (
            _on
            == EmliteMessage.ObjectIdType.tariff_future_prepayment_ecredit_availability
        ):
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.tariff_active_threshold_mask:
            pass
            self.message._write__seq(self._io)
        elif _on == EmliteMessage.ObjectIdType.monetary_info_transaction_count:
            pass
            self.message._write__seq(self._io)
        else:
            pass
            self.message._write__seq(self._io)

    def _check(self):
        pass
        _on = self.object_id
        if _on == EmliteMessage.ObjectIdType.tariff_active_element_b_tou_rate_3:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_active_threshold_values:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_4:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif (
            _on
            == EmliteMessage.ObjectIdType.tariff_active_prepayment_ecredit_availability
        ):
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_4:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_8:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_2:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_future_element_b_tou_rate_1:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.three_phase_instantaneous_voltage_l3:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif (
            _on
            == EmliteMessage.ObjectIdType.tariff_active_element_b_price_index_current
        ):
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif (
            _on == EmliteMessage.ObjectIdType.tariff_active_prepayment_emergency_credit
        ):
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_future_activation_datetime:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_active_element_b_tou_rate_4:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_time_switch_element_a_or_single:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.prepay_token_send:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.csq_net_op:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_8:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_future_element_b_tou_rate_2:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_7:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.hardware_version:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_future_standing_charge:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_active_element_b_tou_rate_1:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif (
            _on
            == EmliteMessage.ObjectIdType.tariff_future_prepayment_debt_recovery_rate
        ):
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.time:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_1:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif (
            _on == EmliteMessage.ObjectIdType.tariff_future_prepayment_emergency_credit
        ):
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_3:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_5:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.monetary_info_transaction_details:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_time_switch_element_b:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.three_phase_instantaneous_voltage_l1:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_active_standing_charge:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.serial:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_1:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.instantaneous_voltage:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_active_gas:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_6:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_active_element_b_tou_rate_2:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_6:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_future_gas:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.prepay_balance:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_active_price_index_current:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_1_rate_2:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_3:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_active_tou_rate_current:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_future_threshold_values:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_future_element_b_tou_rate_3:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.three_phase_instantaneous_voltage_l2:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_active_element_b_tou_rate_current:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_future_tou_flag:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_7:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_active_block_rate_current:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_future_block_1_rate_5:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_future_threshold_mask:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_future_element_b_tou_rate_4:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.prepay_enabled_flag:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif (
            _on
            == EmliteMessage.ObjectIdType.tariff_active_prepayment_debt_recovery_rate
        ):
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_active_element_b_price:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_active_price:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.firmware_version:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif (
            _on
            == EmliteMessage.ObjectIdType.tariff_future_prepayment_ecredit_availability
        ):
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.tariff_active_threshold_mask:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        elif _on == EmliteMessage.ObjectIdType.monetary_info_transaction_count:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )
        else:
            pass
            if self.message._root != self._root:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._root, self._root
                )
            if self.message._parent != self:
                raise kaitaistruct.ConsistencyError(
                    "message", self.message._parent, self
                )

    class MonetaryInfoTransactionCountRec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.count = self._io.read_u2le()

        def _fetch_instances(self):
            pass

        def _write__seq(self, io=None):
            super(EmliteMessage.MonetaryInfoTransactionCountRec, self)._write__seq(io)
            self._io.write_u2le(self.count)

        def _check(self):
            pass

    class ThreePhaseInstantaneousVoltageL1Rec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.voltage = self._io.read_u2le()

        def _fetch_instances(self):
            pass

        def _write__seq(self, io=None):
            super(EmliteMessage.ThreePhaseInstantaneousVoltageL1Rec, self)._write__seq(
                io
            )
            self._io.write_u2le(self.voltage)

        def _check(self):
            pass

    class SerialRec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.serial = (self._io.read_bytes_full()).decode("ASCII")

        def _fetch_instances(self):
            pass

        def _write__seq(self, io=None):
            super(EmliteMessage.SerialRec, self)._write__seq(io)
            self._io.write_bytes((self.serial).encode("ASCII"))
            if not self._io.is_eof():
                raise kaitaistruct.ConsistencyError(
                    "serial", self._io.size() - self._io.pos(), 0
                )

        def _check(self):
            pass

    class PrepayBalanceRec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.balance = self._io.read_s4le()

        def _fetch_instances(self):
            pass

        def _write__seq(self, io=None):
            super(EmliteMessage.PrepayBalanceRec, self)._write__seq(io)
            self._io.write_s4le(self.balance)

        def _check(self):
            pass

    class PrepayTokenSendRec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.token = (self._io.read_bytes(20)).decode("ASCII")

        def _fetch_instances(self):
            pass

        def _write__seq(self, io=None):
            super(EmliteMessage.PrepayTokenSendRec, self)._write__seq(io)
            self._io.write_bytes((self.token).encode("ASCII"))

        def _check(self):
            pass
            if len((self.token).encode("ASCII")) != 20:
                raise kaitaistruct.ConsistencyError(
                    "token", len((self.token).encode("ASCII")), 20
                )

    class U1ValueRec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.value = self._io.read_u1()

        def _fetch_instances(self):
            pass

        def _write__seq(self, io=None):
            super(EmliteMessage.U1ValueRec, self)._write__seq(io)
            self._io.write_u1(self.value)

        def _check(self):
            pass

    class MonetaryInfoTransactionDetailsRec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.undecoded_bytes = self._io.read_bytes(8)
            self.payment_time = self._io.read_u4le()
            self.payment_value = self._io.read_s4le()

        def _fetch_instances(self):
            pass

        def _write__seq(self, io=None):
            super(EmliteMessage.MonetaryInfoTransactionDetailsRec, self)._write__seq(io)
            self._io.write_bytes(self.undecoded_bytes)
            self._io.write_u4le(self.payment_time)
            self._io.write_s4le(self.payment_value)

        def _check(self):
            pass
            if len(self.undecoded_bytes) != 8:
                raise kaitaistruct.ConsistencyError(
                    "undecoded_bytes", len(self.undecoded_bytes), 8
                )

    class CsqNetOpRec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.network_operator = self._io.read_bits_int_be(3)
            self.csq = self._io.read_bits_int_be(5)

        def _fetch_instances(self):
            pass

        def _write__seq(self, io=None):
            super(EmliteMessage.CsqNetOpRec, self)._write__seq(io)
            self._io.write_bits_int_be(3, self.network_operator)
            self._io.write_bits_int_be(5, self.csq)

        def _check(self):
            pass

    class TariffThresholdMaskRec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.rate1 = self._io.read_bits_int_be(1) != 0
            self.rate2 = self._io.read_bits_int_be(1) != 0
            self.rate3 = self._io.read_bits_int_be(1) != 0
            self.rate4 = self._io.read_bits_int_be(1) != 0
            self.rate5 = self._io.read_bits_int_be(1) != 0
            self.rate6 = self._io.read_bits_int_be(1) != 0
            self.rate7 = self._io.read_bits_int_be(1) != 0
            self.rate8 = self._io.read_bits_int_be(1) != 0

        def _fetch_instances(self):
            pass

        def _write__seq(self, io=None):
            super(EmliteMessage.TariffThresholdMaskRec, self)._write__seq(io)
            self._io.write_bits_int_be(1, int(self.rate1))
            self._io.write_bits_int_be(1, int(self.rate2))
            self._io.write_bits_int_be(1, int(self.rate3))
            self._io.write_bits_int_be(1, int(self.rate4))
            self._io.write_bits_int_be(1, int(self.rate5))
            self._io.write_bits_int_be(1, int(self.rate6))
            self._io.write_bits_int_be(1, int(self.rate7))
            self._io.write_bits_int_be(1, int(self.rate8))

        def _check(self):
            pass

    class ThreePhaseInstantaneousVoltageL3Rec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.voltage = self._io.read_u2le()

        def _fetch_instances(self):
            pass

        def _write__seq(self, io=None):
            super(EmliteMessage.ThreePhaseInstantaneousVoltageL3Rec, self)._write__seq(
                io
            )
            self._io.write_u2le(self.voltage)

        def _check(self):
            pass

    class InstantaneousVoltageRec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.voltage = self._io.read_u2le()

        def _fetch_instances(self):
            pass

        def _write__seq(self, io=None):
            super(EmliteMessage.InstantaneousVoltageRec, self)._write__seq(io)
            self._io.write_u2le(self.voltage)

        def _check(self):
            pass

    class FirmwareRec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.version_bytes = []
            i = 0
            while not self._io.is_eof():
                self.version_bytes.append(self._io.read_u1())
                i += 1

        def _fetch_instances(self):
            pass
            for i in range(len(self.version_bytes)):
                pass

        def _write__seq(self, io=None):
            super(EmliteMessage.FirmwareRec, self)._write__seq(io)
            for i in range(len(self.version_bytes)):
                pass
                if self._io.is_eof():
                    raise kaitaistruct.ConsistencyError(
                        "version_bytes", self._io.size() - self._io.pos(), 0
                    )
                self._io.write_u1(self.version_bytes[i])

            if not self._io.is_eof():
                raise kaitaistruct.ConsistencyError(
                    "version_bytes", self._io.size() - self._io.pos(), 0
                )

        def _check(self):
            pass
            for i in range(len(self.version_bytes)):
                pass

    class ThreePhaseInstantaneousVoltageL2Rec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.voltage = self._io.read_u2le()

        def _fetch_instances(self):
            pass

        def _write__seq(self, io=None):
            super(EmliteMessage.ThreePhaseInstantaneousVoltageL2Rec, self)._write__seq(
                io
            )
            self._io.write_u2le(self.voltage)

        def _check(self):
            pass

    class PrepayEnabledRec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.enabled_flag = self._io.read_u1()

        def _fetch_instances(self):
            pass

        def _write__seq(self, io=None):
            super(EmliteMessage.PrepayEnabledRec, self)._write__seq(io)
            self._io.write_u1(self.enabled_flag)

        def _check(self):
            pass

    class U4leValueRec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.value = self._io.read_u4le()

        def _fetch_instances(self):
            pass

        def _write__seq(self, io=None):
            super(EmliteMessage.U4leValueRec, self)._write__seq(io)
            self._io.write_u4le(self.value)

        def _check(self):
            pass

    class HardwareRec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.hardware = (self._io.read_bytes_full()).decode("ASCII")

        def _fetch_instances(self):
            pass

        def _write__seq(self, io=None):
            super(EmliteMessage.HardwareRec, self)._write__seq(io)
            self._io.write_bytes((self.hardware).encode("ASCII"))
            if not self._io.is_eof():
                raise kaitaistruct.ConsistencyError(
                    "hardware", self._io.size() - self._io.pos(), 0
                )

        def _check(self):
            pass

    class TariffTimeSwitchSettingsRec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.switch_settings = self._io.read_bytes(80)

        def _fetch_instances(self):
            pass

        def _write__seq(self, io=None):
            super(EmliteMessage.TariffTimeSwitchSettingsRec, self)._write__seq(io)
            self._io.write_bytes(self.switch_settings)

        def _check(self):
            pass
            if len(self.switch_settings) != 80:
                raise kaitaistruct.ConsistencyError(
                    "switch_settings", len(self.switch_settings), 80
                )

    class TariffThresholdValuesRec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.th1 = self._io.read_u2le()
            self.th2 = self._io.read_u2le()
            self.th3 = self._io.read_u2le()
            self.th4 = self._io.read_u2le()
            self.th5 = self._io.read_u2le()
            self.th6 = self._io.read_u2le()
            self.th7 = self._io.read_u2le()

        def _fetch_instances(self):
            pass

        def _write__seq(self, io=None):
            super(EmliteMessage.TariffThresholdValuesRec, self)._write__seq(io)
            self._io.write_u2le(self.th1)
            self._io.write_u2le(self.th2)
            self._io.write_u2le(self.th3)
            self._io.write_u2le(self.th4)
            self._io.write_u2le(self.th5)
            self._io.write_u2le(self.th6)
            self._io.write_u2le(self.th7)

        def _check(self):
            pass

    class TimeRec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.year = self._io.read_u1()
            self.month = self._io.read_u1()
            self.date = self._io.read_u1()
            self.hour = self._io.read_u1()
            self.minute = self._io.read_u1()
            self.second = self._io.read_u1()
            self.day_of_week = KaitaiStream.resolve_enum(
                EmliteMessage.DayOfWeekType, self._io.read_u1()
            )

        def _fetch_instances(self):
            pass

        def _write__seq(self, io=None):
            super(EmliteMessage.TimeRec, self)._write__seq(io)
            self._io.write_u1(self.year)
            self._io.write_u1(self.month)
            self._io.write_u1(self.date)
            self._io.write_u1(self.hour)
            self._io.write_u1(self.minute)
            self._io.write_u1(self.second)
            self._io.write_u1(self.day_of_week.value)

        def _check(self):
            pass

    class DefaultRec(ReadWriteKaitaiStruct):
        def __init__(self, _io=None, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root

        def _read(self):
            self.payload = self._io.read_bytes_full()

        def _fetch_instances(self):
            pass

        def _write__seq(self, io=None):
            super(EmliteMessage.DefaultRec, self)._write__seq(io)
            self._io.write_bytes(self.payload)
            if not self._io.is_eof():
                raise kaitaistruct.ConsistencyError(
                    "payload", self._io.size() - self._io.pos(), 0
                )

        def _check(self):
            pass

import unittest

from kaitaistruct import BytesIO, KaitaiStream

from emlite_mediator.emlite.messages.emlite_message import EmliteMessage


class TestEmliteMessage(unittest.TestCase):
    def test_serial(self):
        message_hex = "454d4c32313337353830373631202020"
        message = self._deserialize(EmliteMessage.ObjectIdType.serial, message_hex)
        self.assertEqual(message.serial.strip(), "EML2137580761")

    def test_hardware(self):
        def rsp_to_hardware(rsp_hex):
            return (
                self._deserialize(EmliteMessage.ObjectIdType.hardware_version, rsp_hex)
                .hardware.replace("\u0000", "")
                .strip()
            )

        self.assertEqual(rsp_to_hardware("36437720"), "6Cw")
        self.assertEqual(rsp_to_hardware("36430000"), "6C")
        self.assertEqual(rsp_to_hardware("33417720"), "3Aw")

    def test_time(self):
        message_hex = "17080615000100"
        message = self._deserialize(EmliteMessage.ObjectIdType.time, message_hex)
        self.assertEqual(message.year, 23)
        self.assertEqual(message.month, 8)
        self.assertEqual(message.date, 6)
        self.assertEqual(message.hour, 21)
        self.assertEqual(message.minute, 0)
        self.assertEqual(message.second, 1)
        self.assertEqual(message.day_of_week, EmliteMessage.DayOfWeekType.monday)

    def test_csq(self):
        # signal 16 / operator 'O2'
        message = self._deserialize(EmliteMessage.ObjectIdType.csq_net_op, "30")
        self.assertEqual(message.csq, 16)

        # signal 12 / operator 'vodafone'
        message = self._deserialize(EmliteMessage.ObjectIdType.csq_net_op, "4c")
        self.assertEqual(message.csq, 12)

        # signal 16 / operator 'O2'
        message = self._deserialize(EmliteMessage.ObjectIdType.csq_net_op, "29")
        self.assertEqual(message.csq, 9)

    def test_prepay_flag(self):
        message = self._deserialize(
            EmliteMessage.ObjectIdType.prepay_enabled_flag, "00"
        )
        self.assertEqual(message.enabled_flag, 0)
        message = self._deserialize(
            EmliteMessage.ObjectIdType.prepay_enabled_flag, "01"
        )
        self.assertEqual(message.enabled_flag, 1)

    def test_prepay_balance(self):
        message = self._deserialize(
            EmliteMessage.ObjectIdType.prepay_balance, "E0930400"
        )
        self.assertEqual(message.balance, 300000)  # 3.00 GBP
        message = self._deserialize(
            EmliteMessage.ObjectIdType.prepay_balance, "30630300"
        )
        self.assertEqual(message.balance, 222000)  # 2.22 GBP
        message = self._deserialize(
            EmliteMessage.ObjectIdType.prepay_balance, "c07a03fe"
        )
        self.assertEqual(message.balance, -33326400)  # -333.264 GBP

    def test_instantaneous_voltage(self):
        message = self._deserialize(
            EmliteMessage.ObjectIdType.instantaneous_voltage, "5209"
        )
        self.assertEqual(message.voltage, 2386)  # 238.6

    def test_threephase_voltage(self):
        message = self._deserialize(
            EmliteMessage.ObjectIdType.three_phase_instantaneous_voltage_l1, "5209"
        )
        self.assertEqual(message.voltage, 2386)  # 238.6
        message = self._deserialize(
            EmliteMessage.ObjectIdType.three_phase_instantaneous_voltage_l2, "4C09"
        )
        self.assertEqual(message.voltage, 2380)  # 238.0
        message = self._deserialize(
            EmliteMessage.ObjectIdType.three_phase_instantaneous_voltage_l3, "5D09"
        )
        self.assertEqual(message.voltage, 2397)  # 239.7

    def test_threshold_mask(self):
        message = self._deserialize(
            EmliteMessage.ObjectIdType.tariff_active_threshold_mask, "01"
        )
        self.assertEqual(message.rate1, 1)
        self.assertEqual(message.rate2, 0)
        self.assertEqual(message.rate3, 0)
        self.assertEqual(message.rate4, 0)
        self.assertEqual(message.rate5, 0)
        self.assertEqual(message.rate6, 0)
        self.assertEqual(message.rate7, 0)
        self.assertEqual(message.rate8, 0)

        message = self._deserialize(
            EmliteMessage.ObjectIdType.tariff_active_threshold_mask, "21"
        )
        self.assertEqual(message.rate1, 1)
        self.assertEqual(message.rate2, 0)
        self.assertEqual(message.rate3, 0)
        self.assertEqual(message.rate4, 0)
        self.assertEqual(message.rate5, 0)
        self.assertEqual(message.rate6, 1)
        self.assertEqual(message.rate7, 0)
        self.assertEqual(message.rate8, 0)

    def _deserialize(self, object_id, message_hex):
        rsp_bytes = bytearray.fromhex(message_hex)
        data = EmliteMessage(
            len(rsp_bytes), object_id, KaitaiStream(BytesIO(rsp_bytes))
        )
        data._read()
        return data.message

import unittest

from kaitaistruct import KaitaiStream, BytesIO

from emlite_mediator.emlite.messages.emlite_response import EmliteResponse


class TestEmliteResponse(unittest.TestCase):
    def test_serial(self):
        response_hex = "454d4c32313337353830373631202020"
        response = self._deserialize(
            EmliteResponse.ObjectIdType.serial, response_hex)
        self.assertEqual(response.serial.strip(), 'EML2137580761')

    def test_hardware(self):
        def rsp_to_hardware(rsp_hex): return self._deserialize(
            EmliteResponse.ObjectIdType.hardware_version, rsp_hex).hardware.replace('\u0000', '').strip()

        self.assertEqual(rsp_to_hardware('36437720'), '6Cw')
        self.assertEqual(rsp_to_hardware('36430000'), '6C')
        self.assertEqual(rsp_to_hardware('33417720'), '3Aw')

    def test_time(self):
        response_hex = "17080615000100"
        response = self._deserialize(
            EmliteResponse.ObjectIdType.time, response_hex)
        self.assertEqual(response.year, 23)
        self.assertEqual(response.month, 8)
        self.assertEqual(response.date, 6)
        self.assertEqual(response.hour, 21)
        self.assertEqual(response.minute, 0)
        self.assertEqual(response.second, 1)
        self.assertEqual(response.day_of_week,
                         EmliteResponse.DayOfWeekType.monday)

    def test_csq(self):
        # signal 16 / operator 'O2'
        response = self._deserialize(
            EmliteResponse.ObjectIdType.csq_net_op, '30')
        self.assertEqual(response.csq, 16)

        # signal 12 / operator 'vodafone'
        response = self._deserialize(
            EmliteResponse.ObjectIdType.csq_net_op, '4c')
        self.assertEqual(response.csq, 12)

        # signal 16 / operator 'O2'
        response = self._deserialize(
            EmliteResponse.ObjectIdType.csq_net_op, '29')
        self.assertEqual(response.csq, 9)

    def test_prepay_flag(self):
        response = self._deserialize(
            EmliteResponse.ObjectIdType.prepay_enabled_flag, '00')
        self.assertEqual(response.enabled_flag, 0)
        response = self._deserialize(
            EmliteResponse.ObjectIdType.prepay_enabled_flag, '01')
        self.assertEqual(response.enabled_flag, 1)

    def test_prepay_balance(self):
        response = self._deserialize(
            EmliteResponse.ObjectIdType.prepay_balance, 'E0930400')
        self.assertEqual(response.balance, 300000)  # 3.00 GBP
        response = self._deserialize(
            EmliteResponse.ObjectIdType.prepay_balance, '30630300')
        self.assertEqual(response.balance, 222000)  # 2.22 GBP
        response = self._deserialize(
            EmliteResponse.ObjectIdType.prepay_balance, 'c07a03fe')
        self.assertEqual(response.balance, -33326400)  # -333.264 GBP

    def test_instantaneous_voltage(self):
        response = self._deserialize(
            EmliteResponse.ObjectIdType.instantaneous_voltage, '5209')
        self.assertEqual(response.voltage, 2386)  # 238.6

    def test_threephase_voltage(self):
        response = self._deserialize(
            EmliteResponse.ObjectIdType.three_phase_instantaneous_voltage_l1, '5209')
        self.assertEqual(response.voltage, 2386)  # 238.6
        response = self._deserialize(
            EmliteResponse.ObjectIdType.three_phase_instantaneous_voltage_l2, '4C09')
        self.assertEqual(response.voltage, 2380)  # 238.0
        response = self._deserialize(
            EmliteResponse.ObjectIdType.three_phase_instantaneous_voltage_l3, '5D09')
        self.assertEqual(response.voltage, 2397)  # 239.7

    def test_prepay_token_send(self):
        # add credit token
        #
        # see screen shot "Pre-pay - Screen - Payment Code - Generate Add Code.jpg"
        # response payload is empty:
        response_hex = ""
        response = self._deserialize(
            EmliteResponse.ObjectIdType.prepay_token_send, response_hex)
        # nothing to check except that we got a response
        self.assertIsNotNone(response)

    def _deserialize(self, object_id, response_hex):
        rsp_bytes = bytearray.fromhex(response_hex)
        data = EmliteResponse(len(rsp_bytes), object_id,
                              KaitaiStream(BytesIO(rsp_bytes)))
        data._read()
        return data.response

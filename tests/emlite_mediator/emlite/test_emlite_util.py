import unittest
from datetime import datetime

from emlite_mediator.emlite.emlite_util import (
    emop_object_id_encode,
    emop_timestamp_decode,
    emop_timestamp_encode,
)
from emlite_mediator.emlite.messages.emlite_object_id_enum import ObjectIdEnum

leap_year_seconds = 366 * 24 * 60 * 60


class TestEmliteUtil(unittest.TestCase):
    def test_emop_timestamp_encode(self):
        self.assertEqual(
            emop_timestamp_encode(datetime(2001, 1, 1, 0, 0, 0)),
            leap_year_seconds,
        )

    def test_emop_timestamp_decode(self):
        self.assertEqual(
            emop_timestamp_decode(leap_year_seconds),
            datetime(2001, 1, 1, 0, 0, 0),
        )

    def test_emop_object_id_encode(self):
        self.assertEqual(
            emop_object_id_encode(ObjectIdEnum.serial).hex(),
            "600100",
        )
        self.assertEqual(
            emop_object_id_encode(ObjectIdEnum.prepay_enabled_flag).hex(),
            "ffff0d",
        )

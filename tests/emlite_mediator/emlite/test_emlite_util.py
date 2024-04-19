import unittest
from datetime import datetime
from decimal import Decimal

from emlite_mediator.emlite.emlite_util import (
    emop_datetime_to_epoch_seconds,
    emop_encode_amount_as_u4le_rec,
    emop_encode_object_id,
    emop_encode_timestamp_as_u4le_rec,
    emop_epoch_seconds_to_datetime,
    emop_scale_price_amount,
)
from emlite_mediator.emlite.messages.emlite_object_id_enum import ObjectIdEnum

leap_year_seconds = 366 * 24 * 60 * 60


class TestEmliteUtil(unittest.TestCase):
    def test_emop_datetime_to_epoch_seconds(self):
        seconds = emop_datetime_to_epoch_seconds(datetime(2001, 1, 1, 0, 0, 0))
        self.assertEqual(
            seconds,
            leap_year_seconds,
        )
        self.assertIsInstance(seconds, int)

    def test_emop_epoch_seconds_to_datetime(self):
        self.assertEqual(
            emop_epoch_seconds_to_datetime(leap_year_seconds),
            datetime(2001, 1, 1, 0, 0, 0),
        )

    def test_emop_encode_object_id(self):
        self.assertEqual(
            emop_encode_object_id(ObjectIdEnum.serial).hex(),
            "600100",
        )
        self.assertEqual(
            emop_encode_object_id(ObjectIdEnum.prepay_enabled_flag).hex(),
            "ffff0d",
        )

    def test_emop_scale_price_amount(self):
        self.assertEqual(emop_scale_price_amount(Decimal(76500)), Decimal("0.765"))

    def test_emop_encode_timestamp_as_u4le_rec(self):
        self.assertEqual(
            emop_encode_timestamp_as_u4le_rec(datetime(2024, 2, 29, 12, 34, 56)).hex(),
            "7036732d",
        )

    def test_emop_encode_amount_as_u4le_rec(self):
        self.assertEqual(
            emop_encode_amount_as_u4le_rec(Decimal("0.07650")).hex(),
            "e21d0000",
        )

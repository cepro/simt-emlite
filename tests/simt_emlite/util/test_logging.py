import unittest

from simt_emlite.util.logging import logger_module_name, path_to_package_and_module

file_path = "/mediator/emlite-mediator/simt_emlite/mediator/grpc/server.py"
expected_package = "simt_emlite.mediator.grpc.server"


class TestLogging(unittest.TestCase):
    def test_path_to_package_and_module(self):
        self.assertEqual(expected_package, path_to_package_and_module(file_path))

    def test_logger_module_name(self):
        self.assertEqual(
            expected_package,
            logger_module_name("__main__", file_path),
            "builds package from file_path when __name__ is __main__",
        )
        self.assertEqual(
            "__main__",
            logger_module_name("__main__"),
            "when no file_path given just return __name__",
        )
        self.assertEqual(
            "a.b.c",
            logger_module_name("a.b.c", file_path),
            "when __name__ is not __main__ return it and ignore given file_path",
        )

def run_tests():
    import unittest

    loader = unittest.TestLoader()
    suite = loader.discover(".", pattern="test*.py")
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    if not result.wasSuccessful():
        raise Exception("Tests failed")


def run_linter():
    import subprocess

    completed_process = subprocess.run(["ruff", "check", "."], check=True, text=True)
    print(f"stderr [{completed_process.stderr}")
    print(f"stdout [{completed_process.stdout}")

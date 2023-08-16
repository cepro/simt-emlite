from .run_jobs_base import RunJobForAllMeters


def filter_hardware(meter): return meter['hardware'] == 'C1.w'


if __name__ == '__main__':
    runner = RunJobForAllMeters('meter_prepay_sync', filter_hardware)
    runner.run()

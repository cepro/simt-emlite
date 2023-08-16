from .run_jobs_manage_mediators_base import RunJobForAllMeters


def filter_hardware(meter): return meter['hardware'] == 'C1.w'


if __name__ == '__main__':
    runner = RunJobForAllMeters('meter_prepay_sync', 20, filter_hardware)
    runner.run()

from .run_jobs_base import RunJobForAllMeters

if __name__ == '__main__':
    runner = RunJobForAllMeters('meter_csq_sync')
    runner.run()

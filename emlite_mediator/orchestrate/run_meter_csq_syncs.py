from .run_jobs_manage_mediators_base import RunJobForAllMeters

if __name__ == '__main__':
    runner = RunJobForAllMeters('meter_csq_sync', 20)
    runner.run()

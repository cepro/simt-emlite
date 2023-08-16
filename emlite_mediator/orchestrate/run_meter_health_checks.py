from .run_jobs_base import RunJobForAllMeters

if __name__ == '__main__':
    runner = RunJobForAllMeters('meter_health_check')
    runner.run()

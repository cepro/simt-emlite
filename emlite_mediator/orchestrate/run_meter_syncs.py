import argparse

from .run_jobs_base import RunJobForAllMeters

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--freq',
                        required=True,
                        action='store',
                        choices=['hourly', 'daily', '12hourly'],
                        help='Sync meter_metrics that have this frequency')
    args = parser.parse_args()

    freq = args.freq

    def filter_one(meter): return meter['ip_address'] == '100.79.244.33'
    
    runner = RunJobForAllMeters('meter_sync', run_frequency=freq, filter_fn=filter_one)
    runner.run()

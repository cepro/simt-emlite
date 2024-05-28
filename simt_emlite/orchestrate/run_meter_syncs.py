import argparse

from .run_jobs_base import RunJobForAllMeters

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--freq",
        required=True,
        action="store",
        choices=["hourly", "daily", "12hourly"],
        help="Sync meter_metrics that have this frequency",
    )
    args = parser.parse_args()

    freq = args.freq

    runner = RunJobForAllMeters("meter_sync", run_frequency=freq)
    runner.run()

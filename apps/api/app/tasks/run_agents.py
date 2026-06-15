import argparse
import time

from app.services.opportunity_service import OpportunityService


def run_once() -> None:
    run = OpportunityService().run_agents()
    print(f"agent_run={run.run_id} status={run.status} opportunities={len(run.opportunities)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run MagneticSphere AI agents on a schedule.")
    parser.add_argument("--interval", type=int, default=1800, help="Seconds between runs.")
    parser.add_argument("--once", action="store_true", help="Run once and exit.")
    args = parser.parse_args()

    if args.once:
        run_once()
        return

    while True:
        run_once()
        time.sleep(args.interval)


if __name__ == "__main__":
    main()


"""`hse-seed`: generate the lab's traces once, then replay them into every attendee workspace."""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(prog="hse-seed", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("generate", help="Run the v0 agent over the fixtures and save its traces")
    commands.add_parser("upload", help="Replay the saved traces and feedback into each workspace")
    args = parser.parse_args()
    raise NotImplementedError(f"hse-seed {args.command} is not built yet")
